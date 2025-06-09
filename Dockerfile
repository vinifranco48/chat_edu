# Use a imagem base do Python 3.11, a versão 'slim' é menor e mais eficiente
FROM python:3.11-slim

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# --- ATUALIZAÇÃO CRÍTICA ---

# 1. Instala as dependências de sistema para o WebDriver
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
    --no-install-recommends

# 2. Baixa e instala o navegador Google Chrome
RUN wget -q -O google-chrome-stable_current_amd64.deb "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm -f google-chrome-stable_current_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------

# Copia o arquivo de definição do projeto
COPY pyproject.toml .

# Atualiza o pip e instala as dependências do Python
RUN pip install --upgrade pip
RUN pip install .

# Agora, copie o restante do código da sua aplicação
COPY . .

# Exponha a porta 8000, onde a aplicação vai rodar
EXPOSE 8000

# Defina o comando para iniciar sua aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
