#!/usr/bin/env python3
"""Build the routed SKY130 Tiny Tapeout wrapper without changing the IP core.

Requires gdstk. Run from any directory; paths are relative to this script.
The authoritative interface dimensions and pin positions come from the
vendored Tiny Tapeout 1x2, 3.3 V DEF template.
"""
from pathlib import Path
import json
import re
import gdstk

ROOT = Path(__file__).resolve().parents[1]
TOP = 'tt_um_armohamed_r2rvc'
M3, V3, M4 = (70, 20), (70, 44), (71, 20)
PIN4, LABEL4, BOUNDARY = (71, 16), (71, 5), (235, 4)


def parse_template(path):
    text = path.read_text()
    dbu = int(re.search(r'UNITS DISTANCE MICRONS (\d+)', text)[1])
    area = re.search(r'DIEAREA \( 0 0 \) \( (\d+) (\d+) \)', text)
    width, height = int(area[1])/dbu, int(area[2])/dbu
    section = text.split('PINS 51 ;', 1)[1].split('END PINS', 1)[0]
    pins = {}
    for block in re.split(r'\n\s*- ', section)[1:]:
        name = block.split()[0]
        direction = re.search(r'DIRECTION (\w+)', block)[1]
        a = re.search(r'LAYER met4 \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)', block)
        b = re.search(r'PLACED \( (-?\d+) (-?\d+) \) N', block)
        x, y = int(b[1])/dbu, int(b[2])/dbu
        rect = [x+int(a[1])/dbu, y+int(a[2])/dbu,
                x+int(a[3])/dbu, y+int(a[4])/dbu]
        pins[name] = {'rect': rect, 'center': [x, y], 'direction': direction}
    return width, height, pins


def rect(cell, box, spec):
    cell.add(gdstk.rectangle(box[:2], box[2:], layer=spec[0], datatype=spec[1]))


def wire(cell, points, width, spec):
    path = gdstk.FlexPath(points, width, joins='miter', ends='flush',
                          layer=spec[0], datatype=spec[1])
    cell.add(*path.to_polygons())


def via3(cell, x, y):
    # 2x2 via3 array: 0.2 um cuts, 0.2 um gaps, 0.1 um enclosures.
    for spec in [M3, M4]:
        rect(cell, [x-.4, y-.4, x+.4, y+.4], spec)
    for dx in [-.2, .2]:
        for dy in [-.2, .2]:
            rect(cell, [x+dx-.1, y+dy-.1, x+dx+.1, y+dy+.1], V3)


def main():
    width, height, pins = parse_template(ROOT/'templates/tt_analog_1x2_3v3.def')
    source = ROOT/'ip/EF_R2RVC/layout/gds/EF_R2RVC.gds'
    raw_cells = gdstk.read_rawcells(source)
    lib = gdstk.Library()
    lib.add(*raw_cells.values())
    parsed = gdstk.read_gds(ROOT/'ip/EF_R2RVC/layout/gds/EF_R2RVC.gds')
    core = next(c for c in parsed.cells if c.name == 'EF_R2RVC')
    wrapper = lib.new_cell(TOP)
    shift = (39.02, 76.325)  # IP bounding box becomes (35,75)-(98.11,127.495) um.
    wrapper.add(gdstk.Reference(raw_cells['EF_R2RVC'], origin=shift))
    rect(wrapper, [0, 0, width, height], BOUNDARY)
    for name, pin in pins.items():
        rect(wrapper, pin['rect'], M4)
        rect(wrapper, pin['rect'], PIN4)
        wrapper.add(gdstk.Label(name, pin['center'], layer=LABEL4[0], texttype=LABEL4[1]))

    # Three vertical power stripes, clear of the core and signal routes.
    for name, x in [('VDPWR', 2.0), ('VGND', 5.0), ('VAPWR', 10.0)]:
        box = [x-1, 5, x+1, height-5]
        rect(wrapper, box, M4)
        rect(wrapper, box, PIN4)
        wrapper.add(gdstk.Label(name, (x, height/2), layer=71, texttype=5))
        pins[name] = {'rect':box, 'center':[x,height/2],
                      'direction':'INOUT', 'use':'GROUND' if name=='VGND' else 'POWER'}

    labels = {l.text:(float(l.origin[0]+shift[0]), float(l.origin[1]+shift[1])) for l in core.labels}
    # Analog inputs leave the left edge on met3. Their met4 paths are nested.
    for core_pin, external, lane_x, lane_y in [
        ('VINP', 'ua[0]', 25., 35.), ('VINM', 'ua[1]', 20., 30.)]:
        x,y = labels[core_pin]
        wire(wrapper, [(x,y),(lane_x,y)], .6, M3)
        via3(wrapper, lane_x,y)
        tx,ty = pins[external]['center']
        wire(wrapper, [(lane_x,y),(lane_x,lane_y),(tx,lane_y),(tx,ty)], .9, M4)

    # Analog supply, digital supply, and the two core grounds.
    x,y = labels['VDD']
    wire(wrapper, [(x,y),(10.,y)], 1., M3); via3(wrapper,10.,y)
    x,y = labels['VSS']
    wire(wrapper, [(x,y),(104.,y),(104.,160.),(5.,160.)], 1., M3); via3(wrapper,5.,160.)
    x,y = labels['DVDD']
    wire(wrapper, [(x,y),(109.,y),(109.,170.),(2.,170.)], 1., M3); via3(wrapper,2.,170.)
    x,y = labels['DVSS']
    wire(wrapper, [(x,y),(x,65.),(5.,65.)], 1., M3); via3(wrapper,5.,65.)

    # 1.8 V comparator output to the first dedicated digital output.
    x,y = labels['VOUT']
    wire(wrapper, [(x,y),(114.,y)], .6, M3); via3(wrapper,114.,y)
    tx,ty = pins['uo_out[0]']['center']
    wire(wrapper, [(114.,y),(114.,200.),(tx,200.),(tx,224.)], .6, M4)
    wire(wrapper, [(tx,223.8),(tx,ty)], .3, M4)

    # All 23 unused output / output-enable pins are physically tied to VGND.
    ties = [f'uo_out[{i}]' for i in range(1,8)]
    ties += [f'{bus}[{i}]' for bus in ['uio_out','uio_oe'] for i in range(8)]
    wire(wrapper, [(5.,214.),(75.9,214.)], 1., M3); via3(wrapper,5.,214.)
    for name in ties:
        tx,ty = pins[name]['center']
        wire(wrapper, [(tx,214.),(tx,ty)], .3, M4)
        via3(wrapper,tx,214.)

    for folder in ['gds','lef','verification']:
        (ROOT/folder).mkdir(exist_ok=True)
    lib.write_gds(ROOT/f'gds/{TOP}.gds', timestamp=__import__('datetime').datetime(2026,11,18))
    lef = ['VERSION 5.8 ;','BUSBITCHARS "[]" ;','DIVIDERCHAR "/" ;',
           f'MACRO {TOP}','  CLASS BLOCK ;',f'  FOREIGN {TOP} 0 0 ;',
           '  ORIGIN 0 0 ;',f'  SIZE {width:.3f} BY {height:.3f} ;','  SYMMETRY X Y ;']
    for name,pin in pins.items():
        a=pin['rect']
        lef += [f'  PIN {name}',f"    DIRECTION {pin['direction']} ;",
                f"    USE {pin.get('use','SIGNAL')} ;",'    PORT','      LAYER met4 ;',
                '      RECT '+' '.join(f'{v:.3f}' for v in a)+' ;','    END',f'  END {name}']
    lef += [f'END {TOP}','END LIBRARY','']
    (ROOT/f'lef/{TOP}.lef').write_text('\n'.join(lef))
    data={'top':TOP,'size_um':[width,height],'core_origin_um':shift,
          'core_ports_um':labels,'interface_pins':pins,'grounded_outputs':ties,
          'mapping':{'VINP':'ua[0]','VINM':'ua[1]','VOUT':'uo_out[0]',
                     'VDD':'VAPWR','DVDD':'VDPWR','VSS':'VGND','DVSS':'VGND'}}
    (ROOT/'verification/wrapper_geometry.json').write_text(json.dumps(data,indent=2)+'\n')
    print(f'Built {TOP}: {width:.3f} x {height:.3f} um; {len(lib.cells)} cells; 2 analog inputs.')


if __name__ == '__main__':
    main()
