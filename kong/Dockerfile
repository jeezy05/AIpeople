FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests

COPY setup-kong.py .

CMD ["python", "setup-kong.py"]

