import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


def apply_crt(source_surface, dest_surface, warp_amount, warp_x_shift=0):
    """Barrel CRT warp (original math) — no scanline/TV overlays."""
    for y in range(0, SCREEN_HEIGHT, 4):
        norm_y = (y - SCREEN_HEIGHT / 2) / (SCREEN_HEIGHT / 2)
        horizontal_expand = 1.0 + (norm_y ** 2) * warp_amount
        new_width = max(2, int(SCREEN_WIDTH * horizontal_expand))
        x_offset = (SCREEN_WIDTH - new_width) // 2 + warp_x_shift
        row_h = min(4, SCREEN_HEIGHT - y)
        row = source_surface.subsurface((0, y, SCREEN_WIDTH, row_h))
        scaled_row = pygame.transform.scale(row, (new_width, row_h))
        dest_surface.blit(scaled_row, (x_offset, y))
