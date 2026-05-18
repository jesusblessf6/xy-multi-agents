FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /requirements/ {
        proxy_pass http://portal-api:8001;
    }
    location /projects/ {
        proxy_pass http://portal-api:8001;
    }
    location /pipeline {
        proxy_pass http://portal-api:8001;
    }
    location /agents {
        proxy_pass http://portal-api:8001;
    }
    location /health {
        proxy_pass http://portal-api:8001;
    }
}
EOF
EXPOSE 80
