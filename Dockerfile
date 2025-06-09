# Use a imagem base do Python 3.11
FROM python:3.11

# Defina o diretório de trabalho
WORKDIR /app

# Instale quaisquer dependências de sistema, se necessário
# RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copie apenas o arquivo pyproject.toml para aproveitar o cache do Docker
COPY pyproject.toml .

# Atualize o pip e instale as dependências diretamente do pyproject.toml
# O comando "pip install ." lê o pyproject.toml e instala tudo na seção [project.dependencies]
RUN pip install --upgrade pip
RUN pip install .

# Copie o restante do código da sua aplicação
COPY . .

# Exponha a porta que sua aplicação usará
EXPOSE 8000

# Defina o comando para iniciar sua aplicação com uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]