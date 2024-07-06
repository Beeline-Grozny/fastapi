import asyncio
from datetime import datetime
import uuid
from src.prorab.models import Task, Report
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import SessionFactory
from sqlalchemy import select
from typing import List



async def create_mock_data(session: AsyncSession):
    # Создание задач с зависимостями

    task1_id = uuid.uuid4()
    task1 = Task(
        id=task1_id,
        name="Task 1",
        start=datetime(2020, 1, 1),
        end=datetime(2020, 1, 2),
        type="task",
        progress=45,
        is_disabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    task2_id = uuid.uuid4()
    task2 = Task(
        id=task2_id,
        name="Task 2",
        start=datetime(2020, 1, 3),
        end=datetime(2020, 1, 4),
        type="task",
        progress=30,
        is_disabled=False,
        depends_on=str(task1_id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    task3_id = uuid.uuid4()
    task3 = Task(
        id=task3_id,
        name="Task 3",
        start=datetime(2020, 1, 5),
        end=datetime(2020, 1, 6),
        type="task",
        progress=60,
        is_disabled=False,
        depends_on=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Создание отчетов связанных с задачами


    report1 = Report(
        title="Report for Task 1",
        empoyee="user123",
        location="Office A",
        status="empty",
        task=str(task1.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    report2 = Report(
        title="Report for Task 2",
        empoyee="user456",
        location="Office B",
        status="in_progress",
        task=str(task2.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    report3 = Report(
        title="Report for Task 3",
        empoyee="user789",
        location="Office C",
        status="completed",
        task = str(task3.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),)
    session.add_all([task1, task2, task3, report1, report2, report3])
    await session.commit()

if __name__ == "__main__":
    session = SessionFactory()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_mock_data(session))