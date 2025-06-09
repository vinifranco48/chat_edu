# frontend/Dockerfile

# --- Estágio 1: Build da Aplicação React ---
FROM node:18-alpine AS build

WORKDIR /app

# Copia os arquivos de definição de projeto e instala as dependências
COPY package.json ./
COPY package-lock.json ./
RUN npm install

# Copia o restante do código fonte
COPY . ./

# Define a URL da API para o processo de build
# Isso garante que o código do React fará chamadas para /api/...
ARG REACT_APP_API_URL=/api
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

# Roda o script de build para gerar os arquivos estáticos
RUN npm run build

# --- Estágio 2: Servir os arquivos com Nginx ---
FROM nginx:stable-alpine

# Remove a configuração padrão do Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copia a configuração personalizada do Nginx (que criaremos a seguir)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia os arquivos estáticos gerados no estágio de build para o diretório do Nginx
COPY --from=build /app/build /usr/share/nginx/html

# Expõe a porta 80 (padrão do Nginx)
EXPOSE 80

# Inicia o Nginx em modo "foreground"
CMD ["nginx", "-g", "daemon off;"]