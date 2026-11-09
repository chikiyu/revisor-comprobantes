# Etapa 1: compila React a archivos estáticos
FROM node:24-alpine AS compilar
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

# Etapa 2: nginx sirve esos archivos; Node ya no hace falta
FROM nginx:alpine
COPY --from=compilar /app/dist /usr/share/nginx/html
