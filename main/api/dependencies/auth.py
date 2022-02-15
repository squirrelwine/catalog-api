from typing import Callable, Union

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from main.api.dependencies.database import get_database_session
from main.api.exception import ForbiddenException, UnauthorizedException
from main.models.category import CategoryModel
from main.models.item import ItemModel
from main.models.user import UserModel
from main.services.auth import decode_access_token
from main.services.user import get_user_by_id


async def require_authenticated_user(
    session: AsyncSession = Depends(get_database_session),
    http_credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> UserModel:
    if http_credentials is None:
        raise UnauthorizedException()

    try:
        access_token = http_credentials.credentials
        payload = decode_access_token(access_token)
    except JWTError:
        raise UnauthorizedException()

    user_id = int(payload.get("sub"))
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise UnauthorizedException()

    return user


def require_ownership(require_object_function: Callable) -> Callable:
    def verify_ownership(
        possession: Union[CategoryModel, ItemModel] = Depends(require_object_function),
        user: UserModel = Depends(require_authenticated_user),
    ) -> None:
        if possession.user_id != user.id:
            raise ForbiddenException("User does not have permission to perform this action")

    return verify_ownership
