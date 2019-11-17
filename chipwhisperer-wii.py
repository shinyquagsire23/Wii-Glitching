import chipwhisperer as cw
import holoviews as hv
import numpy as np
import time
import logging
from binascii import hexlify
from collections import namedtuple
from chipwhisperer.common.api.settings import Settings
import matplotlib.pyplot as plt
import threading

capture_thread = None
Range = namedtuple('Range', ['min', 'max', 'step'])

hv.extension('bokeh')

SCOPETYPE = 'OPENADC'
PLATFORM = 'CWLITEARM'

Settings().setValue("cwlite-fpga-bitstream-mode", "zipfile") # `debug` for bitstream
Settings().setValue("cwlite-zipbitstream-location", "/home/maxamillion/workspace/chipwhisperer/hardware/capture/chipwhisperer-lite/cwlite_firmware.zip")
Settings().setValue("cwlite-debugbitstream-location", "/home/maxamillion/workspace/chipwhisperer/hardware/capture/chipwhisperer-lite/hdl/cwlite_ise/cwlite_interface.bit")
logging.basicConfig(filename='chipwhisperer-wii.log',level=logging.DEBUG)

# Helper functions
def glitch_on(scope):
    scope.io.glitch_lp = False
    scope.io.glitch_hp = True

def glitch_off(scope):
    scope.io.glitch_hp = False
    scope.io.glitch_lp = False
    
def wii_reset_hold(scope):
    scope.io.nrst = "low"

def wii_reset_release(scope):
    scope.io.nrst = "high_z"

def wii_reset(scope):
    wii_reset_hold(scope)
    time.sleep(0.1)
    wii_reset_release(scope)

last_error = 0x8F
def check_fail(scope):
    global last_error
    time.sleep(0.01)
   
    #pin_check = ['tio1', 'tio2', 'tio3', 'tio4', 'tio5', 'tio6', 'tio8'] # , , 'tio7', 'tio8'
    pin_check = ['tio8', 'tio3', 'tio4']
    val = 0
    for pin in pin_check:
        scope.trigger.triggers = pin

        failed_glitch = True
        for i in range(0, 25):
            time.sleep(0.002)
            #print (pin, scope.adc.state)
            if (scope.adc.state == True):
                bit = (int(pin[-1:]) - 1)
                val |= 1 << bit
                break
        scope.trigger.triggers = PINS_FF

    print ("Output value", hex(val))

    last_error = val
    scope.trigger.triggers = PINS_TRIGGER
    return not(val == 0x88 or val == 0xA or val == 0x0)

def update_plot_thread(data):
    for point in data:
        if (point > 0.4):
            return
    
    h2.set_ydata(data)
    fig.canvas.restore_region(ax2background)
    ax2.draw_artist(h2)
    ax2.draw_artist(text)
    fig.canvas.blit(ax2.bbox)
    fig.canvas.flush_events()

def update_plot(data):
    thread = threading.Thread(target=update_plot_thread, args=(data,))
    thread.start()

# Wii stuff
PINS_Fx = "tio5 and tio6 and tio7 and tio8"
PINS_FF = "tio1 and tio2 and tio3 and tio4 and tio5 and tio6 and tio7 and tio8" #FF
PINS_88 = "tio8 and tio4" #88
PINS_8F = "tio1 and tio2 and tio3 and tio4 and tio8" #8F
PINS_2F = "tio1 and tio2 and tio3 and tio4 and tio6"
PINS_7F = "tio1 and tio2 and tio3 and tio4 and tio5 and tio6 and tio7"
PINS_NRST = "tio7"
PINS_TRIGGER = PINS_NRST
PINS_TRIGGER_MODE = "rising_edge"

# 0.39*6 is powerful?
#width_range = Range(-40, 40, 0.39)
#offset_range = Range(10, 39+0.39, 0.39*5)
width_range = Range(0.39, 0.39*2, 0.39) #-10.9375+0.39
offset_range = Range(10, 10+0.39, 0.39*5)
ext_offset_range = Range(13, 20, 1) # 166000 - 168300 is ~30pages, 20000 is ~2 pages, 10000 is ~1. 13-20 is consistent, 3280, 4768, 4827? 221000 idk, 303000 might be 9, 1210000 is about 42, 1240000 is too far? 1240000, 1240000+30000
repeat_range = Range(1, 15, 1)

# Set up scope
scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
target.baud = 115200
scope.default_setup()

# Glitch triggering init
scope.glitch.clk_src = "clkgen"
scope.glitch.output = "glitch_only"
scope.glitch.trigger_src = "ext_single"
    
scope.glitch.width = width_range.min
scope.glitch.offset = offset_range.min
scope.glitch.repeat = repeat_range.min
scope.glitch.ext_offset = ext_offset_range.min
scope.glitch.width_fine = -20
scope.glitch.arm_timing = "before_scope"

# Clock settings
scope.clock.clkgen_freq = 27000000

# Trigger config
scope.trigger.triggers = PINS_TRIGGER
scope.adc.basic_mode = PINS_TRIGGER_MODE

# ADC capture config
scope.adc.decimate = 100#65535
scope.adc.presamples = 0
scope.adc.samples = 16000
scope.adc.timeout = 0.1
scope.gain.gain = 40
#scope.clock.reset_adc()

# Make sure IO is all high_z
scope.io.tio1 = "high_z"
scope.io.tio2 = "high_z"
scope.io.nrst = "high_z"

print("Scope output:\n", scope)
#print(scope.glitch)
#print(scope.clock)

# Prepare for glitching, hold Wii in reset but keep glitching off
glitch_off(scope)
wii_reset_hold(scope)

print("Glitching start.")

trace_no = 0

glitch_on(scope)

# Set up graph
subsample = 1
trace = [0] * int(scope.adc.samples/subsample)
trace_x = range(0, len(trace))

fig = plt.figure(figsize=(20, 4))
ax2 = fig.add_subplot(1, 1, 1)

fig.canvas.draw()   # note that the first draw comes before setting data 

h2, = ax2.plot(trace_x, linewidth=0.3)
text = ax2.text(0, 0.6, "")
ax2.set_ylim([-1,1])

ax2background = fig.canvas.copy_from_bbox(ax2.bbox)
plt.pause(1e-10)

trace = None
done = False
scope.glitch.ext_offset = ext_offset_range.min
while scope.glitch.ext_offset < ext_offset_range.max:

    scope.glitch.offset = offset_range.min
    while scope.glitch.offset < offset_range.max:

        scope.glitch.width = width_range.min
        while scope.glitch.width < width_range.max:
        
            scope.glitch.repeat = repeat_range.min
            while scope.glitch.repeat < repeat_range.max:
                print (scope.adc.trig_count, scope.glitch.repeat, scope.glitch.width, scope.glitch.offset, scope.glitch.ext_offset)
                
                # begin glitching and pull Wii out of reset
                
                glitch_on(scope)
                
                scope.arm()
                wii_reset_release(scope)
                print("Wait capture...")
                scope.capture()
                print ("done.")

                #glitch_off(scope)
                
                glitch_off(scope)
                failed_glitch = check_fail(scope)
                
                wii_shut_off = False
                last_trace = scope.get_last_trace()
                for val in last_trace:
                    if (val > 0.05):
                        wii_shut_off = False

                if (wii_shut_off):
                    done = True
                    break

                if (trace is not None):
                    trace = np.concatenate([trace, ([0] * 1500)], axis=0)
                    trace = last_trace#np.concatenate([trace, last_trace], axis=0)
                else:
                    trace = last_trace

                newtext = "repeat: " + str(scope.glitch.repeat) + ", width: " + str(scope.glitch.width) + ", offset: " + str(scope.glitch.offset) + ", ext_offset: " + str(scope.glitch.ext_offset) + ", error: " + hex(last_error)
                text.set_text(newtext)

                # Display trace
                if (True):
                    update_plot(trace[::subsample])
                
                '''trace_str = ""
                for val in trace:
                    trace_str += str(val) + "\n"
                open("trace" + str(trace_no) + ".txt", "w").write(trace_str)'''
                trace_no += 1
            
                if (not failed_glitch):
                    print ("!!! fail status:", failed_glitch)
                    done = True
                    break

                scope.glitch.repeat += repeat_range.step
                if (done):
                    break
                wii_reset_hold(scope)
                #time.sleep(2)
            
            scope.glitch.width += width_range.step
            if (done):
                break

        scope.glitch.offset += offset_range.step
        if (done):
            break

    scope.glitch.ext_offset += ext_offset_range.step
    if (scope.glitch.ext_offset >= ext_offset_range.max):
        scope.glitch.ext_offset = ext_offset_range.min
    if (done):
        break

print ("Glitching stop.")

time.sleep(5)
glitch_off(scope)

scope.dis()
target.dis()

plt.show()
