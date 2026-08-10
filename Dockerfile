FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
RUN mkdir -p /app/data /app/artifacts
EXPOSE 8000
CMD ["uvicorn", "reflection_ai.api:app", "--host", "0.0.0.0", "--port", "8000"]

