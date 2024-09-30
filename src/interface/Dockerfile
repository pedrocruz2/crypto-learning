# Usar a imagem base do Python
FROM python:3.9-slim

WORKDIR /app

COPY streamlit.py .

COPY requirements.txt .

RUN chmod -R 755 .

RUN pip install streamlit

RUN ls

EXPOSE 8501

CMD ["streamlit", "run", "streamlit.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
