"""Employee document uploads (contracts, IDs, certificates, etc.)."""
import enum
from sqlalchemy import String, ForeignKey, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class DocumentType(str, enum.Enum):
    CONTRACT = "contract"
    ID_PROOF = "id_proof"
    CERTIFICATE = "certificate"
    RESUME = "resume"
    OTHER = "other"


class Document(TimestampMixin, db.Model):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    employee: Mapped["Employee"] = relationship(back_populates="documents")

    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType), default=DocumentType.OTHER, nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploaded_by: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<Document {self.original_filename} emp={self.employee_id}>"
