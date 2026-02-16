import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_PRIORITY, 6)
except:
    pass

sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)


def sendUDP(ip_addr, port, udp_bytes):
    '''
    Send udp packets to
    '''
    sock.sendto(udp_bytes, (ip_addr, port))
    socket.gethostbyname('')

def lightToBytes(lights, strips):
    '''
    takes in a Lights object and an array with indexes of strips, converts rgb values to sendable udp data
    '''
    leds = []
    for s in range(lights.num_strips):
        if s in strips:
            leds += lights.strips[s].rgb()

    udp_bytes = bytearray()

    udp_bytes.append(2) # DRGB
    udp_bytes.append(1) # leave realtime mode

    for i in range(len(leds)):
        # Bytes -> [...][Index, R, G, B][...]
        for val in leds[i]:
            udp_bytes.append(val)

    return udp_bytes