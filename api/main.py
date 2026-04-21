from typing import TypedDict, Literal
from fastapi import FastAPI
import requests
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from datetime import datetime
from fastapi.responses import Response

# 1. SETUP E CONFIGURAÇÕES
load_dotenv()
llm = ChatGroq(model="llama-3.1-8b-instant")
app = FastAPI(title="Travel Consultant Agent")

# 2. DEFINIÇÃO DO ESTADO (O Quadro Branco)
class AgentState(TypedDict):
    destination: str         # local
    date: str                # data da viagem (YYYY-MM-DD)
    weather_info: str        # clima_encontrado
    itinerary: str           # itinerario
    attempts: int            # tentativas
    error_log: str           # logs de execução/erro

# --- 3. DEFINIÇÃO DOS NÓS (Nodes) ---

def research_node(state: AgentState):
    """Nó A: Busca previsão do clima para uma data específica."""
    destination = state['destination']
    target_date = state['date']
    
    print(f"--- PESQUISANDO CLIMA: {destination} PARA O DIA {target_date} ---")
    
    # Busca coordenadas
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={destination}&count=1&language=en&format=json"
    geo_res = requests.get(geo_url).json()
    
    if not geo_res.get('results'):
        return {"weather_info": "unknown", "error_log": "Cidade não encontrada"}
    
    location = geo_res['results'][0]
    lat, lon = location['latitude'], location['longitude']

    # Busca previsão do clima para a data específica
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&daily=weathercode&start_date={target_date}&end_date={target_date}&timezone=auto"
    )
    weather_res = requests.get(weather_url).json()
    
    # Extrai o código do clima do dia solicitado
    try:
        code = weather_res['daily']['weathercode'][0]
        is_raining = code > 50 
        weather_desc = "raining" if is_raining else "sunny"
    except (KeyError, IndexError):
        return {"weather_info": "unknown", "error_log": "Previsão não disponível para esta data"}
    
    print(f"--- CLIMA PREVISTO: {weather_desc} ---")
    return {"weather_info": weather_desc, "error_log": ""}

def planner_node(state: AgentState):
    """Nó B: Planeja o roteiro com IA baseado na data e clima."""
    destination = state['destination']
    weather = state['weather_info']
    travel_date = state['date']
    error = state.get('error_log', '')
    
    print(f"--- IA PLANEJANDO ROTEIRO PARA {travel_date} ---")
    
    system_prompt = (
        "Você é um consultor de viagens profissional. "
        f"O roteiro é para o dia {travel_date}. "
        f"O clima previsto em {destination} para este dia é {weather}. "
    )
    
    if weather == "raining":
        system_prompt += "Está previsto CHUVA. Sugira APENAS atividades indoor (museus, shoppings)."
    else:
        system_prompt += "Está previsto SOL. Foque em atividades ao ar livre (parques, praias)."

    user_prompt = f"Crie um roteiro de 1 dia para {destination} na data {travel_date}."
    if error:
        user_prompt += f" REJEIÇÃO ANTERIOR: {error}. Corrija o erro no novo roteiro."

    response = llm.invoke([("system", system_prompt), ("human", user_prompt)])
    return {"itinerary": response.content, "error_log": ""}

def validator_node(state: AgentState):
    """Nó C: Valida o roteiro com IA."""
    weather = state['weather_info']
    itinerary = state['itinerary']
    
    print("--- VALIDANDO ROTEIRO ---")
    
    system_prompt = f"Você é um validador. Clima: {weather}. Regra: "
    system_prompt += "Se chover, nada ao ar livre. Se sol, nada só indoor."

    user_prompt = f"Responda 'APROVADO' ou o erro encontrado neste roteiro:\n\n{itinerary}"

    response = llm.invoke([("system", system_prompt), ("human", user_prompt)])
    result = response.content.strip()
    
    current_attempts = state.get("attempts", 0) + 1
    
    if "APROVADO" in result.upper():
        return {"attempts": current_attempts, "error_log": ""}
    else:
        print(f"--- REJEITADO: {result} ---")
        return {"attempts": current_attempts, "error_log": result}

# --- 4. LÓGICA DE CONTROLE (Routing) ---

def should_continue(state: AgentState) -> Literal["retry", "finish"]:
    if state["error_log"] and state["attempts"] < 3:
        return "retry"
    return "finish"

# --- 5. CONSTRUÇÃO DO WORKFLOW ---

workflow = StateGraph(AgentState)

workflow.add_node("researcher", research_node)
workflow.add_node("planner", planner_node)
workflow.add_node("validator", validator_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "planner")
workflow.add_edge("planner", "validator")

workflow.add_conditional_edges(
    "validator",
    should_continue,
    {"retry": "planner", "finish": END}
)

agent_executor = workflow.compile()

# --- 6. ROTA API ---

@app.get("/plan")
async def plan_trip(destination: str, date: str):
    initial_state = {"destination": destination, "date": date, "attempts": 0}
    final_state = await agent_executor.ainvoke(initial_state)
    return final_state

@app.get("/graph")
async def get_graph():
    """Retorna a imagem do fluxo do grafo."""
    img_data = agent_executor.get_graph().draw_mermaid_png()
    return Response(content=img_data, media_type="image/png")
