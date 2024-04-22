FROM python:3.11.5-slim-bullseye AS builder

RUN apt-get update && apt-get upgrade -y

RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /home/appuser

ENV VIRTUALENV=/home/appuser/.venv
RUN python3 -m venv $VIRTUALENV
ENV PATH="$VIRTUALENV/bin:$PATH"

COPY --chown=appuser:appuser pyproject.toml poetry.lock README.md ./
RUN pip install --upgrade pip setuptools poetry
RUN poetry install --no-directory



COPY --chown=appuser:appuser docker_redis_cicd/ ./docker_redis_cicd/
COPY --chown=appuser:appuser tests/ ./tests/

RUN poetry run pytest tests/unit && poetry build
RUN python -m pip install dist/docker_redis_cicd*.whl


FROM python:3.11.5-slim-bullseye

RUN apt-get update && apt-get upgrade -y

RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /home/appuser

ENV VIRTUALENV=/home/appuser/.venv
RUN python3 -m venv $VIRTUALENV
ENV PATH="$VIRTUALENV/bin:$PATH"

COPY --from=builder /home/appuser/dist/docker_redis_cicd*.whl ./

RUN python -m pip install --upgrade pip setuptools && python -m pip install --no-cache-dir docker_redis_cicd*.whl

CMD ["flask", "--app", "docker_redis_cicd.app", "run", "--host", "0.0.0.0", "--port", "5000"]
