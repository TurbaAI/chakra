ARG TURBA_VERSION

FROM python:3.13-slim-bookworm AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y cargo git

RUN pip install poetry==1.8.3
RUN poetry config virtualenvs.in-project true

COPY ./pyproject.toml ./setup.cfg ./setup.py ./README.md /app/
COPY ./src /app/src
COPY ./rust/ /app/rust
COPY ./schema/ /app/schema
RUN python3 -m venv .venv
RUN /app/.venv/bin/python3 -m pip install maturin
RUN /app/.venv/bin/python3 -m pip install .

RUN git clone https://github.com/facebookresearch/param
WORKDIR /app/param/et_replay
RUN git checkout 7b19f586dd8b267333114992833a0d7e0d601630
RUN /app/.venv/bin/python3 -m pip install .
WORKDIR /app/rust
RUN /app/.venv/bin/python3 -m pip install .
WORKDIR /app

FROM python:3.13-slim-bookworm AS final

ARG TURBA_VERSION
ENV TURBA_CONTAINER_VERSION=${TURBA_VERSION}

WORKDIR /workspace
COPY --from=builder /app /app

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:${PATH}"

COPY entrypoint.sh /app/entrypoint.sh
RUN ["chmod", "+x", "/app/entrypoint.sh"]

ENV INPUT_DIRECTORY="/input"
ENV OUTPUT_DIRECTORY="/output"

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["echo", " No command specified. Refer to the documentation on github @ https://github.com/TurbaAI/chakra for available commands!"]