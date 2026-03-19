# Stage 1: Build
FROM node:22.22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_VOICE_CONTROLS_VISIBLE=true
ARG VITE_VOICE_ACTIVATION=push-to-talk
ARG VITE_TTS_VOICE_DE=alloy
ARG VITE_TTS_VOICE_EN=onyx
ENV VITE_VOICE_CONTROLS_VISIBLE=$VITE_VOICE_CONTROLS_VISIBLE
ENV VITE_VOICE_ACTIVATION=$VITE_VOICE_ACTIVATION
ENV VITE_TTS_VOICE_DE=$VITE_TTS_VOICE_DE
ENV VITE_TTS_VOICE_EN=$VITE_TTS_VOICE_EN
RUN npm run build

# Stage 2: Serve
FROM nginx:1.28.2-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]
