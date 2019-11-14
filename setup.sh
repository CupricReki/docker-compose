#!/bin/bash

mkdir /opt/dl/unifi-controller /opt/dl/sonarr /opt/dl/radarr /opt/dl/transmission /opt/dl/sabnzbd /opt/dl/portainer /opt/dl/watchtower /opt/dl/traefik
touch /opt/dl/traefik/acme.json
chmod 600 /opt/dl/traefik/acme.json
cp $PWD/traefik/traefik.toml /opt/dl/traefik/
chown 1007:1008 -R /opt/dl/*
