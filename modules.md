# Modules — Table for Three AI

Документация по каждому модулю проекта.
Статус связности проверен согласно `links.md`.

---

## Module №1 "Entry Point"

### File name: ../main.py

### Waiting_Input:
- HTTP-запросы от браузера/клиента (GET `/`, GET `/health`)
- WebSocket-соединения от `static/index.html` (ws `/ws`)
- Переменные окружения: `PORT` (не используется явно, порт захардкожен)

### Format_Input_Data:
- HTTP GET без тела — стандартные запросы к корневым эндпоинтам
- WebSocket фреймы — произвольный текст (строки), отправленные фронтендом
- Статические файлы монтируются из папки `static/` по пути `/static/*`

### What_Must_Be:
- Запускать ASGI-сервер через uvicorn на `0.0.0.0:5000`
- Монтировать `static/` как файловый сервер по пути `/static`
- Подключать роутер из `api/routes.py` через `app.include_router(router)` — для активации conversation API и WebSocket `/ws/{id}`
- WebSocket `/ws` в `main.py` должен быть либо временным echo для разработки, либо заменён реальным обработчиком
- Настраивать CORS при необходимости доступа с внешних доменов

### What_Is_Now:
- ✅ Сервер поднимается корректно на порту 5000
- ✅ Статика монтируется через `StaticFiles`
- ❌ `api/routes.py` **не подключён** — `app.include_router(router)` отсутствует, все conversation-эндпоинты и WS `/ws/{id}` недоступны
- ❌ WebSocket `/ws` — простой echo (`"Echo: {data}"`), не интегрирован с `ConversationManager`
- ⚠️ `import json` и `import os` присутствуют, но нигде не используются в теле файла
- ⚠️ `except: pass` в WebSocket-обработчике — все ошибки молча проглатываются

### Current_Comments:
- Главный блокер: без `app.include_router(router)` вся архитектура сервисов (`AIService`, `ConversationManager`) полностью мертва — ни один API-эндпоинт недоступен
- Рекомендуется добавить: `from api.routes import router` + `app.include_router(router)` сразу после создания `app`
- Echo WebSocket следует убрать или оставить только как dev-заглушку с явным комментарием
- Неиспользуемые импорты (`json`, `os`) нужно убрать — они создают ложное впечатление функциональности
- Для production рекомендуется вынести `port` и `host` в переменные окружения

## END MODULE №1 "Entry Point"

===

## Module №2 "API Routes"

### File name: ../api/routes.py

### Waiting_Input:
- От `main.py`: подключение через `app.include_router(router)` (сейчас отсутствует)
- POST `/conversations/create`: JSON-тело со списком `participants: List[Dict]` и строкой `mode`
- POST `/conversations/{conversation_id}/message`: параметры `conversation_id` (path) и `message` (query/body)
- GET `/conversations/{conversation_id}`: только `conversation_id` в пути
- WS `/ws/{conversation_id}`: WebSocket-соединение + JSON-фреймы `{"message": "текст"}`
- От `services/__init__.py`: экземпляры `AIService` и `ConversationManager`
- От `models.py`: `ConversationMode`, `Participant`, `ParticipantRole`, `ConversationState`

### Format_Input_Data:
- `participants` — список словарей, каждый должен соответствовать полям модели `Participant`: `{id, name, role, model_name, system_prompt}`
- `mode` — строка `"parallel"` или `"sequential"` (значения `ConversationMode`)
- WebSocket-фреймы — JSON строка `{"message": "...текст..."}`
- `conversation_id` — UUID-строка, ранее выданная при создании беседы

### What_Must_Be:
- Создавать беседы с инициализацией AI-моделей под каждого участника
- Маршрутизировать сообщения в параллельный (`process_parallel_round`) или последовательный (`process_sequential_round`) режим в зависимости от `ConversationMode`
- Поддерживать несколько одновременных WS-соединений к одной беседе через `active_connections`
- Рассылать ответы AI всем подключённым WS-клиентам (broadcast)
- Корректно убирать соединение из `active_connections` при `WebSocketDisconnect`

### What_Is_Now:
- ✅ Логика маршрутов реализована корректно
- ✅ Broadcast по всем WS-соединениям беседы работает
- ✅ `WebSocketDisconnect` обрабатывается
- ❌ Роутер **не зарегистрирован** в `main.py` — модуль существует, но недостижим
- ❌ `AIService()` инициализируется при импорте модуля без `GOOGLE_API_KEY` → упадёт с `ValueError` в момент подключения роутера
- ⚠️ `send_message` принимает `message: str` как query-параметр — для реального payload лучше использовать Pydantic Body
- ⚠️ `conversation.dict()` устарел в Pydantic v2 — нужен `conversation.model_dump()`
- ⚠️ `ParticipantRole` импортируется, но нигде в файле не используется

### Current_Comments:
- Критично: до подключения роутера необходимо убедиться, что `GOOGLE_API_KEY` задан в среде — иначе импорт провалится
- Рекомендуется перенести инициализацию `AIService` и `ConversationManager` в FastAPI dependency (через `Depends`) или lifespan-обработчик — это устранит проблему инициализации при импорте
- Для `send_message` рекомендуется принимать Body: `class MessageRequest(BaseModel): message: str`
- На GitHub существуют паттерны для WebSocket broadcast (например, через `anyio` или `asyncio.Queue`) — более надёжные, чем список соединений, при высокой нагрузке

## END MODULE №2 "API Routes"

===

## Module №3 "Data Models"

### File name: ../models.py

### Waiting_Input:
- Импортируется из: `api/routes.py`, `services/ai_service.py`, `services/conversation_manager.py`
- Данные для конструирования приходят из API-запросов (через routes.py) и внутренней логики сервисов
- Pydantic BaseModel и Field — из библиотеки `pydantic==2.6.0`

### Format_Input_Data:
- `ConversationMode`: строковые литералы `"parallel"` / `"sequential"`
- `ParticipantRole`: строковые литералы `"detective"` / `"innocent"` / `"mafia"`
- `MessageType`: строковые литералы `"user_input"` / `"ai_response"` / `"system_message"` / `"moderator_action"`
- `Participant`: `{id: str, name: str, role: ParticipantRole, model_name: str, system_prompt: str, active: bool, messages_count: int}`
- `Message`: `{id: str, type: MessageType, content: str, sender: str, timestamp: datetime, metadata: Optional[Dict]}`
- `ConversationState`: агрегирует `List[Participant]` и `List[Message]`

### What_Must_Be:
- Быть единственным источником правды по структурам данных в проекте
- Обеспечивать валидацию входящих данных API через Pydantic
- `ModerationResult` — использоваться результатом модерации из `config/moderation.json`
- `IdentityProtectionConfig` — использоваться при фильтрации ответов AI согласно правилам из `config/workflow.json`

### What_Is_Now:
- ✅ Основные модели (`Message`, `Participant`, `ConversationState`) корректны и используются в сервисах
- ✅ Enum-классы (`ConversationMode`, `ParticipantRole`, `MessageType`) определены верно
- ❌ `ModerationResult` — объявлен, но нигде в коде не используется (модерация не интегрирована)
- ❌ `IdentityProtectionConfig` — объявлен, но нигде не применяется (фильтрация AI-ответов не реализована)
- ⚠️ В `ConversationState` поле `current_speaker` всегда `None` — не обновляется в `conversation_manager.py`

### Current_Comments:
- Модели `ModerationResult` и `IdentityProtectionConfig` — заготовки под функционал, описанный в `config/moderation.json` и `config/workflow.json` соответственно; без их интеграции конфиги мертвы
- `current_speaker` в `ConversationState` стоит обновлять в `process_sequential_round` — это важно для UX при стриминге ответов
- Рекомендуется добавить `model_config = ConfigDict(use_enum_values=True)` для совместимости с Pydantic v2
- Поле `metadata` в `Message` и `ConversationState` — хорошая extensibility-точка, но без схемы его содержимое непредсказуемо

## END MODULE №3 "Data Models"

===

## Module №4 "AI Service"

### File name: ../services/ai_service.py

### Waiting_Input:
- От `services/conversation_manager.py`: вызовы `initialize_model(participant)`, `send_message(participant_id, message)`, `send_parallel_messages(participants, message)`
- От `api/routes.py`: косвенно через `ConversationManager`
- `Participant` из `models.py`: поля `id`, `model_name`, `system_prompt`, `active`
- Переменная окружения `GOOGLE_API_KEY` — обязательна при инициализации
- Стриминговые чанки текста от Google Generative AI API

### Format_Input_Data:
- `participant.model_name` — строка, имя Gemini-модели (например `"gemini-pro"`, `"gemini-1.5-flash"`)
- `participant.system_prompt` — строка, системная инструкция для модели (берётся из `config/mafia_prompt.md` через `Participant.system_prompt`)
- `message` — строка, текст сообщения пользователя или контекст из предыдущего хода
- `stream: bool` — флаг стримингового получения ответа (по умолчанию `True`)

### What_Must_Be:
- Инициализировать отдельный `GenerativeModel.start_chat()` для каждого участника беседы
- Отправлять сообщения асинхронно с поддержкой стриминга
- Параллельно опрашивать всех активных участников через `asyncio.gather`
- Накапливать стриминговые чанки в `ResponseBuffer` для возможности промежуточной отдачи клиенту
- Поддерживать очистку истории чата через `clear_history`

### What_Is_Now:
- ✅ `initialize_model` корректно создаёт отдельный chat-сессию на участника
- ✅ `send_message` со стримингом работает и накапливает `full_response`
- ✅ `send_parallel_messages` использует `asyncio.gather` — правильный подход
- ✅ `ResponseBuffer.add_chunk` вызывается при стриминге
- ❌ `get_buffered_response` объявлен, но **нигде не вызывается** извне — чанки пишутся в буфер, но не читаются в реальном времени клиентом
- ❌ При параллельном режиме стриминговые чанки идут в буфер, но WS не рассылает их по мере прихода — клиент получает только итоговый ответ
- ⚠️ `generation_config` захардкожен (`temperature=1.0`, `max_output_tokens=8192`) — не подтягивается из `config/models.json`
- ⚠️ `Message` и `MessageType` импортированы, но в теле класса не используются

### Current_Comments:
- Ключевая архитектурная проблема: стриминг реализован на уровне накопления (`add_chunk`), но не реализован на уровне проталкивания (`push`) клиенту через WebSocket — клиент видит ответ целиком после завершения генерации
- Для реального стриминга в WS нужно передавать callback или channel, куда `send_message` будет пушить чанки в реальном времени
- `config/models.json` хранит конфиг моделей, но `AIService` его не читает — стоит добавить загрузку при `initialize_model`
- Неиспользуемые импорты `Message`, `MessageType` нужно убрать
- На GitHub: паттерн async streaming через WebSocket хорошо описан в репозиториях типа `tiangolo/fastapi` (issues/examples с SSE и WS streaming)

## END MODULE №4 "AI Service"

===

## Module №5 "Conversation Manager"

### File name: ../services/conversation_manager.py

### Waiting_Input:
- От `api/routes.py`: вызовы `create_conversation`, `process_parallel_round`, `process_sequential_round`, `get_conversation`, `end_conversation`
- `participants: List[Participant]` — список объектов участников с заполненными полями (от routes.py)
- `mode: ConversationMode` — режим беседы (`PARALLEL` или `SEQUENTIAL`)
- `conversation_id: str` — UUID беседы для адресации
- `user_message: str` — текст сообщения пользователя
- Инъекция `AIService` через конструктор

### Format_Input_Data:
- `participants` — `List[Participant]`, каждый с `id`, `name`, `role`, `model_name`, `system_prompt`, `active=True`
- `user_message` — обычная строка; в sequential-режиме контекст накапливается добавлением предыдущих ответов
- Возвращаемый формат: `Dict[str, str]` — `{participant_id: response_text}`

### What_Must_Be:
- Хранить все активные беседы в памяти (`active_conversations: Dict[str, ConversationState]`)
- Инициализировать AI-модели через `AIService.initialize_model` для каждого участника при создании беседы
- В параллельном режиме: одновременно запрашивать все модели, сохранять все ответы
- В последовательном режиме: каждый следующий участник видит контекст с ответами предыдущих
- Обновлять `round_number` и `messages_count` после каждого раунда
- Корректно завершать беседу через `end_conversation`

### What_Is_Now:
- ✅ Оба режима (`parallel`, `sequential`) реализованы и логически корректны
- ✅ Контекст в sequential-режиме накапливается правильно: `current_context` расширяется ответами участников
- ✅ `round_number` и `messages_count` обновляются
- ✅ `Message`-объекты сохраняются в `conversation.messages`
- ❌ `active_conversations` хранится в памяти процесса — при перезапуске сервера все беседы теряются (нет персистентности)
- ❌ `end_conversation` выставляет `is_active = False`, но беседа остаётся в `active_conversations` — нет очистки памяти
- ⚠️ `current_speaker` в `ConversationState` не обновляется при sequential-обходе — остаётся `None`
- ⚠️ Нет защиты от гонки: два параллельных запроса к одной беседе могут вызвать конфликт состояний

### Current_Comments:
- Для production необходима персистентность: либо Redis (хранение состояния бесед), либо SQLite/PostgreSQL
- Утечка памяти: завершённые беседы (`is_active=False`) следует убирать из `active_conversations` — добавить `del self.active_conversations[conversation_id]` в `end_conversation`
- Для защиты от race condition в параллельном режиме рекомендуется `asyncio.Lock` на уровне беседы
- `current_speaker` стоит обновлять в `process_sequential_round` перед вызовом `ai_service.send_message`
- На GitHub: паттерны управления сессиями разговора можно найти в `microsoft/botframework-sdk` и аналогах — хороший источник идей для state management

## END MODULE №5 "Conversation Manager"

===

## Module №6 "Services Package"

### File name: ../services/__init__.py

### Waiting_Input:
- Импортируется из `api/routes.py`: `from services import AIService, ConversationManager`
- Транзитивно зависит от `services/ai_service.py` и `services/conversation_manager.py`

### Format_Input_Data:
- Не принимает данные напрямую — только реэкспортирует классы

### What_Must_Be:
- Служить единой точкой импорта для всего пакета `services`
- Корректно экспортировать `AIService` и `ConversationManager` через `__all__`

### What_Is_Now:
- ✅ Реэкспорт настроен корректно
- ✅ `__all__` определён
- ⚠️ При импорте пакета немедленно выполняются импорты `ai_service.py` и `conversation_manager.py`, что при инициализации `AIService` в `routes.py` на уровне модуля приведёт к исполнению кода до настройки окружения

### Current_Comments:
- Файл минимальный и выполняет свою задачу
- Если `AIService` будет перенесён в dependency injection (FastAPI `Depends`), этот файл останется без изменений — архитектурно гибко
- Можно добавить `utils` в общий реэкспорт: `from utils.buffer import ResponseBuffer` — если buffer планируется использовать напрямую из других модулей

## END MODULE №6 "Services Package"

===

## Module №7 "Response Buffer"

### File name: ../utils/buffer.py

### Waiting_Input:
- От `services/ai_service.py`: вызовы `add_chunk(participant_id, chunk)` при стриминге ответа Gemini
- От `services/ai_service.py`: вызов `get_response(participant_id)` через `get_buffered_response`
- `add_response(request_id, model_id, response)` — альтернативный путь для полных (не стриминговых) ответов с callback-логикой

### Format_Input_Data:
- `participant_id` / `request_id` — строки-идентификаторы
- `chunk` — строковый фрагмент от стримингового API
- `response` — строка полного ответа
- `callback` — async-функция `Callable[[Dict[str, Any]], Awaitable[None]]`, регистрируется через `set_callback`

### What_Must_Be:
- `add_chunk` / `get_response`: накапливать стриминговые фрагменты и выдавать накопленный текст по запросу
- `add_response` / `publish_results`: собирать полные ответы нескольких моделей, публиковать результат через callback после достижения `min_responses` или таймаута
- `get_stats`: предоставлять метрики (total_requests, completed, timedout, avg_response_time, success_rate)
- Все операции с разделяемым состоянием должны быть thread/coroutine-safe через `asyncio.Lock`

### What_Is_Now:
- ✅ `add_chunk` и `get_response` реализованы корректно, используют `asyncio.Lock`
- ✅ `add_response` с таймаутом и callback-механизмом реализован
- ✅ `get_stats` предоставляет полезные метрики
- ❌ `add_response` / `set_callback` / `publish_results` нигде не вызываются в проекте — эта часть буфера мертва
- ❌ `get_buffered_response` в `ai_service.py` существует, но нигде не вызывается — чанки пишутся в `chunk_buffer` и никогда не читаются внешним кодом
- ⚠️ `start_timeout` вызывается через `asyncio.create_task` — если event loop не запущен в момент вызова, задача потеряется без ошибки
- ⚠️ `publish_results` может вызываться под `async with self.lock`, что может привести к deadlock если callback тоже попытается захватить lock

### Current_Comments:
- Буфер имеет две изолированные системы (`chunk_buffer` для стриминга и `buffer` для полных ответов) — это создаёт путаницу и дублирование логики
- Рекомендуется определиться с архитектурой: либо стриминг через callback/queue, либо накопление и разовая отдача
- Для реального push-стриминга клиенту лучше подойдёт `asyncio.Queue` — producer (AIService) пишет чанки, consumer (WS handler) читает и отправляет
- Потенциальный deadlock в `publish_results` следует исправить — вызов callback должен происходить вне `async with self.lock`
- Хорошие reference-реализации буферизации стриминга: `openai-python` SDK (streaming iterator pattern), `httpx` streaming response

## END MODULE №7 "Response Buffer"

===

## Module №8 "Frontend Chat"

### File name: ../static/index.html

### Waiting_Input:
- WebSocket-соединение к `ws://<host>/ws` (echo-эндпоинт `main.py`)
- Пользовательский ввод из `<textarea id="msg">`
- CDN: `https://cdn.jsdelivr.net/npm/marked/marked.min.js` для рендеринга Markdown

### Format_Input_Data:
- Отправляет: произвольная строка (plain text), не JSON
- Получает: JSON `{"type": "response", "content": "Echo: <text>"}` от echo-обработчика
- Для реальной интеграции должен отправлять: `{"message": "текст"}` и получать `{"type": "responses", "data": {...}, "round": N}`

### What_Must_Be:
- Устанавливать WebSocket-соединение к `/ws/{conversation_id}` из `api/routes.py`
- Отправлять JSON `{"message": "..."}` при нажатии SEND
- Отображать ответы всех участников беседы (с разбивкой по имени/роли)
- Поддерживать стриминговый вывод (постепенное появление текста)
- Обрабатывать ошибки соединения и переподключение

### What_Is_Now:
- ✅ WebSocket-клиент работает, соединение устанавливается
- ✅ Markdown рендеринг через `marked` подключён
- ✅ Базовый UI (textarea + кнопка + список сообщений) функционален
- ❌ Подключается к `/ws` (echo), а не к `/ws/{conversation_id}` — реального AI-ответа нет
- ❌ Отправляет plain text, а не JSON `{"message": "..."}` — несовместимо с `api/routes.py`
- ❌ Нет логики создания беседы (вызов `POST /conversations/create`) перед отправкой сообщений
- ❌ Нет обработки `ws.onerror` и `ws.onclose` — при разрыве соединения UI зависает
- ⚠️ Весь код и стили в одном минифицированном файле — сложно поддерживать

### Current_Comments:
- Фронтенд является заглушкой: визуально выглядит как чат, но функционально изолирован от всей бизнес-логики
- Минимальный план интеграции: (1) при загрузке страницы вызвать `POST /conversations/create`, получить `conversation_id`, (2) открыть WS к `/ws/{conversation_id}`, (3) отправлять JSON `{"message": "..."}`, (4) отображать ответы по участникам
- Рекомендуется разбить на отдельные файлы: `index.html`, `style.css`, `app.js`
- Для более богатого UI можно использовать `lit-html` или `petite-vue` — лёгкие альтернативы React без сборки

## END MODULE №8 "Frontend Chat"

===

## Module №9 "Configuration Files"

### File name: ../config/

### Waiting_Input:
- `mafia_prompt.md` — читается разработчиком/агентом и вставляется в `Participant.system_prompt` вручную (не загружается автоматически)
- `models.json` — должен читаться `AIService` при инициализации модели (сейчас не читается)
- `workflow.json` — содержит настройки режима, таймаута, фильтрации ответов (сейчас не читается)
- `moderation.json` — содержит конфиг пре/пост-модерации (сейчас не читается)

### Format_Input_Data:
- `mafia_prompt.md`: Markdown-файл с системным промптом; шаблонные переменные `[RANDOM_ID]`, `[CHARACTER]` должны подставляться при создании участника
- `models.json`: JSON `{models: [{id, type, name, endpoint, api_key, selectors}]}`
- `workflow.json`: JSON `{settings: {mode, response_timeout, min_responses, response_strategy}, identity_protection: {enabled, rules: [{pattern, action}]}}`
- `moderation.json`: JSON `{premoderation: {...}, postmoderation: {...}, pii_redaction: {...}}`

### What_Must_Be:
- `mafia_prompt.md` — загружаться автоматически и подставляться как `system_instruction` при `initialize_model`, с заполнением переменных (`[RANDOM_ID]`, `[CHARACTER]`)
- `models.json` — определять доступные AI-модели и их параметры; `AIService` должен выбирать модель по `participant.model_name`
- `workflow.json` — `response_timeout` и `min_responses` должны передаваться в `ResponseBuffer`; правила `identity_protection` — применяться к ответам AI перед отправкой клиенту
- `moderation.json` — использоваться слоем модерации (отдельный сервис) для фильтрации входящих и исходящих сообщений

### What_Is_Now:
- ✅ `mafia_prompt.md` — содержательный и хорошо структурированный промпт
- ✅ `workflow.json` — структура корректна, правила identity_protection готовы к применению
- ✅ `moderation.json` — структура описана, ссылается на `openai_moderation` API
- ❌ Ни один конфиг-файл **не загружается** в коде автоматически — все настройки в них мертвы
- ❌ `workflow.json` задаёт `response_timeout: 8.0` и `min_responses: 2`, но `ResponseBuffer` инициализируется с дефолтами, не читая этот файл
- ❌ `moderation.json` ссылается на `openai_moderation` API, которое не установлено и не интегрировано
- ❌ `mafia_prompt.md` содержит шаблонные плейсхолдеры `[RANDOM_ID]`, `[CHARACTER]` — механизма их подстановки нет

### Current_Comments:
- Конфигурационный слой полностью готов концептуально, но полностью отвязан от исполняемого кода
- Первый шаг: добавить в `AIService.__init__` загрузку `config/workflow.json` через `json.load` и передать `response_timeout`/`min_responses` в `ResponseBuffer`
- Для `mafia_prompt.md`: добавить загрузку файла и `str.replace("[RANDOM_ID]", str(uuid4())[:8])` при инициализации участника
- `moderation.json` использует OpenAI Moderation API — перед интеграцией нужно решить, нужен ли этот внешний API, или заменить на встроенные инструменты Gemini
- Рекомендуется создать `config/loader.py` — единый модуль для загрузки и валидации всех конфиг-файлов через Pydantic-модели

## END MODULE №9 "Configuration Files"

===

## Сводная таблица статуса модулей

| №  | Модуль                       | Файл                              | Связность | Статус       |
|----|------------------------------|-----------------------------------|-----------|--------------|
| 1  | Entry Point                  | main.py                           | ❌ Частичная | 🔴 Блокер    |
| 2  | API Routes                   | api/routes.py                     | ❌ Не подключён | 🔴 Блокер |
| 3  | Data Models                  | models.py                         | ✅ Полная  | 🟡 Заготовки |
| 4  | AI Service                   | services/ai_service.py            | ✅ Полная  | 🟡 Стриминг мёртв |
| 5  | Conversation Manager         | services/conversation_manager.py  | ✅ Полная  | 🟡 Нет персистентности |
| 6  | Services Package             | services/__init__.py              | ✅ Полная  | 🟢 OK        |
| 7  | Response Buffer              | utils/buffer.py                   | ⚠️ Частичная | 🟡 Половина кода не используется |
| 8  | Frontend Chat                | static/index.html                 | ❌ Echo only | 🔴 Не интегрирован |
| 9  | Configuration Files          | config/                           | ❌ Не загружаются | 🔴 Мертвы  |
