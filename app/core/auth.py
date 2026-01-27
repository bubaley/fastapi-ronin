from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fastapi_ronin.state import BaseStateManager


class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: Optional[HTTPAuthorizationCredentials] = None
        try:
            credentials = await super().__call__(request)
        except HTTPException:
            # No credentials provided — allow anonymous
            return None
        return credentials


async def get_current_user(token: Optional[HTTPAuthorizationCredentials] = Depends(OptionalHTTPBearer())):
    if token and token.credentials == 'token':  # Your logic
        user = {'id': 1, 'username': 'john'}
        BaseStateManager.set_user(user)
        return user
    return None
