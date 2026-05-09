# ── build stage ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

# ── serve stage ───────────────────────────────────────────────────────────────
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html

# Forward /upload /analyze /split /download /cleanup to backend
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
