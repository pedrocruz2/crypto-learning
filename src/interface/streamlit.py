import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import datetime
import yfinance as yf

st.set_page_config(page_title="Previsão do Preço do Bitcoin", layout="wide")

st.title("Previsão do Preço do Bitcoin")

# Entrada do usuário: período de previsão
period_options = [1, 7, 14, 30, 60, 90]
period = st.selectbox('Selecione o período de previsão (dias):', period_options)

# Botão para realizar a previsão
if st.button('Prever'):
    # URL da API (backend FastAPI)
    api_url = f"http://0.0.0.0:8000/predict/"

    # Dados para a requisição
    data = {"period": period}

    # Requisição POST à API
    try:
        response = requests.post(api_url, json=data)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP que indicam falha
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao se comunicar com o backend: {e}")
    else:
        # Processar a resposta da API
        result = response.json()

        # Converter o resultado em um DataFrame
        forecast = pd.DataFrame(result['forecast'])
        forecast['Date'] = pd.to_datetime(forecast['Date'])
        forecast.set_index('Date', inplace=True)
        forecast.rename(columns={'Predicted_Price': 'Previsao'}, inplace=True)

        # Mostrar as previsões
        st.subheader('Previsão do Preço do Bitcoin')
        st.write(forecast)

        # Coletar os dados históricos do Bitcoin usando yfinance
        end_date = datetime.datetime.today()
        start_date = end_date - datetime.timedelta(days=60)
        btc = yf.Ticker("BTC-USD")
        df_historical = btc.history(start=start_date, end=end_date)
        df_historical.reset_index(inplace=True)
        df_historical['Date'] = pd.to_datetime(df_historical['Date'])
        df_historical.set_index('Date', inplace=True)

        # Renomear a coluna para 'Preço Real'
        df_historical.rename(columns={'Close': 'Preco_Real'}, inplace=True)

        # Concatenar dados históricos com as previsões
        total_data = pd.concat([df_historical[['Preco_Real']], forecast], axis=1)

        # Preencher possíveis valores NaN com o valor anterior
        total_data.fillna(method='ffill', inplace=True)

        # Plotar o gráfico utilizando Plotly
        st.subheader('Gráfico de Previsão')

        fig = go.Figure()

        # Adicionar a linha do preço histórico
        fig.add_trace(go.Scatter(
            x=total_data.index,
            y=total_data['Preco_Real'],
            mode='lines',
            name='Preço Real'
        ))

        # Adicionar a linha das previsões
        fig.add_trace(go.Scatter(
            x=forecast.index,
            y=forecast['Previsao'],
            mode='lines',
            name='Previsão',
            line=dict(dash='dash')
        ))

        # Configurar o layout do gráfico
        fig.update_layout(
            title="Previsão do Preço do Bitcoin",
            xaxis_title="Data",
            yaxis_title="Preço (USD)",
            legend_title="Legenda",
            hovermode="x"
        )

        # Exibir o gráfico usando st.plotly_chart
        st.plotly_chart(fig, use_container_width=True)
