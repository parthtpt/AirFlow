import uuid

from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import AuditMixin


class Task(Base, AuditMixin):

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    dag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dags.id"),
        index=True,
    )

    task_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    retries: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        default=3600,
    )
