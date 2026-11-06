FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    QT_QPA_PLATFORM=xcb \
    DISPLAY=:99

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        curl \
        fluxbox \
        libegl1 \
        libgl1 \
        libxcb-icccm4 \
        libx11-xcb1 \
        libxcb-cursor0 \
        libxcb-keysyms1 \
        libxcb-shape0 \
        libxcb-xinerama0 \
        libxkbcommon-x11-0 \
        novnc \
        websockify \
        x11vnc \
        xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/database /data

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh \
    && chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 6080 5900

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail http://127.0.0.1:6080/vnc.html || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
