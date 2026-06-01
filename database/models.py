from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(String(500), nullable=True)
    year = Column(Integer, nullable=True)
    doc_type = Column(String(50), nullable=True)
    language = Column(String(10), default="RU")
    file_path = Column(String(500), nullable=True)
    external_url = Column(String(500), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExtractedText(Base):
    __tablename__ = "extracted_texts"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    raw_text = Column(Text, nullable=True)
    normalized_text = Column(Text, nullable=True)
    quality = Column(Float, default=0.0)
    processed_at = Column(DateTime, default=datetime.utcnow)


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    text = Column(Text, nullable=False)
    length_sentences = Column(Integer, default=0)
    method = Column(String(50), default="extractive")
    created_at = Column(DateTime, default=datetime.utcnow)


class Abstract(Base):
    __tablename__ = "abstracts"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    text = Column(Text, nullable=False)
    length_words = Column(Integer, default=0)
    method = Column(String(50), default="hybrid")
    created_at = Column(DateTime, default=datetime.utcnow)


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    keyword = Column(String(200), nullable=False)
    method = Column(String(50), default="hybrid")


class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Связи (определяем после всех классов)
User.documents = relationship("Document", back_populates="owner")
User.processing_history = relationship("ProcessingLog", back_populates="user")

Document.owner = relationship("User", back_populates="documents")
Document.extracted_text = relationship("ExtractedText", back_populates="document", uselist=False)
Document.annotation = relationship("Annotation", back_populates="document", uselist=False)
Document.abstract = relationship("Abstract", back_populates="document", uselist=False)
Document.keywords = relationship("Keyword", back_populates="document")

ExtractedText.document = relationship("Document", back_populates="extracted_text")
Annotation.document = relationship("Document", back_populates="annotation")
Abstract.document = relationship("Document", back_populates="abstract")
Keyword.document = relationship("Document", back_populates="keywords")
ProcessingLog.user = relationship("User", back_populates="processing_history")