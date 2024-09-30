import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import datetime
import yfinance as yf

st.set_page_config(page_title="Previsão do Preço do Bitcoin", layout="wide")

st.title("Previsão do Preço do Bitcoin")

# Entrada do usuário: período de previsão
period = st.text_input(label="Insira o Número de dias")
# Botão para realizar a previsão
if st.button('Prever'):
    api_url = f"http://0.0.0.0:8000/predict/"
    data = {"period": int(period)}
    
    try:
        response = requests.post(api_url, json=data)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP que indicam falha
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao se comunicar com o backend: {e}")
    else:
        # Processar a resposta da API
        result = response.json()
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
        df_historical.rename(columns={'Close': 'Preco_Real'}, inplace=True)

        # Concatenar dados históricos com as previsões
        total_data = pd.concat([df_historical[['Preco_Real']], forecast], axis=1)
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

# Sidebar para reentreinar o modelo
st.sidebar.header("Retreinar o Modelo")
start_date_retrain = st.sidebar.date_input("Data de Início do Retreinamento", datetime.date(2014, 1, 1))
end_date_retrain = st.sidebar.date_input("Data de Fim do Retreinamento", datetime.date.today())

if st.sidebar.button("Retreinar Modelo"):
    retrain_url = "http://0.0.0.0:8000/retrain/"
    retrain_data = {"start_date": str(start_date_retrain), "end_date": str(end_date_retrain)}
    try:
        response_retrain = requests.post(retrain_url, json=retrain_data)
        response_retrain.raise_for_status()
        st.sidebar.success("Modelo retreinado com sucesso!")
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Erro ao retreinar o modelo: {e}")

# Sidebar para visualizar os logs de uso do sistema
st.sidebar.header("Consultar Logs do Sistema")
if st.sidebar.button("Ver Logs"):
    try:
        response_logs = requests.get("http://0.0.0.0:8000/model_usage_logs/")
        response_logs.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Erro ao se comunicar com o backend: {e}")
    else:
        logs = response_logs.json()['logs']
        df_logs = pd.DataFrame(logs)

        # Renomear as colunas e reorganizar
        df_logs = df_logs.rename(columns={
            'timestamp': 'Data',
            'occurrence_type': 'Tipo',
            'start_date': 'Data Início',
            'end_date': 'Data Final'
        })

        # Selecionar as colunas na ordem desejada
        df_logs = df_logs[['Data', 'Tipo', 'Data Início', 'Data Final']]

        # Formatar a data
        df_logs['Data'] = pd.to_datetime(df_logs['Data']).dt.strftime('%d-%m-%Y %H:%M:%S')

        st.sidebar.write("Logs de Uso do Modelo")
        st.sidebar.dataframe(df_logs, use_container_width=True)
