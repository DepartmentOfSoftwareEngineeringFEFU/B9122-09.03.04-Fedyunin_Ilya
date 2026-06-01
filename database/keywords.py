from typing import List
from services.preprocessor import preprocess_for_keywords, STOP_WORDS_RU


def extract_keywords_rake(text: str, top_n: int = 10) -> List[str]:
    """
    Извлечение ключевых слов методом RAKE (упрощённая реализация)
    Rapid Automatic Keyword Extraction
    """
    if not text:
        return []

    # Предобработка текста
    processed = preprocess_for_keywords(text)

    # Разбиваем на слова
    words = processed.split()

    # Выделяем кандидатов (слова, не являющиеся стоп-словами)
    candidates = {}

    # Ищем фразы (длиной 1-3 слова)
    for i in range(len(words)):
        phrase_words = []
        for j in range(i, min(i + 3, len(words))):
            if words[j] in STOP_WORDS_RU:
                break
            phrase_words.append(words[j])

        if phrase_words:
            phrase = " ".join(phrase_words)
            candidates[phrase] = candidates.get(phrase, 0) + 1

    # Сортируем по частоте
    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)

    return [phrase for phrase, _ in sorted_candidates[:top_n]]


def extract_keywords_keybert(text: str, top_n: int = 10) -> List[str]:
    """
    Извлечение ключевых слов с помощью KeyBERT
    (требуется установка sentence-transformers и keybert)
    """
    try:
        from keybert import KeyBERT

        # Инициализация модели
        kw_model = KeyBERT()

        # Предобработка текста
        processed = preprocess_for_keywords(text)

        # Извлечение ключевых слов
        keywords = kw_model.extract_keywords(
            processed,
            keyphrase_ngram_range=(1, 3),
            stop_words=list(STOP_WORDS_RU),
            top_n=top_n,
            use_maxsum=True,
            nr_candidates=20
        )

        return [kw for kw, _ in keywords]

    except (ImportError, Exception) as e:
        print(f"KeyBERT недоступен: {e}, используем RAKE")
        return extract_keywords_rake(text, top_n)


def extract_keywords_hybrid(text: str, top_n: int = 10) -> List[str]:
    """
    Гибридное извлечение ключевых слов:
    - KeyBERT даёт семантически близкие фразы
    - RAKE дополняет частотными фразами
    - Объединение с удалением дубликатов
    """
    keywords_keybert = extract_keywords_keybert(text, top_n=top_n)
    keywords_rake = extract_keywords_rake(text, top_n=top_n)

    # Объединяем, сохраняя порядок (сначала KeyBERT, затем RAKE)
    all_keywords = []
    seen = set()

    for kw in keywords_keybert + keywords_rake:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            all_keywords.append(kw)

    return all_keywords[:top_n]