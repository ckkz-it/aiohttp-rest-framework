import uuid

from aiohttp.test_utils import unittest_run_loop

from tests.functional.sa.orm.base import BaseTestCase


class ExceptionsTestCase(BaseTestCase):
    @unittest_run_loop
    async def test_validation_error_exception(self) -> None:
        user_data = {
            "phone": "1111",
        }
        response = await self.client.put(f"/users/{self.user.id}", json=user_data)
        self.assertEqual(response.status, 400)
        self.assertEqual(response.content_type, "application/json")
        err = await response.json()
        self.assertIn("email", err, "wrong error caught")

    @unittest_run_loop
    async def test_not_found_exception(self) -> None:
        for non_existing_id in [uuid.uuid4(), "123", "non_existing"]:
            response = await self.client.get(f"/users/{non_existing_id}")
            self.assertEqual(response.status, 404)
            self.assertEqual(response.content_type, "application/json")
