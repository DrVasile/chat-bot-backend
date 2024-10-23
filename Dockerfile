FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "chatbot.py", "--server.port=8080", "--server.headless=true"]
