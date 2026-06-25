# Container image for Fly.io / EC2 / Poridhi Lab / any Docker host.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PORT=8000
EXPOSE 8000

# Honor the platform's $PORT if injected, default 8000.
CMD ["sh", "-c", "gunicorn app.main:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 30"]
