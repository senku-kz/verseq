# ── Stage 1: build Quasar SPA ────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (cached layer)
COPY frontend/package*.json ./
RUN npm ci --prefer-offline

# Copy source and build
COPY frontend/ .
RUN npx quasar build

# ── Stage 2: serve with nginx ────────────────────────────────────────────────
FROM nginx:1.27-alpine

COPY --from=builder /app/dist/spa /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
