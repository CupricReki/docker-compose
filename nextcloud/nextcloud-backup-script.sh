#!/bin/bash

# MAINTENANCE MODE ON
docker container exec --user www-data --workdir /var/www/html nextcloud-app php occ maintenance:mode --on

# CREATE DATABASE DUMP, bash -c '...' IS USED OTHERWISE OUTPUT > WOULD TRY TO GO TO THE HOST
docker container exec nextcloud-db bash -c 'mysqldump --single-transaction -h nextcloud-db -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE > /var/lib/mysql/BACKUP.nextcloud.database.sql'

# MAINTENANCE MODE OFF
docker container exec --user www-data --workdir /var/www/html nextcloud-app php occ maintenance:mode --off
