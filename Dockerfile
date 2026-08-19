FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY Task3/faiss_index ./Task3/faiss_index
COPY Task5/rag_bot_secure.py ./Task5/rag_bot_secure.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
