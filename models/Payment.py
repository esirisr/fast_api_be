from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    phone: Mapped[str] = mapped_column(String(32), primary_key=True)
    isPaid: Mapped[bool] = mapped_column("is_paid", Boolean, default=False, nullable=False)
    isSuspended: Mapped[bool] = mapped_column("is_suspended", Boolean, default=False, nullable=False)
    expiryDate: Mapped[Optional[datetime]] = mapped_column("expiry_date", DateTime)
    lastUpdated: Mapped[datetime] = mapped_column("last_updated", DateTime, default=datetime.utcnow, nullable=False)

    class Settings:
        name = "payments"
        indexes = ["phone"]
