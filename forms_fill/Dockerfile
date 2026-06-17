# Forms-fill service image (Railway-ready).
# Includes LibreOffice so DOCX→PDF conversion works in the container (KTD3).
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY forms_fill ./forms_fill
COPY fixtures ./fixtures

RUN pip install --no-cache-dir .

ENV FORMS_DATA_PROVIDER=fixture
EXPOSE 8080

# HTTP service (POST /fill). Override CMD to run the `forms` CLI instead.
CMD ["uvicorn", "forms_fill.api:app", "--host", "0.0.0.0", "--port", "8080"]
