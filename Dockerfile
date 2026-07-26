# Serves the API only. Deliberately does NOT include the agent's heavy
# dependencies (langgraph, chromadb, sentence-transformers, torch) - this
# container reads a pre-computed JSON file, it never runs the agent live.
# The agent itself runs on a schedule in CI (see .github/workflows/).
FROM python:3.11-slim

WORKDIR /app

COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api/ ./api/
COPY data/latest_run.json ./data/latest_run.json

EXPOSE 8000

# Render (and most PaaS) inject the real port via $PORT - fall back to 8000 locally.
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
