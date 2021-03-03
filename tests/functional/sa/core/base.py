from typing import Dict, Mapping, Optional
from uuid import UUID

from aiohttp.test_utils import AioHTTPTestCase
from aiohttp.web_app import Application
from sqlalchemy import desc, select
from sqlalchemy.engine import Row

from aiohttp_rest_framework.db.sa import SAManager
from aiohttp_rest_framework.settings import get_global_config
from tests.functional.sa.core.utils import create_data_fixtures
from tests.functional.sa.utils import create_tables, drop_tables
from tests.test_app.sa.core.app import create_application
from tests.test_app.sa.core.config import DB_URL
from tests.test_app.sa.core.models import SAField, User, meta
from tests.utils import async_session


class BaseTestCase(AioHTTPTestCase):
    rest_config: Optional[Mapping] = None

    async def get_application(self) -> Application:
        return create_application(DB_URL, self.rest_config)

    async def setUpAsync(self) -> None:
        await drop_tables(meta, DB_URL)
        await create_tables(meta, DB_URL)
        await create_data_fixtures(DB_URL)
        self.user = await self.get_test_user()
        self.sa_instance = await self.get_sa_instance()

    async def tearDownAsync(self) -> None:
        await drop_tables(meta, DB_URL)

    async def get_test_user(self) -> Row:
        async with async_session(DB_URL) as session:
            query = select(User).limit(1)
            result = await session.execute(query)
            user = result.one()
            return user

    async def get_sa_instance(self) -> Row:
        async with async_session(DB_URL) as session:
            query = select(SAField).limit(1)
            result = await session.execute(query)
            inst = result.one()
            return inst

    async def get_last_created_user(self) -> Row:
        async with async_session(DB_URL) as session:
            query = select(User).order_by(desc(User.c.created_at))
            result = await session.execute(query)
            user = result.first()
            return user

    async def get_user_by_id(self, user_id: UUID) -> Row:
        async with async_session(DB_URL) as session:
            query = select(User).where(User.c.id == user_id)
            result = await session.execute(query)
            user = result.first()
            return user

    def get_test_user_data(self) -> Dict[str, str]:
        return {
            "name": "Test User",
            "email": "test@test.com",
            "phone": "+123456789",
            "password": "test_pwd"
        }

    async def get_db_manager(self, model) -> SAManager:
        return SAManager(get_global_config(), model)
