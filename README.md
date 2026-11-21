# SKY130 voltage comparator prototype

Tiny Tapeout SKY130A analog/custom-GDS submission for `tt_um_armohamed_r2rvc`.
The project integrates the corrected EF_R2RVC comparator into the official
1x2, 3.3 V template. It uses two analog inputs and one digital output.

| Setting | Value |
|---|---|
| Process | SKY130A |
| Template | `tt_analog_1x2_3v3.def` |
| Wrapper size | 145.360 × 225.760 µm |
| Analog pins | ua[0] = VINP; ua[1] = VINM |
| Digital output | uo_out[0] = comparator output |
| Supplies | VAPWR = 3.3 V; VDPWR = 1.8 V; VGND = common ground |
| Metadata | `analog_pins: 2`; `uses_vapwr: true`; `tiles: "1x2"` |

The final local revision passes all 15 checks in the unmodified Tiny Tapeout
precheck, plus raw Magic full DRC, hierarchical LVS, flattened LVS, and a
separate RC-netlist topology check. Nominal schematic and wrapper C/RC PEX
simulations produce the expected logic output. See
[VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) for results and scope.

The wrapper also contains a 0.4 µm spacing adjustment in a custom-named level
shifter cell. All MOS W/L values are retained. The revised exported GDS passes
raw full DRC without HVI mask restoration, a modified deck, or a waiver.

## Characterized operating limits

This submission is an experimental comparator with a limited characterized
common-mode range. The tested common-mode points from **0.3 to 2.4 V** pass
all 135 deterministic PVT cases and 200 local-mismatch runs at differential
input +/-20 mV, 1 MHz, and a 1 pF internal output load. These finite-grid
results do not establish an unrestricted 0-3.3 V rail-to-rail specification.

At VCM = 2.7 V, 311/335 runs meet the nominal 250 ns settling criterion,
and 320/335 meet late-phase logic. The lower grid endpoint is not a measured
minimum common-mode limit. Internal output HIGH follows VDPWR, nominally 1.8 V.

See [the range-characterization record](verification/operating_range_validation.md)
and [the numeric summary](verification/operating_range_summary.json) for the
grid, conditions, failures, and scope. Device corners and temperature vary;
extracted interconnect R/C remains fixed. MC here is native local mismatch,
not statistical global-process MC or a silicon-yield guarantee.

## Main files

- `gds/tt_um_armohamed_r2rvc.gds`: physical submission.
- `lef/tt_um_armohamed_r2rvc.lef`: matching pin-only abstract.
- `src/project.v`: physical black-box interface.
- `info.yaml`: submission metadata and datasheet pinout.
- `docs/info.md`: operating and test instructions.
- `ip/EF_R2RVC/`: corrected source schematic, editable layout cells, and core GDS.
- `tools/`: rebuild, extraction, LVS, connectivity, and simulation scripts.
- `verification/`: local reports, provenance, and nominal comparison plot.
- `spice/`: extracted and golden wrapper netlists.

## Reproduce locally

Install Magic, Netgen, KLayout, ngspice, and the matching SKY130A PDK, then:

```bash
python3 -m pip install -r requirements.txt
export PDK_ROOT=/path/to/the/directory/containing/sky130A
python3 tools/rebuild.py --pdk-root "$PDK_ROOT" --tt-support-tools /path/to/tt-support-tools
```

The recorded PDK is Open_PDKs
`0536d02d875c8f67dd7cca3902ac457e62f20005`. The provider precheck source is
`TinyTapeout/tt-support-tools` commit
`8f7b5060d7f6df73bfd2e0b8d8fa0fd1dca0a0b1`. See
`verification/tool_versions.json` for local tool versions.

For a headless Netgen installation, pass `--netgen-tcl /path/to/netgen.tcl`.
Add `--no-sim` to omit transient simulations. The spacing conversion script
records the one-time conversion from the previous core; the checked-in
editable layout already includes that conversion.

## GitHub and submission

The official `gds` workflow packages the GDS, LEF, Verilog, and project
metadata and runs Tiny Tapeout's hosted precheck. Review its result for the
exact commit being submitted. The optional viewer deploys from `main` only
when the repository variable `ENABLE_GDS_VIEWER` is set to `true`. Enable
GitHub Pages with GitHub Actions as its source before enabling that variable.
GDS packaging and precheck run regardless of the viewer setting.

After the submission revision is on `main` and its hosted checks pass, import
this repository at https://app.tinytapeout.com/projects/create and select the
SKY130 shuttle, 1x2 area, two analog pins, and 3.3 V analog supply support.
Confirm allocation and price in the app before placing the order. No shuttle
registration or payment is performed by these repository files.

The rebuild script performs nominal TT checks. The additional RC-PEX PVT and
local-mismatch characterization is recorded above and was performed separately.
Neither is complete shuttle or packaged-silicon signoff. Final acceptance
belongs to Tiny Tapeout's hosted flow.
