FROM python:3.12-alpine3.20

RUN apk update
RUN apk add git vim sudo curl gcc make dumb-init ffmpeg

RUN pip install poetry

WORKDIR /app
COPY poetry.lock pyproject.toml .
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY srcs srcs

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["uvicorn", "srcs.main:app", "--host=0.0.0.0", "--port=3000"]
