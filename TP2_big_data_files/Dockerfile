FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY tp02.py ./

RUN mkdir -p /app/report && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
COPY --chown=appuser:appuser data/sales_6gb.csv /app/data/sales_6gb.csv
USER appuser

ENTRYPOINT ["python", "/app/tp02.py"]
CMD ["--data", "/app/data/sales_6gb.csv", "--report", "/app/report", "--skip-oom"]
