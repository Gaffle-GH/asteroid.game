import pygame
import random
from circleshape import CircleShape
from constants import LINE_WIDTH
from particles import Particle

class Bomb(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, 15)
        self.lifetime = 3.0  # seconds before exploding
        self.explode_radius = 100
        self.exploded = False

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0 and not self.exploded:
            self.explode()
            self.exploded = True

    def draw(self, screen):
        # Flicker by alternating visibility
        if int(self.lifetime * 10) % 2 == 0:
            pygame.draw.circle(screen, "red", self.position, self.radius, LINE_WIDTH)

    def explode(self):
        # This will be called from main loop with access to asteroids
        pass