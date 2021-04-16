Nextcloud in docker
guide-by-example

logo
Purpose & Overview

File share & sync.

    Official site
    Github
    DockerHub

Nextcloud is an open source suite of client-server software for creating and using file hosting services with wide cross platform support.

The Nextcloud server is written in PHP and JavaScript. For remote access it employs sabre/dav, an open-source WebDAV server. It is designed to work with several database management systems, including SQLite, MariaDB, MySQL, PostgreSQL.

There are many ways to deploy Nextcloud, this setup is going with the most goodies.
Using PHP-FPM for better performance and using Redis for more reliable transactional file locking and for memory file caching.
Files and directory structure

/home/
└── ~/
    └── docker/
        └── nextcloud/
            ├── nextcloud-data/
            ├── nextcloud-db-data/
            ├── .env
            ├── docker-compose.yml
            ├── nginx.conf
            └── nextcloud-backup-script.sh

    nextcloud-data/ - a directory where nextcloud will store users data and web app data
    nextcloud-db-data/ - a directory where nextcloud will store its database data
    .env - a file containing environment variables for docker compose
    docker-compose.yml - a docker compose file, telling docker how to run the containers
    nginx.conf - nginx web server configuration file
    nextcloud-backup-script.sh - a backup script if you want it

You only need to provide the files.
The directories are created by docker compose on the first run.
docker-compose

Official examples here

Five containers to spin up

    nextcloud-app - nextcloud backend app that stores the files and facilitate the sync and runs the apps
    nextcloud-db - mariadb database where files-metadata and users-metadata are stored
    nextcloud-web - nginx web server with fastCGI PHP-FPM support
    nextcloud-redis - in memory file caching and more reliable transactional file locking
    nextcloud-cron - for periodic maintenance in the background

docker-compose.yml

version: '3'
services:

  nextcloud-db:
    image: mariadb
    container_name: nextcloud-db
    hostname: nextcloud-db
    command: --transaction-isolation=READ-COMMITTED --binlog-format=ROW
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./nextcloud-data-db:/var/lib/mysql

  nextcloud-redis:
    image: redis:5.0.9-alpine
    container_name: nextcloud-redis
    hostname: nextcloud-redis
    restart: unless-stopped

  nextcloud-app:
    image: nextcloud:fpm-alpine
    container_name: nextcloud-app
    hostname: nextcloud-app
    restart: unless-stopped
    env_file: .env
    depends_on:
      - nextcloud-db
      - nextcloud-redis
    volumes:
      - ./nextcloud-data/:/var/www/html

  nextcloud-web:
    image: nginx:alpine
    container_name: nextcloud-web
    hostname: nextcloud-web
    restart: unless-stopped
    volumes:
      - ./nextcloud-data/:/var/www/html:ro
      - ./nginx.conf:/etc/nginx/nginx.conf:ro

  nextcloud-cron:
    image: nextcloud:fpm-alpine
    container_name: nextcloud-cron
    hostname: nextcloud-cron
    restart: unless-stopped
    volumes:
      - ./nextcloud-data/:/var/www/html
    entrypoint: /cron.sh
    depends_on:
      - nextcloud-db
      - nextcloud-redis

networks:
  default:
    external:
      name: $DOCKER_MY_NETWORK

.env

# GENERAL
MY_DOMAIN=example.com
DOCKER_MY_NETWORK=caddy_net
TZ=Europe/Bratislava

# NEXTCLOUD-MARIADB
MYSQL_ROOT_PASSWORD=nextcloud
MYSQL_PASSWORD=nextcloud
MYSQL_DATABASE=nextcloud
MYSQL_USER=nextcloud

# NEXTCLOUD
MYSQL_HOST=nextcloud-db
REDIS_HOST=nextcloud-redis

# USING SENDGRID FOR SENDING EMAILS
MAIL_DOMAIN=example.com
MAIL_FROM_ADDRESS=nextcloud
SMTP_SECURE=ssl
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=465
SMTP_NAME=apikey
SMTP_PASSWORD=<sendgrid-api-key-goes-here>

nginx.conf

I wont be pasting it here
in full text,
but it is included in this github repo.

nginx.conf

This is nginx web server configuration file, specifically setup to support fastCGI PHP-FPM.

Taken from this official nextcloud example setup and has one thing changed in it - the upstream hostname from app to nextcloud-app

upstream php-handler {
    server nextcloud-app:9000;
}

All containers must be on the same network.
Which is named in the .env file.
If one does not exist yet: docker network create caddy_net
notice

current issue, redis version 6.0

Therefore image: redis:5.0.9-alpine is used instead of image: redis like with the rest.
Reverse proxy

Nextcloud official documentation regarding reverse proxy.

Caddy v2 is used, details here.
There are few extra directives here to fix some nextcloud warnings.

Caddyfile

nextcloud.{$MY_DOMAIN} {
    reverse_proxy nextcloud-web:80
    header Strict-Transport-Security max-age=31536000;
    redir /.well-known/carddav /remote.php/carddav 301
    redir /.well-known/caldav /remote.php/caldav 301
}

First run

Nextcloud needs few moments to start, then there is the initial configuration, creating admin account.
If database env variables were not passed in to nextcloud-app then also the database info would be required here.

first-run-pic

The domain or IP you access nextcloud on this first run is added to trusted_domains in config.php. Changing the domain later on will throw "Access through untrusted domain" error.
Editing nextcloud-data/config/config.php and adding the new domain will fix it.
Security & setup warnings

Nextcloud has a status check in Settings > Administration > Overview
There are likely several warnings on a freshly spun containers.
The database is missing some indexes

On the docker host execute:
docker exec --user www-data --workdir /var/www/html nextcloud-app php occ db:add-missing-indices
Some columns in the database are missing a conversion to big int

On the docker host execute:
docker exec --user www-data --workdir /var/www/html nextcloud-app php occ db:convert-filecache-bigint
The "Strict-Transport-Security" HTTP header is not set to at least "15552000" seconds.

Helps to know what is HSTS.
This warning is already fixed in the reverse proxy section in the caddy config,
the line: header Strict-Transport-Security max-age=31536000;
Your web server is not properly set up to resolve "/.well-known/caldav" and Your web server is not properly set up to resolve "/.well-known/carddav".

This warning is already fixed in the reverse proxy section in the caddy config,
The lines:
redir /.well-known/carddav /remote.php/carddav 301
redir /.well-known/caldav /remote.php/caldav 301

status-pic
Troubleshooting

If there is a problem accesing nextcloud from a mobile app, "Please log in before granting access", and being stuck after logging in with the circle animation:

Edit nextcloud-data/config/config.php
adding as the last line: 'overwriteprotocol' => 'https',
Extra info
check if redis container works

At https://<nexcloud url>/ocs/v2.php/apps/serverinfo/api/v1/info
ctrl+f for redis, should be in memcache.distributed and memcache.locking

You can also exec in to redis container:

    docker exec -it nextcloud-redis /bin/sh
    start monitoring: redis-cli MONITOR
    start browsing files on the nextcloud
    there should be activity in the monitoring

check if cron container works

    after letting Nextcloud run for a while
    in settings > administration > basic settings
    background jobs should be set to Cron
    the last job info should never be older than 10 minutes

Update

Watchtower updates the image automatically.

Manual image update:

    docker-compose pull
    docker-compose up -d
    docker image prune

Backup and restore
Backup

Using borg that makes daily snapshot of the entire directory.
Restore

    down the nextcloud containers docker-compose down
    delete the entire nextcloud directory
    from the backup copy back the nextcloud directory
    start the containers docker-compose up -d

Backup of just user data

User data daily export using the official procedure.
For nextcloud it means entering the maintenance mode, doing a database dump and backing up several directories containing data, configs, themes.

For the script it just means database dump as borg backup and its deduplication will deal with the directories, especially useful in the case of nextcloud where hundreds gigabytes can be stored.
Create a backup script

Placed inside ~/docker/nextcloud/ directory on the host.

nextcloud-backup-script.sh

#!/bin/bash

# MAINTENANCE MODE ON
docker container exec --user www-data --workdir /var/www/html nextcloud-app php occ maintenance:mode --on

# CREATE DATABASE DUMP, bash -c '...' IS USED OTHERWISE OUTPUT > WOULD TRY TO GO TO THE HOST
docker container exec nextcloud-db bash -c 'mysqldump --single-transaction -h nextcloud-db -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE > /var/lib/mysql/BACKUP.nextcloud.database.sql'

# MAINTENANCE MODE OFF
docker container exec --user www-data --workdir /var/www/html nextcloud-app php occ maintenance:mode --off

The script must be executable - chmod +x nextcloud-backup-script.sh

Test run the script sudo ./nextcloud-backup-script.sh
The resulting database dump is in nextcloud/nextcloud-data-db/BACKUP.nextcloud.database.sql
Cronjob

Running on the host, so that the script will be periodically run.

    su - switch to root
    crontab -e - add new cron job
    0 23 * * * /home/bastard/docker/nextcloud/nextcloud-backup-script.sh
    runs it every day at 23:00
    crontab -l - list cronjobs to check

Restore the user data

Assuming clean start.

    start the containers: docker-compose up -d
    let them run so they create the file structure
    down the containers: docker-compose down
    delete the directories config, data, themes in the freshly created nextcloud/nextcloud-data/
    from the backup of /nextcloud/nextcloud-data/, copy the directories configs, data, themes in to the new /nextcloud/nextcloud-data/
    from the backup of /nextcloud/nextcloud-data-db/, copy the backup database named BACKUP.nextcloud.database.sql in to the new /nextcloud/nextcloud-data-db/
    start the containers: docker-compose up -d
    set the correct user ownership of the directories copied:
    docker exec --workdir /var/www/html nextcloud-app chown -R www-data:www-data config data themes
    restore the database
    docker exec --workdir /var/lib/mysql nextcloud-db bash -c 'mysql -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE < BACKUP.nextcloud.database.sql'
    turn off the maintenance mode:
    docker container exec --user www-data --workdir /var/www/html nextcloud-app php occ maintenance:mode --off
    update the systems data-fingerprint:
    docker exec --user www-data --workdir /var/www/html nextcloud-app php occ maintenance:data-fingerprint
    restart the containers: docker-compose restart
    log in
