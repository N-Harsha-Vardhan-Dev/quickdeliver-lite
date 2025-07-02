
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.utils.security import SECRET_KEY, ALGORITHM  # Use same values for signing and decoding

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")
            
            token = credentials.credentials
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                return payload  # this will be available in routes
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token expired")
            except jwt.InvalidTokenError:
                raise HTTPException(status_code=403, detail="Invalid token")
        else:
            raise HTTPException(status_code=403, detail="Authorization token missing")
