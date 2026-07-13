import pygame
from constants import (
    PLAYER_TURN_SPEED,
    SHOOT_BAR_MAX,
    SHOOT_BAR_COOLDOWN_RATE,
    PLAYER_SHOOT_SPEED,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


def _angle_diff(a, b):
    return (a - b + 180) % 360 - 180


def _pick_target(player, asteroids, enemy_ships):
    """Prefer close threats; enemy ships slightly weighted over rocks."""
    candidates = []
    for a in asteroids:
        dist = player.position.distance_to(a.position)
        candidates.append((dist - 40, a.position, a))  # closer bias
    for e in enemy_ships:
        dist = player.position.distance_to(e.position)
        candidates.append((dist - 80, e.position, e))  # prioritize ships
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    return candidates[0][1]


def update_demo_pilot(player, dt, asteroids, enemy_ships=None):
    """Fluid menu-background AI: aim, strafe, dodge, and keep firing."""
    enemy_ships = enemy_ships or []

    if player.shoot_timer > 0:
        player.shoot_timer -= dt

    # Cool heat quickly so the demo keeps shooting
    player.heat -= SHOOT_BAR_COOLDOWN_RATE * 2.5 * dt
    if player.heat < 0:
        player.heat = 0.0
    if player.overheated and player.heat <= SHOOT_BAR_MAX * 0.35:
        player.overheated = False

    # Dodge anything about to hit
    dodge = pygame.Vector2(0, 0)
    for threat in list(asteroids) + list(enemy_ships):
        offset = player.position - threat.position
        dist = offset.length()
        danger = getattr(threat, "radius", 18) + player.radius + 50
        if 0 < dist < danger:
            dodge += offset.normalize() * ((danger - dist) / danger)

    target_pos = _pick_target(player, asteroids, enemy_ships)

    if target_pos is None and dodge.length_squared() == 0:
        # Idle orbit near center
        to_center = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2) - player.position
        desired = pygame.Vector2(0, 1).angle_to(to_center) if to_center.length_squared() else player.rotation
        diff = _angle_diff(desired, player.rotation)
        player.rotation += max(-PLAYER_TURN_SPEED * dt, min(PLAYER_TURN_SPEED * dt, diff))
        player.move(dt * 0.4)
        return

    aim_point = target_pos if target_pos is not None else player.position + pygame.Vector2(0, 1).rotate(player.rotation)

    # Lead the target a bit when it's an asteroid with velocity
    to_target = aim_point - player.position
    if to_target.length_squared() == 0:
        return

    # Blend aim with dodge direction for fluid circling
    if dodge.length_squared() > 0:
        dodge_dir = dodge.normalize()
        # Prefer sliding sideways around threats while still facing target
        side = pygame.Vector2(-to_target.y, to_target.x)
        if side.length_squared() > 0:
            side = side.normalize()
            if side.dot(dodge_dir) < 0:
                side = -side
            move_dir = (to_target.normalize() * 0.35 + side * 0.65 + dodge_dir * 0.8)
        else:
            move_dir = dodge_dir
    else:
        # Close the gap, but keep a soft orbit distance
        dist = to_target.length()
        if dist < 140:
            # circle around
            side = pygame.Vector2(-to_target.y, to_target.x).normalize()
            move_dir = to_target.normalize() * 0.15 + side * 0.85
        else:
            move_dir = to_target.normalize()

    desired = pygame.Vector2(0, 1).angle_to(to_target)
    diff = _angle_diff(desired, player.rotation)
    # Snappier turns for fluid aiming
    turn_rate = PLAYER_TURN_SPEED * 1.35 * dt
    player.rotation += max(-turn_rate, min(turn_rate, diff))

    # Thrust toward blended move direction
    move_angle = pygame.Vector2(0, 1).angle_to(move_dir)
    move_diff = abs(_angle_diff(move_angle, player.rotation))
    if move_diff < 90:
        player.move(dt * (1.0 if move_diff < 50 else 0.65))

    # Fire whenever roughly lined up — wider cone when close
    dist = to_target.length()
    aim_tolerance = 22 if dist > 220 else 38
    if abs(diff) < aim_tolerance and not player.overheated and player.shoot_timer <= 0:
        player.shoot()
        player.heat += 8  # lighter heat so AI stays aggressive
        if player.heat >= SHOOT_BAR_MAX:
            player.heat = SHOOT_BAR_MAX
            player.overheated = True
