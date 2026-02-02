import socket
from config.network import *

strip = [[120, 120, 120] for i in range(255)]

def updateLights(udp_bytes):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(udp_bytes, (IP, PORT))

def stripToBytes(leds):
    udp_bytes = bytearray()

    udp_bytes.append(2) # DRGB
    udp_bytes.append(10) # Don't leave realtime mode

    for i in range(len(leds)):
        # Bytes -> [...][Index, R, G, B][...]
        for val in leds[i]:
            udp_bytes.append(val)

    return udp_bytes