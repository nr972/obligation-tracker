FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY ot_app/ ot_app/
COPY ot_frontend/ ot_frontend/
COPY data/sample/ data/sample/

RUN pip install --no-cache-dir .

RUN mkdir -p data/uploads

EXPOSE 8000

CMD ["uvicorn", "ot_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
