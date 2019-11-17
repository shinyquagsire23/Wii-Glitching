#!/bin/bash
gcc -o ecccalc ecccalc.c
thumb-be wii-test.asm
openssl enc -e -aes-128-cbc -K 9258a75264960d82676f904456882a73 -iv 0 -nopad -in wii-test.bin  -out wii-test-enc.bin
./ecccalc wii-test-enc.bin test-payload.bin

# https://github.com/hjudges/NORway
#sudo python2 NANDway.py /dev/ttyACM0 0 write test-payload.bin 0 1
