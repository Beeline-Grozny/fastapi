import uuid
from typing import Annotated
from datetime import datetime
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from fastapi import status, APIRouter, HTTPException, Depends, BackgroundTasks, Response, Cookie, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import ValidationError

from src.auth import services
from src.auth.models import Role, RoleGroup, Group
from src.dependencies import get_db, get_current_user, oauth2_scheme
from src.auth import schemas, models
from src.auth.core.hash import get_password_hash, verify_password
from src.auth.core.jwt import (
    create_token_pair,
    refresh_token_state,
    decode_access_token,
    add_refresh_token_cookie,
    SUB,
    JTI,
    EXP,
    JWTError,
)
from src.auth.exceptions import BadRequestException, NotFoundException, ForbiddenException

router = APIRouter(
    prefix="/auth", tags=["auth"]
)
router2 = APIRouter(
    prefix="/usermod", tags=["usermod"]
)


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
async def get_roles_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> list[Role]:
    query = select(Role).join(RoleGroup, RoleGroup.role_id == Role.id).join(
        Group, Group.id == RoleGroup.group_id
    ).where(Group.id == user_id)
    result = await db.execute(query)
    roles = result.scalars().all()
    return roles


@router.post("/register", response_model=schemas.User)
async def register(
        data: schemas.UserRegister,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
):
    user = await models.User.find_by_email(db=db, email=data.email)
    if user:
        raise HTTPException(status_code=400, detail="Email has already registered")

    # hashing password
    user_data = data.dict(exclude={"confirmPassword"})
    user_data["password"] = get_password_hash(user_data["password"])

    # save user to db
    user = models.User(**user_data)
    user.is_active = True
    await user.save(db=db)
    user_schema = schemas.User.from_orm(user)
    return user_schema


@router.post("/login")
async def login(

        data: schemas.UserLogin,
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db),

):


    user = await models.User.authenticate(
        db=db, email=data.email, password=data.password
    )

    if not user:
        raise BadRequestException(detail="Incorrect email or password")

    if not user.is_active:
        raise ForbiddenException()

    user = schemas.User.from_orm(user)

    token_pair = await create_token_pair(user=user, db=db)

    add_refresh_token_cookie(response=response, token=token_pair.refresh.token)

    return {"token": token_pair.access.token}


@router.get("/refresh")
async def refresh(refresh: Annotated[str | None, Cookie()] = None):
    print(refresh)
    if not refresh:
        raise BadRequestException(detail="refresh token required")
    return refresh_token_state(token=refresh)


@router.post("/logout", response_model=schemas.SuccessResponseScheme)
async def logout(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: AsyncSession = Depends(get_db),
):
    payload = await decode_access_token(token=token, db=db)
    black_listed = models.BlackListToken(
        id=payload[JTI], expire=datetime.utcfromtimestamp(payload[EXP])
    )
    await black_listed.save(db=db)

    return {"msg": "Succesfully logout"}


@router.get("/me", response_model=schemas.UserCredentials)
async def me(
        request: Request,
        token: Annotated[str, Depends(oauth2_scheme)],
        db: AsyncSession = Depends(get_db),
):
    token_data = await decode_access_token(token=token, db=db)
    print(request.cookies)
    return await models.User.find_by_id(db=db, id=token_data[SUB])

@router.get("/users")
async def get_users(
        db: AsyncSession = Depends(get_db),
):
    query = select(models.User)
    result = await db.execute(query)
    users = result.scalars().all()

    # Преобразование результатов запроса в Pydantic модели
    users_data = [schemas.UserCredentials.from_orm(user) for user in users]
    return users_data



#router2 ----------------------------------------------------------------------------

@router2.patch("/change_credits")
async def change_credits(
        token: Annotated[str, Depends(oauth2_scheme)],
        UserFull: schemas.UserFull,
        db: AsyncSession = Depends(get_db),
):
    token_data = await decode_access_token(token=token, db=db)
    user = await models.User.find_by_id(db=db, id=token_data[SUB])
    user.credits = UserFull.credits
    await user.save(db=db)
    return {"msg": "Succesfully change credits"}


@router2.post("/add_permission")
async def add_permissions(
        db: AsyncSession = Depends(get_db),
        permission: schemas.Permission = Depends(),
):
    await services.add_permission(name=permission.name, description=permission.description, db=db)
    return {"msg": "Succesfully add permission"}


@router2.post("/add_role")
async def add_role(
        db: AsyncSession = Depends(get_db),
        role: schemas.Role = Depends(),
):
    await services.add_role(name=role.name, db=db)
    return {"msg": "Succesfully add role"}


@router2.post("/add_group")
async def add_group(
        db: AsyncSession = Depends(get_db),
        group: schemas.Group = Depends(),
):
    await services.add_group(name=group.name, db=db)
    return {"msg": "Succesfully add group"}


@router2.post("/add_role_to_group")
async def add_role_to_group(
        db: AsyncSession = Depends(get_db),
        role_id: uuid.UUID = Body(...),
        group_id: uuid.UUID = Body(...),
):
    await services.set_role_to_group(db=db, role_id=role_id, group_id=group_id)
    return {"msg": "Succesfully add role to group"}


@router2.post("/add_group_to_user")
async def add_group_to_user(
        db: AsyncSession = Depends(get_db),
        user_id: uuid.UUID = Body(...),
        group_id: uuid.UUID = Body(...),
):
    await services.set_group_to_user(db=db, user_id=user_id, group_id=group_id)
    return {"msg": "Succesfully add group to user"}




