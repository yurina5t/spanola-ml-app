FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl && apt-get clean

WORKDIR /app

COPY app/requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app/ .
#COPY app/main.py .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
