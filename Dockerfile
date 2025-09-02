FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# JDK 제거, 최소 의존성만
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefer-binary --no-cache-dir -r requirements.txt \
 && python -m spacy download en_core_web_sm \
 && apt-get purge -y --auto-remove build-essential pkg-config \
 && rm -rf /root/.cache/pip

COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]