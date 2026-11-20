from passlib.context import CryptContext
from jose import jwt

SECRET_KEY = "datadock-ai-secret-key-change-later"

ALGORITHM = "HS256"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(user_id: int):

    data = {
        "user_id": user_id
    }

    return jwt.encode(
        data,
        SECRET_KEY,
        algorithm=ALGORITHM
    ) 
