#!/usr/bin/env python3
"""Check routed wrapper nets independently with KLayout geometry operations."""
from pathlib import Path
import json
import klayout.db as k

ROOT=Path(__file__).resolve().parents[1]
TOP='tt_um_armohamed_r2rvc'


def main():
    meta=json.loads((ROOT/'verification/wrapper_geometry.json').read_text())
    layout=k.Layout();layout.read(str(ROOT/f'gds/{TOP}.gds'))
    top=layout.cell(TOP)
    components={}
    parent=[]
    for layer in [70,71]:
        idx=layout.layer(layer,20)
        reg=k.Region(top.shapes(idx)).merged()
        components[layer]=[]
        for polygon in reg.each():
            i=len(parent);parent.append(i);components[layer].append((i,polygon))

    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i

    def unite(a,b):
        parent[find(a)]=find(b)

    vias=k.Region(top.shapes(layout.layer(70,44)))
    for via in vias.each():
        touched={}
        for layer in [70,71]:
            touched[layer]=[i for i,p in components[layer]
                             if not (k.Region(p)&k.Region(via)).is_empty()]
            assert len(touched[layer])==1, f'Open/ambiguous via on layer {layer}: {via.bbox()}'
        unite(touched[70][0],touched[71][0])

    def node(layer,point):
        x,y=[round(v/layout.dbu) for v in point]
        probe=k.Region(k.Box(x-1,y-1,x+1,y+1))
        hits=[i for i,p in components[layer] if not (k.Region(p)&probe).is_empty()]
        assert len(hits)==1,(layer,point,hits)
        return find(hits[0])

    checks={}
    for core_pin,external in meta['mapping'].items():
        checks[f'{core_pin}_to_{external}']=node(70,meta['core_ports_um'][core_pin])==node(71,meta['interface_pins'][external]['center'])
    ground=node(71,meta['interface_pins']['VGND']['center'])
    checks['unused_digital_outputs_grounded']=all(node(71,meta['interface_pins'][p]['center'])==ground for p in meta['grounded_outputs'])
    functional=['VGND','VDPWR','VAPWR','ua[0]','ua[1]','uo_out[0]']
    roots=[node(71,meta['interface_pins'][p]['center']) for p in functional]
    checks['functional_nets_not_shorted']=len(set(roots))==len(roots)
    # Prove that the supplied IP is geometrically unchanged in the wrapper.
    old=k.Layout();old.read(str(ROOT/'ip/EF_R2RVC/layout/gds/EF_R2RVC.gds'))
    src=old.cell('EF_R2RVC');dst=layout.cell('EF_R2RVC')
    same=True
    for spec in set(old.layer_infos())|set(layout.layer_infos()):
        a=k.Region(src.begin_shapes_rec(old.layer(spec)))
        b=k.Region(dst.begin_shapes_rec(layout.layer(spec)))
        if not (a^b).is_empty():same=False
    checks['original_core_geometry_preserved']=same
    report={'checks':checks,'all_pass':all(checks.values())}
    (ROOT/'verification/wrapper_connectivity.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not report['all_pass']:raise SystemExit(1)


if __name__=='__main__':main()
