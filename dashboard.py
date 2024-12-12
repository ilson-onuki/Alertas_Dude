import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Título da página
st.title("Análise de Quedas por Dispositivo")

# Carregar os dados do CSV
df = pd.read_csv("output.csv")
df["Data"] = pd.to_datetime(df["Data"], format="%Y-%m-%d")

# Configuração da barra lateral
st.sidebar.header("Opções de Personalização")

# Slider para personalização do intervalo de dias
intervalo = st.sidebar.slider(
    "Selecione o intervalo de dias",
    min_value=2,
    max_value=100,
    value=15,  # Valor padrão
    step=1
)

# Selectbox para filtro por categoria
categoria_selecionada = st.sidebar.selectbox(
    "Selecione uma categoria", 
    options=["Todas"] + sorted(df["Categoria"].unique()),  # Opção para todas as categorias
    index=0
)

# Filtrar os dados para o intervalo selecionado
data_limite = pd.to_datetime("today") - pd.Timedelta(days=intervalo)
df = df[df["Data"] >= data_limite]

# Filtrar o DataFrame baseado na categoria selecionada
if categoria_selecionada != "Todas":
    df = df[df["Categoria"] == categoria_selecionada]

# Contar as quedas ('down') por dispositivo no intervalo selecionado
quedas_por_dispositivo = df[df["Status"] == "down"].groupby("Dispositivo").size().reset_index(name="Quedas")
quedas_por_dispositivo = quedas_por_dispositivo.sort_values(by="Quedas", ascending=False)

# Criar o ranking
ranking_df = quedas_por_dispositivo.reset_index(drop=True)
ranking_df["Ranking"] = ranking_df.index + 1

# Exibir as 3 colunas no dataframe
st.subheader(f"Ranking de Quedas nos Últimos {intervalo} Dias")
st.dataframe(ranking_df[[ 'Dispositivo', 'Quedas']], use_container_width=True)

# --------------------------

# Filtrar os últimos eventos do tipo 'down'
df_down = df[df['Status'] == 'down']

# Agregar os eventos por dispositivo e data
aggregated_data = df_down.groupby(['Dispositivo', 'Data']).size().reset_index(name='Contagem')

# Criar uma nova tabela com histórico de eventos por dispositivo
dispositivos = []
views_history = []
total_events = []

for dispositivo in aggregated_data['Dispositivo'].unique():
    device_data = aggregated_data[aggregated_data['Dispositivo'] == dispositivo]
    daily_views = device_data.set_index('Data').reindex(pd.date_range(device_data['Data'].min(), 
                                                                      device_data['Data'].max(), freq='D'), fill_value=0)
    dispositivos.append(dispositivo)
    views_history.append(daily_views['Contagem'].tolist())
    total_events.append(daily_views['Contagem'].sum())

# Criar um DataFrame final
final_df = pd.DataFrame({
    'Dispositivo': dispositivos,
    'views_history': views_history,
    'Total de Eventos': total_events
})

# Ordenar por 'Total de Eventos' do maior para o menor
final_df = final_df.sort_values(by='Total de Eventos', ascending=False)

# Exibir usando Streamlit
st.subheader("Histórico de Eventos por Dispositivo")
st.dataframe(
    final_df,
    column_config={
        "Dispositivo": "Dispositivo",
        "views_history": st.column_config.BarChartColumn(
            f"Eventos ({intervalo} dias)", y_min=0
        ),
        "Total de Eventos": st.column_config.NumberColumn(
            "Total", format="%d"
        )
    },
    hide_index=True,
    use_container_width=True
)
