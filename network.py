import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_PRIORITY, 6)
except:
    pass

sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)


def updateLights(lights, udp_bytes):
    sock.sendto(udp_bytes, (lights.ip_addr, lights.port))
    socket.gethostbyname('')

def stripToBytes(leds):
    udp_bytes = bytearray()

    udp_bytes.append(2) # DRGB
    udp_bytes.append(10) # Don't leave realtime mode

    for i in range(len(leds)):
        # Bytes -> [...][Index, R, G, B][...]
        for val in leds[i]:
            udp_bytes.append(val)

    return udp_bytes