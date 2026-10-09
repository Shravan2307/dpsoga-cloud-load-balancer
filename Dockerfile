FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

ARG INSTALL_AWS=0
COPY requirements.txt .
COPY requirements-aws.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_AWS" = "1" ]; then pip install --no-cache-dir -r requirements-aws.txt; fi
COPY . .

EXPOSE 8000 8501
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
