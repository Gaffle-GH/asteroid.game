import pygame
from core.circleshape import CircleShape
from constants import ENEMY_RADIUS, LINE_WIDTH, ENEMY_SHOOT_SPEED, ENEMY_SHOOT_COOLDOWN_SECONDS, SCREEN_WIDTH, SCREEN_HEIGHT
from player_info.shot import EnemyShot
from enemy.enemy_ship.COM_AI import COM_AI


class EnemyShip(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, ENEMY_RADIUS)
        self.rotation = 0
        self.shoot_cooldown_timer = ENEMY_SHOOT_COOLDOWN_SECONDS
        self.ai = COM_AI(self)

    def draw(self, screen):
        pygame.draw.polygon(screen, "red", self.triangle(), LINE_WIDTH)

    def triangle(self):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]

    def update(self, dt, player_position):
        if self.shoot_cooldown_timer > 0:
            self.shoot_cooldown_timer -= dt
        self.ai.update(dt, player_position)
        # Keep on screen
        self.position.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.position.x))
        self.position.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.position.y))

    def shoot(self, player_position):
        direction = player_position - self.position
        if direction.length() == 0:
            return None
        direction = direction.normalize()
        tip = self.position + direction * self.radius
        shot = EnemyShot(tip.x, tip.y)
        shot.velocity = direction * ENEMY_SHOOT_SPEED
        return shot
