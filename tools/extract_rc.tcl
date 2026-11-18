set root $::env(PROJECT_ROOT)
set top tt_um_armohamed_r2rvc
file mkdir $root/verification/rc
cd $root/verification/rc
drc off
gds readonly true
gds maskhints yes
gds read $root/gds/$top.gds
load $top
select top cell
expand
flatten -dotoplabels ${top}_rc
load ${top}_rc
select top cell
extract path $root/verification/rc
extract all
ext2sim labels on
ext2sim
extresist tolerance 10
extresist all
ext2spice lvs
ext2spice subcircuit top on
ext2spice cthresh 0
ext2spice rthresh 0
ext2spice extresist on
ext2spice resistor tee on
ext2spice short resistor
ext2spice -o $root/spice/${top}_rc_pex.spice
puts "RC_PEX_COMPLETE"
quit -noprompt
