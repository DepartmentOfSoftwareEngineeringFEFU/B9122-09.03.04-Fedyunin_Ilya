import re
from typing import List

STOP_WORDS_RU = {
    'и', 'в', 'во', 'не', 'что', 'на', 'я', 'с', 'со', 'как', 'а',
    'но', 'он', 'она', 'оно', 'они', 'это', 'так', 'вот', 'этот',
    'тот', 'такой', 'быть', 'это', 'или', 'при', 'без', 'для', 'по',
    'из', 'до', 'у', 'же', 'ли', 'только', 'ещё', 'уже', 'даже',
    'все', 'всё', 'всего', 'потом', 'там', 'тут', 'теперь', 'который',
    'весь', 'свой', 'который', 'мочь', 'иметь', 'делать', 'сказать'
}

def normalize_text(text: str) -> str:
    """Нормализация текста"""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def segment_sentences(text: str) -> List[str]:
    """Разбиение на предложения"""
    if not text:
        return []
    # Улучшенное разбиение
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]

def remove_stop_words(text: str) -> str:
    """Удаление стоп-слов"""
    if not text:
        return ""
    words = text.split()
    filtered = [w for w in words if w not in STOP_WORDS_RU and len(w) > 2]
    return ' '.join(filtered)

def preprocess_for_summarization(text: str) -> str:
    """Предобработка для суммаризации"""
    text = normalize_text(text)
    return text

def preprocess_for_keywords(text: str) -> str:
    """Предобработка для ключевых слов"""
    text = normalize_text(text)
    text = remove_stop_words(text)
    return text

def clean_extracted_text(text: str) -> str:
    """Очистка извлечённого текста"""
    if not text:
        return ""
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()