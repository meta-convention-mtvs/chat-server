FROM python

RUN pip install poetry

WORKDIR /app/srcs
COPY pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi
COPY . .

ENTRYPOINT ["python"]
