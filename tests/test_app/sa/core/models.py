import datetime
import enum
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID


def stringified_uuid():
    return str(uuid4())


meta = sa.MetaData()

User = sa.Table(
    "users", meta,
    sa.Column("id", PGUUID, primary_key=True, default=stringified_uuid),
    sa.Column("name", sa.Text, nullable=False, default=""),
    sa.Column("email", sa.Text, nullable=False, unique=True),
    sa.Column("phone", sa.Text, nullable=False, default=""),
    sa.Column("password", sa.Text, nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=False, default=datetime.datetime.utcnow),
    sa.Column("company_id", sa.ForeignKey("companies.id"), nullable=True),
)

Company = sa.Table(
    "companies", meta,
    sa.Column("id", PGUUID, primary_key=True, default=stringified_uuid),
    sa.Column("name", sa.Text),
)


class TestSAEnum(enum.Enum):
    test = "test"
    test2 = "test2"


SAField = sa.Table(
    "sa_fields", meta,
    sa.Column("UUID", PGUUID, primary_key=True, default=stringified_uuid),
    sa.Column("StringifiedUUID", PGUUID),
    sa.Column("BigInteger", sa.BigInteger, nullable=True),
    sa.Column("Boolean", sa.Boolean, server_default=sa.text("FALSE")),
    sa.Column("Date", sa.Date, nullable=True),
    sa.Column("DateTime", sa.DateTime, nullable=True),
    sa.Column("Enum", sa.Enum(TestSAEnum), nullable=True),
    sa.Column("Float", sa.Float, nullable=True),
    sa.Column("Integer", sa.Integer, nullable=True),
    sa.Column("Interval", sa.Interval, nullable=True),
    sa.Column("Numeric", sa.Numeric, nullable=True),
    sa.Column("SmallInteger", sa.SmallInteger, nullable=True),
    sa.Column("String", sa.String, nullable=True),
    sa.Column("Text", sa.Text, nullable=True),
    sa.Column("Time", sa.Time, nullable=True),
    sa.Column("Unicode", sa.Unicode, nullable=True),
    sa.Column("UnicodeText", sa.UnicodeText, nullable=True),
)
