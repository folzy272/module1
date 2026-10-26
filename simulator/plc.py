"""Modbus TCP Unit ID 1 simulator (PyModbus 3.8.6)."""
import asyncio, json, logging, math, os, random, time
from pathlib import Path
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.server import StartAsyncTcpServer
logging.basicConfig(level=logging.INFO,format='%(asctime)s PLC %(message)s')
BASE=Path('/control')
SHIFT=float(os.getenv('SHIFT_REAL_SECONDS','120'))
def control(name):
    try:return json.loads((BASE/name).read_text())
    except (ValueError,OSError):return {}
async def update(slave):
    rng=random.Random(4); start=last=part_clock=shift_start=time.monotonic(); scenario='normal'; scene_start=start
    shift_id=1; count=shift_count=0; downtime=0.
    while True:
        now=time.monotonic()
        selected=control('scenario.json').get('scenario','normal')
        if selected not in ('normal','warning','critical','heat','idle'):selected='normal'
        if selected!=scenario:scenario=selected;scene_start=now;logging.warning('SCENARIO %s',scenario)
        if now-shift_start>=SHIFT:
            shift_start=now;shift_id+=1;shift_count=0;downtime=0.
        elapsed=now-start
        stopped=control('actuators.json').get('estop')=='ON'
        state='FAULT' if stopped or scenario=='critical' else ('IDLE' if scenario=='idle' or elapsed%50>42 else 'RUN')
        vib=2.05+.2*math.sin(elapsed/17)+rng.uniform(-.06,.06)
        if scenario=='warning':vib=5.3+.1*math.sin(elapsed/5)
        if scenario=='critical':vib=8.2+.1*math.sin(elapsed/5)
        temp=47.8+.3*math.sin(elapsed/21)+.004*elapsed+rng.uniform(-.04,.04)
        if scenario=='heat':temp+=min(8.5,8.5*(now-scene_start)/30)
        current=12.8+.7*math.sin(elapsed/12) if state=='RUN' else (.2 if state=='FAULT' else 1.7)
        if state=='RUN':
            if now-part_clock>=3:count+=1;shift_count+=1;part_clock=now
        else:downtime+=max(0,now-last)*28800/SHIFT;part_clock=now
        last=now
        # PyModbus 3.8 SlaveContext maps requested address 0 to backing block address 1.
        registers=[round(vib*100),round(temp*10),round(current*10),count&65535,count>>16,{'IDLE':0,'RUN':1,'FAULT':2}[state],shift_id,shift_count,min(28800,round(downtime))]
        slave.setValues(3,0,registers)
        logging.info('state=%s vibration=%.2f C=%.1f total=%d shift=%d downtime=%.1f min',state,vib,temp,count,shift_id,downtime/60)
        await asyncio.sleep(2)
async def main():
    slave=ModbusSlaveContext(hr=ModbusSequentialDataBlock(1,[0]*64))
    await asyncio.gather(update(slave),StartAsyncTcpServer(context=ModbusServerContext(slaves={1:slave},single=False),address=('0.0.0.0',5020)))
if __name__=='__main__':asyncio.run(main())
