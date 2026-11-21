# RC-PEX operating-range characterization

Date: 21 November 2026.

Source design: [commit 007af30](https://github.com/Ahmed-Reda-SILO/tt_um_armohamed_r2rvc/tree/007af305f79430bfe27b4513410a53def5a6e022).
The submission documentation was subsequently updated; the GDS, LEF, Verilog,
schematics, extracted netlists, and physical verification results are unchanged.

## Result and declared scope

All nine common-mode points from 0.3 to 2.4 V in the tested grid pass every
one of the 335 principal runs. This supports a limited, experimental operating
specification under the conditions below. It does not establish performance
between grid points, the exact lower/upper common-mode boundaries, an
unrestricted 0-3.3 V rail-to-rail range, or manufacturing yield.

At VCM = 2.7 V, 311/335 runs meet the nominal 250 ns settling criterion
and 320/335 meet late-phase logic. A lower comparison frequency is not a
general remedy: standalone SF / 2.97 V / 1.62 V / 125 C diagnostics pass at
2.7 V but still fail at 2.8 V at 100 kHz.

## Coverage and stimulus

- 135 PVT combinations: TT/FF/SS/SF/FS; VAPWR = 2.97/3.30/3.63 V;
  independent VDPWR = 1.62/1.80/1.98 V; temperature = -40/27/125 C.
- 100 local-mismatch samples at TT, 3.3 V analog, 1.8 V digital, 27 C;
  seeds 314159-314258.
- 20 paired local-mismatch seeds per process corner, at 2.97 V analog,
  1.62 V digital, 125 C; seeds 8675309-8675328. These were selected
  to stress the first point beyond the deterministic passing prefix.
  The paired runs are not 100 independent global-process samples.
- Fixed common mode with VINP/VINM complementary +/-10 mV drive;
  VINP - VINM = +/-20 mV, 1 ns input edges, two 1 MHz cycles per point,
  and a 1 pF internal output load.
- Supplies and initial inputs ramp from zero in 10 ns; transient UIC is used.
  Points are tested in ascending order with a prescribed settling history.

There are 4,545 legal common-mode profiles and 145 out-of-rail requests.
The latter were not applied: VCM = 3.0 V with +/-10 mV per input exceeds
the 2.97 V analog rail.

## Acceptance and exact counts

LOW must be below 0.1 VDPWR and HIGH above 0.9 VDPWR at every one of
21 equally spaced samples in each nominal 250-450 ns window, and every
expected transition must occur. Fixed windows begin about 248.5-250 ns
after the actual differential-zero crossing. The nominal 250 ns target
is a declared validation criterion, not a previously guaranteed specification.

Late-phase logic uses the same voltage thresholds 490 ns into each phase
and requires the expected output transitions. Missing transitions are
failures with no numerical delay value.

| VCM (V) | Nominal 250 ns pass / legal | Late-phase pass / legal | Out-of-rail requests |
|---|---:|---:|---:|
| 0.3 | 335/335 | 335/335 | 0 |
| 0.6 | 335/335 | 335/335 | 0 |
| 0.9 | 335/335 | 335/335 | 0 |
| 1.2 | 335/335 | 335/335 | 0 |
| 1.5 | 335/335 | 335/335 | 0 |
| 1.65 | 335/335 | 335/335 | 0 |
| 1.8 | 335/335 | 335/335 | 0 |
| 2.1 | 335/335 | 335/335 | 0 |
| 2.4 | 335/335 | 335/335 | 0 |
| 2.7 | 311/335 | 320/335 | 0 |
| 2.8 | 290/335 | 301/335 | 0 |
| 2.9 | 262/335 | 284/335 | 0 |
| 2.95 | 249/335 | 270/335 | 0 |
| 3 | 184/190 | 188/190 | 145 |

The exact per-group counts, output extrema, delay extrema, and diagnostics
are in [operating_range_summary.json](operating_range_summary.json).
Within the common passing grid, individual edge delays range from
16.87 to 195.30 ns.
Worst sampled LOW is 0.279 mV.
Worst sampled HIGH is 0.999996
times each case's digital supply. Internal HIGH is approximately 1.8 V at
nominal VDPWR; external pad/board levels were not simulated.

Five full-sequence reruns with 1 ns maximum step preserve every pass/fail
classification. The largest mean-delay difference is 1.518 ns. An evidence
audit checks actual input amplitudes, common mode, frequency, native model
hashes, and exactly the expected 50%-level output crossings in the common
passing grid.

## Models and limits

Simulator: ngspice 44.2, KLU. PDK revision:
`0536d02d875c8f67dd7cca3902ac457e62f20005`.
RC-netlist SHA-256:
`c873334a4f1300295571123bb649108d62059a134f5c799650137e11b9d59f18`.

Device process and temperature models vary; extracted interconnect R/C stays
fixed. Native tt_mm/ff_mm/ss_mm/sf_mm/fs_mm sections provide local mismatch.
Global-process statistical MC is excluded: the installed MC model did not
provide a valid bin for an instantiated PMOS, and the alternative continuous
model did not elaborate. No global-process MC or silicon-yield claim is made.

No extraction-corner re-extraction, metal-R temperature-coefficient sweep,
DC offset distribution, noise/metastability qualification, arbitrary startup
or slew/load qualification, shared chip power-grid, package, board, or
external analog-selection-switch model is included.

This is a recorded summary of separate characterization. The repository's
`tools/run_simulations.py` performs the original nominal comparison and does
not reproduce this additional 335-run sweep.
