# ASTEROID CLUSTERS — Patch Notes

All notable changes, additions, and updates to the game are recorded here.
Entries are never removed — only appended. Each entry is dated and summarizes what changed.

---

## 2026-04-08 11:47

### Air Space Map Generation
- Revised portal spawning conditions for more balanced and navigable map layouts
- Adjusted portal topology rules to improve room connectivity across the grid

### Mechanic's Shop
- Added the Mechanic's Shop as an in-game upgrade system
- Shops spawn randomly in air spaces (40% chance per room), marked by a pulsing gold diamond
- Interact with **E** when in proximity to open the shop menu; **ESC** to close
- Upgrades dynamically generated from the player's current drone roster:
  - Combat drones (Kinetic, Explosive, Plasma, Laser): **Damage +15%** and **Fire Rate +12%**
  - Sentinel drone: **Shield Health +2** and **Repair Speed +15%**
- Upgrade prices start at 15 essence and increase by 10 per purchase of that upgrade
- Upgrades apply immediately to all live instances of the upgraded drone class

---

## 2026-04-08

### Project & Identity
- Project renamed from *Asteroids Clone* to *Asteroid Clusters*; moved to personal workspace
- Window title and main menu updated to display "ASTEROID CLUSTERS"
- `pyproject.toml`, README, and git remote updated to match new project name
- VSCode interpreter settings added to point to project `.venv`

### Core Game
- Momentum-based movement: acceleration, boost (2×), strafe, and brake
- Procedural lumpy asteroid visuals with progressive crack damage scarring
- Triangle collision hull for the player ship
- Multiple lives with damage cooldown and blink invulnerability effect
- Screen-edge wrapping for player and asteroids
- Score system with size-scaled asteroid point values
- Start, pause, and game-over menus
- End-of-run stats report with per-source damage, kills, overkills, and shield breakdown

### Combat Systems
- Five drone types: Plasma, Kinetic, Explosive, Laser, Sentinel
- Four projectile types: kinetic round, plasma bolt (burn DoT), laser beam (hitscan + overkill), rocket (AoE explosion)
- Overkill mechanic — excess damage reduces child asteroid spawn count and size
- Sentinel drone generates and repairs a shield around the player

### Shield Visual Overhaul
- Shield body renders at a consistent low opacity regardless of health
- Outer edge fades from fully opaque at full health to invisible at zero
- White flash ring wraps the full shield on hit

### Experience & Drone Progression
- Pre-game drone selection screen; choose your starting drone before each run
- Drone choice milestones at levels 2, 5, 10, 15, and 20 — add or permanently banish a drone
- Experience orbs drop from all destroyed asteroids; larger asteroids drop proportionally more (quadratic scaling)
- Power-curve leveling system: fast early levels for player buy-in, steeper cost at mid and late game

### Starfield Background
- Procedurally generated star field drawn behind all game objects
- Stars parallax-scroll opposite to player movement to reinforce speed and heading
- Star sizes and brightness vary for depth; all wrap seamlessly at screen edges

### Asteroid Essence (New Resource)
- Asteroid essence is a new resource independent of the XP system — lore: you are a space wizard mining asteroids for their essence
- Purple diamond-shaped essence orbs drop from destroyed asteroids alongside XP orbs
- Each orb type rolls independently for drop chance (XP: 80%, essence: 75%) and spawns at a random position within the destroyed asteroid's radius
- Essence count displayed in the HUD top-right as `◆ N` in purple

### Air Space & Portal System
- Each game run takes place across a grid of interconnected air spaces, inspired by the room system in Vampire Survivors
- Screen edges can spawn portals (30% chance per edge); topology is fixed at room creation
- Adjacent rooms mirror portal presence — if room A has no east portal, room B has no west portal toward A
- Every room guarantees at least one outgoing portal so the map never dead-ends; starting room always has at least one exit
- Portals cost essence to unlock; press **E** to interact when in proximity
- Once unlocked, a portal stays open for the run; interact again to transit
- Return portals in newly created rooms are always pre-unlocked (free to go back)
- Player velocity preserved through transit at 75% of entry speed for a warp feel
- Player arrives on the matching side of the new room (fly left → appear near right wall of new room)
- Portal visuals: purple glow when locked, cyan glow when unlocked; proximity prompt shows cost or "ENTER"

### Air Space Persistence
- Each air space retains its asteroid and orb state when the player leaves — asteroids freeze and stop spawning while inactive
- Returning to a visited room restores asteroids, orbs, and asteroid field timer exactly as left
- Projectiles and visual effects are cleared on transit; drones, health, and essence carry over

### Mini-Map
- Bottom-left HUD overlay shows the grid of visited air spaces
- Current room highlighted in cyan; visited rooms shown in dark gray
- Portal stubs drawn between rooms — purple for locked, cyan for unlocked; full connectors when both sides visited

### Mechanic's Shop
- Shops spawn randomly in air spaces (40% chance per room), shown as a pulsing gold diamond
- Interact with **E** when in proximity to open the shop menu; **ESC** closes it
- Shop upgrades dynamically generated from the player's current drone roster:
  - Combat drones (Kinetic, Explosive, Plasma, Laser): **Damage +15%** and **Fire Rate +12%**
  - Sentinel drone: **Shield Health +2** and **Repair Speed +15%**
- Prices start at 15 essence and increase by 10 each time that specific upgrade is purchased
- Upgrades apply immediately to all live instances of the upgraded drone class
- Sentinel shield health and repair rate upgrades driven by per-instance attributes for independent scaling

---
