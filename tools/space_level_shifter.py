#!/usr/bin/env python3
"""Increase mixed-voltage well spacing by 0.4um without changing MOS W/L.

The source is the included, corrected comparator. The local custom level
shifter gets a distinct name because its geometry differs from the PDK cell.
The output-pin landing geometry retains its original left edge, so the
existing comparator routes still reach the level shifter.
"""
from pathlib import Path
import re, json, hashlib

ROOT=Path(__file__).resolve().parents[1]
OLD='sky130_fd_sc_hvl__lsbufhv2lv_1'
NEW='arm_r2rvc_lsbufhv2lv'
MAG=ROOT/'ip/EF_R2RVC/layout/mag'
path=MAG/(OLD+'.mag')
if not path.exists():
    raise SystemExit('Already prepared, or source level-shifter cell missing.')
source=path.read_text()
def sx(v):return int(v)+80 if int(v)>=706 else int(v)
def rect(m):
    x1,y1,x2,y2=map(int,m.groups())
    return f'rect {sx(x1)} {y1} {sx(x2)} {y2}'
s=re.sub(r'(?m)^rect (-?\d+) (-?\d+) (-?\d+) (-?\d+)$',rect,source)
def label(m):
    prefix,x1,y1,x2,y2,tail=m.groups()
    return f'{prefix}{sx(x1)} {y1} {sx(x2)} {y2}{tail}'
s=re.sub(r'(?m)^((?:rlabel|flabel) \S+ \S+ )(-?\d+) (-?\d+) (-?\d+) (-?\d+)( .*)$',label,s)
for prop in ['FIXED_BBOX','MASKHINTS_HVI']:
    def update(m):
        nums=list(map(int,m.group(1).split()))
        assert len(nums)%4==0
        for i in range(0,len(nums),4):nums[i]=sx(nums[i]);nums[i+2]=sx(nums[i+2])
        return 'string '+prop+' '+' '.join(map(str,nums))
    s=re.sub(r'(?m)^string '+prop+r' (.*)$',update,s)
(MAG/(NEW+'.mag')).write_text(s)
path.unlink()
parent=MAG/'EF_R2RVC.mag'
text=parent.read_text().replace('use '+OLD+' ', 'use '+NEW+' ')
text=text.replace('transform 0 1 10130 1 0 3048','transform 0 1 10130 1 0 2968')
out=[];layer='';moved=0
for line in text.splitlines():
    if line.startswith('<<'):layer=line[3:-3]
    if line.startswith('rect ') and layer in ['locali','viali','metal1','via1','metal2']:
        x1,y1,x2,y2=map(int,line.split()[1:])
        if 11090<=x1 and x2<=11180 and 2800<=y1 and y2<=3350:
            line=f'rect {x1} {y1-80} {x2} {y2-80}';moved+=1
    out.append(line)
text='\n'.join(out)+'\n'
text=text.replace('<< metal2 >>\n','<< metal2 >>\nrect 11090 2830 11190 3020\n',1)
parent.write_text(text)
for f in (ROOT/'ip/EF_R2RVC/spice/schematic').glob('*.spice'):
    f.write_text(f.read_text().replace(OLD,NEW))
audit={'change':'0.4um horizontal separation added at local x=3.53um',
       'source_cell':OLD,'custom_cell':NEW,'source_mag_sha256':hashlib.sha256(source.encode()).hexdigest(),
       'custom_mag_sha256':hashlib.sha256(s.encode()).hexdigest(),
       'MOS_channel_geometry':'L and W retained; verify independently with LVS',
       'parent_cell_adjustments':'Instance shifted down 0.4um; input landing follows it; met2 enclosure restored',
       'moved_input_landing_rectangles':moved,
       'purpose':'Pass raw full DRC without inferred-HVI mask restoration or a rule waiver'}
(ROOT/'verification/level_shifter_spacing_change.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
