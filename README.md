# Сервис распознавания содержимого платежных счетов
Программное обеспечение для получения данных из сканов платежных документов в JSON-формате через телеграм-бота.

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZzdvYTdqMHViM3hsbWxkdGk2dDcwY3o5MGN2b3MxMWFwOWFhbWt3eSZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/j0AIRCrezHXxkvaEFt/giphy.gif" width="30"/> ![Static Badge](https://img.shields.io/badge/WhyWhiteSnow-a?label=Team&labelColor=rgb(118%2C%2083%2C%2056))
![GitHub top language](https://img.shields.io/github/languages/top/WhyWhiteSnow/TeleHack2025)

<div align="center">
  <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzh4NWgzNnNiNmtkenNkc2xxazY4NnJieHE4eGpxZ3E2eXptaGVpdCZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/oifKB3IrjgeRZzZzrY/giphy.gif" width="200"/>
</div>

## Запуск приложения
### Запуск Docker-контейнера
1. Клонирование репозитория

```git clone https://github.com/WhyWhiteSnow/TeleHack2025.git```

2. Создание контейнера

```docker compose up —build -d```

### Запуск из консоли
1. Установка пакетного менеджера

```pip install uv```
   
2. Клонирование репозитория
   
```git clone https://github.com/WhyWhiteSnow/TeleHack2025.git```

3. Переход в директорию сервера

```cd TeleHack2025/documentviewer-api```

4. Установка зависимостей

```uv sync```

5. Запуск сервера

```uv run uvicorn main:app```

6. Переход в директорию бота

```cd TeleHack2025/telegrambot```

7. Переименовать файл .env.example в .env, вставить токен бота и адрес сервера с портом 8000

8. Запуск телеграм-бота

```uv run main.py```

## Принцип работы
Телеграм-бот используется в качестве UI-интерфейса для взаимодействия с сервером, OCR-сканер находится на сервере.
Созданному телеграм-боту пользователь отправляет pdf-файл или изображение со сканом платежного документа, который позже отправляется на сервер, где OCR-сканер считывает содержимое и возвращает пользователю в виде JSON с сохранением иерархической структуры документа.

## Используемый стэк
Все приложение разрабатывалось на python с использованием библиотек для разработки отдельных сервисов и пакетного менеджера uv. Для контейнеризации использовался Docker.
### Телеграм-бот
Написан на Aiogram, позволяет отправлять асинхронные запросы серверу.
### OCR-сканер
Написан на PyTesseract. CV-модуль, считывающий содержимое документа. API написано на FastAPI.
