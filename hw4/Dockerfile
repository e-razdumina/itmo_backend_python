FROM python:3.12-slim

WORKDIR /demo_service

RUN apt-get update && apt-get install -y \
    libpq-dev gcc

COPY .. /demo_service

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "demo_service.api.main:create_app", "--host", "0.0.0.0", "--port", "8000",  "--reload"]