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
- [x] Входящие и витрина: `POST /capture`, `GET /tasks`, `POST /tasks/{id}/done`, `GET /notes`, `GET /audit`
- [x] Ручная правка записей с `needs_review`
- [x] Десять фиксированных входов: `tests_data/inputs.jsonl`
- [x] Живой LLM: ProxyAPI или OpenAI по env, в тестах остаётся `LLM_MODE=mock`
- [x] Веб-панель: Входящие / Задачи / Журнал / карточка, экспорт JSON и CSV
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

Панель (отдельный процесс, пока API уже запущен):

```bat
cd frontend
npm install
npm run dev
```

Открыть http://127.0.0.1:5173. Запросы к API проксируются на порт 8000.

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

```bat
curl.exe -X POST http://127.0.0.1:8000/capture -H "Content-Type: application/json" -d "{\"text\": \"оплатить хостинг\", \"user_id\": \"u_1\"}"
curl.exe "http://127.0.0.1:8000/tasks?user_id=u_1&status=open"
curl.exe -X POST http://127.0.0.1:8000/tasks/1/done -H "Content-Type: application/json" -d "{\"user_id\": \"u_1\"}"
curl.exe -X POST http://127.0.0.1:8000/tasks/1/review -H "Content-Type: application/json" -d "{\"user_id\": \"u_1\", \"title\": \"Разобрать почту\", \"priority\": \"high\"}"
```

В PowerShell вызывай `curl.exe`: короткое `curl` там псевдоним `Invoke-WebRequest`.

## API


| Метод | Путь                  | Описание                                                    |
| ----- | --------------------- | ----------------------------------------------------------- |
| GET   | `/health`             | Проверка живости сервиса                                     |
| POST  | `/ai/structure`       | Разбор текста в строгую схему, без записи                    |
| POST  | `/capture`            | Разобрать текст и сохранить задачу или заметку               |
| GET   | `/tasks`              | Задачи пользователя, фильтр `status=open\|done`              |
| POST  | `/tasks/{id}/done`    | Закрыть задачу, идемпотентно                                 |
| POST  | `/tasks/{id}/review`  | Поправить заголовок и приоритет, снять `needs_review`        |
| GET   | `/notes`              | Заметки пользователя, последние 50                           |
| POST  | `/notes/{id}/review`  | Поправить заголовок заметки, снять `needs_review`            |
| GET   | `/audit`              | Журнал прогонов пользователя, последние 100                  |


Все запросы идут в разрезе пользователя: `user_id` передаётся в теле (`/capture`, `/tasks/{id}/done`, `/tasks/{id}/review`, `/notes/{id}/review`) или в query (`/tasks`, `/notes`, `/audit`). Пока аутентификации нет, доступны засеянные `u_1` и `u_2`. Чужая или несуществующая запись отвечает `404`, а не `403`, чтобы наружу не утекало само её существование. Время в ответах — UTC с явной зоной.

`status=open` возвращает всё, что не `done`. Повторный `POST /tasks/{id}/done` по закрытой задаче тоже отвечает `{"status":"ok"}`.

Ручная проверка: `POST /tasks/{id}/review` принимает `title` и `priority` (`low|medium|high`), снимает `needs_review` и очищает `review_reason`. У заметки приоритета нет — правится только `title`. Прогон пишется в журнал отдельным действием `update`, рядом с исходным `capture`, а не вместо него.

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
| `MIXED_INTENTS`   | В одном тексте и действие, и заметка, несводимо в одну запись |
| `LOW_CONFIDENCE`  | Модель сама не уверена                                     |

Срок и приоритет не выдумываются: нет срока в тексте — `due_date` останется `null`, не названный приоритет — всегда `medium`. Любой запрос, включая отказы и таймауты модели, оставляет строку в `audit_runs` с входом, ответом и длительностью.

## Десять тестовых входов

Файл `tests_data/inputs.jsonl` — ровно 10 строк `{text, user_id}`. Все с `user_id=u_1`. Прогон: `python -m pytest tests/test_inputs.py`.

Шумный ввод (строка 9) разбирается по **стратегии B**: один элемент с `needs_review=true`. `POST /capture` сохраняет одну сущность, поэтому стратегия A (задача + заметка) здесь была бы ложью. Причина в журнале — `MIXED_INTENTS`: в тексте и действие, и идея.

| № | `item_type` | `needs_review` | Почему |
|---|-------------|----------------|--------|
| 1 | `task` | нет | Простое действие: «купить кофе и бумагу» |
| 2 | `task` | нет | «завтра» распознано как срок, дедлайн не выдуман |
| 3 | `task` | нет | «срочно» → `priority=high` |
| 4 | `task` | нет | Два действия созвона сведены в одну задачу |
| 5 | `note` | нет | Идея без действия |
| 6 | `note` | нет | Ссылка сохранена как заметка |
| 7 | `note` | нет | Наблюдение без действия |
| 8 | `note` | нет | Черновик без однозначного действия |
| 9 | `note` | да | Шум + два несводимых намерения, стратегия B |
| 10 | `task` | да | «сделай важное, разберись» — слишком общий вход |

Пустой ввод, слишком длинный текст и prompt injection в эти 10 строк не входят: они проверяются отдельными тестами в `tests/test_inputs.py` и `tests/test_ai_structure.py`.

## Журнал прогонов

Строку пишет каждая точка доступа, в том числе когда запрос закончился отказом: `404` попадает в журнал с кодом `NOT_FOUND`, непредвиденная ошибка — с `INTERNAL_ERROR`. Один `POST /capture` оставляет две строки: `structure` с черновиком модели и причиной проверки, затем `capture` с ответом API. Для списков (`tasks`, `notes`, `audit`) в `output` пишется размер выдачи, а не сама выдача: иначе журнал начал бы разрастаться от собственных просмотров.

Журнал показывается только владельцу записей. Прогоны `POST /ai/structure`, вызванного напрямую без `user_id`, владельца не имеют и в панели не видны — это контрактный эндпоинт для curl и Swagger.

## Переменные окружения

Значения берутся из окружения или из `.env` в корне репозитория. Шаблон — `.env.example`.


| Переменная               | По умолчанию                             | Зачем                                                                                        |
| ------------------------ | ---------------------------------------- | -------------------------------------------------------------------------------------------- |
| `APP_NAME`               | `Foxfocus`                               | Заголовок API и Swagger                                                                      |
| `DATABASE_URL`           | `sqlite+aiosqlite:///./data/foxfocus.db` | Настройка базы. Относительный путь считается от корня репозитория, а не от текущего каталога |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000`                                   | Ожидание снятия блокировки SQLite                                                            |
| `LLM_MODE`               | `mock`                                   | `mock` — без сети. `live` — ProxyAPI или официальный OpenAI                                  |
| `PROXYAPI_KEY`           | пусто                                    | Если задан и не placeholder — провайдер `proxyapi`                                           |
| `OPENAI_API_KEY`         | пусто                                    | Официальный ключ, если ProxyAPI не задан. Синоним: `OPENAI_KEY`                              |
| `OPENAI_BASE_URL`        | пусто                                    | Свой base URL. Иначе `https://api.proxyapi.ru/openai/v1` или `https://api.openai.com/v1`     |
| `OPENAI_MODEL`           | `gpt-5.4-mini`                           | Модель Chat Completions                                                                      |
| `LLM_TIMEOUT_SECONDS`    | `25`                                     | Таймаут вызова модели. Сбой → `needs_review`, не пустой 500                                  |
| `LLM_TEMPERATURE`        | `0.1`                                    | Температура 0–0.2                                                                            |


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

Тесты работают на том же движке SQLite, пишут во временный файл и в сеть не ходят. Живой вызов модели — только `LLM_E2E=1` плюс рабочий ключ: `set LLM_E2E=1` и `python -m pytest tests/test_llm.py -k live_structure`.

## Структура

```
backend/app/          # настройки, движок базы, роутеры
backend/migrations/   # Alembic
frontend/             # Vite + React, в разработке на :5173
tests/                # pytest
data/                 # файл SQLite, вне git
.env.example
```

