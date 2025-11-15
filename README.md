# Сервис распознавания содержимого платежных счетов
Программное обеспечение для получения данных из сканов платежных документов в удобочитаемом виде.

![Static Badge](https://img.shields.io/badge/WhyWhiteSnow-a?label=Team&labelColor=rgb(118%2C%2083%2C%2056))
![GitHub top language](https://img.shields.io/github/languages/top/WhyWhiteSnow/TeleHack2025)

<div id="header" align="center">
  <img src="https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3N3ozam41aDRpb3A3eW93OTlneGN3c3JjZDJidGRmMmdjNDNtam5kaSZlcD12MV9zdGlja2Vyc190cmVuZGluZyZjdD10cw/WsvbZxS6Se8wAa41p2/giphy.gif" width="230" />
</div>

## Принцип работы
Через существующего телеграм-бота отправляется pdf-файл со сканом платежного документа, который позже отправляется на сервер, 
где обученная модель считывает содержимое файла и возвращает пользователю в виде JSON с сохранением иерархической структуры документа.
## Используемый стэк
Бот и сервер целиком разрабатывались на python с использованием библиотек.
### Телеграм-бот
Написан на aiogram с обеспечением асинхронного взаимодействия с сервером.
### Сервер
Серверное приложение разработано на FastAPI, взаимодействует с телеграм-ботом, также содержит модель для обработки файлов.
### OCR-сканер
Написан на python, обрабатывает содержимое файла
