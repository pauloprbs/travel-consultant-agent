import streamlit as st
import requests
from datetime import date, timedelta

# Configuração da página
st.set_page_config(page_title="Agente de Viagens IA", page_icon="✈️")
with st.sidebar:
    st.header("Configurações do Agente")
    if st.button("Ver Fluxo do Agente (Grafo)"):
        try:
            # Busca a imagem do grafo na API
            graph_res = requests.get("http://api:8000/graph")
            if graph_res.status_code == 200:
                st.image(graph_res.content, caption="Fluxo de Trabalho do LangGraph (Nós e Arestas)")
            else:
                st.error("Erro ao gerar o grafo na API.")
        except Exception as e:
            st.error(f"Não foi possível conectar à API para buscar o grafo: {e}")

st.title("✈️ Consultor de Viagens Inteligente")
st.markdown("""
Esta IA planeja seu dia com base no clima previsto para o destino na data escolhida. 
Se houver previsão de chuva, o roteiro será focado em atividades indoor!
""")

# Campos de entrada
col_dest, col_date = st.columns([2, 1])

with col_dest:
    destination = st.text_input("Para onde você deseja ir?", placeholder="Ex: Rio de Janeiro, Paris, Xique-Xique...")

with col_date:
    travel_date = st.date_input(
        "Data da viagem", 
        value=date.today(),
        min_value=date.today(),
        max_value=date.today() + timedelta(days=6) # Limite de 7 dias da API gratuita
    )

if st.button("Planejar meu dia"):
    if destination:
        with st.spinner(f"Consultando o clima para {travel_date.strftime('%d/%m/%Y')} e planejando seu dia em {destination}..."):
            try:
                # Chamada para a nossa API passando a data formatada
                formatted_date = travel_date.strftime("%Y-%m-%d")
                response = requests.get(f"http://api:8000/plan?destination={destination}&date={formatted_date}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Exibição dos resultados
                    st.success(f"Roteiro Gerado para {travel_date.strftime('%d/%m/%Y')}!")
                    
                    # Colunas para informações rápidas
                    col1, col2 = st.columns(2)
                    with col1:
                        weather_pt = data['weather_info'].replace("sunny", "Ensolarado").replace("raining", "Chuvoso").replace("unknown", "Indisponível")
                        st.metric("Clima Previsto", weather_pt)
                    with col2:
                        st.metric("Tentativas do Agente", data['attempts'])

                    # O Roteiro em Markdown
                    st.divider()
                    st.markdown(data['itinerary'])
                    
                    if data['attempts'] > 1:
                        st.info(f"Nota: O agente precisou de {data['attempts']} tentativas para validar este roteiro com as regras climáticas.")
                else:
                    st.error("A API retornou um erro ao processar o roteiro.")

            except Exception as e:
                st.error(f"Erro ao conectar com a API: {e}")
    else:
        st.warning("Por favor, digite um destino.")
