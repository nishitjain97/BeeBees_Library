from sqlalchemy import Integer, String, UniqueConstraint, Boolean, Column
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author_first: Mapped[str] = mapped_column(String(255), index=True)
    author_last: Mapped[str] = mapped_column(String(255), index=True)
    year: Mapped[str] = mapped_column(String(10), index=True)
    isbn: Mapped[str] = mapped_column(String(32), index=True)

    available = Column(Boolean, default=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_users_username"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))