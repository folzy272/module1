"""Negative security checks on broker, run inside gateway container."""
import os,socket,ssl,time,threading
import paho.mqtt.client as mqtt

def mk(user=None,password=None,id='probe'):
    c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id=id)
    if user:c.username_pw_set(user,password)
    c.tls_set(ca_certs='/certs/ca.crt',cert_reqs=ssl.CERT_REQUIRED);return c
status=[];anon=mk(id='anon');anon.on_connect=lambda c,u,f,r,p:status.append(str(r))
try:anon.connect('mosquitto',8883);anon.loop_start();time.sleep(1);anon.disconnect();anon.loop_stop()
except Exception as e:status.append(str(e))
print('Anonymous TLS (must not succeed):',status)
try:
    with socket.create_connection(('mosquitto',8883),timeout=2) as s:
        s.settimeout(2);s.sendall(bytes.fromhex('101000044d5154540402000f000470726f62'));response=s.recv(4)
    print('Plaintext (must NOT be CONNACK success):',response.hex())
except (OSError,TimeoutError) as e:print('Plaintext rejected:',type(e).__name__)
found=threading.Event();admin=mk('admin',os.environ['PWD_ADMIN'],'admin-probe')
admin.on_connect=lambda c,u,f,r,p:c.subscribe('iiot/line1/bearing/telemetry')
admin.on_message=lambda c,u,m:found.set() if m.payload==b'UNAUTHORIZED_PROBE' else None
admin.connect('mosquitto',8883);admin.loop_start();time.sleep(1)
wrong=mk('sensor_vibration',os.environ['PWD_SENSOR_VIBRATION'],'wrong-probe');wrong.connect('mosquitto',8883);wrong.loop_start();time.sleep(.5)
wrong.publish('iiot/line1/bearing/telemetry',b'UNAUTHORIZED_PROBE',qos=1);time.sleep(1.5)
print('ACL unrelated sensor telemetry publish:', 'FAIL' if found.is_set() else 'PASS - blocked')
wrong.disconnect();wrong.loop_stop();admin.disconnect();admin.loop_stop()
