# aiohttp-rest-framework

[![Codecov](https://img.shields.io/codecov/c/github/ckkz-it/aiohttp-rest-framework)](https://codecov.io/gh/ckkz-it/aiohttp-rest-framework)
[![PyPI](https://img.shields.io/pypi/v/aiohttp-rest-framework)](https://pypi.org/project/aiohttp-rest-framework/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/aiohttp-rest-framework)](https://pypi.org/project/aiohttp-rest-framework/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aiohttp-rest-framework)](https://pypi.org/project/aiohttp-rest-framework/)
---

Fully asynchronous rest framework for aiohttp web server, inspired by [Django Rest Framework](https://www.django-rest-framework.org) (DRF), powered by [marshmallow](https://github.com/marshmallow-code/marshmallow) and [SQLAlchemy](https://www.sqlalchemy.org).

Currently supports only combination of postgres (thanks to [databases](https://github.com/encode/databases) library) and sqlalchemy (core). MySQL support will be shipped in the near future.

## Installation

```bash
pip install aiohttp-rest-framework
```

## Usage example

Consider we have the following SQLAlchemy ORM models:

```python
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from app.utils import get_stringified_uuid

Base = declarative_base()
meta = Base.metadata


class User(Base):
    __tablename__ = "users"

    id = sa.Column(UUID, primary_key=True, default=get_stringified_uuid)
    name = sa.Column(sa.Text)
    email = sa.Column(sa.Text, nullable=False, unique=True)
    phone = sa.Column(sa.Text)
    company_id = sa.Column(sa.ForeignKey("companies.id"), nullable=True)


class Company(Base):
    __tablename__ = "companies"

    id = sa.Column(UUID, primary_key=True, default=get_stringified_uuid)
    name = sa.Column(sa.Text, nullable=False)
```

SQLAlchemy Core tables are also supported.

```python
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.utils import get_stringified_uuid

meta = sa.MetaData()

User = sa.Table(
    "users", meta,
    sa.Column("id", UUID, primary_key=True, default=get_stringified_uuid),
    sa.Column("name", sa.Text),
    sa.Column("email", sa.Text, unique=True),
    sa.Column("phone", sa.Text),
    sa.Column("company_id", sa.ForeignKey("companies.id"), nullable=True),
)

Company = sa.Table(
    "companies", meta,
    sa.Column("id", UUID, primary_key=True, default=get_stringified_uuid),
    sa.Column("name", sa.Text),
)
```

Now we can use very familiar to us from DRF serializer, built on top of marshmalow's `Schema`:

```python
from aiohttp_rest_framework import serializers

from app.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        dump_only = ("id",)
```

> Note: for more information about field declaration please refer to [marshmallow](https://github.com/marshmallow-code/marshmallow)

For SQLAlchemy ORM `ModelSerializer` supports generic typing:

```python
class UserSerializer(serializers.ModelSerializer[User]):  # <- mention `User` here
    class Meta:
        model = User
        fields = "__all__"
```

Now type hints will be available for serializers methods like `create()`, `update()`, etc.


And, finally, now we can use our serializer in class based views:

```python
from aiohttp_rest_framework import views

from app.serializers import UserSerializer


class UsersListCreateView(views.ListCreateAPIView):
    serializer_class = UserSerializer


class UsersRetrieveUpdateDestroyView(views.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
```

Our simple app would look like this:

```python
from aiohttp import web
from aiohttp_rest_framework import setup_rest_framework, create_connection
from aiohttp_rest_framework.utils import create_tables

from app import views, config, models


async def db_cleanup_context(app_: web.Application) -> None:
    app_["db"] = await create_connection(config.db_url)
    # in case you need to create tables in the database
    # for sqlalchemy this is the same as `meta.create_all()`, but asynchronous
    await create_tables(models.meta, app_["db"])
    yield 
    await app_["db"].dispose()


app = web.Application()
app.cleanup_ctx.append(db_cleanup_context)
app.router.add_view("/users", views.UsersListCreateView)
app.router.add_view("/users/{id}", views.UsersRetrieveUpdateDestroyView)
setup_rest_framework(app)
web.run_app(app)
```

> Note: 
> If you want to use other property than "db", in order to application work you have to specify
> `app_connection_property` in config, passing to `setup_rest_framework`.
>
> Example:
> `setup_rest_framework(app, {"app_connection_property": "custom_db_prop"})`

Mention `setup_rest_framework()` function, it is required to call it to configure framework to work with your app.
For available rest framework's config options refer to [documentation]().
For detailed aiohttp web app configuration please refer to [their docs](https://docs.aiohttp.org/en/stable/web.html).

After starting the app, we can make a `POST /users` request to create a new user.

```bash
curl -H "Content-Type: application/json" 
     -d '{
            "name": "John Doe",
            "email": "john@mail.com",
            "phone": "+123456789"
         }'
     -X POST http://localhost:8080/users
```

And get the following `HTTP 201 Response`:

```json
{
  "id": "aa392cc9-c734-44ff-9d7c-1602ecb4df2a",
  "name": "John Doe",
  "email": "john@mail.com",
  "phone": "+123456789",
  "company_id": null
}
```

Let's try to update user's company. Making `PATCH /users/aa392cc9-c734-44ff-9d7c-1602ecb4df2a` request

```bash
curl -H "Content-Type: application/json" 
     -d '{"company_id": "0413de74-d9fb-494b-ba56-b56599261fb0"}'
     -X PATCH http://localhost:8080/users/a392cc9-c734-44ff-9d7c-1602ecb4df2a
```

`HTTP 200 Response`:

```json
{
  "id": "aa392cc9-c734-44ff-9d7c-1602ecb4df2a",
  "name": "John Doe",
  "email": "john@mail.com",
  "phone": "+123456789",
  "company_id": "0413de74-d9fb-494b-ba56-b56599261fb0"
}
```

For more examples and usages please refer to [documentation]().

## Requirements

Python >= 3.6

#### Dependencies:
- aiohttp
- databases[postgresql] (actually [the fork](https://pypi.org/project/databases-extended/0.4.1/) of it with fixed sqlalchemy column defaults)
- sqlalchemy
- marshmallow

## Documentation

`setup_rest_framework(app, config)`

Config is just a simple `dict` object. Config can accept following parameters (everything is optional):
- `schema_type: str` - Specifies what combination of database and SQL toolkit to use. Currently supports only combination of SQLAlchemy and PostgreSQL.

    **Default:** `"sa"`


- `app_connection_property: str` - The property name of the database connection in your aiohttp application.

    **Default:** `"db"`.

```python
custom_db_prop = "db_conn"

async def db_cleanup_context(app_: web.Application) -> None:
    app_[custom_db_prop] = await create_connection(config.db_url)
    yield 
    await app_[custom_db_prop].dispose()

app = web.Application()
app.cleanup_ctx.append(db_cleanup_context)
setup_rest_framework(app, {"app_connection_property": custom_db_prop})
```


- `get_connection: Callable[[], Awaitable]` - An async callable that receive no arguments and returns database connection. You would only need it if you don't want to store your database connection in aiohttp application, then you have to provide it to `aiohttp-rest-framework` so framework can work with a database.

    **Default:** uses `app[app_connection_property]`

```python
from app.utils import create_db_connection
custom_db_prop = "db_conn"

async def get_db_connection():
    return await create_db_connection()

app = web.Application()
setup_rest_framework(app, {"get_connection": get_db_connection})
```


- `db_manager: BaseDBManager` - Specifies what database manager to use.  You would need it if you want to use custom logic in database operations (class should be inherited from `BaseDBManager` imported from `aiohttp_rest_framework.db.base`). Usually you wouldn't need it because framework's built-in `SAManager` (if you use `schema_type = "sa"`, which is default) already handles all CRUD operations and also has `execute()` method where you can pass custom sqlalchemy queries.

    **Default:** uses manager specific to the current `schema_type`.

Just a dumb useless example just to show how it can be used:
```python
from aiohttp_rest_framework.db.sa import SAManager

class SAManagerWithLogging(SAManager):
    async def execute(self, query, *args, **kwargs):
        print(query)
        return await super().execute(query, *args, **kwargs)

app = web.Application()
setup_rest_framework(app, {"db_manager": SAManagerWithLogging})
```
