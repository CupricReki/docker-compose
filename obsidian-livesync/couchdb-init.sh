#!/bin/bash
source .env
if [[ -z "$COUCHDB_HOSTNAME" ]]; then
    echo "ERROR: COUCHDB_HOSTNAME missing"
    exit 1
fi
if [[ -z "$COUCHDB_USER" ]]; then
    echo "ERROR: COUCHDB_USER missing"
    exit 1
fi

if [[ -z "$COUCHDB_PW" ]]; then
    echo "ERROR: COUCHDB_PW missing"
    exit 1
fi

echo "-- Configuring CouchDB by REST APIs... -->"

until (curl -X POST "${COUCHDB_HOSTNAME}/_cluster_setup" -H "Content-Type: application/json" -d "{\"action\":\"enable_single_node\",\"COUCHDB_USER\":\"${COUCHDB_USER}\",\"COUCHDB_PW\":\"${COUCHDB_PW}\",\"bind_address\":\"0.0.0.0\",\"port\":5984,\"singlenode\":true}" --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done
until (curl -X PUT "${COUCHDB_HOSTNAME}/_node/nonode@nohost/_config/chttpd/require_valid_user" -H "Content-Type: application/json" -d '"true"' --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done
until (curl -X PUT "${COUCHDB_HOSTNAME}/_node/nonode@nohost/_config/chttpd_auth/require_valid_user" -H "Content-Type: application/json" -d '"true"' --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done
until (curl -X PUT "${COUCHDB_HOSTNAME}/_node/nonode@nohost/_config/httpd/WWW-Authenticate" -H "Content-Type: application/json" -d '"Basic realm=\"couchdb\""' --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done
until (curl -X PUT "${COUCHDB_HOSTNAME}/_node/nonode@nohost/_config/httpd/enable_cors" -H "Content-Type: application/json" -d '"true"' --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done
until (curl -X PUT "${COUCHDB_HOSTNAME}/_node/nonode@nohost/_config/chttpd/enable_cors" -H "Content-Type: application/json" -d '"true"' --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done
until (curl -X PUT "${COUCHDB_HOSTNAME}/_node/nonode@nohost/_config/chttpd/max_http_request_size" -H "Content-Type: application/json" -d '"4294967296"' --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done
until (curl -X PUT "${COUCHDB_HOSTNAME}/_node/nonode@nohost/_config/couchdb/max_document_size" -H "Content-Type: application/json" -d '"50000000"' --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done
until (curl -X PUT "${COUCHDB_HOSTNAME}/_node/nonode@nohost/_config/cors/credentials" -H "Content-Type: application/json" -d '"true"' --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done
until (curl -X PUT "${COUCHDB_HOSTNAME}/_node/nonode@nohost/_config/cors/origins" -H "Content-Type: application/json" -d '"app://obsidian.md,capacitor://localhost,http://localhost"' --user "${COUCHDB_USER}:${COUCHDB_PW}"); do sleep 5; done

echo "<-- Configuring CouchDB by REST APIs Done!"
