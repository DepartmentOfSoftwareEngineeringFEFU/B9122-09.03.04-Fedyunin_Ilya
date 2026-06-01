import pdfplumber
import re
from typing import Tuple


def extract_text_from_pdf(file_path: str) -> Tuple[str, float]:
    """Извлекает текст из PDF-файла и оценивает качество извлечения"""
    try:
        full_text = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)

        result_text = "\n".join(full_text)

        # Оценка качества извлечения
        if len(result_text) < 100:
            quality = 0.1
        elif len(result_text) < 500:
            quality = 0.4
        elif len(result_text) < 2000:
            quality = 0.7
        else:
            quality = 0.95

        return result_text, quality

    except Exception as e:
        print(f"Ошибка извлечения текста: {e}")
        return "", 0.0


def clean_extracted_text(text: str) -> str:
    """Базовая очистка извлечённого текста"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()