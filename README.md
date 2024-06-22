# TgMailing_bot
О проекте:
1. Telegam бот для рассылки информации о статусах выполнения работ.
3. Над проектом работали:
<a href="https://github.com/Knstxx" target="_blank">Константин</a>

Проект поднят на облачном сервере Ubuntu 22.04 LTS, функционирует в настоящее время через pyTelegramBotAPI и Yandex UserAPI. Применено и настроено логирование(модуль Logging) работы сервиса.

Tech.Stack: Python(+logging, +requests, +exceptions), pyTelegramBotAPI
# Как запустить проект:

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
