
from sqlalchemy.orm import Session

from backend.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.database.models import User


def register_user(db: Session, name: str, email: str, password: str):
    email = email.strip().lower()
    name = name.strip()

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise ValueError("An account with this email already exists.")

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, email: str, password: str):
    email = email.strip().lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        return None

    return user


def create_user_token(user: User) -> str:
    return create_access_token(user.id)
