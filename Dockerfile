FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY src ./src
COPY app ./app
COPY configs ./configs
COPY scripts ./scripts
COPY docs ./docs
COPY contributions ./contributions
COPY .streamlit ./.streamlit

RUN python -m pip install --upgrade pip && \
    python -m pip install -e ".[dashboard]"

RUN useradd --create-home --uid 10001 dynnav && \
    mkdir -p /workspace/results && \
    chown -R dynnav:dynnav /workspace

USER dynnav

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)" || exit 1

CMD ["streamlit", "run", "app/dashboard.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]
