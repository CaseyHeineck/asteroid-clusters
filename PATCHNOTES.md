# ASTEROID CLUSTERS — Patch Notes

All notable changes, additions, and updates to the game are recorded here.
Entries are never removed — only appended. Each entry is dated and summarizes what changed.

---

## 2026-04-12

### Banishment Feedback
- After banishing a drone, the screen now displays a notification in the same style as the level-up flash — centered on screen, gold text, fades out over 3 seconds
- Message format: **"{Drone} gains {keyword}"** (e.g. "Plasma gains burn") or **"Player gains life regen"** when the Sentinel is banished

### Shop — Drone Keyword Tags
- Drone entries in both the Technomancer and Elementalmancer menus now display the drone's projectile keyword(s) in brackets next to the drone name
- Base keywords by type: Kinetic → **IMPACT**, Plasma → **BURN**, Explosive → **EXPLOSION**, Laser → **OVERKILL**
- Extra abilities gained through banishment are appended to the tag (e.g. `[IMPACT, BURN]`)
- Multiple keywords are comma-separated

### Ability Keyword Canonicalization
- Internal ability identifiers renamed to match their in-game keywords: `"dot"` → `"burn"`, `"aoe"` → `"explosion"`
- All checks in projectile hit logic and banishment maps updated to use the new names — no behavior change, terminology is now consistent throughout

### Elemental Asteroid Visuals (Revised)
- Removed the previous element-colored outline approach
- Elemental asteroids now render with a **white outline that pulses toward the element's primary color** — the outline smoothly cycles between near-white and full element color at ~0.9 Hz
- The pulse never bottoms out at pure white — a minimum blend of 30% element color is always present, so elemental asteroids are always distinguishable from non-elemental ones
- Cracks, craters, and the hit-flash all share the same color so the whole asteroid reads consistently

### Strafe Exhaust Fix
- Lateral thruster exhaust effects now emit from the correct side of the ship: strafing right fires from the left thruster, strafing left fires from the right thruster

---

## 2026-04-11 (2)

### Sorcerous Sundries — Mancer Shop Overhaul
- Renamed the Mechanic's Shop to **Sorcerous Sundries** to match the space wizard theme; proximity prompt updated accordingly
- The single monolithic shop menu has been replaced with a multi-level mancer roster system
- Every shop now contains a guaranteed **Technomancer** (handles drone stat upgrades) plus 0–5 **Elementalmancers** (handle elemental infusion), each appearing as a separate entry with a colored orb sprite
  - Probability distribution for elementalmancer count: 0 (~20%), 1 (~40%), 2 (~22%), 3 (~10%), 4 (~5%), 5 (~3%)
- Selecting a mancer enters their dedicated submenu; **BACK TO SHOP** or **ESC** returns to the roster
- The selection cursor now holds its position within a mancer's menu after making a purchase — no more snapping back to the top on every upgrade
- Fixed crash: pressing the back button mid-frame no longer causes a `KeyError` when the shop mode changes between `update()` and `draw()`

### Elemental Asteroid Visuals
- Elemental asteroids no longer render a circular glow halo; the pulsing ring overlay has been removed
- Element identity is now conveyed entirely through the asteroid's irregular polygon outline, which is tinted in the element's primary color

---

## 2026-04-11

### Elemental System
- Added five elements: **Solar**, **Cryo**, **Flux**, **Ion**, and **Void**, each with a distinct color identity and visual style
- Elements follow a pentagon advantage table — each element deals 2× damage against two others and 0.5× against two others:
  - Solar → strong vs. Cryo, Void | weak vs. Flux, Ion
  - Cryo → strong vs. Flux, Ion | weak vs. Void, Solar
  - Flux → strong vs. Void, Solar | weak vs. Ion, Cryo
  - Ion → strong vs. Solar, Flux | weak vs. Cryo, Void
  - Void → strong vs. Ion, Cryo | weak vs. Solar, Flux
- Any object that can be elemental holds exactly one element at a time

### Elemental Asteroids
- 20% of field-spawned asteroids are randomly assigned one of the five elements
- Elemental asteroids render with a pulsing colored glow halo and element-tinted outline
- Elemental asteroids that split pass their element to children: 65% chance per child, with at least one child guaranteed to inherit the element
- Non-elemental asteroids can never gain an element later
- Elemental asteroids drop **elemental essence** on death in addition to regular drops; larger asteroids drop proportionally more

### Elemental Essence (New Resource)
- Elemental essence is a single shared currency dropped only by elemental asteroids
- Displayed on the HUD below regular essence as `✦ N` in gold
- Used exclusively to pay for wizard infusions at the Mechanic's Shop

### Space Wizards & Drone Infusion
- Each Mechanic's Shop spawns with 1–5 space wizards (heavily weighted toward 1, decreasing probability for each additional wizard)
- Multiple wizards in a shop are always different element types
- Wizard element distribution is balanced globally across the whole map — elements already well-represented in existing shops are less likely to appear in new ones
- A wizard can infuse any of the player's drones with their element for **20 elemental essence** (blank drone) or **35 elemental essence** (overwriting an existing element)
- Infused drones glow with their element's colors
- Infused drones pass their element to every projectile they fire; projectiles render in the element's primary color
- Elemental damage multipliers apply at the moment a projectile hits an asteroid

### Strafe Movement Fix
- Releasing the strafe key now immediately kills all lateral speed — no more drifting sideways after a brief strafe tap
- When strafe is active, lateral speed is driven entirely by live input and drops to zero the frame input is released
- Fixed a secondary issue where hitting the max speed cap during a strafe would bake strafe velocity into the persistent perpendicular speed component, causing it to linger after releasing the strafe key

---

## 2026-04-09

### Drone Banishment — Weapon Type Transference
- Banishing a combat drone (Kinetic, Explosive, Plasma, Laser) now grants a bonus ability to a random surviving drone rather than being a pure sacrifice
- Each drone class transfers a distinct ability: Kinetic → impact knockback, Plasma → damage-over-time burn, Explosive → area-of-effect blast, Laser → overkill size/count reduction
- Banishing a Sentinel drone grants the player passive life regeneration instead of transferring to a drone
- Ability transference stacks — a drone can accumulate multiple abilities from multiple banishments

### Player Ship Visual Effects
- Added ship-relative thruster exhaust effects that appear while inputs are held and disappear instantly on release — no trailing, full intensity
- **Main engines**: twin flame torches emit from a pair of exhaust ports at the rear of the ship; boost doubles the flame size
- **RCS thrusters**: small side jets appear at the front-corner of the ship when rotating left or right, oriented to visually push the nose in the correct direction
- **Lateral thrusters**: larger side jets fire perpendicular to the nose when strafing
- Braking suppresses the main engine exhaust to avoid misleading feedback during deceleration
- Two small exhaust port squares with silver outlines are drawn on the rear hull to anchor the main engine flames

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
