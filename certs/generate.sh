#!/bin/sh
set -eu
mkdir -p certs
if [ ! -f certs/ca.crt ] || [ ! -f certs/ca.key ]; then
 openssl req -x509 -newkey rsa:3072 -sha256 -days 365 -nodes -subj '/CN=IIoT variant 4 CA' -keyout certs/ca.key -out certs/ca.crt >/dev/null 2>&1
fi
if [ ! -f certs/server.crt ] || [ ! -f certs/server.key ]; then
 openssl req -newkey rsa:3072 -nodes -subj '/CN=mosquitto' -keyout certs/server.key -out certs/server.csr >/dev/null 2>&1
 printf 'subjectAltName=DNS:mosquitto,DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\nkeyUsage=digitalSignature,keyEncipherment\n' > certs/ext.cnf
 openssl x509 -req -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial -out certs/server.crt -days 365 -sha256 -extfile certs/ext.cnf >/dev/null 2>&1
fi
chmod 600 certs/ca.key
chown 1883:1883 certs/server.key
chmod 640 certs/server.key
chmod 644 certs/server.crt certs/ca.crt
