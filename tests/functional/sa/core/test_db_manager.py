import uuid

from aiohttp.test_utils import unittest_run_loop
from sqlalchemy import and_

from aiohttp_rest_framework.exceptions import MultipleObjectsReturned, ObjectNotFound
from tests.functional.sa.core.base import BaseTestCase
from tests.functional.sa.utils import get_fixtures_by_name
from tests.test_app.sa.core import models


class DBManagerTestCase(BaseTestCase):
    @unittest_run_loop
    async def test_db_get(self) -> None:
        service = await self.get_db_manager(models.User)
        user_from_db = await service.get(whereclause=and_(models.User.c.id == self.user.id))
        self.assertIsNotNone(user_from_db)
        self.assertEqual(user_from_db.id, self.user.id)

    @unittest_run_loop
    async def test_db_all(self) -> None:
        service = await self.get_db_manager(models.User)
        users_from_db = await service.all()
        self.assertIsInstance(users_from_db, list)
        self.assertGreater(len(users_from_db), 1)

    @unittest_run_loop
    async def test_db_filter_with_operator(self):
        service = await self.get_db_manager(models.User)
        users_from_db = await service.filter({"id": self.user.id})
        self.assertIsInstance(users_from_db, list)
        self.assertEqual(users_from_db[0].id, self.user.id)

    @unittest_run_loop
    async def test_db_create(self) -> None:
        service = await self.get_db_manager(models.User)
        test_user_data = self.get_test_user_data()
        user_from_db = await service.create(test_user_data)
        self.assertIsNotNone(user_from_db)
        self.assertEqual(user_from_db.name, test_user_data["name"])

    @unittest_run_loop
    async def test_db_update(self) -> None:
        service = await self.get_db_manager(models.User)
        new_name = "New Name"
        user_from_db = await service.update(self.user, dict(name=new_name))
        self.assertIsNotNone(user_from_db)
        self.assertEqual(new_name, user_from_db.name)

    @unittest_run_loop
    async def test_db_complex_query(self):
        service = await self.get_db_manager(models.User)
        where = and_(models.User.c.id == self.user.id, models.User.c.phone == self.user.phone)
        user_from_db = await service.get(whereclause=where)
        self.assertIsNotNone(user_from_db)
        self.assertEqual(self.user["id"], user_from_db["id"])
        self.assertEqual(self.user["phone"], user_from_db["phone"])

    @unittest_run_loop
    async def test_db_object_not_found(self) -> None:
        service = await self.get_db_manager(models.User)
        with self.assertRaises(ObjectNotFound):
            await service.get(dict(id=123))

    @unittest_run_loop
    async def test_db_multiple_objects_returned(self) -> None:
        service = await self.get_db_manager(models.User)
        duplicated_phone = get_fixtures_by_name("User")[1]["phone"]
        with self.assertRaises(MultipleObjectsReturned):
            await service.get(dict(phone=duplicated_phone))

    @unittest_run_loop
    async def test_pass_invalid_uuid(self) -> None:
        service = await self.get_db_manager(models.User)
        with self.assertRaises(ObjectNotFound):
            await service.update(self.user, dict(company_id="non existent"))

    @unittest_run_loop
    async def test_pass_invalid_enum(self) -> None:
        service = await self.get_db_manager(models.SAField)
        with self.assertRaises(ObjectNotFound):
            await service.update(self.sa_instance, dict(Enum="not enum"))

    @unittest_run_loop
    async def test_foreign_key_object_not_found(self):
        service = await self.get_db_manager(models.User)
        with self.assertRaises(ObjectNotFound):
            await service.update(self.user, dict(company_id=str(uuid.uuid4())))
