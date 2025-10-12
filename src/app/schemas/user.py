from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=256)


class UserRead(UserBase):
    id: int
    role: str  # "user" | "admin"
