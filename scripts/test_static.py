from pathlib import Path
import ast,yaml
root=Path(__file__).resolve().parents[1]
for src in (root/'simulator').glob('*.py'):ast.parse(src.read_text(encoding='utf-8'))
compose=yaml.safe_load((root/'docker-compose.yml').read_text(encoding='utf-8'))
assert len(compose['services'])==5
assert 'allow_anonymous false' in (root/'mosquitto/config/mosquitto.conf').read_text()
for sensor in ('vibration','bearing','current','parts','machine'):
    assert 'user sensor_'+sensor in (root/'mosquitto/config/acl').read_text()
assert 'AI_USAGE.md' in [p.name for p in root.iterdir()]
print('Static syntax/structure/security checks: PASS')
