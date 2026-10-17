from fastapi.testclient import TestClient


def register_user(client: TestClient, email: str, password: str = "StrongPass!123"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login_user(client: TestClient, email: str, password: str = "StrongPass!123"):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    return data["access_token"], data["refresh_token"]


def test_health_and_readiness(client: TestClient):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200


def test_register_login_and_me(client: TestClient):
    email = "alice@example.com"
    register_user(client, email)
    token, _ = login_user(client, email)
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_organization_and_project_isolation(client: TestClient):
    alice = register_user(client, "orgowner@example.com")
    bob = register_user(client, "orgmember@example.com")
    a_token, _ = login_user(client, "orgowner@example.com")
    b_token, _ = login_user(client, "orgmember@example.com")

    org_a = client.post("/api/v1/organizations", json={"name": "Org A"}, headers={"Authorization": f"Bearer {a_token}"})
    assert org_a.status_code == 201
    org_a_id = org_a.json()["id"]

    org_b = client.post("/api/v1/organizations", json={"name": "Org B"}, headers={"Authorization": f"Bearer {b_token}"})
    assert org_b.status_code == 201
    org_b_id = org_b.json()["id"]

    proj_a = client.post(f"/api/v1/projects", json={"name": "Project A", "organization_id": org_a_id}, headers={"Authorization": f"Bearer {a_token}"})
    assert proj_a.status_code == 201
    proj_b = client.post(f"/api/v1/projects", json={"name": "Project B", "organization_id": org_b_id}, headers={"Authorization": f"Bearer {b_token}"})
    assert proj_b.status_code == 201

    list_a = client.get(f"/api/v1/projects?organization_id={org_a_id}", headers={"Authorization": f"Bearer {a_token}"})
    list_b = client.get(f"/api/v1/projects?organization_id={org_b_id}", headers={"Authorization": f"Bearer {b_token}"})
    assert list_a.status_code == 200 and list_b.status_code == 200
    assert any(item["name"] == "Project A" for item in list_a.json()["items"])
    assert any(item["name"] == "Project B" for item in list_b.json()["items"])

    forbidden = client.get(f"/api/v1/projects/{proj_a.json()['id']}", headers={"Authorization": f"Bearer {b_token}"})
    assert forbidden.status_code == 403


def test_task_and_message_flow(client: TestClient):
    owner = register_user(client, "manager@example.com")
    member = register_user(client, "dev@example.com")
    owner_token, _ = login_user(client, "manager@example.com")
    member_token, _ = login_user(client, "dev@example.com")

    org = client.post("/api/v1/organizations", json={"name": "Platform Org"}, headers={"Authorization": f"Bearer {owner_token}"})
    org_id = org.json()["id"]

    project = client.post("/api/v1/projects", json={"name": "Platform Launch", "organization_id": org_id}, headers={"Authorization": f"Bearer {owner_token}"})
    project_id = project.json()["id"]

    member_endpoint = client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": 2, "role": "member", "domain": "Backend"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert member_endpoint.status_code == 201

    task = client.post(
        "/api/v1/tasks",
        json={"title": "Implement login API", "description": "Create secure login flow.", "project_id": project_id, "domain": "Backend", "priority": "high"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]

    assign = client.post(f"/api/v1/tasks/{task_id}/assign", json={"member_id": 2}, headers={"Authorization": f"Bearer {owner_token}"})
    assert assign.status_code == 200

    dispatch = client.post(
        "/api/v1/messages/dispatch",
        json={"task_id": task_id, "recipient": "dev@example.com", "content": "Please update on login endpoint."},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert dispatch.status_code == 201

    reply = client.post(
        "/api/v1/messages/simulate-reply",
        json={"task_id": task_id, "reply": "Started the API; login validation is done."},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert reply.status_code == 201


def test_ai_plan_returns_valid_schema(client: TestClient):
    email = "planner@example.com"
    register_user(client, email)
    token, _ = login_user(client, email)

    org = client.post("/api/v1/organizations", json={"name": "Planner Org"}, headers={"Authorization": f"Bearer {token}"})
    org_id = org.json()["id"]
    project = client.post("/api/v1/projects", json={"name": "Planner Project", "organization_id": org_id}, headers={"Authorization": f"Bearer {token}"})
    project_id = project.json()["id"]

    plan = client.post(
        "/api/v1/ai/plan",
        json={"goal": "Build a secure login flow and responsive UI", "project_id": project_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert plan.status_code == 200, plan.text
    payload = plan.json()
    assert "tasks" in payload
    assert len(payload["tasks"]) >= 1
    assert payload["tasks"][0]["title"]
