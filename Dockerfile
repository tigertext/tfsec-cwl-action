FROM python:3.8-slim AS builder
COPY . /app

WORKDIR /app
RUN pip install --target=/app boto3 requests

FROM gcr.io/distroless/python3-debian11
COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH /app

CMD ["/app/main.py"]