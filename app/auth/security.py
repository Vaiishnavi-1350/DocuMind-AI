import os

from datetime import datetime, timedelta, timezone

import jwt

from dotenv import load_dotenv

from pwdlib import PasswordHash


load_dotenv()


# =========================================
# JWT CONFIGURATION
# =========================================

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60"
    )
)


if not SECRET_KEY:

    raise ValueError(
        "JWT_SECRET_KEY is missing from .env"
    )


# =========================================
# PASSWORD HASHING
# =========================================

password_hash = PasswordHash.recommended()


# =========================================
# HASH PASSWORD
# =========================================

def hash_password(
    password: str
) -> str:

    return password_hash.hash(
        password
    )


# =========================================
# VERIFY PASSWORD
# =========================================

def verify_password(
    password: str,
    hashed_password: str
) -> bool:

    return password_hash.verify(
        password,
        hashed_password
    )


# =========================================
# CREATE ACCESS TOKEN
# =========================================

def create_access_token(
    user_id: str
) -> str:

    expire = (

        datetime.now(
            timezone.utc
        )

        + timedelta(
            minutes=
                ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )


    payload = {

        "sub": user_id,

        "exp": expire

    }


    token = jwt.encode(

        payload,

        SECRET_KEY,

        algorithm=ALGORITHM
    )


    return token


# =========================================
# DECODE ACCESS TOKEN
# =========================================

def decode_access_token(
    token: str
):

    try:

        payload = jwt.decode(

            token,

            SECRET_KEY,

            algorithms=[
                ALGORITHM
            ]
        )


        user_id = payload.get(
            "sub"
        )


        if not user_id:

            return None


        return user_id


    except jwt.PyJWTError:

        return None