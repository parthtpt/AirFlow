import uuid

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import AuditMixin


class TaskRun(Base, AuditMixin):

    __tablename__ = "task_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id"),
        index=True,
    )

    state: Mapped[str] = mapped_column(
        String(50),
        index=True,
    )
