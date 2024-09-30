from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

import numpy as np
import pandas as pd
import yfinance as yf
import datetime

from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

# Definir a aplicação FastAPI
app = FastAPI(
    title="API de Previsão do Preço do Bitcoin",
    description="Uma API para prever o preço do Bitcoin usando um modelo LSTM treinado.",
    version="1.0"
)

# Carregar o modelo salvo
model = load_model('model_close.h5')

# Definir o modelo de dados para a entrada da previsão
class PredictionRequest(BaseModel):
    period: int  # Número de dias para prever

# Endpoint raiz
@app.get("/")
def read_root():
    return {"message": "API de Previsão do Preço do Bitcoin"}

# Endpoint para realizar a previsão
@app.post("/predict/")
def predict_price(request: PredictionRequest):
    period = request.period

    # Obter dados históricos do Bitcoin
    btc = yf.Ticker("BTC-USD")
    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=365*5)  # Últimos 5 anos
    data = btc.history(start=start_date, end=end_date)
    data.reset_index(inplace=True)

    # Preparação dos dados para a previsão
    df = data[['Date', 'Close']]

    # Ordenar os dados por data
    df.sort_values('Date', inplace=True)

    # Normalização dos dados
    close_data = df['Close'].values.reshape(-1, 1)

    scaler_close = MinMaxScaler(feature_range=(0, 1))
    scaled_close = scaler_close.fit_transform(close_data)

    # Preparar os dados para a previsão
    look_back = 60  # Usando os últimos 60 dias
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
    future_dates = [last_date + datetime.timedelta(days=i) for i in range(1, period+1)]

    # Formatar a resposta
    forecast = pd.DataFrame({'Date': future_dates, 'Predicted_Price': predicted_prices.flatten()})
    forecast_list = forecast.to_dict(orient='records')

    return {'forecast': forecast_list}



if __name__ == "__main__":
    # OBRIGADO LUAN PELO MÉTODO, UVICORN EU TE DESPREZO
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)