import random
from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    ASTEROID_MIN_RADIUS,
    ASTEROID_KINDS,
    ENEMY_RADIUS,
    WAVE_ANNOUNCE_SECONDS,
    WAVE_BASE_ASTEROIDS,
    WAVE_ASTEROIDS_PER_LEVEL,
    WAVE_BASE_SPAWN_INTERVAL,
    WAVE_MIN_SPAWN_INTERVAL,
    WAVE_SHIP_UNLOCK,
    WAVE_BASE_SHIPS,
    WAVE_SHIPS_PER_LEVEL,
)
from enemy.enemy_ship.enemy_ships import EnemyShip


class WaveManager:
    def __init__(self):
        self.wave = 1
        self.state = "announce"  # announce -> spawning -> clearing
        self.announce_timer = WAVE_ANNOUNCE_SECONDS
        self.spawn_timer = 0.0
        self.asteroids_to_spawn = 0
        self.ships_to_spawn = 0
        self._begin_wave(1)

    def reset(self):
        self._begin_wave(1)

    def _begin_wave(self, wave):
        self.wave = wave
        self.state = "announce"
        self.announce_timer = WAVE_ANNOUNCE_SECONDS
        self.spawn_timer = 0.0
        self.asteroids_to_spawn = WAVE_BASE_ASTEROIDS + (wave - 1) * WAVE_ASTEROIDS_PER_LEVEL
        if wave >= WAVE_SHIP_UNLOCK:
            levels_with_ships = wave - WAVE_SHIP_UNLOCK + 1
            self.ships_to_spawn = WAVE_BASE_SHIPS + (levels_with_ships - 1) * WAVE_SHIPS_PER_LEVEL
        else:
            self.ships_to_spawn = 0

    def spawn_interval(self):
        # Faster spawns as waves increase
        interval = WAVE_BASE_SPAWN_INTERVAL - (self.wave - 1) * 0.05
        return max(WAVE_MIN_SPAWN_INTERVAL, interval)

    def asteroid_speed_range(self):
        base_min = 40 + (self.wave - 1) * 8
        base_max = 100 + (self.wave - 1) * 12
        return base_min, base_max

    def enemies_on_field(self, asteroids, enemy_ships):
        return len(asteroids) + len(enemy_ships)

    def remaining_to_spawn(self):
        return self.asteroids_to_spawn + self.ships_to_spawn

    def update(self, dt, asteroid_field, asteroids, enemy_ships):
        if self.state == "announce":
            self.announce_timer -= dt
            if self.announce_timer <= 0:
                self.state = "spawning"
            return

        if self.state == "spawning":
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval():
                self.spawn_timer = 0.0
                self._spawn_next(asteroid_field)
            if self.remaining_to_spawn() == 0:
                self.state = "clearing"
            return

        if self.state == "clearing":
            if self.enemies_on_field(asteroids, enemy_ships) == 0:
                self._begin_wave(self.wave + 1)

    def _spawn_next(self, asteroid_field):
        # Prefer asteroids early; mix in ships when both remain
        spawn_ship = False
        if self.ships_to_spawn > 0 and self.asteroids_to_spawn > 0:
            # Weight ships slightly lower so asteroids lead the wave
            spawn_ship = random.random() < 0.35
        elif self.ships_to_spawn > 0:
            spawn_ship = True

        if spawn_ship:
            self._spawn_enemy_ship()
            self.ships_to_spawn -= 1
        elif self.asteroids_to_spawn > 0:
            self._spawn_asteroid(asteroid_field)
            self.asteroids_to_spawn -= 1

    def _spawn_asteroid(self, asteroid_field):
        edge = random.choice(asteroid_field.edges)
        speed_min, speed_max = self.asteroid_speed_range()
        speed = random.randint(int(speed_min), int(speed_max))
        velocity = edge[0] * speed
        velocity = velocity.rotate(random.randint(-30, 30))
        position = edge[1](random.uniform(0, 1))
        kind = random.randint(1, ASTEROID_KINDS)
        asteroid_field.spawn(ASTEROID_MIN_RADIUS * kind, position, velocity)

    def _spawn_enemy_ship(self):
        edge = random.choice(("left", "right", "top", "bottom"))
        if edge == "left":
            x, y = -ENEMY_RADIUS, random.uniform(0, SCREEN_HEIGHT)
        elif edge == "right":
            x, y = SCREEN_WIDTH + ENEMY_RADIUS, random.uniform(0, SCREEN_HEIGHT)
        elif edge == "top":
            x, y = random.uniform(0, SCREEN_WIDTH), -ENEMY_RADIUS
        else:
            x, y = random.uniform(0, SCREEN_WIDTH), SCREEN_HEIGHT + ENEMY_RADIUS
        EnemyShip(x, y)
