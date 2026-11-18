## How it works

EF_R2RVC is a rail-to-rail voltage comparator in SKY130A. Its analog circuitry
uses VAPWR = 3.3 V, and its level shifter produces a VDPWR = 1.8 V logic
output. The design occupies the 1x2 Tiny Tapeout analog template with two
analog inputs. It does not require a clock.

The output is high when VINP exceeds VINM and low when VINP is below VINM.
Near equal inputs, the output is sensitive to offset, noise, and settling.
The current revision retains the bias resistor's VDD-biased well and describes
that body connection explicitly in the schematic.

| Interface | Function |
|---|---|
| ua[0] | VINP, noninverting analog input |
| ua[1] | VINM, inverting analog input |
| uo[0] | Comparator logic output |
| VAPWR | 3.3 V analog supply |
| VDPWR | 1.8 V digital supply |
| VGND | Common ground |

The other dedicated outputs, bidirectional outputs, and output enables are
physically tied to ground. The bidirectional pins are never driven.

## How to test

1. Select the project and enable the board's 3.3 V analog supply.
2. Connect a common ground between the board and the signal generator.
3. Apply VINM = 1.65 V to ua[1].
4. Apply a low-frequency waveform around 1.65 V to ua[0]. A useful initial
   test is 1.55–1.75 V at 10 kHz.
5. Observe uo[0] on an oscilloscope or logic analyzer. It should follow the
   comparator polarity above.
6. Sweep VINP slowly through VINM to observe the transition.

Keep analog inputs within 0–3.3 V. Pin loading, the analog selection switches,
board wiring, and measurement equipment affect measured behavior. The local
post-layout test uses TT models at 27 °C with a 1 pF output load. It is not a
measurement of packaged silicon or an input-offset qualification.

## External hardware

A dual-channel voltage source or waveform generator, oscilloscope or logic
analyzer, and the Tiny Tapeout board's analog breakout connections.
