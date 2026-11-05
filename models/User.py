from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base


class User(Base):
    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(String(32), primary_key=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    deviceId: Mapped[Optional[str]] = mapped_column("device_id", String(255))
    storeNumber: Mapped[Optional[str]] = mapped_column("store_number", String(255), index=True)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime, default=datetime.utcnow, nullable=False)
