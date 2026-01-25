FROM  ghcr.io/astral-sh/uv:debian

WORKDIR app/
COPY . .
RUN rm -rf .venv && uv venv
RUN if [ ! -d ".venv" ]; then uv venv; fi
RUN uv pip install -e .

