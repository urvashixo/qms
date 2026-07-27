from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(160), default="")
    product_name: Mapped[str] = mapped_column(String(200), default="")
    batch_number: Mapped[str] = mapped_column(String(100), default="")
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

