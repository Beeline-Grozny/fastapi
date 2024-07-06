FROM python:slim
LABEL authors="exizman"
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    libgstreamer1.0-0 \
    libx264-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
