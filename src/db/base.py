from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # SQLAlchemy's typing conflicts with ClassVar here
    __mapper_args__ = {"eager_defaults": True}  # noqa: RUF012
