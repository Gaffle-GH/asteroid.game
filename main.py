import sys
import pygame
import random
from player import Player, draw_health_bar, draw_shoot_bar
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot
from particles import Particle
from healthpack import HealthPack
from bomb import Bomb
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SHOOT_BAR_MAX

def apply_crt(source_surface, dest_surface, warp_amount, warp_x_shift):
    for y in range(0, SCREEN_HEIGHT, 4):
        norm_y = (y - SCREEN_HEIGHT / 2) / (SCREEN_HEIGHT / 2) 
        horizontal_expand = 1.0 + (norm_y**2 * warp_amount)
        new_width = int(SCREEN_WIDTH * horizontal_expand)
        x_offset = (SCREEN_WIDTH - new_width) // 2 + warp_x_shift
        row = source_surface.subsurface((0, y, SCREEN_WIDTH, 4))
        scaled_row = pygame.transform.scale(row, (new_width, 4))
        if y % 8 == 0:
            scaled_row.set_alpha(200) 
        dest_surface.blit(scaled_row, (x_offset, y))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    text_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    warp_amount = 0.04  # Increase for more curve
    # global horizontal shift applied to the warped image (pixels)
    warp_x_shift = 0
    font = pygame.font.SysFont(None, 24)
    large_font = pygame.font.SysFont(None, 48)

    # Pre-compute background glow
    GLOW_COLOR = (38, 38, 38) 
    GLOW_RADIUS = max(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.8
    glow_surface = pygame.Surface((GLOW_RADIUS * 2, GLOW_RADIUS * 2), pygame.SRCALPHA)
    for i in range(10, 0, -1):
        alpha = (i / 10.0) * 150
        current_radius = int(GLOW_RADIUS * (i / 10.0))
        if current_radius > 0:
            glow_rect = pygame.Rect(GLOW_RADIUS - current_radius, GLOW_RADIUS - int(current_radius * 0.8), current_radius * 2, int(current_radius * 1.6))
            pygame.draw.ellipse(glow_surface, (*GLOW_COLOR, alpha), glow_rect)
    glow_center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    health_packs = pygame.sprite.Group()
    bombs = pygame.sprite.Group()

    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable)
    Shot.containers = (shots, updatable, drawable)
    Particle.containers = (particles, updatable, drawable)
    HealthPack.containers = (health_packs, updatable, drawable)
    Bomb.containers = (bombs, updatable, drawable)

    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    asteroid_field = AsteroidField()
    score = 0

    clock = pygame.time.Clock()
    dt = 0
    last_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds

    game_state = 'start'  # 'start', 'playing', 'end'

    # FPS averaging
    fps_history = []
    fps_average_count = 10

    # Health pack spawning
    health_pack_spawn_timer = 0.0
    health_pack_spawn_interval = 8.0  # seconds

    # Bomb spawning
    bomb_spawn_timer = 0.0
    bomb_spawn_interval = 15.0  # seconds

    # Screen flash
    flash_timer = 0.0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if game_state == 'start' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_state = 'playing'
            elif game_state == 'end' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Reset game
                    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                    asteroid_field = AsteroidField()
                    score = 0
                    # Clear groups
                    updatable.empty()
                    drawable.empty()
                    asteroids.empty()
                    shots.empty()
                    particles.empty()
                    health_packs.empty()
                    bombs.empty()
                    # Re-add containers
                    Player.containers = (updatable, drawable)
                    Asteroid.containers = (asteroids, updatable, drawable)
                    AsteroidField.containers = (updatable)
                    Shot.containers = (shots, updatable, drawable)
                    Particle.containers = (particles, updatable, drawable)
                    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                    asteroid_field = AsteroidField()
                    fps_history = []
                    flash_timer = 0.0
                    health_pack_spawn_timer = 0.0
                    bomb_spawn_timer = 0.0
                    game_state = 'playing'

        if game_state == 'playing':
            updatable.update(dt)

            # Check for bomb explosions
            for bomb in list(bombs):
                if bomb.exploded:
                    # Explode: destroy nearby asteroids
                    for asteroid in list(asteroids):
                        if bomb.position.distance_to(asteroid.position) <= bomb.explode_radius:
                            # award points
                            score += int(asteroid.radius * 2)
                            # spawn particles
                            count = max(6, int(asteroid.radius * 0.6))
                            for _ in range(count):
                                angle = random.uniform(0, 360)
                                speed = random.uniform(80, 260)
                                vel = pygame.Vector2(0, 1).rotate(angle) * speed
                                p = Particle(asteroid.position.x, asteroid.position.y, vel, radius=4, life=1.0)
                            asteroid.kill()
                    # Damage player if in radius
                    if bomb.position.distance_to(player.position) <= bomb.explode_radius:
                        player.target_health -= 30  # Bomb damage
                        flash_timer = 0.2  # Longer flash for bomb
                    # Explosion particles
                    for _ in range(30):
                        angle = random.uniform(0, 360)
                        speed = random.uniform(100, 300)
                        vel = pygame.Vector2(0, 1).rotate(angle) * speed
                        Particle(bomb.position.x, bomb.position.y, vel, radius=5, life=1.5)
                    bomb.kill()

            # Spawn health packs
            health_pack_spawn_timer += dt
            if health_pack_spawn_timer > health_pack_spawn_interval:
                health_pack_spawn_timer = 0
                # Spawn at random position, not too close to edges
                margin = 50
                x = random.randint(margin, SCREEN_WIDTH - margin)
                y = random.randint(margin, SCREEN_HEIGHT - margin)
                HealthPack(x, y)

            # Spawn bombs
            bomb_spawn_timer += dt
            if bomb_spawn_timer > bomb_spawn_interval:
                bomb_spawn_timer = 0
                margin = 50
                x = random.randint(margin, SCREEN_WIDTH - margin)
                y = random.randint(margin, SCREEN_HEIGHT - margin)
                Bomb(x, y)

            # Shots vs asteroids: destroy asteroid and spawn particles
            for shot in list(shots):
                for asteroid in list(asteroids):
                    if shot.collides_with(asteroid):
                        shot.kill()
                        # award points based on asteroid size (larger = more points)
                        score += int(asteroid.radius * 2)
                        # spawn particles
                        count = min(20, max(6, int(asteroid.radius * 0.6)))
                        for _ in range(count):
                            angle = random.uniform(0, 360)
                            speed = random.uniform(80, 260)
                            vel = pygame.Vector2(0, 1).rotate(angle) * speed
                            p = Particle(asteroid.position.x, asteroid.position.y, vel, radius=4, life=1.0)
                        asteroid.kill()
                        break

            for asteroid in asteroids:
                if player.collides_with(asteroid):
                    player.target_health -= 20
                    flash_timer = 0.1  # Flash screen
                    # spawn small particles
                    for _ in range(12):
                        angle = random.uniform(0, 360)
                        speed = random.uniform(60, 180)
                        vel = pygame.Vector2(0, 1).rotate(angle) * speed
                        Particle(asteroid.position.x, asteroid.position.y, vel, radius=4, life=1.0)
                    asteroid.kill() # Destroy asteroid on impact
                    if player.target_health <= 0:
                        game_state = 'end'

            # Check health pack collisions
            for pack in list(health_packs):
                if player.collides_with(pack):
                    player.target_health = min(100, player.target_health + 25)  # Heal
                    pack.kill()

            # Asteroid - asteroid elastic collisions and separation
            ast_list = list(asteroids)
            for i in range(len(ast_list)):
                a1 = ast_list[i]
                for j in range(i + 1, len(ast_list)):
                    a2 = ast_list[j]
                    # check collision
                    n = a2.position - a1.position
                    dist = n.length()
                    if dist == 0:
                        continue
                    if dist <= (a1.radius + a2.radius):
                        # normalize
                        unit_n = n / dist
                        # approximate mass by area (radius^2)
                        m1 = a1.radius * a1.radius
                        m2 = a2.radius * a2.radius
                        # relative velocity
                        rel = a1.velocity - a2.velocity
                        p = 2 * rel.dot(unit_n) / (m1 + m2)
                        a1.velocity = a1.velocity - (p * m2) * unit_n
                        a2.velocity = a2.velocity + (p * m1) * unit_n
                        # separate overlapping
                        overlap = (a1.radius + a2.radius) - dist
                        correction = unit_n * (overlap / 2 + 0.1)
                        a1.position -= correction
                        a2.position += correction

        # 1. Draw game to the internal buffer. Draw particles that belong to the game_surface (thrusters)
        game_surface.fill((0, 0, 0))  # Clear to black
        text_surface.fill((0, 0, 0, 0))  # Clear to transparent
        if game_state == 'playing':
            for obj in drawable:
                if isinstance(obj, Particle):
                    # if particle is meant to be drawn to the game_surface (warp with scene), draw it here
                    if not getattr(obj, "on_screen", True):
                        obj.draw(game_surface)
                    continue
                obj.draw(game_surface)

            draw_health_bar(game_surface, 50, 50, player.health, 100)
            # Render score under the health bar on text_surface for separate CRT layer
            score_text = font.render(f"SCORE: {score}", True, (255, 255, 255))
            text_surface.blit(score_text, (50, 50 + 26))
            # draw shooting heat bar at bottom-left parallel to health
            draw_shoot_bar(game_surface, 50, SCREEN_HEIGHT - 70, player.heat, SHOOT_BAR_MAX, player.overheated)

        # Draw screen text for start and end
        if game_state == 'start':
            title_text = large_font.render("ASTEROIDS", True, (255, 0, 0))
            start_text = font.render("Press SPACE to Start", True, (255, 255, 255))
            text_surface.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            text_surface.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
        elif game_state == 'end':
            game_over_text = large_font.render("GAME OVER", True, (255, 0, 0))
            final_score_text = font.render(f"Final Score: {score}", True, (255, 255, 255))
            restart_text = font.render("Press SPACE to Restart", True, (255, 255, 255))
            text_surface.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            text_surface.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2))
            text_surface.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        # 2. Start Drawing to Main Screen: Clear background to near-black
        screen.fill((194, 194, 198)) 
        
        # --- Draw the pre-computed background glow effect ---
        screen.blit(glow_surface, (glow_center[0] - GLOW_RADIUS, glow_center[1] - GLOW_RADIUS))
        # -------------------------------------------

        # 3. Apply Curved CRT effect to game
        apply_crt(game_surface, screen, warp_amount, warp_x_shift)
        # Apply CRT to text layer on top
        apply_crt(text_surface, screen, warp_amount, warp_x_shift)

        # Draw particles on top of the warped CRT output so explosion particles remain crisp and visible
        if game_state == 'playing':
            for p in particles:
                if getattr(p, "on_screen", True):
                    p.draw(screen)

        # Screen flash effect
        if flash_timer > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, 100))  # Semi-transparent white
            screen.blit(flash_surface, (0, 0))
            flash_timer -= dt

        
        # 4. UI Overlays
        current_time = pygame.time.get_ticks() / 1000.0
        real_dt = current_time - last_time
        last_time = current_time
        fps_history.append(real_dt)
        if len(fps_history) > fps_average_count:
            fps_history.pop(0)
        average_dt = sum(fps_history) / len(fps_history) if fps_history else 0
        real_fps = 1 / average_dt if average_dt > 0 else 0
        fps_text = font.render(f"FPS: {real_fps:.1f}", True, (0, 255, 0))
        screen.blit(fps_text, (20, 20))
        
        pygame.display.flip()
        dt = clock.tick(60) / 1000

if __name__ == "__main__":
    main()
