FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn sentence-transformers

COPY app.py .

ENV EMBEDDING_MODEL=intfloat/multilingual-e5-small

EXPOSE 80

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
