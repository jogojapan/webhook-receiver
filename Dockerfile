FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY webhook_receiver.py .
EXPOSE 5000
CMD ["python", "webhook_receiver.py"]
