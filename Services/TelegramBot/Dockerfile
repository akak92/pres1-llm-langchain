FROM python:3.11-slim

WORKDIR /app

# Evitar que Python bufee stdout (para ver bien los logs)
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_bot.py .

CMD ["python", "telegram_bot.py"]
