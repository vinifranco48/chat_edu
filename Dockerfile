# Use a imagem base do Python 3.11, a versão 'slim' é menor e mais eficiente
FROM python:3.11-slim

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# --- CORREÇÃO CRÍTICA ---
# Instala as dependências de sistema necessárias para o Chrome/WebDriver funcionar
# em modo headless dentro de um ambiente Linux mínimo.
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-6 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libsm6 \
    libxrandr2 \
    libxrender1 \
    libdbus-1-3 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copia o arquivo de definição do projeto
COPY pyproject.toml .

# Atualiza o pip e instala as dependências do Python
# Isso aproveita o cache do Docker: as dependências só são reinstaladas
# se o arquivo pyproject.toml mudar.
RUN pip install --upgrade pip
RUN pip install .

# Agora, copie o restante do código da sua aplicação
COPY . .

# Exponha a porta 8000, onde a aplicação vai rodar
EXPOSE 8000

# --- CORREÇÃO DE PRODUÇÃO ---
# Defina o comando para iniciar sua aplicação.
# A flag "--reload" foi removida, pois ela é para desenvolvimento e não para produção.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]