from circleshape import CircleShape
from constants import SHOT_RADIUS, PLAYER_SHOOT_SPEED, LINE_WIDTH
import pygame

class Shot(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, SHOT_RADIUS)

    def draw(self, screen):
        pygame.draw.circle(screen, "white", self.position, self.radius, LINE_WIDTH)

    def update(self, dt):
        self.position += self.velocity * dt
        self.position += self.velocity * dt