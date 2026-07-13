import pygame
from core.circleshape import CircleShape
from constants import PLAYER_RADIUS, LINE_WIDTH, PLAYER_TURN_SPEED, PLAYER_SPEED, PLAYER_SHOOT_SPEED, PLAYER_SHOOT_COOLDOWN_SECONDS, SHOOT_BAR_MAX, SHOOT_BAR_FILL_RATE, SHOOT_BAR_COOLDOWN_RATE, SHOOT_BAR_RECOVERY_FRACTION, SCREEN_WIDTH, SCREEN_HEIGHT
from player_info.shot import Shot
from effects.particles import Particle
from core.ui import draw_health_bar, draw_shoot_bar  # re-export for existing imports
import random

class Player(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_RADIUS)
        self.rotation = 0
        self.shoot_timer = 0
        self.health = 100
        self.target_health = 100
        self.health_bar_width = 200
        self.lerp_speed = 5
        self.health = 100
        self.target_health = 100
        self.lerp_speed = 5.0
        # shooting heat meter
        self.heat = 0.0
        self.overheated = False

    def draw(self, screen):
        pygame.draw.polygon(screen, "white", self.triangle(), LINE_WIDTH)

    def update(self, dt):
        # Slowly move health toward target_health
        if self.health > self.target_health:
            self.health -= self.lerp_speed * dt * 20
        elif self.health < self.target_health:
            self.health = self.target_health
        
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.rotate(-dt)
        if keys[pygame.K_d]:
            self.rotate(dt)
        if keys[pygame.K_w]:
            self.move(dt)
        if keys[pygame.K_s]:
            self.move(-dt)
        # Shooting and heat management
        firing = keys[pygame.K_SPACE]
        if firing and not self.overheated:
            # attempt to fire (shoot() will respect shoot_timer)
            self.shoot()
            # increase heat while the fire button is held
            self.heat += SHOOT_BAR_FILL_RATE * dt
            if self.heat >= SHOOT_BAR_MAX:
                self.heat = SHOOT_BAR_MAX
                self.overheated = True
        else:
            # cool down when not firing or when overheated
            self.heat -= SHOOT_BAR_COOLDOWN_RATE * dt
            if self.heat <= 0:
                self.heat = 0.0

        # recover from overheat when below recovery threshold
        if self.overheated and self.heat <= (SHOOT_BAR_MAX * SHOOT_BAR_RECOVERY_FRACTION):
            self.overheated = False

        self.shoot_timer -= dt

        if self.health < self.target_health:
            self.health -= self.lerp_speed * dt * 20
        elif self.health < self.target_health:
            self.health = self.target_health

    def triangle(self):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]

    def rotate(self, dt):
        self.rotation += PLAYER_TURN_SPEED * dt

    def move(self, dt):
        direction = pygame.Vector2(0, 1).rotate(self.rotation)
        self.position += direction * PLAYER_SPEED * dt
        # Clamp position to screen bounds
        self.position.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.position.x))
        self.position.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.position.y))
        # spawn small thruster particles behind ship when moving forward
        if dt > 0:
            # rear position slightly behind the hull
            rear = self.position - direction * (self.radius * 1.1)
            # spawn a couple small particles with inverse velocity + random spread
            for _ in range(2):
                angle = random.uniform(-20, 20) + self.rotation + 180
                speed = random.uniform(20, 80)
                vel = pygame.Vector2(0, 1).rotate(angle) * (speed + PLAYER_SPEED * 0.2)
                Particle(rear.x, rear.y, vel, radius=2, life=0.4, on_screen=False)

    def shoot(self):
        if self.shoot_timer > 0:
            return
        self.shoot_timer = PLAYER_SHOOT_COOLDOWN_SECONDS
        # spawn shot at triangle tip
        tip = pygame.Vector2(self.triangle()[0])
        shot = Shot(tip.x, tip.y)
        direction = pygame.Vector2(0, 1).rotate(self.rotation)
        shot.velocity = direction * PLAYER_SHOOT_SPEED
        return shot