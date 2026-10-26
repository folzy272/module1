"""Two own-login actuators; subscribe .../set and acknowledge JSON .../state."""
import json,logging,os,ssl,threading,time
from pathlib import Path
import paho.mqtt.client as mqtt
logging.basicConfig(level=logging.INFO,format='%(asctime)s ACTUATOR %(message)s')
BASE='iiot/line1';FILE=Path('/control/actuators.json');LOCK=threading.Lock()
try:STATES=json.loads(FILE.read_text())
except (OSError,ValueError):STATES={'tower':'GREEN','estop':'OFF'}
STATES.setdefault('tower','GREEN');STATES.setdefault('estop','OFF')
CLIENTS={}
def store():
    temp=FILE.with_suffix('.tmp');temp.write_text(json.dumps(STATES));temp.replace(FILE)
def report(dev):
    if dev in CLIENTS:CLIENTS[dev].publish(f'{BASE}/{dev}/state',json.dumps({'state':STATES[dev],'ts':int(time.time())}),qos=1,retain=True)
def make(dev):
    c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='actuator-'+dev)
    c.username_pw_set('actuator_'+dev,os.environ['PWD_ACTUATOR_'+dev.upper()]);c.tls_set(ca_certs='/certs/ca.crt',cert_reqs=ssl.CERT_REQUIRED)
    c.will_set(f'{BASE}/{dev}/status','offline',qos=1,retain=True)
    def on_connect(c,user,flags,reason,properties):
        if reason==0:
            c.subscribe(f'{BASE}/{dev}/set',qos=1);c.publish(f'{BASE}/{dev}/status','online',qos=1,retain=True)
            report(dev)
    def on_message(c,user,msg):
        try:state=json.loads(msg.payload.decode())['state']
        except (UnicodeDecodeError,ValueError,KeyError,TypeError):return
        allowed=('GREEN','YELLOW','RED') if dev=='tower' else ('ON','OFF')
        if state not in allowed:return
        with LOCK:
            if dev=='tower' and STATES['estop']=='ON':state='RED'
            STATES[dev]=state
            if dev=='estop' and state=='ON':STATES['tower']='RED'
            store();report(dev)
            if dev=='estop' and state=='ON':report('tower')
        logging.warning('%s state confirmed=%s',dev,state)
    c.on_connect=on_connect;c.on_message=on_message;c.connect('mosquitto',8883,15);return c
forbidden=('OFF',)
def main():
    for dev in ('tower','estop'):
        while dev not in CLIENTS:
            try:CLIENTS[dev]=make(dev);CLIENTS[dev].loop_start()
            except OSError as exc:logging.warning('MQTT wait %s: %s',dev,exc);time.sleep(2)
    while True:time.sleep(2)
if __name__=='__main__':main()
