# architecture-pro-ai-rag

Проектная работа 7 спринта курса «Программный архитектор» от Яндекс Практикума.

Кейс: компания QuantumForge Software - разработка RAG-бота для корпоративной базы знаний с исследованием моделей, эмбеддингов и векторных баз.

## Структура

- [project_overview.md](project_overview.md) - описание кейса, требования и общие шаги
- [how_to_complete_project.md](how_to_complete_project.md) - требования к сдаче работы
- [Task1/](Task1/) - Исследование моделей и инфраструктуры
- [Task2/](Task2/) - Подготовка базы знаний
- [Task3/](Task3/) - Создание векторного индекса базы знаний
- [Task4/](Task4/) - Реализация RAG-бота с техниками промптинга
- [Task5/](Task5/) - Запуск и демонстрация работы бота
- [Task6/](Task6/) - Автоматическое ежедневное обновление базы знаний
- [Task7/](Task7/) - Аналитика покрытия и качества базы знаний
- [images/](images/) - общие картинки кейса

## Docker

Бот упакован в минимальный Docker-образ: [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml), [requirements.txt](requirements.txt), точка входа - [app.py](app.py).

Образ включает готовый индекс FAISS ([Task3/faiss_index/](Task3/faiss_index/)) и защищённого бота с тремя слоями защиты от prompt-инъекций ([Task5/rag_bot_secure.py](Task5/rag_bot_secure.py)). Запуск:

```
docker compose up --build
```

Локальная LLM (`Qwen/Qwen2.5-0.5B-Instruct`) и модель эмбеддингов (`BAAI/bge-m3`) скачиваются при первом запуске и кэшируются в именованном томе `huggingface_cache`, чтобы не загружаться заново при каждом перезапуске контейнера. Если задать переменную окружения `OPENAI_API_KEY`, бот переключится на облачную `gpt-4o-mini`.

## Как сдавать

Работа сдаётся через пул-реквест из ветки `rag` в основную ветку. Подробнее - в [how_to_complete_project.md](how_to_complete_project.md).
