# aiohttp-rest-framework

[![codecov](https://codecov.io/gh/ckkz-it/aiohttp-rest-framework/branch/master/graph/badge.svg)](https://codecov.io/gh/ckkz-it/aiohttp-rest-framework)

---

Fully asynchronous rest framework for aiohttp web server, inspired by [Django Rest Framework](https://www.django-rest-framework.org) (DRF), powered by [marshmallow](https://github.com/marshmallow-code/marshmallow) and [SQLAlchemy](https://www.sqlalchemy.org).

Currently supports only combination of postgres (thanks to [aiopg](https://github.com/aio-libs/aiopg)) and sqlalchemy.

## Installation

```bash
pip install aiohttp-rest-framework
```

## Usage example

Consider we have the following sqlalchemy tables (models):

```python
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

meta = sa.MetaData()

users = sa.Table(
    "users", meta,
    sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    sa.Column("name", sa.Text),
    sa.Column("email", sa.Text, unique=True),
    sa.Column("phone", sa.Text),
    sa.Column("company_id", sa.ForeignKey("companies.id"), nullable=True),
)

companies = sa.Table(
    "companies", meta,
    sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    sa.Column("name", sa.Text),
)
```

Now we can use very familiar to us from DRF serializer, built on top of marshmalow's `Schema`:

```python
from aiohttp_rest_framework import serializers

from app.models import users


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = users
        fields = "__all__"
```

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
from aiohttp_rest_framework import setup_rest_framework

from app import views


app = web.Application()
app.router.add_view("/users", views.UsersListCreateView)
app.router.add_view("/users/{id}", views.UsersRetrieveUpdateDestroyView)
setup_rest_framework(app)
web.run_app(app)
```

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
- aiopg
- sqlalchemy
- marshmallow

## Documentation

TBD
