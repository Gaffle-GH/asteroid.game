# Asteroids

A retro Asteroids-style arcade game built with Python and Pygame. Clear waves of rocks, dodge enemy ships, manage your heat meter, and grab pickups — all with a CRT warp aesthetic.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup

```bash
# with uv
uv sync
uv run python main.py

# or with pip
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install pygame==2.6.1
python main.py
```

## Controls

| Action | Keys |
| --- | --- |
| Thrust / reverse | `W` / `S` |
| Rotate | `A` / `D` |
| Shoot | `Space` |
| Pause | `Esc` |
| Menu navigate | `W` / `S` or arrow keys |
| Menu select | `Space` or `Enter` |
| Adjust settings | `A` / `D` or arrow keys |

## Gameplay

- Survive escalating **waves** of asteroids. Each wave packs more rocks and faster spawns.
- From **wave 4** onward, AI enemy ships join the fight and return fire.
- Your ship has a **health bar** and a **heat meter** — hold fire too long and you overheat until the bar cools down.
- Pick up green **health packs** (+) to recover HP.
- Red **bombs** explode after a short fuse and clear nearby asteroids for bonus score.
- The title screen runs a live **AI demo** in the background.

## Settings

Open **Settings** from the start, pause, or game-over menus:

- **CRT Warp** — `LOW` / `MED` / `HIGH` screen distortion
- **Show FPS** — toggle an FPS counter

## Project layout

```
main.py                 # game loop, menus, scoring
constants.py            # tuning (speeds, waves, sizes)
core/                   # CRT effect, UI, waves, demo AI, base shapes
player_info/            # player ship + shots
enemy/                  # asteroids, field spawner, enemy ships
items/                  # health packs, bombs
effects/                # particles, explosions
```

## License

Personal project — see the repository for details.
