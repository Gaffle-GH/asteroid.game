import random
import pygame
from effects.particles import Particle


def spawn_ship_explosion(x, y):
    """Big multi-stage burst when the player ship is destroyed."""
    # Bright core flash
    for _ in range(18):
        angle = random.uniform(0, 360)
        speed = random.uniform(20, 90)
        vel = pygame.Vector2(0, 1).rotate(angle) * speed
        Particle(x, y, vel, radius=random.randint(3, 6), life=random.uniform(0.25, 0.55))

    # Fast debris shards
    for _ in range(28):
        angle = random.uniform(0, 360)
        speed = random.uniform(120, 380)
        vel = pygame.Vector2(0, 1).rotate(angle) * speed
        Particle(x, y, vel, radius=random.randint(2, 4), life=random.uniform(0.5, 1.1))

    # Slower smoke/embers
    for _ in range(16):
        angle = random.uniform(0, 360)
        speed = random.uniform(40, 140)
        vel = pygame.Vector2(0, 1).rotate(angle) * speed
        Particle(x, y, vel, radius=random.randint(4, 7), life=random.uniform(0.8, 1.6))
