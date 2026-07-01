# Прототип системы реферирования и аннотирования документов для пользователей Научной библиотеки ДВФУ

ВКР Федюнин Илья Максимович, 09.03.04 Программная инженерия, ДВФУ 2026

---

## Запуск

Нужно установить Python 3.11, Node.js 18+

**1. Клонировать репозиторий**

```bash
git clone https://github.com/xaxich/VKR.git
cd VKR
```

**2. Запустить бэкенд**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Бэкенд запустится на http://127.0.0.1:8000

**3. Запустить фронтенд (открыть второй терминал)**

```bash
cd frontend
npm install
npm run dev
```

Фронтенд запустится на http://localhost:5173

Чтобы зарегистрировать нового пользователя, используйте форму на странице регистрации.
---

## Структура проекта

```
VKR/
 api/
  routes.py          # API-эндпоинты
 database/
  auth.py            # JWT и bcrypt
  database.py        # Подключение к БД (SQLite)
  models.py          # SQLAlchemy модели
 services/
  pdf_extractor.py   # Извлечение текста из PDF
  preprocessor.py    # Нормализация текста
  summarization.py   # Суммаризация (3 метода)
  keywords.py        # Извлечение ключевых слов
 frontend/
  src/               # React-компоненты
  public/
  package.json
  ...
 uploads/               # Загруженные PDF-файлы
 main.py                # Точка входа (FastAPI)
 requirements.txt       # Python-зависимости
 library.db             # SQLite база данных (создаётся автоматически)
 README.md
```

---

## API документация

Когда бэкенд запущен, документация доступна по адресу http://127.0.0.1:8000/docs


## Демонстрация интерфейса
Скриншоты интерфейса находятся в файле "Скриншоты демонстрация интерфейса.pdf"
