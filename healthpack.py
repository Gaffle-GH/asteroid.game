import pygame
from circleshape import CircleShape
from constants import LINE_WIDTH

class HealthPack(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, 10)
        self.lifetime = 5.0  # seconds before disappearing

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()

    def draw(self, screen):
        # Draw + sign
        half = self.radius
        pygame.draw.line(screen, "green", (self.position.x - half, self.position.y), (self.position.x + half, self.position.y), LINE_WIDTH)
        pygame.draw.line(screen, "green", (self.position.x, self.position.y - half), (self.position.x, self.position.y + half), LINE_WIDTH)