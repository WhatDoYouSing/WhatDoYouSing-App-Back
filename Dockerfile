# ─── Debian 기반 Python 3.11 ─────────────────────────
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        openjdk-17-jdk-headless \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefer-binary -r requirements.txt \
 && apt-get purge -y --auto-remove build-essential

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]