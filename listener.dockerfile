FROM python:3.10-alpine

ARG SEQ_SERVER_API_KEY

# Set the timezone to UTC
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Update the package repository and install curl
RUN apk update && apk add curl bash tzdata

WORKDIR /app/

ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.1.5/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=9aeb41e00cc7b71d30d33c57a2333f2c2581a201

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

RUN pip install --force-reinstall httpcore==0.15
RUN pip install "uvicorn[standard]"

RUN curl -fsSLO "$SUPERCRONIC_URL" \
    && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
    && chmod +x "$SUPERCRONIC" \
    && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
    && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

# Create logs directory if it doesn't exist
RUN mkdir -p /app-logs/

COPY ./src /app

# Replace {{SEQ_SERVER_API_KEY}} with environment variable SEQ_SERVER_API_KEY in seqlog.yml
RUN sed -i "s/{{SEQ_SERVER_API_KEY}}/${SEQ_SERVER_API_KEY}/g" /app/config/seqlog.yml

ENV PYTHONPATH=/app

CMD ["python", "-m", "web3_listener"]
