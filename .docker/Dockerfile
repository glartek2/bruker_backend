FROM python:3.11

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
        curl \
        build-essential \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY . .

RUN poetry install --no-interaction

COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000
