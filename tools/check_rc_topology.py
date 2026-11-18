#!/usr/bin/env python3
"""Compare RC topology independently after removing C and shorting only route R."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
TOP='tt_um_armohamed_r2rvc'
src=ROOT/f'spice/{TOP}_rc_pex.spice'
s=re.sub(r'\n\+\s*',' ',src.read_text());parent={}
def find(x):
    parent.setdefault(x,x)
    if parent[x]!=x:parent[x]=find(parent[x])
    return parent[x]
for l in s.splitlines():
    v=l.split()
    if v and v[0][0].upper()=='R':
        a,b=find(v[1]),find(v[2])
        if a!=b:parent[b]=a
pins=re.search(r'(?im)^\.subckt\s+\S+\s+([^\n]+)',s).group(1).split()
canon={}
for p in pins:
    root=find(p)
    if root not in canon or p=='VGND':canon[root]=p
out=['* TOPOLOGY CHECK ONLY: C removed and distributed route R shorted.']
for l in s.splitlines():
    v=l.split()
    if v and v[0][0].upper()=='X':
        i=next(j for j,x in enumerate(v) if x.startswith('sky130_'))
        for j in range(1,i):v[j]=canon.get(find(v[j]),find(v[j]))
        out.append(' '.join(v))
    elif l.lower().startswith('.subckt'):
        out.append(l)
        for p in pins:
            c=canon[find(p)]
            if p!=c:out.append('RTIE'+str(len(out))+' '+p+' '+c+' 0')
    elif l.lower().startswith('.ends'):out.append(l)
(ROOT/f'spice/{TOP}_rc_shorted.spice').write_text('\n'.join(out)+'\n')
print('RC topology reference prepared.')
