FROM python:3.11-slim

WORKDIR /app

# Copia apenas o necessário para instalar as dependências primeiro (cache do Docker)
COPY requirements.txt .

# Instala as bibliotecas Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Portas da API e Streamlit
EXPOSE 8000
EXPOSE 8501

CMD ["bash"]
