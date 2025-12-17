FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY src /app/src
EXPOSE 8000
ENV PORT=8000
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
