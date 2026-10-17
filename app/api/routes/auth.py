import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.db.database import get_db
from app.db.models import Organization, OrganizationMembership, RevokedToken, User
from app.schemas.auth import RefreshTokenRequest, TokenResponse, UserLoginRequest, UserPublic, UserRegisterRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)) -> User:
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists.")

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=get_password_hash(payload.password),
        is_active=True,
    )
    org = Organization(name=f"{payload.full_name.strip()}'s Workspace", description="Personal workspace", owner_id=0)
    db.add(user)
    db.flush()
    org.owner_id = user.id
    db.add(org)
    db.flush()
    db.add(OrganizationMembership(organization_id=org.id, user_id=user.id, role="admin"))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    access_jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())
    access_token = create_access_token(str(user.id), extra={"jti": access_jti})
    refresh_token = create_refresh_token(str(user.id), extra={"jti": refresh_jti})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> dict:
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.") from exc
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token type is invalid.")
    if decoded.get("jti"):
        revoked = db.query(RevokedToken).filter(RevokedToken.jti == decoded["jti"]).first()
        if revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked.")
    user_id = int(decoded["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists.")
    access_jti = str(uuid.uuid4())
    new_access = create_access_token(str(user.id), extra={"jti": access_jti})
    new_refresh = create_refresh_token(str(user.id), extra={"jti": str(uuid.uuid4())})
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer "):
        return {"status": "logged_out"}
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        return {"status": "logged_out"}
    jti = payload.get("jti")
    if jti and not db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        db.add(RevokedToken(jti=jti))
        db.commit()
    return {"status": "logged_out"}
