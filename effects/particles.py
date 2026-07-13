import pygame
from core.circleshape import CircleShape
from constants import LINE_WIDTH


class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, velocity, radius=3, life=1.0, on_screen=True):
        # follow same containers pattern as other sprites so instances auto-register
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(velocity)
        self.radius = radius
        self.life = life
        self.on_screen = on_screen
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        if self.age >= self.life:
            self.kill()
            return
        self.position += self.velocity * dt

    def draw(self, surface):
        # draw with fading alpha based on remaining life
        t = max(0.0, 1.0 - (self.age / self.life))
        alpha = int(255 * t)
        d = int(self.radius * 2)
        surf = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255, alpha), (self.radius, self.radius), self.radius)
        surface.blit(surf, (self.position.x - self.radius, self.position.y - self.radius))
