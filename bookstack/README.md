# Bookstacks docker-compose template
https://hub.docker.com/r/linuxserver/bookstack

Will use docker volumes for the data that isn't import
volumes:
* mariadb-data:
* uploads:
* storage-uploads:



## environment:
* PUID=1007
* PGID=1008
* DB_HOST=bookstack_db
* DB_USER=bookstack
* DB_PASS=tacotuesday
* DB_DATABASE=bookstackapp
* APP_URL=https://kb.ogbase.net


## LDAP Authentication

https://www.bookstackapp.com/docs/admin/installation/
