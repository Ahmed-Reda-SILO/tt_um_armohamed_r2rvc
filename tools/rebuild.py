#!/usr/bin/env python3
"""Rebuild, extract, and verify the routed Tiny Tapeout submission."""
from pathlib import Path
import argparse,os,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1]
TOP='tt_um_armohamed_r2rvc'
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pdk-root',default=os.environ.get('PDK_ROOT'),required=not bool(os.environ.get('PDK_ROOT')))
    p.add_argument('--tt-support-tools',help='Official tt-support-tools checkout for the unmodified provider precheck.')
    p.add_argument('--netgen-tcl',default=os.environ.get('NETGEN_TCL'))
    p.add_argument('--no-sim',action='store_true')
    args=p.parse_args();env=os.environ.copy()
    env.update(PDK_ROOT=str(Path(args.pdk_root).resolve()),PROJECT_ROOT=str(ROOT))
    if args.netgen_tcl:env['NETGEN_TCL']=str(Path(args.netgen_tcl).resolve())
    magic=os.environ.get('MAGIC','magic');netgen=os.environ.get('NETGEN','netgen')
    def run(cmd,log,extra=None,cwd=None):
        e=env.copy();e.update(extra or {})
        print(log,flush=True)
        with (ROOT/'verification'/log).open('w') as f:
            subprocess.run(list(map(str,cmd)),env=e,cwd=cwd or ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
    def mtcl(name,log):
        run([magic,'-dnull','-noconsole','-rcfile',Path(env['PDK_ROOT'])/'sky130A/libs.tech/magic/sky130A.magicrc',ROOT/'tools'/name],log)
    def lvs(log,extra=None):
        cmd=['tclsh',ROOT/'tools/run_lvs.tcl'] if args.netgen_tcl else [netgen,'-batch','source',ROOT/'tools/run_lvs.tcl']
        run(cmd,log,extra)
    mtcl('export_core.tcl','export_core.log')
    run(['python3',ROOT/'tools/build_wrapper.py'],'build_wrapper.log')
    run(['python3',ROOT/'tools/check_wrapper_connectivity.py'],'connectivity.log')
    mtcl('extract_and_drc.tcl','extract_and_drc.log')
    for n in ['core_native_drc.txt','magic_drc.txt']:
        assert 'ERROR_BOX_COUNT=0' in (ROOT/'verification'/n).read_text(),n
    run(['python3',ROOT/'tools/prepare_lvs_reference.py'],'prepare_lvs.log')
    lvs('netgen.log');lvs('netgen_flat.log',{'FLAT_LVS':'1'})
    mtcl('extract_rc.tcl','extract_rc.log')
    run(['python3',ROOT/'tools/check_rc_topology.py'],'rc_topology_preparation.log')
    lvs('netgen_rc_topology.log',{'RC_LVS':'1'})
    for n in ['lvs_report.txt','lvs_flat_report.txt','lvs_rc_topology_report.txt']:
        text=(ROOT/'verification'/n).read_text()
        assert 'Circuits match uniquely.' in text and 'Netlists do not match.' not in text,n
    if args.tt_support_tools:
        support=Path(args.tt_support_tools).resolve()
        shutil.copy2(ROOT/'src/project.v',ROOT/f'gds/{TOP}.v')
        run(['python3','precheck.py','--gds',ROOT/f'gds/{TOP}.gds'],'precheck.log',cwd=support/'precheck')
        dst=ROOT/'verification/precheck_reports';dst.mkdir(exist_ok=True)
        for n in ['results.md','results.xml','magic_drc.txt']:shutil.copy2(support/'precheck/reports'/n,dst/n)
    if not args.no_sim:run(['python3',ROOT/'tools/run_simulations.py'],'run_simulations.log')
    print('Verification completed. Inspect reports before submission.')
if __name__=='__main__':main()
