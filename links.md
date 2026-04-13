# Project Link Tree — Table for Three AI

Дерево связей между файлами проекта с пояснениями для агента.
Каждая стрелка `→` означает «импортирует / использует / обращается к».

---

## Точка входа

```
main.py                          # Запуск приложения: uvicorn на 0.0.0.0:5000
  → fastapi (FastAPI)            # Создаёт ASGI-приложение
  → fastapi.staticfiles          # Монтирует /static → папку static/
  → api/routes.py                # (не подключён напрямую в текущей версии main.py;
                                 #  routes.py готов к подключению через app.include_router)
```

> ⚠️ **Агенту:** `api/routes.py` содержит полный роутер с conversation API и WebSocket,
> но в `main.py` пока не подключён через `app.include_router(router)`.
> Чтобы активировать REST и WS эндпоинты, нужно добавить этот вызов в `main.py`.

---

## API-слой

```
api/routes.py                        # REST + WebSocket маршруты
  → fastapi (APIRouter, WebSocket…)  # Фреймворк маршрутизации
  → models.py                        # ConversationMode, Participant,
                                     #   ParticipantRole, ConversationState
  → services/__init__.py             # Реэкспортирует AIService и ConversationManager
      → services/ai_service.py
      → services/conversation_manager.py
```

Эндпоинты в `api/routes.py`:
- `POST /conversations/create`         — создать беседу с участниками
- `POST /conversations/{id}/message`   — отправить сообщение в беседу
- `GET  /conversations/{id}`           — получить состояние беседы
- `WS   /ws/{conversation_id}`         — WebSocket для real-time обновлений

---

## Сервисы

```
services/__init__.py                    # Пакетный реэкспорт
  → services/ai_service.py             # AIService — работа с Google Gemini
  → services/conversation_manager.py  # ConversationManager — состояние бесед
```

```
services/ai_service.py
  → google.generativeai                # SDK для Gemini (env: GOOGLE_API_KEY)
  → models.py                          # Message, Participant, MessageType
  → utils/buffer.py                    # ResponseBuffer.add_chunk() / get_response()
                                       #   — буферизация стримингового ответа
  ↓ используется в:
      services/conversation_manager.py
      api/routes.py
```

```
services/conversation_manager.py
  → models.py                          # ConversationState, ConversationMode,
                                       #   Participant, Message, MessageType
  → services/ai_service.py            # AIService.send_message(),
                                       #   AIService.send_parallel_messages()
  ↓ используется в:
      api/routes.py
```

---

## Утилиты

```
utils/__init__.py                      # Пустой пакетный файл (нет реэкспортов)

utils/buffer.py                        # ResponseBuffer
  → asyncio                            # Блокировки (asyncio.Lock) и задачи
  → time                               # Хронометраж ответов для мониторинга
  Методы:
    add_chunk(participant_id, chunk)   # Накапливает стриминговый фрагмент
    get_response(participant_id)       # Возвращает и очищает накопленный ответ
    add_response(req_id, model_id, r)  # Полный ответ в буфер (с таймаутом)
    publish_results(request_id)        # Вызывает callback и очищает буфер
    get_stats()                        # Метрики: запросы, таймауты, avg_time
  ↓ используется в:
      services/ai_service.py
```

---

## Модели данных

```
models.py                              # Все Pydantic-схемы проекта
  Enums:
    ConversationMode                   # "parallel" | "sequential"
    ParticipantRole                    # "detective" | "innocent" | "mafia"
    MessageType                        # "user_input" | "ai_response" |
                                       #   "system_message" | "moderator_action"
  Models:
    Message                            # id, type, content, sender, timestamp
    Participant                        # id, name, role, model_name,
                                       #   system_prompt, active, messages_count
    ConversationState                  # id, mode, participants, messages,
                                       #   current_speaker, round_number, is_active
    ModerationResult                   # is_safe, confidence, categories
    IdentityProtectionConfig           # Маскировка имён, локаций, чувств. данных
  ↓ используется в:
      api/routes.py
      services/ai_service.py
      services/conversation_manager.py
```

---

## Конфигурация

```
config/models.json                     # Описания AI-моделей (id, type, endpoint,
                                       #   api_key-placeholder, selectors)
                                       # ⚠️ Агенту: поле api_key здесь — заглушка.
                                       #   Реальный ключ берётся из env GOOGLE_API_KEY

config/mafia_prompt.md                 # Системные промпты для ролей Мафии:
                                       #   Detective, Innocent, Mafia
                                       # Используются как system_instruction
                                       #   при инициализации модели Gemini

config/moderation.json                 # Настройки модерации контента
                                       # (структура описана, интеграция — в roadmap)

config/workflow.json                   # Описание рабочего процесса (flow конфиг)
                                       # (структура описана, интеграция — в roadmap)
```

---

## Фронтенд

```
static/index.html                      # SPA-чат (HTML + vanilla JS)
  → wss://<host>/ws                    # WebSocket к main.py (простое echo)
  → https://cdn.jsdelivr.net/…/marked  # Рендеринг Markdown в сообщениях
  ⚠️ Агенту: фронт подключается к /ws (echo-эндпоинт в main.py),
             а не к /ws/{conversation_id} из api/routes.py.
             Для полной интеграции нужно синхронизировать оба.

static/mermaid_map.html                # Визуальная Mermaid-карта архитектуры
  → https://cdn.jsdelivr.net/…/mermaid # Рендеринг диаграммы на клиенте
  (Вспомогательный файл, не часть логики приложения)
```

---

## Инфраструктура

```
requirements.txt                       # Зависимости pip:
  fastapi==0.110.0                     # Web-фреймворк
  uvicorn[standard]==0.29.0            # ASGI-сервер (с uvloop, httptools)
  httpx==0.27.0                        # Async HTTP-клиент
  websockets==12.0                     # WebSocket-протокол
  pydantic==2.6.0                      # Валидация данных
  playwright==1.42.0                   # Browser automation (в roadmap)
  pytest / pytest-asyncio              # Тестирование (тесты ещё не написаны)
  google-generativeai                  # Gemini SDK (добавлен при настройке)
  gunicorn                             # Production WSGI/ASGI сервер

.replit                                # Конфигурация Replit: python-3.12, порт 5000
Dockerfile / docker-compose.yml        # Контейнеризация (не используется в Replit)
```

---

## Граф зависимостей (сводка)

```
main.py
└── static/                  (статика через FastAPI.mount)
    ├── index.html            → WebSocket /ws (echo, main.py)
    └── mermaid_map.html      (только визуализация)

api/routes.py
├── models.py
└── services/
    ├── __init__.py
    ├── ai_service.py
    │   ├── models.py
    │   ├── utils/buffer.py
    │   └── google-generativeai  ← env: GOOGLE_API_KEY
    └── conversation_manager.py
        ├── models.py
        └── ai_service.py

config/
├── models.json              ← читается ai_service (в расширенной версии)
├── mafia_prompt.md          ← system_prompt для Participant
├── moderation.json          ← не интегрирован
└── workflow.json            ← не интегрирован
```
