from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import numpy as np
import pandas as pd
import yfinance as yf
import datetime
import os

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, GRU
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
from tensorflow.keras.models import load_model

# Definir a aplicação FastAPI
app = FastAPI(
    title="API de Previsão do Preço do Bitcoin",
    description="Uma API para prever e reentreinar o modelo de previsão do preço do Bitcoin.",
    version="1.0"
)

# Inicializar conexão com SQLite e criar tabela de logs
conn = sqlite3.connect('logs.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS prediction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        occurrence_type TEXT,
        timestamp TEXT,
        start_date TEXT,
        end_date TEXT
    )
''')
conn.commit()

# Definir os modelos de dados para as entradas da API
class PredictionRequest(BaseModel):
    period: int

class RetrainRequest(BaseModel):
    start_date: str
    end_date: str

# Carregar o modelo salvo
model_path = 'model_close.h5'
if os.path.exists(model_path):
    model = load_model(model_path)

# Endpoint raiz
@app.get("/")
def read_root():
    return {"message": "API de Previsão do Preço do Bitcoin"}

# Endpoint para realizar a previsão
@app.post("/predict/")
def predict_price(request: PredictionRequest):
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Modelo não encontrado. Reentreine o modelo.")

    period = request.period

    # Registrar a requisição de previsão no banco de dados
    timestamp = datetime.datetime.now().isoformat()
    start_date = datetime.datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.datetime.now() + datetime.timedelta(days=period)).strftime('%Y-%m-%d')

    cursor.execute("INSERT INTO prediction_logs (occurrence_type, timestamp, start_date, end_date) VALUES (?, ?, ?, ?)",
                   ("Predição", timestamp, start_date, end_date))
    conn.commit()

    # Obter dados históricos do Bitcoin
    btc = yf.Ticker("BTC-USD")
    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=365*5)
    data = btc.history(start=start_date, end=end_date)
    data.reset_index(inplace=True)

    # Preparação dos dados para a previsão
    df = data[['Date', 'Close']]
    df.sort_values('Date', inplace=True)

    # Normalização dos dados
    close_data = df['Close'].values.reshape(-1, 1)
    scaler_close = MinMaxScaler(feature_range=(0, 1))
    scaled_close = scaler_close.fit_transform(close_data)

    # Preparar os dados para a previsão
    look_back = 60
    recent_data = scaled_close[-look_back:]
    prediction_list = recent_data.copy()

    # Previsão para o período selecionado
    for _ in range(period):
        x_input = prediction_list[-look_back:]
        x_input = x_input.reshape((1, look_back, 1))
        y_pred = model.predict(x_input, verbose=0)
        prediction_list = np.append(prediction_list, y_pred, axis=0)

    # Extrair as previsões
    predicted_prices = prediction_list[-period:]
    predicted_prices = scaler_close.inverse_transform(predicted_prices)

    # Criar datas futuras
    last_date = df['Date'].iloc[-1]
    future_dates = [last_date + datetime.timedelta(days=i) for i in range(1, period + 1)]

    # Formatar a resposta
    forecast = pd.DataFrame({'Date': future_dates, 'Predicted_Price': predicted_prices.flatten()})
    forecast_list = forecast.to_dict(orient='records')

    return {'forecast': forecast_list}

# Endpoint para reentreinar o modelo
@app.post("/retrain/")
def retrain_model(request: RetrainRequest):
    start_date = request.start_date
    end_date = request.end_date

    # Registrar a requisição de reentreinamento no banco de dados
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO prediction_logs (occurrence_type, timestamp, start_date, end_date) VALUES (?, ?, ?, ?)",
                   ("Retreinamento", timestamp, start_date, end_date))
    conn.commit()

    # Coletar os dados do Bitcoin para o período especificado
    btc = yf.Ticker("BTC-USD")
    data_gru_close = btc.history(start=start_date, end=end_date)
    if data_gru_close.empty:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para o período especificado.")

    # Preparação dos dados para o treinamento
    df_gru_close = data_gru_close[['Close']].reset_index()
    dataset_gru_close = df_gru_close['Close'].values.reshape(-1, 1)

    # Normalização dos dados
    scaler_gru_close = MinMaxScaler(feature_range=(0, 1))
    scaled_data_gru_close = scaler_gru_close.fit_transform(dataset_gru_close)

    # Divisão em conjuntos de treino e teste
    train_data_gru_close, test_data_gru_close = train_test_split(scaled_data_gru_close, test_size=0.2, shuffle=False)

    # Parâmetro look_back
    look_back = 60

    # Usando TimeseriesGenerator para criar os conjuntos de dados para o GRU
    train_generator_gru_close = TimeseriesGenerator(train_data_gru_close, train_data_gru_close, length=look_back, batch_size=64)
    test_generator_gru_close = TimeseriesGenerator(test_data_gru_close, test_data_gru_close, length=look_back, batch_size=64)

    # Construção do modelo GRU
    model_gru_close = Sequential()
    model_gru_close.add(GRU(units=50, return_sequences=True, input_shape=(look_back, 1)))
    model_gru_close.add(GRU(units=50))
    model_gru_close.add(Dense(1))

    # Compilação do modelo
    model_gru_close.compile(loss='mean_squared_error', optimizer='adam')

    # Treinamento do modelo
    model_gru_close.fit(train_generator_gru_close, epochs=20, validation_data=test_generator_gru_close, verbose=1)

    # Salvar o novo modelo, sobrescrevendo o antigo
    model_gru_close.save(model_path)

    return {"message": "Modelo retreinado e salvo com sucesso."}

# Endpoint para consultar logs
@app.get("/model_usage_logs/")
def get_logs():
    cursor.execute("SELECT * FROM prediction_logs")
    logs = cursor.fetchall()
    logs_list = [{"id": log[0], "occurrence_type": log[1], "timestamp": log[2], "start_date": log[3], "end_date": log[4]} for log in logs]
    return {"logs": logs_list}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
