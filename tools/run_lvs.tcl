if {![namespace exists ::netgen]} {source $::env(NETGEN_TCL)}
set root $::env(PROJECT_ROOT)
set top tt_um_armohamed_r2rvc
set file $root/spice/${top}_extracted.spice
set subckt $top
set report $root/verification/lvs_report.txt
if {[info exists ::env(FLAT_LVS)]} {
    set file $root/spice/${top}_flat_extracted.spice
    set subckt ${top}_flat
    set report $root/verification/lvs_flat_report.txt
}
if {[info exists ::env(RC_LVS)]} {
    set file $root/spice/${top}_rc_shorted.spice
    set subckt ${top}_rc
    set report $root/verification/lvs_rc_topology_report.txt
}
netgen::lvs [list $file $subckt] [list $root/spice/${top}_reference.spice $top] \
    $::env(PDK_ROOT)/sky130A/libs.tech/netgen/sky130A_setup.tcl $report -json
exit
