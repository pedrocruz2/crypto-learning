FROM python:3.9-slim

WORKDIR /app

COPY streamlit.py /app/

COPY requirements.txt /app/

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

RUN ls -la /app

CMD ["streamlit", "run", "app/streamlit.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
