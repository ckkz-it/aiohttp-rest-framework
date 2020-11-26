import datetime
import enum
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base


def stringified_uuid():
    return str(uuid4())


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = sa.Column(PGUUID, primary_key=True, default=stringified_uuid)
    name = sa.Column(sa.Text, nullable=False, default="")
    email = sa.Column(sa.Text, nullable=False, unique=True)
    phone = sa.Column(sa.Text, nullable=False, default="")
    password = sa.Column(sa.Text, nullable=False)
    created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    company_id = sa.Column(sa.ForeignKey("companies.id"), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<User id={self.id}, name={self.name}, email={self.email}, phone={self.email}, password={self.password}, "
            f"created_at={self.created_at}, company_id={self.company_id}>"
        )


class Company(Base):
    __tablename__ = "companies"

    id = sa.Column(PGUUID, primary_key=True, default=stringified_uuid)
    name = sa.Column(sa.Text)


class TestSAEnum(enum.Enum):
    test = "test"
    test2 = "test2"


class SAField(Base):
    __tablename__ = "sa_fields"

    UUID = sa.Column(PGUUID, primary_key=True, default=stringified_uuid)
    StringifiedUUID = sa.Column(PGUUID)
    BigInteger = sa.Column(sa.BigInteger, nullable=True)
    Boolean = sa.Column(sa.Boolean, server_default=sa.text("FALSE"))
    Date = sa.Column(sa.Date, nullable=True)
    DateTime = sa.Column(sa.DateTime, nullable=True)
    Enum = sa.Column(sa.Enum(TestSAEnum), nullable=True)
    Float = sa.Column(sa.Float, nullable=True)
    Integer = sa.Column(sa.Integer, nullable=True)
    Interval = sa.Column(sa.Interval, nullable=True)
    Numeric = sa.Column(sa.Numeric, nullable=True)
    SmallInteger = sa.Column(sa.SmallInteger, nullable=True)
    String = sa.Column(sa.String, nullable=True)
    Text = sa.Column(sa.Text, nullable=True)
    Time = sa.Column(sa.Time, nullable=True)
    Unicode = sa.Column(sa.Unicode, nullable=True)
    UnicodeText = sa.Column(sa.UnicodeText, nullable=True)
