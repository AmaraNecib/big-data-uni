# Reuse the existing TP04 Python environment instead of downloading it again.
# This base contains the TP02 dependencies, not the 6 GB dataset.
FROM amaranecib/sales-bigdata-tp04:1.0

USER root
WORKDIR /app
COPY --chown=appuser:appuser tp02.py node_server.py check_connections.py /app/
RUN mkdir -p /app/report && chown appuser:appuser /app/report
USER appuser

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8000
ENTRYPOINT []
CMD ["python", "/app/node_server.py"]
