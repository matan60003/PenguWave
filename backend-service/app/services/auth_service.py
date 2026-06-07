from app.core.exceptions import AuthError
from app.schemas import schemas
from app.core import security
from app.database.repositories import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(
        self, login_data: schemas.LoginRequest
    ) -> schemas.LoginResponse:
        user = self.user_repo.get_by_email(login_data.email)

        if not user or not security.verify_password(
            login_data.password, user.hashed_password
        ):
            raise AuthError("Invalid email or password")

        token = security.create_access_token(data={"sub": user.id, "role": user.role})

        user_response = schemas.UserResponse.model_validate(user)

        return schemas.LoginResponse(
            access_token=token,
            token_type="bearer",
            token=token,
            user=user_response,
        )
