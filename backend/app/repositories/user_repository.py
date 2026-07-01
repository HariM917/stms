"""
User repository — async CRUD operations for User model.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.user import User


async def create_user(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    password_hash: str,
    role: str = "user",
) -> User:
    """Create a new user and return the ORM instance."""
    user = User(name=name, email=email, password_hash=password_hash, role=role)
    db.add(user)
    await db.flush()  # Populate id/defaults without committing
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Look up a user by primary key."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(
    db: AsyncSession,
    user: User,
    **fields,
) -> User:
    """Update arbitrary fields on a user instance."""
    for key, value in fields.items():
        if hasattr(user, key):
            setattr(user, key, value)
    await db.flush()
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    """Delete a user (cascades to sessions and reports)."""
    await db.delete(user)
    await db.flush()


async def list_users(
    db: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[User]:
    """Return a paginated list of users."""
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
