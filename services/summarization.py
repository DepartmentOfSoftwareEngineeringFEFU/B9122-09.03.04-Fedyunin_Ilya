import re
from typing import List, Tuple
from .preprocessor import segment_sentences

# Глобальные переменные для кэширования моделей
_summarizer_model = None
_summarizer_tokenizer = None


def _get_summarizer():
    """Ленивая загрузка модели суммаризации"""
    global _summarizer_model, _summarizer_tokenizer
    if _summarizer_model is None:
        try:
            from transformers import T5Tokenizer, T5ForConditionalGeneration
            # Используем русскоязычную модель ruT5 для суммаризации
            model_name = "cointegrated/ruT5-base-absum"
            _summarizer_tokenizer = T5Tokenizer.from_pretrained(model_name)
            _summarizer_model = T5ForConditionalGeneration.from_pretrained(model_name)
            print("✅ Модель суммаризации загружена")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки модели: {e}")
            _summarizer_model = False
    return _summarizer_model, _summarizer_tokenizer


def extractive_summarization(text: str, num_sentences: int = 5) -> Tuple[str, List[str]]:
    """Экстрактивная суммаризация на основе TF-IDF и TextRank"""
    if not text or len(text) < 100:
        return "", []

    sentences = segment_sentences(text)
    if len(sentences) <= num_sentences:
        return " ".join(sentences), sentences

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        # Векторизация предложений
        vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b', stop_words=None)
        tfidf_matrix = vectorizer.fit_transform(sentences)

        # Матрица сходства
        similarity_matrix = cosine_similarity(tfidf_matrix)

        # Алгоритм TextRank
        scores = np.ones(len(sentences))
        damping = 0.85
        iterations = 10

        for _ in range(iterations):
            new_scores = np.zeros(len(sentences))
            for i in range(len(sentences)):
                for j in range(len(sentences)):
                    if i != j and similarity_matrix[i, j] > 0:
                        col_sum = np.sum(similarity_matrix[:, j])
                        if col_sum > 0:
                            new_scores[i] += damping * similarity_matrix[i, j] / col_sum * scores[j]
                new_scores[i] += (1 - damping)
            scores = new_scores

        # Отбор топ предложений
        ranked = sorted([(scores[i], sentences[i]) for i in range(len(sentences))], reverse=True)
        selected = ranked[:num_sentences]

        # Сохраняем порядок
        selected_indices = sorted([i for i, s in enumerate(sentences) if any(s == s2 for _, s2 in selected)])
        selected_sentences = [sentences[i] for i in selected_indices]

        return " ".join(selected_sentences), selected_sentences

    except Exception as e:
        print(f"Ошибка экстрактивной суммаризации: {e}")
        # Fallback: первые N предложений
        return " ".join(sentences[:num_sentences]), sentences[:num_sentences]


def abstractive_summarization(text: str, max_length_words: int = 150) -> str:
    """Абстрактивная суммаризация с помощью ruT5"""
    model, tokenizer = _get_summarizer()

    if model is None or tokenizer is None:
        # Если модель не загрузилась, используем экстрактивную
        summary, _ = extractive_summarization(text, num_sentences=8)
        return summary

    try:
        # Ограничиваем входной текст (модель имеет ограничение)
        max_input_tokens = 1024
        inputs = tokenizer(
            text,
            max_length=max_input_tokens,
            truncation=True,
            return_tensors="pt"
        )

        # Генерация суммаризации
        output_ids = model.generate(
            inputs["input_ids"],
            max_length=max_length_words * 2,
            min_length=30,
            num_beams=4,
            early_stopping=True,
            temperature=0.7,
            do_sample=True
        )

        summary = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return summary if len(summary) > 20 else text[:500]

    except Exception as e:
        print(f"Ошибка абстрактивной суммаризации: {e}")
        summary, _ = extractive_summarization(text, num_sentences=8)
        return summary


def hybrid_summarization(text: str, target_words: int = 150) -> str:
    """
    Гибридная суммаризация:
    1. Экстрактивный отбор ключевых предложений (сжатие)
    2. Абстрактивная генерация по отобранным фрагментам
    """
    sentences = segment_sentences(text)

    # Шаг 1: отбираем наиболее важные предложения (30-40% от исходного)
    if len(sentences) > 10:
        extracted_text, _ = extractive_summarization(text, num_sentences=max(5, len(sentences) // 3))
    else:
        extracted_text = text

    # Шаг 2: применяем абстрактивную суммаризацию к сокращённому тексту
    summary = abstractive_summarization(extracted_text, max_length_words=target_words)

    # Если результат слишком короткий, делаем fallback
    if len(summary.split()) < 30:
        summary, _ = extractive_summarization(text, num_sentences=10)

    return summary