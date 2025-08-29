from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .base import Base


class Content(Base):
    __tablename__ = "contents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    external_id = Column(String(255), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    embedding = Column(Vector(768))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    customer = relationship("Customer", back_populates="contents")
    
    __table_args__ = (
        UniqueConstraint("customer_id", "external_id", name="uq_customer_external_id"),
    )
    
    def __repr__(self):
        return f"<Content(id={self.id}, title='{self.title}', type='{self.type}')>"