#!/usr/bin/env python3
"""Golden corrected transistor schematic plus the physical wrapper specification."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
TOP='tt_um_armohamed_r2rvc'
src=(ROOT/'ip/EF_R2RVC/spice/schematic/EF_R2RVC_reference.spice').read_text()
src=re.sub(r'(?im)^\s*\.end\s*$','',src)
meta=json.loads((ROOT/'verification/wrapper_geometry.json').read_text())
ports=list(meta['interface_pins'])
lines=['* Corrected transistor schematic and explicit wrapper/tie-off specification',src,
       '.subckt '+TOP+' '+' '.join(ports),
       'XCORE VAPWR VGND VGND VDPWR ua[0] ua[1] uo_out[0] EF_R2RVC']
lines += [f'RTIE{i} VGND {pin} 0' for i,pin in enumerate(meta['grounded_outputs'])]
lines += ['.ends '+TOP,'']
(ROOT/'spice').mkdir(exist_ok=True)
p=ROOT/f'spice/{TOP}_reference.spice';p.write_text('\n'.join(lines))
print(p)
