# LMS — 32.2 Документирование и безопасность

## Документация API (drf-spectacular)
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI-схема: `/api/schema/`

Описаны все эндпоинты; нестандартные (подписка, оплата, статус оплаты) описаны вручную через `@extend_schema`
с параметрами, ответами и ошибками.

## Оплата курсов через Stripe
Сервисные функции — `users/services.py`:
- `create_stripe_product` — создание продукта
- `create_stripe_price` — создание цены (сумма переводится в копейки)
- `create_stripe_session` — создание сессии оплаты, возвращает ссылку
- `retrieve_stripe_session` — получение статуса сессии (доп. задание)

Эндпоинты:
- `POST /payments/create/` с `{"course_id": <id>}` — создаёт продукт, цену и сессию, сохраняет платёж
  (ID продукта, цены, сессии, ссылку) и возвращает ссылку на оплату
- `GET /payments/<id>/status/` — проверяет статус в Stripe и обновляет платёж

У курса добавлено поле `price` (руб.). Тестовая карта Stripe: `4242 4242 4242 4242`, любая будущая дата и CVC.

## Запуск
```
pip install -r requirements.txt
cp .env.sample .env   # указать STRIPE_API_KEY (sk_test_...)
python manage.py migrate
python manage.py loaddata groups.json
python manage.py runserver
```

## Тесты
```
coverage run --source='.' manage.py test
coverage report
```
Stripe в тестах замокан. Отчёт покрытия — `coverage_report.txt` (94%).
