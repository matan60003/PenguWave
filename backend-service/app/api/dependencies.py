from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.database.models import User
from app.database.repositories import UserRepository
from app.core import security

security_scheme = HTTPBearer()


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    token = credentials.credentials
    payload = security.decode_access_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_role(allowed_roles: list[str]):
    def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized (wrong role)",
            )
        return current_user

    return dependency


require_admin = require_role(["admin"])
