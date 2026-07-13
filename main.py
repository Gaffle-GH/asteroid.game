import sys
import pygame
import random
from player_info.player import Player
from enemy.asteroid import Asteroid
from enemy.asteroidfield import AsteroidField
from player_info.shot import Shot, EnemyShot
from effects.particles import Particle
from effects.ship_explosion import spawn_ship_explosion
from items.healthpack import HealthPack
from items.bomb import Bomb
from enemy.enemy_ship.enemy_ships import EnemyShip
from core.waves import WaveManager
from core.crt import apply_crt
from core.demo_ai import update_demo_pilot
from core.ui import (
    draw_health_bar,
    draw_shoot_bar,
    draw_hud_stats,
    draw_wave_announce,
    draw_cursor_menu,
)
from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SHOOT_BAR_MAX,
    WAVE_SHIP_UNLOCK,
    ASTEROID_MIN_RADIUS,
    ENEMY_RADIUS,
    ENEMY_SPAWN_RATE_SECONDS,
    ASTEROID_SPAWN_RATE_SECONDS,
)

WARP_LEVELS = [0.04, 0.08, 0.14]
WARP_LABELS = ["LOW", "MED", "HIGH"]
GUI_WARP = WARP_LEVELS[0]  # gameplay HUD always uses LOW warp
DEATH_EXPLODE_TIME = 1.0
DEATH_FADE_TIME = 1.0


def main():
    pygame.init()
    pygame.display.set_caption("Asteroids")
    # SCALED helps on Retina Macs so the logical size matches the window
    flags = pygame.SCALED
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    except pygame.error:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    text_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    warp_x_shift = 0

    # Match original font style
    font = pygame.font.SysFont(None, 24)
    large_font = pygame.font.SysFont(None, 48)
    title_font = pygame.font.SysFont(None, 64)
    menu_font = pygame.font.SysFont(None, 32)

    # Settings — default warp matches original 0.04
    warp_level = 0  # LOW / original
    show_fps = False

    # Menu navigation
    menu_index = 0
    settings_index = 0
    menu_return_state = "start"  # where Settings "Back" returns

    # Pre-compute background glow
    GLOW_COLOR = (38, 38, 38)
    GLOW_RADIUS = max(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.8
    glow_surface = pygame.Surface((GLOW_RADIUS * 2, GLOW_RADIUS * 2), pygame.SRCALPHA)
    for i in range(10, 0, -1):
        alpha = (i / 10.0) * 150
        current_radius = int(GLOW_RADIUS * (i / 10.0))
        if current_radius > 0:
            glow_rect = pygame.Rect(
                GLOW_RADIUS - current_radius,
                GLOW_RADIUS - int(current_radius * 0.8),
                current_radius * 2,
                int(current_radius * 1.6),
            )
            pygame.draw.ellipse(glow_surface, (*GLOW_COLOR, alpha), glow_rect)
    glow_center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    enemy_shots = pygame.sprite.Group()
    enemy_ships = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    health_packs = pygame.sprite.Group()
    bombs = pygame.sprite.Group()

    def setup_containers():
        Player.containers = (updatable, drawable)
        Asteroid.containers = (asteroids, updatable, drawable)
        AsteroidField.containers = (updatable,)
        Shot.containers = (shots, updatable, drawable)
        EnemyShot.containers = (enemy_shots, updatable, drawable)
        EnemyShip.containers = (enemy_ships, drawable)
        Particle.containers = (particles, updatable, drawable)
        HealthPack.containers = (health_packs, updatable, drawable)
        Bomb.containers = (bombs, updatable, drawable)

    def clear_world():
        updatable.empty()
        drawable.empty()
        asteroids.empty()
        shots.empty()
        enemy_shots.empty()
        enemy_ships.empty()
        particles.empty()
        health_packs.empty()
        bombs.empty()

    def start_new_run():
        nonlocal player, asteroid_field, waves, score
        nonlocal health_pack_spawn_timer, bomb_spawn_timer, flash_timer, fps_history
        nonlocal demo_mode, player_dying, death_timer, death_fade
        clear_world()
        setup_containers()
        player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        asteroid_field = AsteroidField()
        asteroid_field.auto_spawn = False
        waves = WaveManager()
        score = 0
        fps_history = []
        flash_timer = 0.0
        health_pack_spawn_timer = 0.0
        bomb_spawn_timer = 0.0
        demo_mode = False
        player_dying = False
        death_timer = 0.0
        death_fade = 0.0

    def begin_player_death():
        """Explosion, fade to black, then game over."""
        nonlocal player_dying, death_timer, death_fade, flash_timer
        if player_dying or player is None or not player.alive():
            return
        player_dying = True
        death_timer = DEATH_EXPLODE_TIME + DEATH_FADE_TIME
        death_fade = 0.0
        flash_timer = 0.35
        player.target_health = 0
        player.health = 0
        spawn_ship_explosion(player.position.x, player.position.y)
        player.kill()

    def ensure_demo():
        """Background AI gameplay for the start menu."""
        nonlocal player, asteroid_field, demo_mode, demo_enemy_timer
        if demo_mode and player is not None and player.alive() and asteroid_field is not None:
            return
        clear_world()
        setup_containers()
        player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        asteroid_field = AsteroidField()
        asteroid_field.auto_spawn = True
        # Faster rocks in the demo
        asteroid_field.spawn_timer = ASTEROID_SPAWN_RATE_SECONDS
        # Seed rocks + a couple enemy ships
        for _ in range(7):
            edge = random.choice(asteroid_field.edges)
            speed = random.randint(50, 120)
            velocity = edge[0] * speed
            velocity = velocity.rotate(random.randint(-35, 35))
            position = edge[1](random.uniform(0.1, 0.9))
            kind = random.randint(1, 3)
            asteroid_field.spawn(ASTEROID_MIN_RADIUS * kind, position, velocity)
        for _ in range(2):
            _spawn_demo_enemy()
        demo_enemy_timer = 0.0
        demo_mode = True

    def _spawn_demo_enemy():
        edge = random.choice(("left", "right", "top", "bottom"))
        if edge == "left":
            x, y = -ENEMY_RADIUS, random.uniform(80, SCREEN_HEIGHT - 80)
        elif edge == "right":
            x, y = SCREEN_WIDTH + ENEMY_RADIUS, random.uniform(80, SCREEN_HEIGHT - 80)
        elif edge == "top":
            x, y = random.uniform(80, SCREEN_WIDTH - 80), -ENEMY_RADIUS
        else:
            x, y = random.uniform(80, SCREEN_WIDTH - 80), SCREEN_HEIGHT + ENEMY_RADIUS
        EnemyShip(x, y)

    def demo_background_active():
        return game_state == "start" or (
            game_state == "settings" and menu_return_state == "start"
        )

    setup_containers()
    player = None
    asteroid_field = None
    waves = WaveManager()
    score = 0
    demo_mode = False
    demo_enemy_timer = 0.0
    player_dying = False
    death_timer = 0.0
    death_fade = 0.0

    clock = pygame.time.Clock()
    dt = 0
    last_time = pygame.time.get_ticks() / 1000.0
    effect_time = 0.0

    game_state = "start"  # start, playing, paused, settings, end

    fps_history = []
    fps_average_count = 10

    health_pack_spawn_timer = 0.0
    health_pack_spawn_interval = 8.0
    bomb_spawn_timer = 0.0
    bomb_spawn_interval = 15.0
    flash_timer = 0.0

    def start_menu_options():
        return ["Start", "Settings", "Quit"]

    def pause_menu_options():
        return ["Resume", "Settings", "Quit"]

    def end_menu_options():
        return ["Retry", "Settings", "Quit"]

    def settings_menu_options():
        return [
            f"CRT Warp     < {WARP_LABELS[warp_level]} >",
            f"Show FPS     < {'ON' if show_fps else 'OFF'} >",
            "Back",
        ]

    def handle_menu_nav(event, option_count):
        nonlocal menu_index, settings_index
        idx = settings_index if game_state == "settings" else menu_index
        if event.key in (pygame.K_w, pygame.K_UP):
            idx = (idx - 1) % option_count
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            idx = (idx + 1) % option_count
        if game_state == "settings":
            settings_index = idx
        else:
            menu_index = idx
        return idx

    def adjust_setting(direction):
        nonlocal warp_level, show_fps
        opt = settings_index
        if opt == 0:
            warp_level = (warp_level + direction) % len(WARP_LEVELS)
        elif opt == 1:
            show_fps = not show_fps

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type != pygame.KEYDOWN:
                continue

            # Pause from gameplay
            if game_state == "playing" and event.key == pygame.K_ESCAPE:
                game_state = "paused"
                menu_index = 0
                continue

            if game_state == "start":
                opts = start_menu_options()
                handle_menu_nav(event, len(opts))
                if event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
                    pass  # nothing to adjust on main menu
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    choice = opts[menu_index]
                    if choice == "Start":
                        start_new_run()
                        game_state = "playing"
                    elif choice == "Settings":
                        menu_return_state = "start"
                        settings_index = 0
                        game_state = "settings"
                    elif choice == "Quit":
                        return

            elif game_state == "paused":
                opts = pause_menu_options()
                handle_menu_nav(event, len(opts))
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    choice = opts[menu_index]
                    if choice == "Resume":
                        game_state = "playing"
                    elif choice == "Settings":
                        menu_return_state = "paused"
                        settings_index = 0
                        game_state = "settings"
                    elif choice == "Quit":
                        return
                if event.key == pygame.K_ESCAPE:
                    game_state = "playing"

            elif game_state == "end":
                opts = end_menu_options()
                handle_menu_nav(event, len(opts))
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    choice = opts[menu_index]
                    if choice == "Retry":
                        start_new_run()
                        game_state = "playing"
                    elif choice == "Settings":
                        menu_return_state = "end"
                        settings_index = 0
                        game_state = "settings"
                    elif choice == "Quit":
                        return

            elif game_state == "settings":
                opts = settings_menu_options()
                handle_menu_nav(event, len(opts))
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    adjust_setting(-1)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    adjust_setting(1)
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if settings_index == 2:  # Back
                        menu_index = 0
                        game_state = menu_return_state
                if event.key == pygame.K_ESCAPE:
                    menu_index = 0
                    game_state = menu_return_state

        # AI demo gameplay behind the start / settings menu
        if demo_background_active():
            ensure_demo()
            for sprite in list(updatable):
                if isinstance(sprite, Player):
                    continue
                sprite.update(dt)

            for enemy in enemy_ships:
                enemy.update(dt, player.position)

            update_demo_pilot(player, dt, asteroids, enemy_ships)

            # Periodically bring in more enemy ships (cap so it stays readable)
            demo_enemy_timer += dt
            if demo_enemy_timer >= ENEMY_SPAWN_RATE_SECONDS and len(enemy_ships) < 4:
                demo_enemy_timer = 0.0
                _spawn_demo_enemy()

            for shot in list(shots):
                hit = False
                for asteroid in list(asteroids):
                    if shot.collides_with(asteroid):
                        shot.kill()
                        for _ in range(10):
                            angle = random.uniform(0, 360)
                            speed = random.uniform(70, 200)
                            vel = pygame.Vector2(0, 1).rotate(angle) * speed
                            Particle(asteroid.position.x, asteroid.position.y, vel, radius=3, life=0.75)
                        asteroid.kill()
                        hit = True
                        break
                if hit:
                    continue
                for enemy in list(enemy_ships):
                    if shot.collides_with(enemy):
                        shot.kill()
                        for _ in range(12):
                            angle = random.uniform(0, 360)
                            speed = random.uniform(80, 220)
                            vel = pygame.Vector2(0, 1).rotate(angle) * speed
                            Particle(enemy.position.x, enemy.position.y, vel, radius=3, life=0.8)
                        enemy.kill()
                        hit = True
                        break
                if not hit and (
                    shot.position.x < -50 or shot.position.x > SCREEN_WIDTH + 50
                    or shot.position.y < -50 or shot.position.y > SCREEN_HEIGHT + 50
                ):
                    shot.kill()

            for shot in list(enemy_shots):
                if player.collides_with(shot):
                    shot.kill()
                    for _ in range(6):
                        angle = random.uniform(0, 360)
                        speed = random.uniform(40, 120)
                        vel = pygame.Vector2(0, 1).rotate(angle) * speed
                        Particle(player.position.x, player.position.y, vel, radius=2, life=0.4)
                elif (
                    shot.position.x < -50 or shot.position.x > SCREEN_WIDTH + 50
                    or shot.position.y < -50 or shot.position.y > SCREEN_HEIGHT + 50
                ):
                    shot.kill()

            for asteroid in list(asteroids):
                if player.collides_with(asteroid):
                    for _ in range(10):
                        angle = random.uniform(0, 360)
                        speed = random.uniform(60, 160)
                        vel = pygame.Vector2(0, 1).rotate(angle) * speed
                        Particle(asteroid.position.x, asteroid.position.y, vel, radius=3, life=0.7)
                    asteroid.kill()
                    away = player.position - asteroid.position
                    if away.length_squared() == 0:
                        away = pygame.Vector2(1, 0)
                    player.position += away.normalize() * 40
                    player.position.x = max(player.radius, min(SCREEN_WIDTH - player.radius, player.position.x))
                    player.position.y = max(player.radius, min(SCREEN_HEIGHT - player.radius, player.position.y))

            for enemy in list(enemy_ships):
                if player.collides_with(enemy):
                    for _ in range(10):
                        angle = random.uniform(0, 360)
                        speed = random.uniform(60, 160)
                        vel = pygame.Vector2(0, 1).rotate(angle) * speed
                        Particle(enemy.position.x, enemy.position.y, vel, radius=3, life=0.7)
                    enemy.kill()

            # asteroid collisions
            ast_list = list(asteroids)
            for i in range(len(ast_list)):
                a1 = ast_list[i]
                for j in range(i + 1, len(ast_list)):
                    a2 = ast_list[j]
                    n = a2.position - a1.position
                    dist = n.length()
                    if dist == 0:
                        continue
                    if dist <= (a1.radius + a2.radius):
                        unit_n = n / dist
                        m1 = a1.radius * a1.radius
                        m2 = a2.radius * a2.radius
                        rel = a1.velocity - a2.velocity
                        impulse = 2 * rel.dot(unit_n) / (m1 + m2)
                        a1.velocity = a1.velocity - (impulse * m2) * unit_n
                        a2.velocity = a2.velocity + (impulse * m1) * unit_n
                        overlap = (a1.radius + a2.radius) - dist
                        correction = unit_n * (overlap / 2 + 0.1)
                        a1.position -= correction
                        a2.position += correction

        if game_state == "playing":
            updatable.update(dt)

            if player_dying:
                death_timer -= dt
                if death_timer <= DEATH_FADE_TIME:
                    death_fade = 1.0 - max(0.0, death_timer) / DEATH_FADE_TIME
                if death_timer <= 0:
                    player_dying = False
                    death_timer = 0.0
                    death_fade = 1.0
                    menu_index = 0
                    game_state = "end"
            else:
                for enemy in enemy_ships:
                    enemy.update(dt, player.position)

                waves.update(dt, asteroid_field, asteroids, enemy_ships)

                for bomb in list(bombs):
                    if bomb.exploded:
                        for asteroid in list(asteroids):
                            if bomb.position.distance_to(asteroid.position) <= bomb.explode_radius:
                                score += int(asteroid.radius * 2)
                                count = max(6, int(asteroid.radius * 0.6))
                                for _ in range(count):
                                    angle = random.uniform(0, 360)
                                    speed = random.uniform(80, 260)
                                    vel = pygame.Vector2(0, 1).rotate(angle) * speed
                                    Particle(asteroid.position.x, asteroid.position.y, vel, radius=4, life=1.0)
                                asteroid.kill()
                        for enemy in list(enemy_ships):
                            if bomb.position.distance_to(enemy.position) <= bomb.explode_radius:
                                score += 50
                                for _ in range(12):
                                    angle = random.uniform(0, 360)
                                    speed = random.uniform(80, 260)
                                    vel = pygame.Vector2(0, 1).rotate(angle) * speed
                                    Particle(enemy.position.x, enemy.position.y, vel, radius=4, life=1.0)
                                enemy.kill()
                        if bomb.position.distance_to(player.position) <= bomb.explode_radius:
                            player.target_health -= 30
                            flash_timer = 0.2
                            if player.target_health <= 0:
                                begin_player_death()
                        for _ in range(30):
                            angle = random.uniform(0, 360)
                            speed = random.uniform(100, 300)
                            vel = pygame.Vector2(0, 1).rotate(angle) * speed
                            Particle(bomb.position.x, bomb.position.y, vel, radius=5, life=1.5)
                        bomb.kill()

                health_pack_spawn_timer += dt
                if health_pack_spawn_timer > health_pack_spawn_interval:
                    health_pack_spawn_timer = 0
                    margin = 50
                    x = random.randint(margin, SCREEN_WIDTH - margin)
                    y = random.randint(margin, SCREEN_HEIGHT - margin)
                    HealthPack(x, y)

                bomb_spawn_timer += dt
                if bomb_spawn_timer > bomb_spawn_interval:
                    bomb_spawn_timer = 0
                    margin = 50
                    x = random.randint(margin, SCREEN_WIDTH - margin)
                    y = random.randint(margin, SCREEN_HEIGHT - margin)
                    Bomb(x, y)

                for shot in list(shots):
                    for asteroid in list(asteroids):
                        if shot.collides_with(asteroid):
                            shot.kill()
                            score += int(asteroid.radius * 2)
                            count = min(20, max(6, int(asteroid.radius * 0.6)))
                            for _ in range(count):
                                angle = random.uniform(0, 360)
                                speed = random.uniform(80, 260)
                                vel = pygame.Vector2(0, 1).rotate(angle) * speed
                                Particle(asteroid.position.x, asteroid.position.y, vel, radius=4, life=1.0)
                            asteroid.kill()
                            break

                for shot in list(shots):
                    for enemy in list(enemy_ships):
                        if shot.collides_with(enemy):
                            shot.kill()
                            score += 50
                            for _ in range(12):
                                angle = random.uniform(0, 360)
                                speed = random.uniform(80, 220)
                                vel = pygame.Vector2(0, 1).rotate(angle) * speed
                                Particle(enemy.position.x, enemy.position.y, vel, radius=4, life=1.0)
                            enemy.kill()
                            break

                for shot in list(enemy_shots):
                    if player.collides_with(shot):
                        shot.kill()
                        player.target_health -= 15
                        flash_timer = 0.1
                        if player.target_health <= 0:
                            begin_player_death()

                for shot in list(shots) + list(enemy_shots):
                    if (shot.position.x < -50 or shot.position.x > SCREEN_WIDTH + 50
                            or shot.position.y < -50 or shot.position.y > SCREEN_HEIGHT + 50):
                        shot.kill()

                for asteroid in asteroids:
                    if player.collides_with(asteroid):
                        player.target_health -= 20
                        flash_timer = 0.1
                        for _ in range(12):
                            angle = random.uniform(0, 360)
                            speed = random.uniform(60, 180)
                            vel = pygame.Vector2(0, 1).rotate(angle) * speed
                            Particle(asteroid.position.x, asteroid.position.y, vel, radius=4, life=1.0)
                        asteroid.kill()
                        if player.target_health <= 0:
                            begin_player_death()

                for enemy in list(enemy_ships):
                    if player.collides_with(enemy):
                        player.target_health -= 25
                        flash_timer = 0.1
                        for _ in range(12):
                            angle = random.uniform(0, 360)
                            speed = random.uniform(60, 180)
                            vel = pygame.Vector2(0, 1).rotate(angle) * speed
                            Particle(enemy.position.x, enemy.position.y, vel, radius=4, life=1.0)
                        enemy.kill()
                        if player.target_health <= 0:
                            begin_player_death()

                for pack in list(health_packs):
                    if player.collides_with(pack):
                        player.target_health = min(100, player.target_health + 25)
                        pack.kill()

                ast_list = list(asteroids)
                for i in range(len(ast_list)):
                    a1 = ast_list[i]
                    for j in range(i + 1, len(ast_list)):
                        a2 = ast_list[j]
                        n = a2.position - a1.position
                        dist = n.length()
                        if dist == 0:
                            continue
                        if dist <= (a1.radius + a2.radius):
                            unit_n = n / dist
                            m1 = a1.radius * a1.radius
                            m2 = a2.radius * a2.radius
                            rel = a1.velocity - a2.velocity
                            p = 2 * rel.dot(unit_n) / (m1 + m2)
                            a1.velocity = a1.velocity - (p * m2) * unit_n
                            a2.velocity = a2.velocity + (p * m1) * unit_n
                            overlap = (a1.radius + a2.radius) - dist
                            correction = unit_n * (overlap / 2 + 0.1)
                            a1.position -= correction
                            a2.position += correction

        # --- Draw (original style: game + text layers, both CRT-warped) ---
        game_surface.fill((0, 0, 0))
        text_surface.fill((0, 0, 0, 0))

        # Keep world under the death fade; game-over screen stays black underneath the flat menu
        show_world = demo_background_active() or game_state in ("playing", "paused") or (
            game_state == "settings" and menu_return_state in ("paused", "end")
        )
        if show_world:
            for obj in drawable:
                if isinstance(obj, Particle):
                    if not getattr(obj, "on_screen", True):
                        obj.draw(game_surface)
                    continue
                obj.draw(game_surface)

        # HUD on text layer so it can use a fixed LOW warp
        if game_state == "playing" or (
            game_state in ("paused", "settings") and menu_return_state in ("paused", "end") and player is not None
        ):
            if player is not None and player.alive():
                draw_health_bar(text_surface, 50, 50, player.health, 100)
                draw_shoot_bar(
                    text_surface, 50, SCREEN_HEIGHT - 70, player.heat, SHOOT_BAR_MAX, player.overheated
                )
                on_field = waves.enemies_on_field(asteroids, enemy_ships)
                still_incoming = waves.remaining_to_spawn()
                draw_hud_stats(text_surface, font, score, waves.wave, on_field, still_incoming, 50, 50 + 26)

        if game_state == "playing" and waves.state == "announce":
            draw_wave_announce(
                text_surface,
                title_font,
                font,
                waves.wave,
                show_ship_warning=waves.wave >= WAVE_SHIP_UNLOCK,
            )

        if game_state == "start":
            draw_cursor_menu(text_surface, large_font, menu_font, "ASTEROIDS", start_menu_options(), menu_index)
        elif game_state == "paused":
            draw_cursor_menu(text_surface, large_font, menu_font, "PAUSED", pause_menu_options(), menu_index)
        elif game_state == "settings":
            draw_cursor_menu(text_surface, large_font, menu_font, "SETTINGS", settings_menu_options(), settings_index)
        # Game over menu is drawn flat (no CRT warp) after the screen composite

        if flash_timer > 0 and game_state == "playing":
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, 100))
            game_surface.blit(flash_surface, (0, 0))
            flash_timer -= dt

        # Bezel + glow (original)
        screen.fill((194, 194, 198))
        screen.blit(glow_surface, (glow_center[0] - GLOW_RADIUS, glow_center[1] - GLOW_RADIUS))

        world_warp = WARP_LEVELS[warp_level]
        # Gameplay HUD stays on a fixed LOW warp; menus follow the setting
        text_warp = GUI_WARP if game_state in ("playing", "paused") else world_warp
        apply_crt(game_surface, screen, world_warp, warp_x_shift)
        apply_crt(text_surface, screen, text_warp, warp_x_shift)

        # Explosion particles stay crisp on top (original)
        if show_world:
            for p in particles:
                if getattr(p, "on_screen", True):
                    p.draw(screen)

        # Fade the whole scene (including particles) to black after the explosion
        if death_fade > 0:
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(int(255 * min(1.0, death_fade)))
            screen.blit(fade_surface, (0, 0))

        # Game over box/text stay sharp — no barrel warp
        if game_state == "end":
            menu_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            draw_cursor_menu(
                menu_overlay,
                large_font,
                menu_font,
                "GAME OVER",
                end_menu_options(),
                menu_index,
                subtitle=f"Final Score: {score}   Wave: {waves.wave}",
            )
            screen.blit(menu_overlay, (0, 0))

        current_time = pygame.time.get_ticks() / 1000.0
        real_dt = current_time - last_time
        last_time = current_time
        effect_time += dt
        fps_history.append(real_dt)
        if len(fps_history) > fps_average_count:
            fps_history.pop(0)
        average_dt = sum(fps_history) / len(fps_history) if fps_history else 0
        real_fps = 1 / average_dt if average_dt > 0 else 0
        if show_fps:
            fps_text = font.render(f"FPS: {real_fps:.1f}", True, (0, 255, 0))
            screen.blit(fps_text, (20, 20))

        pygame.display.flip()
        dt = clock.tick(60) / 1000


if __name__ == "__main__":
    main()
