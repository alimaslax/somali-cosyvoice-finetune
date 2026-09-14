FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY . .

ENV PORT=7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "wsgi:application"]
