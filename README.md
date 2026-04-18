# Asteroid Clusters

A top-down arcade shooter built with Python and Pygame. You're a space wizard mining an asteroid field with a fleet of autonomous combat drones while enemy ships hunt you across a grid of interconnected air spaces.

## Getting Started

### Requirements

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — fast Python package and project manager

### Clone and run

```bash
git clone https://github.com/cjheineck/asteroid-clusters.git
cd asteroid-clusters
uv sync
uv run main.py
```

`uv sync` creates a local `.venv` and installs all dependencies. No system packages required. The game opens fullscreen immediately.

## Controls

| Input | Action |
|---|---|
| `W` / `↑` | Accelerate forward |
| `S` / `↓` | Accelerate backward |
| `A` / `←` | Rotate left |
| `D` / `→` | Rotate right |
| `Ctrl` + direction | Strafe |
| `Shift` | Boost (2× speed) |
| `Space` | Full brake |
| `E` | Interact (portals, shops) |
| `Escape` | Pause / resume |

## Mechanics

### Asteroids and Essence

The asteroid field is your primary resource. Destroying asteroids drops **essence** (purple ◆), the currency used to unlock portals and buy shop upgrades. Larger asteroids drop more. Asteroids that aren't destroyed cleanly spawn smaller child asteroids.

### Elements

Five elements follow a pentagon advantage cycle — each element deals **2× damage** against two others and **0.5× damage** against two others:

```
Solar → strong vs. Cryo, Void  |  weak vs. Flux, Ion
Cryo  → strong vs. Flux, Ion   |  weak vs. Void, Solar
Flux  → strong vs. Void, Solar |  weak vs. Ion, Cryo
Ion   → strong vs. Solar, Flux |  weak vs. Cryo, Void
Void  → strong vs. Ion, Cryo   |  weak vs. Solar, Flux
```

**Elemental asteroids** — 20% of spawned asteroids carry one of the five elements, shown by a pulsing colored outline. They drop **elemental essence** (gold ✦) on death, in addition to regular essence. Elemental asteroids pass their element to child asteroids with a 65% chance per child.

### Enemy Ships

Enemy ships spawn on a timer and close directly on the player — collision deals damage. Some enemies fire projectiles; enemy fire is always **red** and easy to read at a glance.

**35% of enemies spawn with a random element**, applying the pentagon advantage table when your drones hit them. Reading the elemental matchup is the difference between melting an enemy in two shots or chipping it down in eight.

The **Plasma Enemy** is the current named type: a ranged gunship that pursues the player and fires plasma bolts applying a burn damage-over-time on hit.

### Drones

Before each run, choose one of five drone types to orbit you. Drones target and fire automatically.

| Drone | Style | Special |
|---|---|---|
| **Plasma** | Medium range, moderate fire rate | Plasma bolts apply burn DoT |
| **Kinetic** | Short range, high fire rate | Impact knockback |
| **Explosive** | Medium range | Rockets with area-of-effect blast |
| **Laser** | Long range, hitscan | Targets highest-HP asteroid; overkill reduces child spawns |
| **Sentinel** | No attack | Creates and repairs a shield around the player |

Drones can be infused with an element at the Sorcerous Sundries shop, spending elemental essence. An infused drone fires projectiles carrying its element, applying damage multipliers against elemental asteroids and enemies.

### Leveling and Drone Choices

Killing enemy ships drops XP. Leveling up triggers a drone choice: **add** a new drone to your fleet, or **banish** one permanently. Banishing a drone transfers its ability to a surviving drone — banishing a Plasma drone grants another drone the burn DoT, for example. Abilities stack across multiple banishments.

### Air Spaces and Portals

Each run spans a procedurally generated grid of rooms. Portals appear at room edges and cost essence to unlock; once open they stay open for the run. Asteroid fields, orbs, and enemies persist in each room — leaving and returning restores the room exactly as you left it. Your drones, health, and essence carry over through every transit.

### Sorcerous Sundries (Shop)

Shops spawn in ~40% of rooms, marked by a pulsing gold diamond. Press `E` to open. Each shop contains:
- **Technomancer** — stat upgrades for any drone you own (+15% damage, +12% fire rate for combat drones; +shield health / +repair rate for Sentinel)
- **Elementalmancers** (0–5 per shop) — each infuses one of your drones with their element for elemental essence (20 to infuse a blank drone, 35 to overwrite an existing element)

Upgrade prices start at 15 essence and increase by 10 per purchase of that specific upgrade.

## Roadmap

### Near-term

- Additional enemy types with distinct attack behaviors
- Score popup on kill
- Bomb weapon the player can place

### PvE Battle Royale

The long-term goal is a **PvE Battle Royale** mode where multiple players share the same procedurally generated map. Key design targets:

- **Multiple players per lobby** — likely 4–16; everyone starts in separate rooms and builds their own fleet
- **Shared map** — all players explore the same room grid; the minimap shows which rooms any player has visited
- **Collapsing field** — the playable asteroid field shrinks over time, forcing players toward the center (similar to a zone mechanic); enemy spawn rate increases as the zone tightens
- **No direct PvP damage initially** — threat comes from the field and enemies, not other players; scarcity of essence and shop slots creates indirect competition
- **Endgame** — last surviving wizard wins, or highest score when the zone fully collapses

### Other Planned Features

- Player stat upgrades tied to level (movement speed, turn rate)
- Distinct explosion visuals per weapon type
- Ore and fuel drops from asteroid destruction
- Settings and keybind customization menu
- Background music and sound effects
