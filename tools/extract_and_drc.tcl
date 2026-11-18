# Run with Magic's SKY130A startup file; environment: PROJECT_ROOT.
set root $::env(PROJECT_ROOT)
set top tt_um_armohamed_r2rvc
file mkdir $root/verification/extraction
cd $root/verification/extraction
gds readonly true
gds maskhints yes
gds read $root/gds/$top.gds
load $top
select top cell
expand
drc euclidean on
drc style drc(full)
drc check
drc catchup
set out [open $root/verification/magic_drc.txt w]
set count 0
foreach {rule boxes} [drc listall why] {
    puts $out $rule
    foreach box $boxes { puts $out $box; incr count }
}
puts $out "ERROR_BOX_COUNT=$count"
close $out
puts "DRC_ERROR_BOX_COUNT=$count"
# Save editable Magic cells independently of the authoritative GDS.
extract path $root/verification/extraction
extract all
ext2spice lvs
ext2spice subcircuit top on
ext2spice short resistor
ext2spice -o $root/spice/${top}_extracted.spice
# PEX: include capacitances for a separate post-layout simulation netlist.
ext2spice cthresh 0
ext2spice -o $root/spice/${top}_pex.spice
flatten -dotoplabels ${top}_flat
load ${top}_flat
select top cell
extract all
ext2spice lvs
ext2spice subcircuit top on
ext2spice short resistor
ext2spice -o $root/spice/${top}_flat_extracted.spice
quit -noprompt
