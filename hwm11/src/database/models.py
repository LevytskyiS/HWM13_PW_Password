import enum

from sqlalchemy import Column, Integer, String, Date, DateTime, func, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Roles(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(25), nullable=False)
    last_name = Column(String(40), nullable=False)
    email = Column(String(50), unique=True, index=True)
    phone = Column(Integer, unique=True, index=True)
    birthday = Column(Date)
    password = Column(String(255), nullable=False)
    created_at = Column("created_at", DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    reset_password_token = Column(String(255), nullable=True)
    roles = Column("role", Enum(Roles), default=Roles.user)
    confirmed = Column(Boolean, default=False)
    marital_status = Column(Boolean, default=False)


# create type roles as enum ('admin', 'moderator', 'user');
# Script for Postgres
