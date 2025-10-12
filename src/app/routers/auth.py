from fastapi import APIRouter, HTTPException

from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead
from app.security import create_token, hash_password, verify_password
from app.storage import create_user, get_user_by_username

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead)
def register(data: UserCreate):
    if get_user_by_username(data.username):
        raise HTTPException(status_code=409, detail="username already exists")
    user = create_user(username=data.username, pwd_hash=hash_password(data.password))
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


@router.post("/login", response_model=Token)
def login(data: UserCreate):
    user = get_user_by_username(data.username)
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = create_token(sub=user["id"], role=user["role"])
    return {"access_token": token, "token_type": "bearer"}
