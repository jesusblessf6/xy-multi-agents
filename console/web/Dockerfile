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

    location /auth/ {
        proxy_pass http://console-api:8002;
    }
    location /agents/ {
        proxy_pass http://console-api:8002;
    }
    location /reviews/ {
        proxy_pass http://console-api:8002;
    }
    location /projects/ {
        proxy_pass http://console-api:8002;
    }
    location /dashboard {
        proxy_pass http://console-api:8002;
    }
    location /users/ {
        proxy_pass http://console-api:8002;
    }
    location /health {
        proxy_pass http://console-api:8002;
    }
}
EOF
EXPOSE 80
