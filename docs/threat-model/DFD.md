# DFD — Data Flow Diagram (Quiz Builder)

## Диаграмма (Mermaid)

```mermaid
flowchart LR
  U[Browser User] -->|F1: HTTPS /auth (creds)| API[FastAPI App]
  U -->|F2: HTTPS /api (Bearer JWT)| API

  subgraph Edge[Trust Boundary: Edge/Internet]
    API
  end

  subgraph Core[Trust Boundary: App Core]
    API -->|F4: FS read (index)| STATIC[(Static Files)]
    API -->|F6: stdout/json| LOG[(Logs/Monitoring)]
  end

  subgraph Data[Trust Boundary: Secrets & Data]
    API -->|F5: SECRET_KEY| JWT[(JWT Secret)]
    API -->|F3: CRUD models| DB[(Data Store: In-Memory / Future DB)]
  end

  classDef boundary stroke-dasharray: 5 5;
  class Edge,Core,Data boundary;
```

## Список потоков

| ID | Откуда → Куда          | Канал/Протокол         | Данные/PII                            | Комментарий |
|----|-------------------------|-------------------------|---------------------------------------|-------------|
| F1 | Browser → FastAPI       | HTTPS POST /auth/*      | creds (username, password)            | Регистрация/логин |
| F2 | Browser → FastAPI       | HTTPS /api/v1/*         | Bearer JWT (access_token)             | CRUD квизы/вопросы, публичные submit |
| F3 | FastAPI → Data Store    | python driver / TCP     | users, quizzes, questions, results    | Сейчас in-memory; далее БД |
| F4 | FastAPI → Static Files  | local FS (read-only)    | —                                     | Выдача `index.html`, статики |
| F5 | FastAPI → JWT Secret    | local env/KMS           | SECRET_KEY                            | Подпись/проверка JWT |
| F6 | FastAPI → Logs          | stdout/json             | request_id, error.code, метаданные    | Без PII по умолчанию |
