from datetime import datetime

from sqlalchemy import insert, select, update

from aiohttp_rest_framework.fields import Interval
from tests.functional.sa.utils import get_fixtures_data
from tests.test_app.sa.core import models
from tests.utils import async_engine_connection


async def create_data_fixtures(db_url: str):
    data = get_fixtures_data()
    async with async_engine_connection(db_url) as conn:
        for class_name, table_data in data.items():
            table = getattr(models, class_name)
            for td in table_data:
                if "Date" in td:
                    td["Date"] = datetime.strptime(td["Date"], "%Y-%m-%d").date()
                if "DateTime" in td:
                    td["DateTime"] = datetime.strptime(td["DateTime"], "%Y-%m-%d %H:%M:%S")
                if "Time" in td:
                    td["Time"] = datetime.strptime(td["Time"], "%H:%M:%S")
                if "Interval" in td:
                    td["Interval"] = Interval().deserialize(td["Interval"])
                await conn.execute(insert(table).values(td))

        company_query = select(models.Company.c.id).limit(1)
        result = await conn.execute(company_query)
        company = result.first()
        await conn.execute(update(models.User).values({"company_id": company["id"]}))
