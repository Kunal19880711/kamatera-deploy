#!/bin/sh

/docker-entrypoint.sh nginx & /opt/nginx-certbot/bin/set_certs.py