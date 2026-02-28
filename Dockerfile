# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
 && python -m pip wheel --wheel-dir=/wheels -r /app/requirements.txt


FROM python:3.11-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Non-root user
RUN addgroup --system appuser \
 && adduser --system --ingroup appuser --home /app appuser

# Install deps from wheels only (small final image)
COPY --from=builder /wheels /wheels
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels -r /app/requirements.txt \
 && rm -rf /wheels

# Copy only necessary project files
COPY --chown=appuser:appuser manage.py /app/manage.py
COPY --chown=appuser:appuser teamflow /app/teamflow
COPY --chown=appuser:appuser core /app/core
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh

# Production defaults (override via runtime env)
ENV DJANGO_SETTINGS_MODULE=teamflow.settings.production \
    SECRET_KEY=change-me

RUN mkdir -p /app/staticfiles /app/media \
 && chown -R appuser:appuser /app/staticfiles /app/media \
 && chmod +x /app/entrypoint.sh

USER appuser

# Collect static at build time
RUN python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "teamflow.wsgi:application", "--workers", "3", "--timeout", "120", "--bind", "0.0.0.0:8000"]

