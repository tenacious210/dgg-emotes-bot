FROM python:3.11-alpine

WORKDIR /dgg-emotes-bot
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV LOGLEVEL=DEBUG

RUN adduser -D appuser
RUN mkdir -p /dgg-emotes-bot/config && chown -R appuser:appuser /dgg-emotes-bot/config
USER appuser

ENTRYPOINT ["python", "main.py"]