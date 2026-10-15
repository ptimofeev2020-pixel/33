# LMS — 33 Celery

## Что добавлено
- `config/celery.py` — приложение Celery, настройки читаются из `settings.py` с префиксом `CELERY_`
- Адреса Redis (брокер и бэкенд результатов) вынесены в `.env` (`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`)
- `CELERY_TIMEZONE` совпадает с `TIME_ZONE` проекта (Europe/Moscow)
- `lms/tasks.py` — `send_course_update_email`: письмо всем подписчикам курса об обновлении материалов
- Задача вызывается через `.delay()` после успешного обновления курса или урока (`perform_update`)
- Доп. задание: письмо уходит, только если курс не обновлялся больше 4 часов (`timezone.now() - updated_at`)
- `users/tasks.py` — `block_inactive_users`: блокирует (`is_active=False`) пользователей, не заходивших
  больше месяца по `last_login`; обновление одним запросом (батчем)
- Расписание celery-beat в `CELERY_BEAT_SCHEDULE`: проверка неактивных пользователей каждый день в 00:00

## Запуск
Нужен запущенный Redis.
```
pip install -r requirements.txt
cp .env.sample .env
python manage.py migrate
python manage.py loaddata groups.json
python manage.py runserver
```
В отдельных терминалах:
```
celery -A config worker -l info
celery -A config beat -l info
```
На Windows воркер запускать так: `celery -A config worker -l info -P solo`

## Тесты
```
coverage run --source='.' manage.py test
coverage report
```
