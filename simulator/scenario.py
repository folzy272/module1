import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('scenario',choices=['normal','warning','critical','heat','idle']);a=p.parse_args()
f=Path('/control/scenario.json');t=f.with_suffix('.tmp');t.write_text(json.dumps({'scenario':a.scenario}));t.replace(f)
print('Scenario selected:',a.scenario, '(manual reset E-stop OFF after critical)')
