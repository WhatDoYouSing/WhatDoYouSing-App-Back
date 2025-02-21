# Python 3.9.6 기반 이미지 사용
FROM python:3.9.6-alpine
ENV PYTHONUNBUFFERED=1

# 앱 디렉토리 생성 및 설정
RUN mkdir /app
WORKDIR /app

# MySQL 클라이언트 의존성 설치
RUN apk add --no-cache mariadb-connector-c-dev
RUN apk update && apk add --no-cache \
    python3 \
    python3-dev \
    mariadb-dev \
    build-base && \
    pip3 install mysqlclient && \
    apk del python3-dev mariadb-dev build-base

# 의존성 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . /app/