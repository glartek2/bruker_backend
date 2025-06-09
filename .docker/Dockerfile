FROM python:alpine@sha256:18159b2be11db91f84b8f8f655cd860f805dbd9e49a583ddaac8ab39bf4fe1a7

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
