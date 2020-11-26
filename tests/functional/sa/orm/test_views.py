from aiohttp.test_utils import unittest_run_loop

from tests.functional.sa.orm.base import BaseTestCase


class ViewsTestCase(BaseTestCase):
    @unittest_run_loop
    async def test_list_view(self) -> None:
        response = await self.client.get("/users")
        self.assertEqual(response.status, 200)
        data = await response.json()
        self.assertTrue(data)
        user = data[0]
        self.assertTrue(user["id"])
        self.assertIsNone(user.get("password"))

    @unittest_run_loop
    async def test_retrieve_view(self) -> None:
        response = await self.client.get(f"/users/{self.user.id}")
        self.assertEqual(response.status, 200)
        data = await response.json()
        self.assertTrue(data)
        self.assertEqual(str(self.user.id), data["id"])

    @unittest_run_loop
    async def test_create_view(self):
        response = await self.client.post("/users", json=self.get_test_user_data())
        assert response.status == 201, "invalid response status code"

        data = await response.json()
        self.assertTrue(data)
        self.assertIn("id", data)

        user = await self.get_last_created_user()
        self.assertEqual(str(user.id), data["id"])
        self.assertEqual(user.name, data["name"])
        self.assertEqual(user.phone, data["phone"])
        self.assertEqual(user.email, data["email"])

    @unittest_run_loop
    async def test_update_view(self):
        user_data = {
            "id": str(self.user.id),  # serialize uuid
            "created_at": str(self.user.created_at),  # serialize datetime,
            "name": "Updated Name",
            "email": "updated@mail.com",
            "phone": "+7346352401",
        }
        response = await self.client.put(f"/users/{self.user.id}", json=user_data)
        assert response.status == 200, "invalid response"

        response_data = await response.json()
        updated_user = await self.get_user_by_id(self.user.id)
        self.assertEqual(response_data["id"], user_data["id"])
        self.assertEqual(response_data["name"], user_data["name"])
        self.assertEqual(response_data["name"], updated_user.name)
        self.assertEqual(response_data["email"], user_data["email"])
        self.assertEqual(response_data["email"], updated_user.email)
        self.assertEqual(response_data["phone"], user_data["phone"])
        self.assertEqual(response_data["phone"], updated_user.phone)

    @unittest_run_loop
    async def test_create_with_null_value_that_must_not_be_null(self):
        test_user_data = self.get_test_user_data()
        test_user_data.pop("password")
        response = await self.client.post("/users", json=test_user_data)
        self.assertEqual(response.status, 400)
        data = await response.json()
        self.assertTrue("password" in data["error"] and "null" in data["error"])

    @unittest_run_loop
    async def test_invalid_json(self):
        user_data = '{"name": "My Name", "email": "test@email.com", "phone": "123",}'
        response = await self.client.post("/users", data=user_data, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status, 400)
        data = await response.json()
        self.assertEqual(data["error"], "invalid json")

    @unittest_run_loop
    async def test_partial_update_view(self):
        user_data = {
            "email": "updated@mail.com",
        }
        response = await self.client.patch(f"/users/{self.user.id}", json=user_data)
        assert response.status == 200, "invalid response"

        response_data = await response.json()
        updated_user = await self.get_user_by_id(self.user.id)
        self.assertEqual(response_data["email"], user_data["email"])
        self.assertEqual(response_data["email"], updated_user.email)
        self.assertNotEqual(updated_user.email, self.user.email)
        self.assertEqual(response_data["name"], self.user.name)

    @unittest_run_loop
    async def test_update_non_existent_user(self):
        response = await self.client.put("/users/123", json={})
        self.assertEqual(response.status, 404)

    @unittest_run_loop
    async def test_destroy_view(self):
        response = await self.client.delete(f"/users/{self.user.id}")
        assert response.status == 204, "invalid response"

        user = await self.get_user_by_id(self.user.id)
        self.assertIsNone(user)

    @unittest_run_loop
    async def test_destroy_non_existent_user(self):
        response = await self.client.delete("/users/123")
        self.assertEqual(response.status, 404)
