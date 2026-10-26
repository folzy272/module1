"""Five independent TLS MQTT sensor identities, readings from Modbus TCP."""
import json,logging,os,ssl,time
from pymodbus.client import ModbusTcpClient
import paho.mqtt.client as mqtt
logging.basicConfig(level=logging.INFO,format='%(asctime)s GATEWAY %(message)s')
BASE='iiot/line1';SENSORS=('vibration','bearing','current','parts','machine')
def client_for(dev):
    c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='sensor-'+dev)
    c.username_pw_set('sensor_'+dev,os.environ['PWD_SENSOR_'+dev.upper()])
    c.tls_set(ca_certs='/certs/ca.crt',cert_reqs=ssl.CERT_REQUIRED)
    c.will_set(f'{BASE}/{dev}/status','offline',qos=1,retain=True)
    def connected(c,userdata,flags,reason,properties):
        if reason==0:c.publish(f'{BASE}/{dev}/status','online',qos=1,retain=True)
        else:logging.error('MQTT rejected for %s: %s',dev,reason)
    c.on_connect=connected;c.connect('mosquitto',8883,15);c.loop_start();return c
def sample(v,unit,**extras):return json.dumps({'value':v,'unit':unit,'ts':int(time.time()),**extras})
def main():
    clients={}
    for dev in SENSORS:
        while dev not in clients:
            try:clients[dev]=client_for(dev)
            except OSError as exc:logging.warning('MQTT connection %s: %s',dev,exc);time.sleep(2)
    modbus=ModbusTcpClient('plc',port=5020,timeout=3);errors=0;online=True
    try:
        while True:
            try:
                if not modbus.connected and not modbus.connect():raise ConnectionError('Modbus PLC offline')
                response=modbus.read_holding_registers(address=0,count=9,slave=1)
                if response.isError():raise ConnectionError(str(response))
                r=response.registers
                values={
                    'vibration':sample(round(r[0]/100,2),'mm/s'),
                    'bearing':sample(round(r[1]/10,1),'C'),
                    'current':sample(round(r[2]/10,1),'A'),
                    'parts':sample(r[3]+65536*r[4],'pcs',shift_count=r[7],shift_id=r[6]),
                    'machine':sample({0:'IDLE',1:'RUN',2:'FAULT'}.get(r[5],'FAULT'),'state',shift_id=r[6],downtime_minutes=round(r[8]/60,1))}
                for dev,data in values.items():
                    if not online:clients[dev].publish(f'{BASE}/{dev}/status','online',qos=1,retain=True)
                    clients[dev].publish(f'{BASE}/{dev}/telemetry',data,qos=0,retain=False)
                errors=0;online=True
            except Exception as exc:
                logging.warning('Modbus poll failed: %s',exc);errors+=1;modbus.close()
                if errors>=3 and online:
                    for dev in SENSORS:clients[dev].publish(f'{BASE}/{dev}/status','offline',qos=1,retain=True)
                    online=False
            time.sleep(2)
    finally:
        for dev,c in clients.items():c.publish(f'{BASE}/{dev}/status','offline',qos=1,retain=True);c.disconnect();c.loop_stop()
if __name__=='__main__':main()
