set root $::env(PROJECT_ROOT)
cd $root/ip/EF_R2RVC/layout/mag
path search +$root/ip/EF_R2RVC/layout/mag
load EF_R2RVC
select top cell
expand
drc euclidean on
drc style drc(full)
drc check
drc catchup
set f [open $root/verification/core_native_drc.txt w]
set n 0
foreach {rule boxes} [drc listall why] {
    puts $f $rule
    foreach b $boxes {puts $f $b;incr n}
}
puts $f "ERROR_BOX_COUNT=$n"
close $f
puts "CORE_NATIVE_DRC_BOX_COUNT=$n"
gds write $root/ip/EF_R2RVC/layout/gds/EF_R2RVC.gds
quit -noprompt
