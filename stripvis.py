import pygame
import sys

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