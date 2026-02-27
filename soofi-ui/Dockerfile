# Stage 1: Build
FROM node:22.22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_VOICE_CONTROLS_VISIBLE=true
ARG VITE_VOICE_ACTIVATION=push-to-talk
ENV VITE_VOICE_CONTROLS_VISIBLE=$VITE_VOICE_CONTROLS_VISIBLE
ENV VITE_VOICE_ACTIVATION=$VITE_VOICE_ACTIVATION
RUN npm run build

# Stage 2: Serve
FROM nginx:1.28.2-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
