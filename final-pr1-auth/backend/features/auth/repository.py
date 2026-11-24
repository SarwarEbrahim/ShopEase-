"""All database queries for users."""

from sqlmodel import Session, select

from features.auth.models import User


def get_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def get_by_username(session: Session, username: str) -> User | None:
    return session.exec(select(User).where(User.username == username)).first()


def get_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def save(session: Session, user: User) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
