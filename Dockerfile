FROM python:3.11.5-slim-bullseye AS builder

RUN apt-get update && apt-get upgrade -y

RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /home/appuser

ENV VIRTUALENV=/home/appuser/.venv
RUN python3 -m venv $VIRTUALENV
ENV PATH="$VIRTUALENV/bin:$PATH"

COPY --chown=appuser:appuser pyproject.toml poetry.lock ./
RUN pip install --upgrade pip setuptools poetry
RUN poetry install --no-directory

COPY --chown=appuser:appuser docker_redis_cicd/ ./docker_redis_cicd/
COPY --chown=appuser:appuser tests/ ./tests/

RUN poetry run pytest tests/unit && \
    poetry build && \
    pip install dist/*.whl


FROM python:3.11.5-slim-bullseye

RUN apt-get update && apt-get upgrade -y

RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /home/appuser

ENV VIRTUALENV=/home/appuser/.venv
RUN python3 -m venv $VIRTUALENV
ENV PATH="$VIRTUALENV/bin:$PATH"

COPY --from=builder /home/appuser/dist/*.whl ./

RUN pip install --no-cache-dir *.whl

RUN poetry run pytest tests/unit && \
    poetry build && \
    pip install dist/*.whl

CMD ["flask", "--app", "docker_redis_cicd.app", "run", "--host", "0.0.0.0", "--port", "5000"]
