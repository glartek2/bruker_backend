FROM python:alpine@sha256:b4d299311845147e7e47c970566906caf8378a1f04e5d3de65b5f2e834f8e3bf

WORKDIR /deploy/app

# RUN apk add curl build-base postgresql-client
RUN apk add curl postgresql-client

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY . .

RUN poetry install --no-interaction

COPY ./.docker/entrypoint.sh /deploy/entrypoint.sh
RUN chmod +x /deploy/entrypoint.sh

# if exec /deploy/entrypoint.sh fails then you probably need to save the script
# with LF (Unix) linebreaks and not CRLF (DOS) linebreaks
ENTRYPOINT ["/deploy/entrypoint.sh"]

EXPOSE 8000
