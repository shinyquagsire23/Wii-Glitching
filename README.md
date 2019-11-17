# Wii-Glitching

This repository is more or less a dumping ground for some of my Wii Mini (and future?) glitching scripts for Chipwhisperer/CWLite.

## Contents

- thumb-be: Helper script for compiling wii-test.asm
- wii-test.asm: boot1 code to be run
- wii-compile.sh: Compiles wii-test.asm, boot1-crypts it and flashes it to NAND
- chipwhisperer-wii.py: CWLite script for executing the power glitch. Bit messy atm.

## Wii Mini boot1 code exec setup

Install https://github.com/shinyquagsire23/chipwhisperer/tree/wii-gpio. Technically this is not strictly required, but it makes fuzzing for specific errors easier. It remaps PD -> IO5, PC -> IO6, SCK -> IO7 and MOSI -> IO8.

The Wii Mini outputs status codes to eight GPIO during boot0. This is used to determine glitching success.

```
TP221 - IO1
TP222 - IO2
TP223 - IO3
TP224 - IO4
TP225 - IO5
TP226 - IO6
TP219 - IO7
TP220 - disconnected
```

TP119 (Hollywood reset) should be connected to both nRST and IO8. This allows the CWLite to trigger on the reset being deasserted by itself when nRST is set to high-z.

NAND writing can be done using https://github.com/hjudges/NORway and a Teensy++ 2.0. I used the signal booster configuration (with A0-7, B0-7, C0-7, D0-7 bridged together) and an on-board 3.3v regulator. To get the Wii Mini to fail in boot0, D7 can be pulled to ground for one boot, then use NANDway to write the payload. Writing is generally successful as-is, however I found that reading requires pull-down resistors on all of the NAND D0-7 IO since Hollywood is still on the same lines as the Teensy even while error-looping. I used values 120ohm, 100ohm, and 82ohm because it's what I had lying around and it pushed some voltage spikes that appeared on the 0 bit below the 1.5v threshold.

To isolate the 1.0v line for glitching, cut the PCB trace between L1 and D6. Then solder three wires to the 2x3 set of vias on the other side of L1 for the CWLite glitch+ADC SMA and external power feed-in. Use a DMM to measure if you are uncertain. Additionally, tie the collector pin (facing C246) of Q22 to ground to disable the associated PGOOD signal from on-board regulators.

With everything set up, run `chipwhisperer-wii.py` and it should successfully glitch into the provided boot1 payload. The current configuration leaves the eFuses unreadable.
