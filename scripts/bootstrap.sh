#!/bin/sh
set -eu
cd /workspace
apk add --no-cache openssl mosquitto openjdk21-jre-headless >/dev/null
if [ ! -f .env ]; then
 umask 077
 for var in PWD_SENSOR_VIBRATION PWD_SENSOR_BEARING PWD_SENSOR_CURRENT PWD_SENSOR_PARTS PWD_SENSOR_MACHINE PWD_ACTUATOR_TOWER PWD_ACTUATOR_ESTOP PWD_OPENHAB PWD_ADMIN; do
  printf '%s=%s\n' "$var" "$(openssl rand -hex 18)" >> .env
 done
fi
set -a;. ./.env;set +a
sh certs/generate.sh
if [ ! -f certs/truststore.p12 ]; then
 keytool -importkeystore -noprompt -srckeystore /usr/lib/jvm/default-jvm/lib/security/cacerts -srcstorepass changeit -destkeystore certs/truststore.p12 -deststoretype PKCS12 -deststorepass changeit >/dev/null 2>&1
 keytool -importcert -noprompt -alias iiot-local-ca -file certs/ca.crt -keystore certs/truststore.p12 -storetype PKCS12 -storepass changeit >/dev/null 2>&1
fi
rm -f mosquitto/config/passwd
mosquitto_passwd -c -b mosquitto/config/passwd sensor_vibration "$PWD_SENSOR_VIBRATION"
mosquitto_passwd -b mosquitto/config/passwd sensor_bearing "$PWD_SENSOR_BEARING"
mosquitto_passwd -b mosquitto/config/passwd sensor_current "$PWD_SENSOR_CURRENT"
mosquitto_passwd -b mosquitto/config/passwd sensor_parts "$PWD_SENSOR_PARTS"
mosquitto_passwd -b mosquitto/config/passwd sensor_machine "$PWD_SENSOR_MACHINE"
mosquitto_passwd -b mosquitto/config/passwd actuator_tower "$PWD_ACTUATOR_TOWER"
mosquitto_passwd -b mosquitto/config/passwd actuator_estop "$PWD_ACTUATOR_ESTOP"
mosquitto_passwd -b mosquitto/config/passwd openhab "$PWD_OPENHAB"
mosquitto_passwd -b mosquitto/config/passwd admin "$PWD_ADMIN"
chown 1883:1883 mosquitto/config/passwd
chmod 640 mosquitto/config/passwd
sed "s/@PASSWORD@/$PWD_OPENHAB/g" openhab/conf/things/factory.things.template > openhab/conf/things/factory.things
chown 9001:9001 openhab/conf/things/factory.things
chmod 640 openhab/conf/things/factory.things
chmod 644 certs/truststore.p12
chmod 600 .env
printf 'Secrets + certificates + openHAB configuration generated locally.\n'
