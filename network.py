import socket
import time
import aiohttp

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

async def triggerLED(message_str, ip):
    ip_url = f"http://{ip}/json/state"
    message = eval(message_str)
    if message == "":
        print("No function")
        return False
    
    # Defaults -----

    message["transition"] = 1

    if "seg" in message and type(message["seg"]) is dict:
            message["seg"] = [message["seg"]]
            if "bri" not in message:
                message["bri"] = 255

    if "seg" in message:
        for item in message["seg"]:
            if "fx" in item and item["fx"] != 0 and not "sx" in item:
                item["sx"] = 80

    if "seg" in message:
        if len(message["seg"]) == 1 and not "id" in message["seg"][0]:
            newMessage = []
            message["seg"] = message["seg"][0]
            newMessage.insert(0, {"id":2, "start":160, "stop":240, "on":True} | message["seg"])
            newMessage.insert(0, {"id":1, "start":80, "stop":160, "on":True} | message["seg"])
            newMessage.insert(0, {"id":0, "start":0, "stop":80, "on":True} | message["seg"])
            message["seg"] = newMessage
        elif len(message["seg"]) == 1 and "id" in message["seg"][0]:
            newMessage = []
            newMessage.append({"id":2, "start": 10, "stop":0})
            newMessage.append({"id":1, "start": 10, "stop":0})
            newMessage.append({"id":0, "start": 10, "stop":0})
            newMessage.append(message["seg"][0])
            message["seg"] = newMessage
    # --------------

    print(message)
        
    print("Sending WLED request...")
    headers = {'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(ip_url, headers=headers, data=json.dumps(message)) as response:
                if response.status == 200:
                    print("Device triggered successfully.")
                    return True
                else:
                    text = await response.text()
                    print(f"Failed to trigger on device. Status code: {response.status}, Response: {text}")
                    return False
        except Exception as e:
            print(f"<! Error during request !>")
            return False