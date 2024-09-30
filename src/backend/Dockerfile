FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN chmod -R 755 .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

RUN ls

CMD ["python3", "main.py"]
