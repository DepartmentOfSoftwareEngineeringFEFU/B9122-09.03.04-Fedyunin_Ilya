from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Header
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil
import re
from typing import Optional, List, Tuple

from database.database import SessionLocal
from database.models import Base, Document, ExtractedText, Annotation, Abstract, Keyword, ProcessingLog, User
from database.auth import hash_password, verify_password, create_access_token, decode_access_token
from services.pdf_extractor import extract_text_from_pdf, clean_extracted_text
from services.preprocessor import preprocess_for_summarization, segment_sentences
from services.summarization import extractive_summarization, abstractive_summarization, hybrid_summarization
from services.keywords import extract_keywords_hybrid

router = APIRouter()

# Папка для загрузок
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Получение текущего пользователя из JWT токена"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Не авторизован")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Неверный формат авторизации")

        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Недействительный токен")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Пользователь не найден или заблокирован")

        return user
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Недействительный токен")


# ============== Аутентификация ==============

@router.post("/auth/register")
async def register(
        login: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        db: Session = Depends(get_db)
):
    """Регистрация нового пользователя"""

    existing_user = db.query(User).filter(User.login == login).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Логин уже занят")

    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    hashed_pwd = hash_password(password)
    new_user = User(
        login=login,
        email=email,
        hashed_password=hashed_pwd,
        full_name=full_name or login,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Регистрация успешна",
        "user_id": new_user.id,
        "login": new_user.login
    }


@router.post("/auth/login")
async def login(login: str, password: str, db: Session = Depends(get_db)):
    """Вход в систему"""

    user = db.query(User).filter(User.login == login).first()
    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "login": user.login,
        "email": user.email,
        "full_name": user.full_name
    }


@router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Информация о текущем пользователе"""
    return {
        "id": current_user.id,
        "login": current_user.login,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


# ============== Работа с документами ==============

@router.post("/upload-pdf")
async def upload_pdf(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Загрузка PDF-файла и извлечение текста"""

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Только PDF-файлы")

    safe_filename = f"{datetime.now().timestamp()}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = Document(
        title=file.filename,
        file_path=file_path,
        user_id=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    raw_text, quality = extract_text_from_pdf(file_path)
    cleaned_text = clean_extracted_text(raw_text)
    normalized_text = preprocess_for_summarization(cleaned_text)

    extracted = ExtractedText(
        document_id=doc.id,
        raw_text=cleaned_text[:5000] if cleaned_text else "",
        normalized_text=normalized_text[:5000] if normalized_text else "",
        quality=quality
    )
    db.add(extracted)

    log = ProcessingLog(
        document_id=doc.id,
        user_id=current_user.id,
        status="success" if quality > 0.3 else "error",
        error_message=None if quality > 0.3 else "Низкое качество извлечения текста"
    )
    db.add(log)
    db.commit()

    return {
        "document_id": doc.id,
        "title": file.filename,
        "quality": quality,
        "text_preview": cleaned_text[:500] if cleaned_text else ""
    }


@router.post("/process/{doc_id}")
async def process_document(
        doc_id: int,
        method: str = "hybrid",
        annotation_sentences: int = 5,
        abstract_words: int = 150,
        keywords_count: int = 10,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Запуск аннотирования и реферирования документа"""

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому документу")

    extracted = db.query(ExtractedText).filter(ExtractedText.document_id == doc_id).first()
    if not extracted or not extracted.normalized_text:
        raise HTTPException(status_code=400, detail="Текст документа не извлечён")

    text = extracted.normalized_text
    if len(text) < 50:
        raise HTTPException(status_code=400, detail="Текст документа слишком короткий для обработки")

    # Формируем аннотацию
    annotation_text, _ = extractive_summarization(text, num_sentences=annotation_sentences)
    if not annotation_text:
        annotation_text = "Не удалось сформировать аннотацию."

    existing_annotation = db.query(Annotation).filter(Annotation.document_id == doc_id).first()
    if existing_annotation:
        existing_annotation.text = annotation_text[:3000]
        existing_annotation.length_sentences = annotation_sentences
        existing_annotation.method = "extractive"
        existing_annotation.created_at = datetime.utcnow()
    else:
        new_annotation = Annotation(
            document_id=doc_id,
            text=annotation_text[:3000],
            length_sentences=annotation_sentences,
            method="extractive"
        )
        db.add(new_annotation)

    # Формируем реферат
    if method == "extractive":
        abstract_text, _ = extractive_summarization(text, num_sentences=min(15, annotation_sentences * 2))
    elif method == "abstractive":
        abstract_text = abstractive_summarization(text, max_length_words=abstract_words)
    else:
        abstract_text = hybrid_summarization(text, target_words=abstract_words)

    if not abstract_text:
        abstract_text = "Не удалось сформировать реферат."

    existing_abstract = db.query(Abstract).filter(Abstract.document_id == doc_id).first()
    if existing_abstract:
        existing_abstract.text = abstract_text[:3000]
        existing_abstract.length_words = len(abstract_text.split())
        existing_abstract.method = method
        existing_abstract.created_at = datetime.utcnow()
    else:
        new_abstract = Abstract(
            document_id=doc_id,
            text=abstract_text[:3000],
            length_words=len(abstract_text.split()),
            method=method
        )
        db.add(new_abstract)

    # Извлекаем ключевые слова
    keywords_list = extract_keywords_hybrid(text, top_n=keywords_count)
    db.query(Keyword).filter(Keyword.document_id == doc_id).delete()
    for kw in keywords_list:
        new_keyword = Keyword(
            document_id=doc_id,
            keyword=kw[:200],
            method="hybrid"
        )
        db.add(new_keyword)

    log = ProcessingLog(
        document_id=doc_id,
        user_id=current_user.id,
        status="success"
    )
    db.add(log)
    db.commit()

    return {
        "document_id": doc_id,
        "annotation": annotation_text[:1000],
        "abstract": abstract_text[:1000],
        "keywords": keywords_list[:keywords_count],
        "method_used": method
    }


@router.get("/document/{doc_id}")
async def get_document_info(
        doc_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение информации о документе с результатами обработки"""

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому документу")

    annotation = db.query(Annotation).filter(Annotation.document_id == doc_id).first()
    abstract = db.query(Abstract).filter(Abstract.document_id == doc_id).first()
    keywords = db.query(Keyword).filter(Keyword.document_id == doc_id).all()
    extracted = db.query(ExtractedText).filter(ExtractedText.document_id == doc_id).first()

    return {
        "id": doc.id,
        "title": doc.title,
        "authors": doc.authors,
        "year": doc.year,
        "quality_extraction": extracted.quality if extracted else 0,
        "annotation": annotation.text if annotation else None,
        "abstract": abstract.text if abstract else None,
        "keywords": [kw.keyword for kw in keywords],
        "processing_method": abstract.method if abstract else None,
        "created_at": doc.created_at
    }


@router.get("/my-documents")
async def get_my_documents(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Список документов текущего пользователя"""
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "authors": doc.authors,
            "year": doc.year,
            "has_processing": db.query(Abstract).filter(Abstract.document_id == doc.id).first() is not None,
            "created_at": doc.created_at
        }
        for doc in documents
    ]


@router.delete("/document/{doc_id}")
async def delete_document(
        doc_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Удаление документа и всех связанных данных"""

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому документу")

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()

    return {"message": f"Документ {doc_id} удалён"}