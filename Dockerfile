FROM python:3.11-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir hatchling
COPY pyproject.toml .
COPY src/ src/
RUN pip wheel --no-deps --wheel-dir /wheels .

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# 非rootユーザー
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
