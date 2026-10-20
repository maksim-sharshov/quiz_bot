FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /bot

COPY requirements.txt .

RUN rm -rf /etc/localtime \
    && ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime \
    && echo "Europe/Moscow" > /etc/timezone

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /usr/sbin/nologin botuser

COPY --chown=botuser:botuser . .

USER botuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "healthcheck.py"]

CMD ["python", "bot.py"]
