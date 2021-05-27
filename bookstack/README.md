# Bookstacks docker-compose template

Will use docker volumes forthe data that isn't import
volumes:
 mariadb-data:
 uploads:
 storage-uploads:



## environment:
* PUID=1007
* PGID=1008
* DB_HOST=bookstack_db
* DB_USER=bookstack
* DB_PASS=tacotuesday
* DB_DATABASE=bookstackapp
* APP_URL=https://kb.ogbase.net
