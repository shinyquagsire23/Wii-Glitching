.arm

start:
@ GPIO fixing
ldr r4, =0xD8000DC
ldr r2, =0x00FF0000
str r2, [r4]

ldr r4, =0xD8000E4
str r2, [r4]

ldr r0, =1000000

wait_loop:
sub r0, r0, #0x1
cmp r0, #0x0
bne wait_loop

@ OTP eFuses
mov r5, #0x0
MOV     R3, #0xD800000
MOV     R6, #0x80000000
and r4, r5, #0x1F
orr r4, r4, r6
str r4, [r3, #0x1EC]
str r4, [r3, #0x1EC]
str r4, [r3, #0x1EC]
str r4, [r3, #0x1EC]
ldr r4, [r3, #0x1F0]

@ panic
ldr r3, =0xFFFF00A4
lsr r4, r4, #0
and r0, r4, #0xFF
@mov r0, #0xFF
bx r3




@ old stuff

ldr r0, =1000000
bl delay

mov r0, #0xFF
bl debug_port_out

ldr r0, =1000000
bl delay

mov r0, #0x00
bl debug_port_out

mov r5, #0x0
b loop

.align 4
.pool


loop:
MOV     R3, #0xD800000
MOV     R6, #0x80000000
and r4, r5, #0x1F
orr r4, r4, r6
str r4, [r3, #0x1EC]
ldr r4, [r3, #0x1F0]



mov r0, #0x00
bl debug_port_out

ldr r0, =1000000
bl delay

and r0, r4, #0xFF
bl debug_port_out

ldr r0, =1000000
bl delay



lsr r4, r4, #0x8
mov r0, #0x00
bl debug_port_out

ldr r0, =1000000
bl delay

and r0, r4, #0xFF
bl debug_port_out

ldr r0, =1000000
bl delay



lsr r4, r4, #0x8
mov r0, #0x00
bl debug_port_out

ldr r0, =1000000
bl delay

and r0, r4, #0xFF
bl debug_port_out

ldr r0, =1000000
bl delay



lsr r4, r4, #0x8
mov r0, #0x00
bl debug_port_out

ldr r0, =1000000
bl delay

and r0, r4, #0xFF
bl debug_port_out

ldr r0, =1000000
bl delay


add r5, r5, #0x1
b loop

.pool


debug_port_out:
ldr r3, =0xFFFF0084
bx r3

delay:
ldr r3, =0xFFFF0588
bx r3

.pool
