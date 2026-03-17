FROM alpine AS extract

RUN apk add --no-cache curl unzip

# Download the latest release ZIP (contains pre-built dist/ and plugin/)
RUN curl -L https://github.com/hakimel/reveal.js/archive/refs/tags/5.1.0.zip -o reveal.zip \
    && unzip reveal.zip \
    && mv reveal.js-5.1.0 /reveal

# ---

FROM nginx:alpine

COPY --from=extract /reveal/dist /usr/share/nginx/html/dist
COPY --from=extract /reveal/plugin /usr/share/nginx/html/plugin

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
