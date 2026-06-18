import uuid

from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import AuditMixin

DEFAULT_POOL = "default_pool"


class Pool(Base, AuditMixin):
    """A named concurrency pool. Tasks assigned to a pool share its slots:
    at most `slots` of them run at once."""

    __tablename__ = "pools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    slots: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
