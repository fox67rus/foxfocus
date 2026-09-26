# Foxfocus

Сырой текст → строгий JSON → задача или заметка. Если модель не уверена, запись получает флаг `needs_review`, а не выдуманный срок. Каждый вызов API пишется в журнал прогонов.

```
веб-панель → FastAPI → LLM (строгая JSON-схема) → pydantic → SQLite → журнал
```

- Ответ модели проходит только через pydantic-схему. Никакого `eval`.
- Нет срока в тексте — в JSON `null`.
- Журнал заполняется всегда, включая ошибки и таймауты модели.
- Данные читаются в разрезе пользователя, чужой ресурс отдаёт 404.

**Стек:** Python 3.12, FastAPI, SQLAlchemy 2 async + aiosqlite, Alembic, Pydantic v2, pytest, ruff. Фронтенд — Vite + React + Tailwind. SQLite одна и та же в тестах и в рабочем запуске.

## Статус

- [x] Каркас API, настройки из окружения, движок SQLite (`WAL`, `foreign_keys=ON`, `busy_timeout`), миграции Alembic, `GET /health`
- [x] Схема данных: `users`, `tasks`, `notes`, `memory_facts`, `audit_runs`, сид пользователей `u_1` и `u_2`
- [x] Разбор текста: `POST /ai/structure` со строгой схемой и журналом причин
- [ ] Входящие и витрина: `POST /capture`, `GET /tasks`, `POST /tasks/{id}/done`
- [ ] Ручная правка записей с `needs_review`
- [ ] Веб-панель, экспорт в JSON и CSV
- [ ] Сборка в один контейнер

## Установка

Нужен **Python 3.12** и Git. Если 3.12 нет в системе, окружение собирается через [uv](https://docs.astral.sh/uv/) без смены системной версии: `uv python install 3.12`, затем `uv venv --python 3.12 --seed .venv`.

```bat
git clone https://github.com/fox67rus/foxfocus
cd foxfocus
python -m venv .venv
.venv\Scripts\activate
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

## Запуск

```bat
cd backend
alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Swagger — [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

```bat
curl.exe http://127.0.0.1:8000/health
```

```json
{"status":"ok"}
```

```bat
curl.exe -X POST http://127.0.0.1:8000/ai/structure -H "Content-Type: application/json" -d "{\"text\": \"завтра до 12 отправить счёт клиенту Иванову\"}"
```

```json
{"item_type":"task","title":"завтра до 12 отправить счёт клиенту Иванову","due_date":"2026-09-27","priority":"medium","tags":[],"confidence":"high","needs_review":false}
```

В PowerShell вызывай `curl.exe`: короткое `curl` там псевдоним `Invoke-WebRequest`.

## API


| Метод | Путь             | Описание                                        |
| ----- | ---------------- | ----------------------------------------------- |
| GET   | `/health`        | Проверка живости сервиса                        |
| POST  | `/ai/structure`  | Разбор текста в строгую схему, без записи задачи |


Остальные эндпоинты добавляются в таблицу по мере готовности.

## Разбор текста и `needs_review`

`POST /ai/structure` отвечает ровно семью полями: `item_type` (`task` или `note`), `title`, `due_date` (ISO-дата или `null`), `priority` (`low|medium|high`), `tags`, `confidence` (`high|medium|low`), `needs_review`. Ничего сверх схемы в ответ не попадает.

Запись помечается `needs_review`, когда доверять разбору нельзя. Причина в ответе не возвращается — её код пишется в `audit_runs.error`:

| Код               | Когда                                                      |
| ----------------- | ---------------------------------------------------------- |
| `EMPTY_INPUT`     | Пустой ввод                                                |
| `TEXT_TOO_LONG`   | Текст длиннее 4000 символов, запрос отклонён с 422          |
| `INVALID_JSON`    | Ответ модели не разобрался как JSON                        |
| `SCHEMA_MISMATCH` | Модель вернула структуру не по схеме                       |
| `LLM_TIMEOUT`     | Модель не ответила вовремя                                 |
| `LLM_ERROR`       | Модель ответила ошибкой                                    |
| `PROMPT_INJECTION`| В тексте попытка перебить инструкции                       |
| `VAGUE_INPUT`     | Вход слишком общий: «сделай важное»                        |
| `LOW_CONFIDENCE`  | Модель сама не уверена                                     |

Срок и приоритет не выдумываются: нет срока в тексте — `due_date` останется `null`, не названный приоритет — всегда `medium`. Любой запрос, включая отказы и таймауты модели, оставляет строку в `audit_runs` с входом, ответом и длительностью.

## Переменные окружения

Значения берутся из окружения или из `.env` в корне репозитория. Шаблон — `.env.example`.


| Переменная               | По умолчанию                             | Зачем                                                                                        |
| ------------------------ | ---------------------------------------- | -------------------------------------------------------------------------------------------- |
| `APP_NAME`               | `Foxfocus`                               | Заголовок API и Swagger                                                                      |
| `DATABASE_URL`           | `sqlite+aiosqlite:///./data/foxfocus.db` | Настройка базы. Относительный путь считается от корня репозитория, а не от текущего каталога |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000`                                   | Ожидание снятия блокировки SQLite                                                            |
| `LLM_MODE`               | `mock`                                   | Режим разбора. `mock` — детерминированные правила без сети и ключей                          |


## Данные

База — файл `data/foxfocus.db`, вне git и вне образа. Путь меняется через `DATABASE_URL`.

Миграции создают пользователей `u_1` и `u_2`: пока аутентификации нет, их `user_id` передаётся в запросах, и каждый запрос читает только свои строки.

Список таблиц (из корня репозитория) и текущая версия миграций:

```bat
python -c "import sqlite3; print([n for n, t in sqlite3.connect(r'data\foxfocus.db').execute('SELECT name, type FROM sqlite_master') if t == 'table'])"
cd backend && alembic current
```

## Разработка

```bat
pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Тесты работают на том же движке SQLite, пишут во временный файл и в сеть не ходят.

## Структура

```
backend/app/          # настройки, движок базы, роутеры
backend/migrations/   # Alembic
tests/                # pytest
data/                 # файл SQLite, вне git
.env.example
```

