from sqlalchemy import Column, Integer, Text, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from .database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    storage_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    size = Column(BigInteger, nullable=True)
    uploaded_by = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class ClauseSuggestion(Base):
    __tablename__ = "clause_suggestions"
    id = Column(Integer, primary_key=True)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    suggested_text = Column(Text, nullable=False)
    error_type = Column(String, nullable=False)
    confidence = Column(String, nullable=True)
    applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)


    
