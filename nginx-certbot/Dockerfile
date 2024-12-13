# Dockerfile
FROM nginx:mainline-alpine

# Installations
RUN apk add --no-cache python3 py3-pip \
    && python3 -m venv /opt/certbot/ \
    && /opt/certbot/bin/pip install --upgrade pip \
    && /opt/certbot/bin/pip install certbot certbot-nginx python-dotenv Jinja2 PyYAML \
    && ln -s /opt/certbot/bin/certbot /usr/bin/certbot \
    && mkdir -p /var/www/html /opt/nginx-certbot

# Set work directory
WORKDIR /opt/nginx-certbot

# Copying
COPY . .

# Adding Entrypoint
ENTRYPOINT [ "/opt/nginx-certbot/bin/newDockerEntrypoint.sh" ]
