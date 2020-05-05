import asyncio

import pytest
from aiopg.sa.result import RowProxy

from aiohttp_rest_framework import MultipleObjectsReturned, ObjectNotFound
from aiohttp_rest_framework.db import AioPGSAService
from tests import models
from tests.aiopg_sa.utils import (
    create_data_fixtures,
    create_pg_db,
    create_tables,
    drop_pg_db,
    drop_tables,
    get_async_engine,
)
from tests.config import db


def setup_module():
    create_pg_db(db_name=db["database"])


def teardown_module():
    drop_pg_db(db_name=db["database"])


def setup_function():
    create_tables()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_data_fixtures())
    loop.close()


def teardown_function():
    drop_tables()


@pytest.fixture
async def get_db_service():
    async def _get_service(model):
        connection = await get_async_engine()
        return AioPGSAService(connection, model)

    return _get_service


async def test_db_get(get_db_service, user: RowProxy):
    service: AioPGSAService = await get_db_service(models.users)
    user_from_db = await service.get(id=user.id)
    assert user_from_db is not None
    assert user_from_db.id == user.id


@pytest.mark.run_loop
async def test_db_all(get_db_service):
    service: AioPGSAService = await get_db_service(models.users)
    users_from_db = await service.all()
    assert isinstance(users_from_db, list)
    assert len(users_from_db) > 1


async def test_db_filter(get_db_service, user: RowProxy):
    service: AioPGSAService = await get_db_service(models.users)
    users_from_db = await service.filter(id=user.id)
    assert isinstance(users_from_db, list)


@pytest.mark.run_loop
async def test_db_create(get_db_service, test_user_data):
    service: AioPGSAService = await get_db_service(models.users)
    user_from_db = await service.create(**test_user_data)
    assert user_from_db is not None
    assert user_from_db["name"] == test_user_data["name"]


async def test_db_update(get_db_service, user: RowProxy):
    service: AioPGSAService = await get_db_service(models.users)
    new_name = "New Name"
    user_from_db = await service.update(user, name=new_name)
    assert user_from_db is not None
    assert new_name == user_from_db["name"]


@pytest.mark.run_loop
async def test_db_multiple_objects_returned(get_db_service, users_fixtures):
    service: AioPGSAService = await get_db_service(models.users)
    duplicated_phone = users_fixtures[1]["phone"]
    with pytest.raises(MultipleObjectsReturned):
        await service.get(phone=duplicated_phone)


@pytest.mark.run_loop
async def test_db_object_not_found(get_db_service):
    service: AioPGSAService = await get_db_service(models.users)
    with pytest.raises(ObjectNotFound):
        await service.get(id=123)