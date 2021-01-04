#!/usr/bin/env python
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# See https://docs.pycom.io for more information regarding library specific
import utime
import pycom
import machine
from machine import Pin
import struct
import math
from network import Sigfox
from machine import ADC
import socket
import binascii
import time
from pysense import Pysense
# initialise Ultrasonic Sensor pins

py = Pysense()
echo = Pin('P11', mode=Pin.IN) # Lopy4 specific: Pin('P20', mode=Pin.IN)
trigger = Pin('P10', mode=Pin.OUT) # Lopy4 specific Pin('P21', mode=Pin.IN)
MF = Pin('P12', mode=Pin.OUT)

adc_bat = ADC()
p_bat = adc_bat.channel(pin='P16', attn=ADC.ATTN_11DB)
vol_bat = p_bat.voltage() * 2.067
print(vol_bat)
vol_batTrunc = math.trunc(vol_bat)

led = Pin(Pin.exp_board.G16, mode=Pin.OUT)

MF(1)

led(0)
trigger(0)
if pycom.wifi_on_boot() == True:
    pycom.wifi_on_boot(False)
# init Sigfox for RCZ1 (Europe)
sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
# create a Sigfox socket
s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
print('I am device ',  binascii.hexlify(sigfox.id()) )
# make the socket blocking
s.setblocking(True)
# configure it as uplink only
s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)
packet = 0
# Ultrasonic distance measurment
def distance_measure():
    # trigger pulse LOW for 2us (just in case)
    trigger(0)
    utime.sleep_us(2)
    # trigger HIGH for a 10us pulse
    trigger(1)
    utime.sleep_us(10)
    trigger(0)

    # wait for the rising edge of the echo then start timer
    while echo() == 0:
        pass
    start = utime.ticks_us()

    # wait for end of echo pulse then stop timer
    while echo() == 1:
        pass
    finish = utime.ticks_us()

    # pause for 20ms to prevent overlapping echos
    utime.sleep_ms(20)

    # calculate distance by using time difference between start and stop
    # speed of sound 340m/s or .034cm/us. Time * .034cm/us = Distance sound travelled there and back
    # divide by two for distance to object detected.
    distance = ((utime.ticks_diff(start, finish)) * .034)/2

    return distance

def distance_median():

    # initialise the list
    distance_samples = []
    sumDistance = 0
    # take 10 samples and append them into the list
    for count in range(10):
        distance_samples.append(int(distance_measure()))
        sumDistance += distance_samples[count]
    # sort the list
    distance_samples = sorted(distance_samples)
    distance_average = math.trunc(sumDistance/10)
    # take the center list row value (median average)
    distance_median = distance_samples[int(len(distance_samples)/2)]
    # apply the function to scale to volts

    print(distance_samples)
    packet = struct.pack('iii', distance_median,distance_average, vol_batTrunc)
    print(packet)
    s.send(packet)
    return int(distance_median)

print(distance_median())

MF(0)

    #s.send(sendPacket)
py.setup_sleep(720)
py.go_to_sleep(False)
