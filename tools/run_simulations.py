#!/usr/bin/env python3
"""Compare corrected schematic and routed-wrapper C/RC PEX at nominal TT."""
from pathlib import Path
import json,os,re,subprocess,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
TOP='tt_um_armohamed_r2rvc'
SIM=ROOT/'verification/simulation'

def crossing(t,v,level,d):
    k=np.flatnonzero((v[:-1]<level)&(v[1:]>=level)) if d>0 else np.flatnonzero((v[:-1]>level)&(v[1:]<=level))
    return t[k]+(level-v[k])*(t[k+1]-t[k])/(v[k+1]-v[k])

def main():
    pdk=Path(os.environ['PDK_ROOT']).resolve()/'sky130A'
    binary=os.environ.get('NGSPICE',shutil.which('ngspice'))
    if not binary:raise SystemExit('ngspice not found')
    SIM.mkdir(parents=True,exist_ok=True)
    (SIM/'.spiceinit').write_text('set ngbehavior=hsa\nset skywaterpdk\nset ng_nomodcheck\nset num_threads=2\noption klu\n')
    choices={'schematic':ROOT/'ip/EF_R2RVC/spice/schematic/EF_R2RVC_reference.spice',
             'pex_c':ROOT/f'spice/{TOP}_pex.spice','pex_rc':ROOT/f'spice/{TOP}_rc_pex.spice'}
    metrics={};data={}
    for kind,src in choices.items():
        s=re.sub(r'(?im)^\s*\.end\s*$','',src.read_text())
        net=SIM/(kind+'_circuit.spice');net.write_text(s)
        top='EF_R2RVC' if kind=='schematic' else (TOP+'_rc' if kind=='pex_rc' else TOP)
        clean=re.sub(r'\n\+\s*',' ',s)
        h=re.search(r'(?im)^\.subckt '+re.escape(top)+r'\s+([^\n]+)',clean)
        assert h,top
        mapping={'VGND':'0','VAPWR':'VDD','VDPWR':'DVDD','ua[0]':'VINP','ua[1]':'VINM','uo_out[0]':'VOUT',
                 'VSS':'0','DVSS':'0','VDD':'VDD','DVDD':'DVDD','VINP':'VINP','VINM':'VINM','VOUT':'VOUT'}
        pins=h.group(1).split();nodes=[];extras=[]
        for pin in pins:
            if pin in mapping:nodes.append(mapping[pin]);continue
            node='NC_'+re.sub(r'\W','_',pin);nodes.append(node)
            if pin.startswith('ua['):extras.append('R_'+node+' '+node+' 0 1e12')
            elif pin.startswith(('uo_out','uio_out','uio_oe')):pass
            else:extras.append('V_'+node+' '+node+' 0 '+('1.8' if pin=='ena' else '0'))
        deck=f'''Nominal TT {kind}, 27C, 3.3V/1.8V, 1pF load
.lib "{pdk}/libs.tech/ngspice/sky130.lib.spice" tt
.include "{net}"
VANA VDD 0 3.3
VDIG DVDD 0 1.8
VINP VINP 0 PULSE(1.55 1.75 500n 1n 1n 500n 1u)
VINM VINM 0 1.65
CLOAD VOUT 0 1p
XU {' '.join(nodes)} {top}
{chr(10).join(extras)}
.options temp=27 tnom=27 wnflag=1 reltol=1e-4 abstol=1e-12 vntol=1e-6
.control
set noaskquit
set wr_vecnames
set wr_singlescale
tran 0.2n 3u 0 1n
let iana=-i(VANA)
let idig=-i(VDIG)
wrdata {SIM}/{kind}.dat v(VINP) v(VINM) v(VOUT) iana idig
quit
.endc
.end
'''
        bench=SIM/(kind+'.spice');bench.write_text(deck)
        env=os.environ.copy();env['SPICE_SCRIPTS']=str(pdk/'libs.tech/ngspice')
        print('Simulating',kind,flush=True)
        with (SIM/(kind+'.log')).open('w') as f:
            proc=subprocess.run([binary,'-b',str(bench)],cwd=SIM,env=env,stdout=f,stderr=subprocess.STDOUT)
        assert proc.returncode==0,kind
        a=np.loadtxt(SIM/(kind+'.dat'),skiprows=1);data[kind]=a
        t,vi,vo=a[:,0],a[:,1],a[:,3]
        m={}
        for d,title in [(1,'rise'),(-1,'fall')]:
            ci=crossing(t,vi,1.65,d);co=crossing(t,vo,.9,d);delays=[]
            for edge in ci:
                q=co[(co>=edge)&(co<edge+200e-9)]
                assert len(q),kind+' missing output transition'
                delays.append((q[0]-edge)*1e9)
            m['tpd_'+title+'_ns']=float(np.mean(delays))
        def avg(v):
            left,right=.2e-6,2.8e-6;mask=(t>left)&(t<right)
            tt=np.r_[left,t[mask],right];vv=np.r_[np.interp(left,t,v),v[mask],np.interp(right,t,v)]
            return float(np.trapezoid(vv,tt)/(right-left))
        m['analog_current_uA']=avg(a[:,4])*1e6;m['digital_current_uA']=avg(a[:,5])*1e6
        m['power_mW']=3.3*m['analog_current_uA']/1000+1.8*m['digital_current_uA']/1000
        m['low_V']=float(np.interp(200e-9,t,vo));m['high_V']=float(np.interp(800e-9,t,vo))
        m['logic_pass']=m['low_V']<.18 and m['high_V']>1.62
        assert m['logic_pass'],kind
        metrics[kind]=m
    result={'conditions':{'corner':'TT','temperature_C':27,'VAPWR_V':3.3,'VDPWR_V':1.8,'load_pF':1,'VINP_low_V':1.55,'VINP_high_V':1.75,'VINM_V':1.65,'input_edges_ns':1,'frequency_MHz':1},'metrics':metrics}
    (ROOT/'verification/simulation_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(11,4.0))
    colors={'schematic':'#566b7a','pex_c':'#dc9a33','pex_rc':'#0c8190'}
    labels={'schematic':'Corrected schematic','pex_c':'Wrapper C PEX','pex_rc':'Wrapper RC PEX'}
    for k,a in data.items():
        axes[0].plot(a[:,0]*1e6,a[:,3],color=colors[k],label=labels[k],ls='--' if k=='schematic' else '-')
        axes[1].plot((a[:,0]-.5005e-6)*1e9,a[:,3],color=colors[k],ls='--' if k=='schematic' else '-')
    axes[0].set(xlim=(.4,2.2),ylim=(-.05,1.9),xlabel='Time (µs)',ylabel='VOUT (V)',title='Complete-wrapper pulse response');axes[0].legend(fontsize=8)
    axes[1].set(xlim=(-5,45),ylim=(-.05,1.9),xlabel='Time after input midpoint (ns)',ylabel='VOUT (V)',title='Rising transition')
    for ax in axes:ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('TT · 27 °C · 3.3 V/1.8 V supplies · 1 pF load · 1.55–1.75 V input',fontsize=11)
    fig.tight_layout();fig.savefig(ROOT/'verification/nominal_PEX.png',dpi=180)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
