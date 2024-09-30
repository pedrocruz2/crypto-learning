# app.py

import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import datetime

from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

# Título da Aplicação
st.title('Previsão do Preço do Bitcoin')

# Carregar o modelo salvo
@st.cache_resource
def load_trained_model():
    model = load_model('model_with_volume.h5')
    return model

model = load_trained_model()

# Função para obter dados atualizados do Bitcoin
@st.cache_data
def get_data():
    # Obter dados históricos do Bitcoin
    btc = yf.Ticker("BTC-USD")
    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=365*5)  # Últimos 5 anos
    data = btc.history(start=start_date, end=end_date)
    data.reset_index(inplace=True)
    return data

data = get_data()

# Mostrar os dados recentes
st.subheader('Dados Recentes do Bitcoin')
st.write(data.tail())

# Entrada do usuário: período de previsão
period_options = [1, 7, 14, 30, 60, 90]
period = st.selectbox('Selecione o período de previsão (dias):', period_options)

# Botão para realizar a previsão
if st.button('Prever'):
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
    
    # DataFrame com as previsões
    forecast = pd.DataFrame({'Date': future_dates, 'Previsão': predicted_prices.flatten()})
    forecast.set_index('Date', inplace=True)
    
    # Dados históricos para plotagem
    historical_data = df.set_index('Date')
    historical_data = historical_data[['Close']]
    historical_data = historical_data.rename(columns={'Close': 'Preço Real'})
    
    # Concatenar dados históricos com as previsões
    total_data = pd.concat([historical_data, forecast], axis=0)
    
    # Mostrar as previsões
    st.subheader('Previsão do Preço do Bitcoin')
    st.write(forecast)
    
    # Plotar o gráfico utilizando st.line_chart
    st.subheader('Gráfico de Previsão')
    st.line_chart(total_data)
