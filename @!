import uuid

from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import AuditMixin


class DAG(Base, AuditMixin):

    __tablename__ = "dags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    dag_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    schedule: Mapped[str] = mapped_column(
        String(100),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
