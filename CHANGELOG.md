# Changelog

All notable changes to this project are documented here. Entries are added manually when commits are made, referencing the commit message for detail.

---

## [Unreleased]

---

## Project & Identity

- Project renamed from *Asteroids Clone* to *Asteroid Clusters* and moved to personal workspace
- Window title and main menu updated to display "ASTEROID CLUSTER****S"
- `pyproject.toml`, README, and git remote updated to match new project name
- VSCode interpreter settings added to point to project `.venv`

## Starfield Background

- Procedurally generated star field drawn behind all game objects
- Stars parallax-scroll in the opposite direction of player movement to reinforce speed and heading
- Star sizes and brightness vary for depth; all wrap seamlessly at screen edges

## Asteroid Essence (New Resource)

- Asteroid essence is a new resource independent of the XP system — lore framing: you are a space wizard mining asteroids for their essence
- Purple diamond-shaped essence orbs drop from destroyed asteroids alongside XP orbs
- Each orb type rolls independently for drop chance (XP: 80%, essence: 75%) and spawns at a random position within the destroyed asteroid's radius rather than dead center
- Essence count displayed in the HUD top-right as `◆ N` in purple

## Air Space & Portal System

- Each game run takes place across a grid of interconnected air spaces, inspired by the room system in Vampire Survivors
- Screen edges can spawn portals (30% chance per edge); portal topology is fixed at room creation — portals cannot appear or disappear after a room is generated
- Adjacent rooms mirror each other's portal presence: if room A has no east portal, room B cannot have a west portal toward A
- Every room guarantees at least one outgoing portal so the map never dead-ends; the starting room always has at least one exit
- Portals cost essence to unlock; press **E** to interact when in proximity
- Once unlocked, a portal stays open for the run — interact again to transit, since the player still wraps freely within a room
- Return portals in newly created rooms are always pre-unlocked (free to go back)
- Player velocity is preserved through transit at 75% of entry speed for a warp feel
- Player arrives on the same side of the new room they entered from (fly left → appear near the right wall of the new room)
- Portal visuals: purple glow when locked, cyan glow when unlocked; proximity prompt shows cost or "ENTER"

## Air Space Persistence

- Each air space retains its asteroid and orb state when the player leaves — asteroids freeze in place and stop spawning while the room is inactive
- Returning to a previously visited room restores asteroids, orbs, and the asteroid field timer exactly as left
- Projectiles and visual effects are cleared on transit; drones, health, and essence carry over

## Mini-Map

- Bottom-left HUD overlay shows the grid of visited air spaces
- Current room highlighted in cyan; visited rooms shown in dark gray
- Portal stubs drawn between rooms — purple for locked, cyan for unlocked; full-length connectors when both sides have been visited

## Mechanic's Shop

- Shops spawn randomly in the interior of air spaces (40% chance per room), shown as a pulsing gold diamond
- Interact with **E** when in proximity to open the shop menu; **ESC** closes it
- Shop upgrades are dynamically generated from the player's current drone roster:
  - Combat drones (Kinetic, Explosive, Plasma, Laser): **Damage +15%** and **Fire Rate +12%**
  - Sentinel drone: **Shield Health +2** and **Repair Speed +15%**
- Prices start at 15 essence and increase by 10 each time that specific upgrade is purchased
- Upgrades apply immediately to all live instances of the upgraded drone class
- Sentinel shield health and repair rate upgrades are now driven by per-instance attributes, allowing independent scaling per drone

---

## Experience & Drone Progression

- Pre-game drone selection screen; choose your starting drone before each run
- Drone choice milestones at levels 2, 5, 10, 15, and 20 — add or permanently banish a drone
- Experience orbs drop from all destroyed asteroids; larger asteroids drop proportionally more (quadratic scaling)
- Power-curve leveling system: fast early levels for player buy-in, steeper cost at mid and late game

## Shield Visual Overhaul

- Shield body now renders at a consistent low opacity regardless of health
- Outer edge fades from fully opaque at full health to invisible at zero
- White flash ring wraps the full shield on hit

## Combat Systems

- Five drone types: Plasma, Kinetic, Explosive, Laser, Sentinel
- Four projectile types: kinetic round, plasma bolt (burn DoT), laser beam (hitscan + overkill), rocket (AoE explosion)
- Overkill mechanic — excess damage reduces child asteroid spawn count and size
- Sentinel drone generates and repairs a shield around the player

## Core Game

- Procedural lumpy asteroid visuals with progressive crack damage scarring
- Triangle collision hull for the player ship
- Momentum-based movement: acceleration, boost (2×), strafe, and brake
- Multiple lives with damage cooldown and blink invulnerability effect
- Screen-edge wrapping for player and asteroids
- End-of-run stats report with per-source damage, kills, overkills, and shield breakdown
- Score system with size-scaled asteroid point values
- Start, pause, and game-over menus
