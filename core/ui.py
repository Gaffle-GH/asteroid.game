import pygame


def draw_health_bar(surface, x, y, health, max_health, font=None):
    """Original-style hull bar: dark track, white fill, white border."""
    pygame.draw.rect(surface, (50, 50, 50), (x, y, 200, 20))
    current_width = max(0, int((health / max_health) * 200)) if max_health else 0
    pygame.draw.rect(surface, (255, 255, 255), (x, y, current_width, 20))
    pygame.draw.rect(surface, (255, 255, 255), (x, y, 200, 20), 2)


def draw_shoot_bar(surface, x, y, heat, max_heat, overheated, font=None):
    """Original-style heat bar; red border when overheated."""
    pygame.draw.rect(surface, (50, 50, 50), (x, y, 200, 20))
    current_width = max(0, int((heat / max_heat) * 200)) if max_heat else 0
    pygame.draw.rect(surface, (255, 255, 255), (x, y, current_width, 20))
    color = (255, 100, 100) if overheated else (255, 255, 255)
    pygame.draw.rect(surface, color, (x, y, 200, 20), 2)


def draw_hud_stats(surface, font, score, wave, enemies_on_field, incoming, x, y):
    """Score / wave / enemies in one bordered box like the bars."""
    lines = [
        f"SCORE: {score}",
        f"WAVE: {wave}",
        f"ENEMIES: {enemies_on_field}" + (f" (+{incoming})" if incoming else ""),
    ]
    box_w = 200
    pad_x = 8
    pad_y = 6
    line_h = max(20, font.get_height() + 2)
    box_h = pad_y * 2 + line_h * len(lines)

    pygame.draw.rect(surface, (50, 50, 50), (x, y, box_w, box_h))
    pygame.draw.rect(surface, (255, 255, 255), (x, y, box_w, box_h), 2)

    for i, text in enumerate(lines):
        surf = font.render(text, True, (255, 255, 255))
        surface.blit(surf, (x + pad_x, y + pad_y + i * line_h))


def draw_wave_announce(surface, title_font, body_font, wave, show_ship_warning):
    """Centered wave title — drawn onto the warped text layer."""
    title = title_font.render(f"WAVE {wave}", True, (255, 255, 255))
    cx = surface.get_width() // 2
    cy = surface.get_height() // 2
    surface.blit(title, (cx - title.get_width() // 2, cy - title.get_height() // 2 - (14 if show_ship_warning else 0)))
    if show_ship_warning:
        hint = body_font.render("ENEMY SHIPS INBOUND", True, (255, 80, 80))
        surface.blit(hint, (cx - hint.get_width() // 2, cy + 28))


def draw_cursor_menu(
    surface,
    title_font,
    body_font,
    title,
    options,
    selected_index,
    title_color=(255, 0, 0),
    subtitle=None,
):
    """
    Retro menu with '>' cursor inside one bordered box:
      > Start
        Settings
        Quit

    Optional subtitle sits cleanly between title and the menu box.
    """
    cx = surface.get_width() // 2
    cy = surface.get_height() // 2 - 70

    title_surf = title_font.render(title, True, title_color)
    title_y = cy
    surface.blit(title_surf, (cx - title_surf.get_width() // 2, title_y))

    box_top = title_y + title_surf.get_height() + 18
    if subtitle:
        sub_surf = body_font.render(subtitle, True, (255, 255, 255))
        surface.blit(sub_surf, (cx - sub_surf.get_width() // 2, box_top))
        box_top += sub_surf.get_height() + 16

    labels = []
    for i, opt in enumerate(options):
        prefix = "> " if i == selected_index else "  "
        labels.append(prefix + opt)

    # Fixed box size so it doesn't jump when the cursor moves or options change
    line_h = 32
    pad_x = 16
    pad_y = 14
    box_w = 320
    box_h = pad_y * 2 + line_h * 3
    box_x = cx - box_w // 2
    box_y = box_top

    pygame.draw.rect(surface, (50, 50, 50), (box_x, box_y, box_w, box_h))
    pygame.draw.rect(surface, (255, 255, 255), (box_x, box_y, box_w, box_h), 2)

    y = box_y + pad_y
    for i, label in enumerate(labels):
        color = (255, 255, 255) if i == selected_index else (180, 180, 180)
        line = body_font.render(label, True, color)
        surface.blit(line, (box_x + pad_x, y + (line_h - line.get_height()) // 2))
        y += line_h

    hint = body_font.render("W/S move   A/D adjust   SPACE select", True, (160, 160, 160))
    surface.blit(hint, (cx - hint.get_width() // 2, surface.get_height() - 48))
