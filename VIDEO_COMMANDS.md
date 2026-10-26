# Команди для відеозахисту — варіант 4

## 1. Запуск системи
docker compose down
docker compose up -d
docker compose ps

## 2. Відкрити openHAB
$port = (docker compose port openhab 8080).Split(':')[-1]
Start-Process "http://localhost:$port/basicui/app?sitemap=factory"


## 3. Попередження про вібрацію
docker compose exec plc python scenario.py warning

## 4. Аварійна вібрація
docker compose exec plc python scenario.py critical

## 5. Повернення нормального режиму
docker compose exec plc python scenario.py normal

## 6. Перегрів підшипника
docker compose exec plc python scenario.py heat

## 7. Простій верстата
docker compose exec plc python scenario.py idle

## 8. Перевірка безпеки
docker compose exec gateway python security_tests.py

## 9. Логи MQTT
docker compose logs --tail=60 mosquitto

## 10. Завершення демонстрації
docker compose exec plc python scenario.py normal


docker compose exec gateway python -c "import os; from paho.mqtt import subscribe; subscribe.callback(lambda c,u,m: print(m.topic, m.payload.decode(), flush=True), 'iiot/line1/+/telemetry', hostname='mosquitto', port=8883, auth={'username':'admin','password':os.environ['PWD_ADMIN']}, tls={'ca_certs':'/certs/ca.crt'})"