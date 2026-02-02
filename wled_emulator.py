import socket
import pygame
import sys

# --- Configuration (Match these to your sender) ---
IP = "0.0.0.0"  # Listen on all interfaces
PORT = 21324     # Must match the PORT in your config.network
STRIP_LENGTH = 70
NUM_STRIPS = 3


class StripVisualizer:
    def __init__(self, width: int, height: int, lights_obj):
        pygame.init()
        self.width = width
        self.height = height
        self.lights_obj = lights_obj

        self.screen = pygame.display.set_mode((self.width * lights_obj.num_strips, self.height))
        pygame.display.set_caption("LED Strip Visualizer")

        self.num_segments = lights_obj.num_strips * lights_obj.strip_length
        self.seg_height = self.height / lights_obj.strip_length

    def update(self):
        """
        Redraws the screen by multiplying RGB values by the alpha fraction.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        self.screen.fill((0, 0, 0))  # Background for "off" pixels

        for i, strip in enumerate(self.lights_obj.strips):
            for j, (r, g, b, a) in enumerate(strip.strip):
                # Calculate alpha fraction (0.0 to 1.0)
                alpha_factor = a / 255.0

                # Apply alpha to colors
                display_color = (
                    int(r * alpha_factor),
                    int(g * alpha_factor),
                    int(b * alpha_factor)
                )

                # Render the segment
                rect = pygame.Rect(
                    i * self.width,  # x position of the strip
                    j * self.seg_height,  # y position of the segment
                    self.width,  # width of the strip
                    int(self.seg_height) + 1  # height of the segment
                )
                pygame.draw.rect(self.screen, display_color, rect)

        pygame.display.flip()

class RemoteLights:
    """A dummy container to hold LED data for the visualizer."""
    def __init__(self, strip_length, num_strips):
        self.strip_length = strip_length
        self.num_strips = num_strips
        # The visualizer expects strip.strip to be [[r, g, b, a], ...]
        self.strips = [RemoteStrip(strip_length) for _ in range(num_strips)]

class RemoteStrip:
    def __init__(self, length):
        self.strip = [[0, 0, 0, 255] for _ in range(length)]

def run_receiver():
    # 1. Setup Networking
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP, PORT))
    print(f"Listening for LED data on {IP}:{PORT}...")

    # 2. Setup Data and Visualizer
    lights_data = RemoteLights(STRIP_LENGTH, NUM_STRIPS)
    visualizer = StripVisualizer(width=50, height=800, lights_obj=lights_data)

    try:
        while True:
            # 3. Receive Packet
            data, addr = sock.recvfrom(4096) # Adjust buffer if strips are very long
            
            # 4. Parse Packet (Reverse of stripToBytes)
            # Index 0: Mode (DRGB = 2)
            # Index 1: Flags (Realtime = 10)
            # Index 2+: R, G, B, R, G, B...
            if len(data) > 2:
                payload = data[2:]
                
                # Flattened list of all pixels across all strips
                total_pixels = len(payload) // 3
                
                for p_idx in range(total_pixels):
                    # Determine which strip and which LED this belongs to
                    strip_idx = p_idx // STRIP_LENGTH
                    led_idx = p_idx % STRIP_LENGTH
                    
                    if strip_idx < NUM_STRIPS:
                        r = payload[p_idx * 3]
                        g = payload[p_idx * 3 + 1]
                        b = payload[p_idx * 3 + 2]
                        # Update the data object the visualizer is watching
                        # We keep Alpha at 255 because your sender only sends RGB
                        lights_data.strips[strip_idx].strip[led_idx] = [r, g, b, 255]

            # 5. Update Visualizer
            visualizer.update()

    except KeyboardInterrupt:
        print("\nClosing receiver...")
    finally:
        sock.close()
        pygame.quit()

if __name__ == "__main__":
    run_receiver()