# NFR — Приёмка (BDD)

Feature: Единый формат ошибок
  Scenario: 404 Not Found в контракте ошибок
    Given сервис запущен
    When клиент запрашивает GET /items/999
    Then статус 404 и тело содержит error.code="not_found"

Feature: Валидация входных данных
  Scenario: 422 Validation Error в контракте ошибок
    Given сервис запущен
    When клиент отправляет POST /items с пустым name
    Then статус 422 и error.code="validation_error" и details не пустой

Feature: Отсутствие IDOR
  Scenario: Чужой пользователь не видит чужой квиз
    Given User A создал quiz #X
    And User B вошёл в систему
    When B запрашивает GET /api/v1/quizzes/X
    Then статус 403 и error.code="forbidden"

Feature: JWT TTL
  Scenario: Токен имеет срок жизни не более 15 минут
    Given пользователь успешно прошёл логин
    When клиент декодирует токен без проверки подписи
    Then поле exp ≤ now()+15min

Feature: Лимит логинов
  Scenario: Превышение порога попыток логина
    Given 5 неуспешных попыток логина за последние 60 секунд
    When выполняется 6-я попытка
    Then статус 429 и error.code="too_many_requests"
