FROM ubuntu/nginx:latest

RUN rm -f /etc/nginx/sites-enabled/* /etc/nginx/sites-available/*

COPY nginx.conf /etc/nginx/sites-enabled/default

COPY index.html /var/www/html/index.html