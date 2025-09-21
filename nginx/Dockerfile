FROM nginx:alpine

RUN apk add --no-cache bash gettext

# Directories for ACME challenges and certs (mounted as volumes in compose)
RUN mkdir -p /var/www/certbot

# Copy templates and entrypoint
COPY conf.d/app_http.conf.template /etc/nginx/templates/app_http.conf.template
COPY conf.d/app_https.conf.template /etc/nginx/templates/app_https.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]

