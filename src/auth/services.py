from src.auth import models
from sqlalchemy.ext.asyncio import AsyncSession
import uuid


async def set_group_to_user(db: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID):
    user_group = models.GroupUser(user_id=user_id, group_id=group_id)
    db.add(user_group)
    await db.commit()
    return user_group
async def set_role_to_group(db: AsyncSession, role_id: uuid.UUID, group_id: uuid.UUID):
    role_group = models.RoleGroup(role_id=role_id, group_id=group_id)
    db.add(role_group)
    await db.commit()
    return role_group
async def add_group(db: AsyncSession, name: str):
    group = models.Group(name=name)
    db.add(group)
    await db.commit()
    return group

async def add_role(db: AsyncSession, name: str):
    role = models.Role(name=name)
    db.add(role)
    await db.commit()
    return role



async def add_permission(db: AsyncSession, name: str, description: str):
    permission = models.Permission(name=name, description=description)
    db.add(permission)
    result = await db.commit()
    return


