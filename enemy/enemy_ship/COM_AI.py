import pygame
from constants import ENEMY_SPEED, ENEMY_SHOOT_COOLDOWN_SECONDS


class COM_AI:
    def __init__(self, ship):
        self.ship = ship

    def update(self, dt, player_position):
        self._move_toward(dt, player_position)
        self._face_player(player_position)
        self._try_shoot(player_position)

    def _move_toward(self, dt, player_position):
        direction = player_position - self.ship.position
        if direction.length() == 0:
            return
        direction = direction.normalize()
        self.ship.position += direction * ENEMY_SPEED * dt

    def _face_player(self, player_position):
        direction = player_position - self.ship.position
        if direction.length() == 0:
            return
        # pygame Vector2.angle_to: angle from (0,1) is awkward; store rotation like player
        self.ship.rotation = pygame.Vector2(0, 1).angle_to(direction)

    def _try_shoot(self, player_position):
        if self.ship.shoot_cooldown_timer > 0:
            return
        self.ship.shoot(player_position)
        self.ship.shoot_cooldown_timer = ENEMY_SHOOT_COOLDOWN_SECONDS
