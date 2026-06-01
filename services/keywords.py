from typing import List
import re
from .preprocessor import preprocess_for_keywords

# Глобальный кэш для модели KeyBERT
_keybert_model = None


def _get_keybert():
    """Ленивая загрузка KeyBERT модели"""
    global _keybert_model
    if _keybert_model is None:
        try:
            from keybert import KeyBERT
            _keybert_model = KeyBERT()
            print("✅ Модель KeyBERT загружена")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки KeyBERT: {e}")
            _keybert_model = False
    return _keybert_model


def extract_keywords_rake(text: str, top_n: int = 10) -> List[str]:
    """Извлечение ключевых слов методом RAKE"""
    if not text:
        return []

    stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'о', 'для', 'от', 'из', 'за',
                  'что', 'это', 'как', 'так', 'все', 'но', 'а', 'или', 'бы', 'еще',
                  'уже', 'даже', 'только', 'очень', 'было', 'была', 'были', 'был'}

    processed = preprocess_for_keywords(text)
    words = processed.split()

    candidates = {}
    i = 0
    while i < len(words):
        if words[i] not in stop_words and len(words[i]) > 2:
            phrase = words[i]
            j = i + 1
            while j < len(words) and j < i + 3 and words[j] not in stop_words and len(words[j]) > 2:
                phrase += " " + words[j]
                j += 1
            candidates[phrase] = candidates.get(phrase, 0) + 1
            i = j
        else:
            i += 1

    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    return [phrase for phrase, _ in sorted_candidates[:top_n]]


def extract_keywords_keybert(text: str, top_n: int = 10) -> List[str]:
    """Извлечение ключевых слов с помощью KeyBERT"""
    model = _get_keybert()

    if model is None or model is False:
        return extract_keywords_rake(text, top_n)

    try:
        processed = preprocess_for_keywords(text)

        keywords = model.extract_keywords(
            processed,
            keyphrase_ngram_range=(1, 2),
            stop_words=['и', 'в', 'на', 'с', 'по', 'к', 'у', 'о', 'для', 'от', 'из', 'за',
                        'что', 'это', 'как', 'так', 'все', 'но', 'а', 'или', 'бы', 'еще'],
            top_n=top_n,
            use_maxsum=True,
            nr_candidates=15
        )

        return [kw for kw, _ in keywords]

    except Exception as e:
        print(f"Ошибка KeyBERT: {e}")
        return extract_keywords_rake(text, top_n)


def extract_keywords_hybrid(text: str, top_n: int = 10) -> List[str]:
    """
    Гибридное извлечение ключевых слов:
    - KeyBERT для семантической близости
    - RAKE для частотных фраз
    """
    keywords_keybert = extract_keywords_keybert(text, top_n=top_n)
    keywords_rake = extract_keywords_rake(text, top_n=top_n)

    # Объединяем, сохраняя уникальность
    seen = set()
    result = []

    for kw in keywords_keybert + keywords_rake:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            result.append(kw)

    return result[:top_n]