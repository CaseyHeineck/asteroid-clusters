# Asteroid Clusters

A top-down arcade shooter built with Python and Pygame, inspired by the classic Asteroids with roguelite progression. Each run is a short session where you choose and build a fleet of autonomous combat drones as you level up.

## Getting Started

**Requirements:** Python 3.13+, [uv](https://github.com/astral-sh/uv)

```bash
git clone <repo-url>
cd asteroid-clusters
uv sync
uv run main.py
```

The game launches fullscreen. No additional assets or configuration needed.

## Controls

| Input | Action |
|---|---|
| `W` / `↑` | Accelerate forward |
| `S` / `↓` | Brake |
| `A` / `←` | Rotate left |
| `D` / `→` | Rotate right |
| `Ctrl` + direction | Strafe |
| `Shift` | Boost (2× speed) |
| `Space` | Full brake |
| `Escape` | Pause |

## How to Play

At the start of each run, choose one of five drone types to orbit you. Drones attack automatically — your job is to survive and position well. Destroying asteroids drops experience orbs; fly near them to collect. Level up to unlock more drone decisions: add a drone to your fleet or permanently banish it.

**Drone types:**
- **Plasma** — medium range, burning damage over time
- **Kinetic** — short range, high rate of fire
- **Explosive** — medium range, rockets with area damage
- **Laser** — long range, instant hitscan, targets highest-HP asteroid
- **Sentinel** — creates and repairs a protective shield around you

## Roadmap

**Progression**
- Drone upgrade system — improve individual drones between milestones
- Player stat upgrades tied to level (movement, fire rate, etc.)
- Additional drone choice mechanics beyond add/banish

**Gameplay**
- Asteroid drop system — ore and fuel resources from destruction
- Score popup on asteroid kill showing the amount added
- Bomb weapon the player can drop
- Projectiles that miss wrap the screen instead of escaping off-edge

**World**
- Map exploration across multiple screens per run, warp-gate unlocked by currency
- Background imagery and parallax

**Polish**
- Distinct explosion visuals per weapon type
- Settings and keybind customization menu
- Background music and sound effects
