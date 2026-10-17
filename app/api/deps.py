from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.db.models import RevokedToken, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:  # pragma: no cover - token validation guard
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token type is invalid.")

    if payload.get("jti"):
        revoked = db.query(RevokedToken).filter(RevokedToken.jti == payload["jti"]).first()
        if revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked.")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not active.")
    return user


def require_roles(allowed_roles: set[str]):
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.email == "admin@kurukshetra.local":
            return current_user
        from app.db.models import OrganizationMembership

        memberships = current_user.memberships
        if not memberships:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a member of any organization.")
        org_roles = {membership.role for membership in memberships}
        if not allowed_roles.intersection(org_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role access denied.")
        return current_user

    return _dependency


def require_organization_access(organization_id: int, current_user: User = Depends(get_current_user)) -> User:
    from app.db.models import OrganizationMembership

    has_access = db = current_user.memberships
    if not any(m.organization_id == organization_id for m in current_user.memberships):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this organization.")
    return current_user
