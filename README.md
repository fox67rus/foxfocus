# Foxfocus

Личный помощник: сырой текст разбирается в строгий JSON и сохраняется как **задача** или **заметка**. Если разбору нельзя доверять, запись помечается `needs_review` — срок и приоритет из воздуха не появляются. Каждый запрос пишется в журнал.

Панель и API живут на одном порту. База — один файл SQLite.

## Как это работает

```
текст → LLM (JSON) → pydantic → задача или заметка → SQLite → журнал
```

1. На **Входящих** вставляете текст и нажимаете «Разобрать» (`POST /capture`).
2. Модель возвращает ровно семь полей: `item_type`, `title`, `due_date`, `priority`, `tags`, `confidence`, `needs_review`. Ответ проходит только через pydantic, без `eval`.
3. Действие со сроком или приоритетом становится задачей. Идея, ссылка, наблюдение — заметкой.
4. Нет даты в тексте → `due_date` остаётся `null`. Приоритет, если не назван, — `medium`.
5. Сомнение, обрыв сети, битый JSON — карточка с меткой «требует проверки». Причина пишется в `audit_runs.error`, не в ответ API.
6. Задачи смотрите списком, заметки — стикерами. На карточке можно поправить заголовок, срок и приоритет, подтвердить проверку или удалить запись.
7. **Журнал** показывает вход, выход, ошибку и длительность каждого прогона.

Пока нет логина: в запросах передаётся `user_id`. Засеяны `u_1` и `u_2`. Чужой или несуществующий ресурс отвечает **404**, не 403.

## Запуск

Нужны Docker Desktop или Python 3.12. С нуля до открытой панели — меньше десяти минут.

### Docker

```bat
git clone https://github.com/fox67rus/foxfocus
cd foxfocus
copy .env.example .env
docker compose up --build
```

Панель и API: http://127.0.0.1:8000  
Swagger: http://127.0.0.1:8000/docs

Для живой модели впишите в `.env` ключ `PROXYAPI_KEY` или `OPENAI_API_KEY` и `LLM_MODE=live`. Переменные Windows в контейнер не попадают. Без ключа сервис стартует, разбор идёт в режиме `mock`.

### Windows без Docker

Если в системе нет Python 3.12: `uv python install 3.12`, затем `uv venv --python 3.12 --seed .venv`.

```bat
git clone https://github.com/fox67rus/foxfocus
cd foxfocus
python -m venv .venv
.venv\Scripts\activate
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
cd backend
alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

После `npm run build` в `frontend` FastAPI сам отдаёт панель с порта 8000. Для горячей перезагрузки UI: API на `:8000`, в другом терминале `npm install` и `npm run dev` в `frontend` — панель на http://127.0.0.1:5173, запросы проксируются на API.

В PowerShell вызывайте `curl.exe`: короткое `curl` — это `Invoke-WebRequest`.

## Примеры запросов

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
```

`POST /ai/structure` только разбирает текст. `POST /capture` разбирает и сохраняет.

## Переменные окружения

Шаблон — `.env.example` в корне репозитория.

| Переменная | По умолчанию | Зачем |
|---|---|---|
| `APP_NAME` | `Foxfocus` | Заголовок API и Swagger |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/foxfocus.db` | Файл базы. Относительный путь считается от корня репозитория |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | Ожидание снятия блокировки SQLite |
| `LLM_MODE` | `mock` | `mock` — без сети. `live` — ProxyAPI или OpenAI. Без ключа остаётся `mock` |
| `PROXYAPI_KEY` | пусто | Если задан и не placeholder — провайдер ProxyAPI |
| `OPENAI_API_KEY` | пусто | Официальный ключ, если ProxyAPI не задан. Синоним: `OPENAI_KEY` |
| `OPENAI_BASE_URL` | пусто | Свой base URL. Иначе адрес выбранного провайдера |
| `OPENAI_MODEL` | `gpt-5.4-mini` | Модель Chat Completions |
| `LLM_TIMEOUT_SECONDS` | `60` | Таймаут вызова. Сбой → `needs_review`, не пустой 500 |
| `LLM_TEMPERATURE` | `0.1` | Температура 0–0.2 |
| `STATIC_DIR` | пусто | Каталог собранной панели. Пусто — `frontend/dist` или `static/` |

## API

| Метод | Путь | Описание |
|---|---|---|
| GET | `/health` | Живость сервиса |
| GET | `/llm/status` | Проверка связи с моделью (`user_id`), без генерации |
| POST | `/ai/structure` | Разбор в семь полей, без записи |
| POST | `/capture` | Разбор и сохранение задачи или заметки |
| GET | `/tasks` | Задачи, фильтр `status=open\|done` |
| POST | `/tasks/{id}/done` | Закрыть задачу, идемпотентно |
| POST | `/tasks/{id}/review` | Поправить title, priority, due_date; снять `needs_review` |
| POST | `/tasks/{id}/delete` | Удалить задачу |
| GET | `/notes` | Заметки, последние 50 |
| POST | `/notes/{id}/review` | Поправить title заметки; снять `needs_review` |
| POST | `/notes/{id}/delete` | Удалить заметку |
| GET | `/audit` | Журнал прогонов, последние 100 |

`user_id` — в теле (`/capture`, `done`, `review`, `delete`) или в query (`/tasks`, `/notes`, `/audit`). `status=open` — всё, что не `done`. Повторный `done` тоже `{"status":"ok"}`. Время в ответах — UTC с зоной.

На карточке задачи правятся `title`, `priority` и `due_date` (пустое поле снимает срок). У заметки — только `title`. Удаление — с подтверждением на карточке. Прогон `update` или `delete` пишется в журнал рядом с исходным `capture`.

## `needs_review`

Ответ `/ai/structure` — только семь полей. Код причины остаётся в `audit_runs.error`:

| Код | Когда |
|---|---|
| `EMPTY_INPUT` | Пустой ввод |
| `TEXT_TOO_LONG` | Длиннее 4000 символов, ответ 422 |
| `INVALID_JSON` | Ответ модели не JSON |
| `SCHEMA_MISMATCH` | Структура не по схеме |
| `LLM_TIMEOUT` | Модель не уложилась в таймаут |
| `LLM_ERROR` | Ошибка сети или провайдера |
| `PROMPT_INJECTION` | Попытка перебить инструкции |
| `VAGUE_INPUT` | Слишком общий вход |
| `MIXED_INTENTS` | Действие и заметка в одном тексте |
| `LOW_CONFIDENCE` | Модель не уверена |

При сбое сети в `output` прогона `structure` появляется `error_detail` (в HTTP-ответ схемы оно не входит). Проверка связи: `GET /llm/status?user_id=u_1` или кнопка в журнале.

## Десять тестовых входов

Файл `tests_data/inputs.jsonl` — 10 строк `{text, user_id}`, все `u_1`. Прогон: `python -m pytest tests/test_inputs.py`.

Строка 9 — один элемент с `needs_review`: `POST /capture` сохраняет одну сущность, поэтому из шума не делается пара «задача + заметка».

| № | `item_type` | `needs_review` | Почему |
|---|---|---|---|
| 1 | `task` | нет | Простое действие: «купить кофе и бумагу» |
| 2 | `task` | нет | «завтра» — срок из текста, не выдуман |
| 3 | `task` | нет | «срочно» → `priority=high` |
| 4 | `task` | нет | Два шага созвона сведены в одну задачу |
| 5 | `note` | нет | Идея без действия |
| 6 | `note` | нет | Ссылка сохранена как заметка |
| 7 | `note` | нет | Наблюдение без действия |
| 8 | `note` | нет | Черновик без однозначного действия |
| 9 | `note` | да | Шум и два несводимых намерения |
| 10 | `task` | да | «сделай важное, разберись» — слишком общий вход |

Пустой ввод, слишком длинный текст и prompt injection проверяются отдельными тестами, не этими десятью строками.

## Данные

Файл `data/foxfocus.db` — вне git и вне образа. В Docker монтируется volume `./data`.

```bat
python -c "import sqlite3, pprint; db=sqlite3.connect(r'data\foxfocus.db'); pprint.pp(db.execute('SELECT id, action, status, error, duration_ms FROM audit_runs ORDER BY id DESC LIMIT 10').fetchall())"
python -c "import sqlite3; print([n for n, t in sqlite3.connect(r'data\foxfocus.db').execute('SELECT name, type FROM sqlite_master') if t == 'table'])"
```

Таблицы: `users`, `tasks`, `notes`, `memory_facts`, `audit_runs`. Один `POST /capture` даёт две строки журнала: `structure` и `capture`. Списки пишут в `output` только `{count: N}`.

Ручная проверка: в панели открыть карточку с меткой, поправить поля, «Подтвердить проверку». Автотест того же сценария: `python -m pytest tests/test_review.py`.

## Разработка

```
backend/app/          API, разбор, журнал
backend/migrations/   Alembic
frontend/             Vite + React + Tailwind
tests/                pytest
data/                 SQLite, не в git
```

Стек: Python 3.12, FastAPI, SQLAlchemy 2 async, aiosqlite, Alembic, Pydantic v2. Тесты ходят в тот же SQLite, во временный файл, в сеть не идут.

```bat
pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Живой вызов модели: `set LLM_E2E=1` и `python -m pytest tests/test_llm.py -k live_structure` при рабочем ключе.
