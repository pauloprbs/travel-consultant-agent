# Agente de Itinerário Inteligente com LangGraph

Este projeto foi desenvolvido como trabalho final para a disciplina de Agentes de IA. O sistema consiste em um agente capaz de planejar roteiros de viagem baseados na previsão do tempo real, utilizando uma lógica de grafos cíclicos para auto-correção.

## 🚀 Tecnologias Utilizadas
- **LangGraph**: Orquestração do agente e controle de estado.
- **LangChain & Groq (Llama 3.3)**: Modelos de linguagem para planejamento e validação.
- **FastAPI**: Backend para execução do agente.
- **Streamlit**: Interface de usuário moderna e interativa.
- **Open-Meteo API**: Dados meteorológicos em tempo real.
- **Docker & Docker Compose**: Containerização de toda a aplicação.

## 🧠 Arquitetura do Agente
O agente utiliza um `StateGraph` composto por três nós principais:
1. **Researcher**: Identifica as coordenadas do destino e busca a previsão do tempo para a data escolhida.
2. **Planner**: Gera um roteiro de 1 dia seguindo as regras de negócio (Atividades indoor para chuva, outdoor para sol).
3. **Validator**: Analisa o roteiro gerado e decide se ele cumpre os requisitos climáticos. Caso negativo, o fluxo retorna ao Planner com as instruções de correção.

## 📈 Visualização do Grafo
O fluxo de trabalho do agente pode ser visualizado abaixo, destacando o ciclo de correção entre o Validador e o Planejador:

![Grafo do Agente](imgs/grafo.png)

## 🛠️ Como Executar
1. Clone o repositório.
2. Copie o arquivo de exemplo de ambiente:
   ```bash
   cp .env.example .env
   ```
3. Edite o arquivo `.env` e insira sua `GROQ_API_KEY`.
4. Execute o comando:
   ```bash
   docker compose up --build
   ```
5. Acesse:
   - Interface: `http://localhost:8501`
   - Documentação da API: `http://localhost:8000/docs`

## 📸 Evidências de Execução

### Interface do Usuário (Streamlit)
Abaixo, a interface demonstrando o planejamento para diferentes cenários:

![Interface Principal](imgs/ui_screenshot.png)

### Logs de Auto-Correção (Caso de Londres - Chuva)
Neste log, é possível observar o agente identificando que o roteiro inicial continha atividades ao ar livre em um dia chuvoso, forçando uma segunda tentativa de planejamento:

![Logs Londres](imgs/logs_londres.png)

### Planejamento de Sucesso (Caso de Xique-Xique - Sol)
Exemplo de roteiro validado com sucesso na primeira tentativa para um dia ensolarado:

![Logs Xique-Xique](imgs/logs_xique_xique.png)

## 📝 Regras de Negócio Implementadas
- **Clima Chuvoso**: Roteiro deve ser 100% focado em atividades indoor (museus, shoppings, teatros).
- **Clima Ensolarado**: Roteiro deve focar em atividades ao ar livre (praias, parques, caminhadas).
- **Validação Automática**: O agente revisa seu próprio trabalho por até 3 tentativas caso as regras não sejam atendidas.
