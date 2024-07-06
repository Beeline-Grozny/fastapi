import uuid
from datetime import timedelta, datetime, timezone
from sqlalchemy import select

from jose import JWTError, jwt
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src import config
from src.auth.schemas import User, TokenPair, JwtTokenSchema
from src.auth.exceptions import AuthFailedException
from src.auth.models import BlackListToken, Group, RoleGroup, Role, User, GroupUser



REFRESH_COOKIE_NAME = "refresh"
SUB = "sub"
EXP = "exp"
IAT = "iat"
JTI = "jti"
ROLES = "roles"

async def get_roles_by_user_id(user_id: uuid.UUID, db: AsyncSession) -> list[Role]:
    # query = select(Role).join(RoleGroup, RoleGroup.role_id == Role.id).join(
    #     Group, Group.id == RoleGroup.group_id
    # ).join(GroupUser, GroupUser.group_id == Group.id).join(User, User.id == GroupUser.user_id).where(User.id == user_id)
    query = select(Role).join(RoleGroup, RoleGroup.role_name == Role.id).join(
        Group, Group.id == RoleGroup.group_name
    ).join(GroupUser, GroupUser.group_name == Group.id).join(User, User.id == GroupUser.user_id).where(User.id == user_id)
    result = await db.execute(query)
    roles = result.scalars().all()
    return roles
def _create_access_token(payload: dict, minutes: int | None = None) -> JwtTokenSchema:
    expire = datetime.utcnow() + timedelta(
        minutes=minutes or config.ACCESS_TOKEN_EXPIRES_MINUTES
    )

    payload[EXP] = expire

    token = JwtTokenSchema(
        token=jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM),
        payload=payload,
        expire=expire,
    )

    return token


def _create_refresh_token(payload: dict) -> JwtTokenSchema:
    expire = datetime.utcnow() + timedelta(minutes=config.REFRESH_TOKEN_EXPIRES_MINUTES)

    payload[EXP] = expire

    token = JwtTokenSchema(
        token=jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM),
        expire=expire,
        payload=payload,
    )

    return token


async def create_token_pair(user: User, db: AsyncSession) -> TokenPair:
    roles = await get_roles_by_user_id(user_id=user.id, db=db)
    print(roles)
    payload = {SUB: str(user.id), JTI: str(uuid.uuid4()), IAT: datetime.utcnow(), ROLES: [r.name for r in roles]}

    return TokenPair(
        access=_create_access_token(payload={**payload}),
        refresh=_create_refresh_token(payload={**payload}),
    )


async def decode_access_token(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        # black_list_token = await BlackListToken.find_by_id(db=db, id=payload[JTI])
        # if black_list_token:
        #     raise JWTError("Token is blacklisted")
    except JWTError as ex:
        print(str(ex))
        raise AuthFailedException()

    return payload


def refresh_token_state(token: str):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except JWTError as ex:
        print(str(ex))
        raise AuthFailedException()

    return {"token": _create_access_token(payload=payload).token}


async def mail_token(user: User, db: AsyncSession):
    """Return 2 hour lifetime access_token"""
    roles = await get_roles_by_user_id(user_id=user.id, db=db)
    payload = {SUB: str(user.id), JTI: str(uuid.uuid4()), IAT: datetime.utcnow(), ROLES: [r.name for r in roles]}
    return _create_access_token(payload=payload, minutes=2 * 60).token


def add_refresh_token_cookie(response: Response, token: str):
    exp = datetime.utcnow() + timedelta(minutes=config.REFRESH_TOKEN_EXPIRES_MINUTES)
    exp.replace(tzinfo=timezone.utc)

    response.set_cookie(
        key="refresh",
        value=token,
        expires=int(exp.timestamp()),
        httponly=True,
        samesite='lax',
    )