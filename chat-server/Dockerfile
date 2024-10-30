FROM python:3.12-alpine3.20

RUN apk update
RUN apk add git vim sudo curl gcc make dumb-init ffmpeg

RUN pip install poetry

WORKDIR /app/srcs
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi
COPY . .

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=3000"]
