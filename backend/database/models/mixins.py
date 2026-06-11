from sqlalchemy import DateTime
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func


class AuditMixin:

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
