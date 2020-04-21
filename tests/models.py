import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

meta = sa.MetaData()

users = sa.Table(
    "users", meta,
    sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    sa.Column("name", sa.Text, nullable=False, default=""),
    sa.Column("email", sa.Text, nullable=False, unique=True, default=""),
    sa.Column("phone", sa.Text, nullable=False, default=""),
    sa.Column("password", sa.Text, nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=False, default=datetime.datetime.utcnow),
)
