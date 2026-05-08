# ASTEROID CLUSTERS — Patch Notes

---

## 2026-05-08

### Slayer Drone — Variant Redesign

Three Slayer variants violated core design constraints and have been retired. The class has been rebuilt around five mechanically distinct identities.

**Retired:**
- `BreachPlatform` — bypassed the elemental system, which is a game-wide mechanic no single variant should touch
- `CascadePlatform` — used area-of-effect damage, the Explosive drone's exclusive mechanical identity
- `OverchargePlatform` — was functionally just a slower Laser Beam with higher numbers; no meaningful differentiation

**Replacement variants:**

| Variant | Platform | Identity |
|---------|----------|----------|
| Laser Beam | `LaserPlatform` | Baseline hitscan; overkill on kill reduces child asteroid spawn count and size |
| Finisher | `FinisherPlatform` | Scales damage with target's missing HP; weak opener, devastating closer |
| Long Shot | `LongShotPlatform` | Damage scales linearly with distance; rewards kiting and fighting from max range |
| Resonant Beam | `ResonantBeamPlatform` | Consecutive hits on the same target ramp damage up tier by tier; resets on target switch |
| Life Siphon | `LifeSiphonPlatform` | Shots heal HP (health mode) or bank life essence toward a free life (lives mode); kill bonus on each kill |

#### New upgrade paths

**Laser Beam** — two new variant-specific paths added:
- **Overkill Intensity** (`overkill_intensity`): increases `overkill_amp`; amplifies the overkill tier calculation so excess damage counts for more when splitting asteroids
- **Rapid Retarget** (`rapid_retarget`): one-time upgrade; on a killing shot the cooldown resets to zero so the drone can immediately lock onto the next target

**Finisher** — one new variant-specific path added:
- **Kill Momentum** (`kill_momentum`): one-time upgrade; on a killing shot the cooldown resets to zero

#### Long Shot mechanics

`range_ratio = clamp(distance / platform.range, 0.0, 1.0)`
`effective_damage = int(base_damage × lerp(MIN_MULT, MAX_MULT, range_ratio))`

Default `MIN_MULT = 0.5`, `MAX_MULT = 2.5`. Point-blank fires at half base damage; at full range fires at 2.5× base. Range is 480 px (wider than baseline) to give room to work.

Upgrade paths: **Range Multiplier** (+20% to `MAX_MULT`), **Extended Range** (+15% to `range`).

#### Resonant Beam mechanics

Tracks `resonance_target` and `resonance_tier` (0–`max_tier`). On each shot: hitting the same target increments tier, hitting a different target resets it to 0. Damage multiplier: `1.0 + tier × tier_multiplier`. Default `max_tier = 4`, `tier_multiplier = 0.5`; at peak `base × 3.0`. On target death tier resets.

Upgrade paths: **Resonance Buildup** (reduces hits needed to reach peak), **Resonance Cap** (+20% to `tier_multiplier`).

#### Life Siphon mechanics

After each shot: `drain_amount = max(1, floor(damage × drain_rate))` (default `drain_rate = 0.10`).

- **Health mode** (`player.uses_health`): adds drain directly to `player.health`, capped at `max_health`. Kill bonus adds `floor(target.max_health × kill_drain_rate)` to the same heal.
- **Lives mode** (default): accumulates a hidden `life_essence_pool`. When `pool >= LIFE_SIPHON_LIFE_THRESHOLD`, player gains one life and pool resets to zero (capped at `max_lives`). Kill bonus adds to pool the same way.

Default `kill_drain_rate = 0.05` (5% of target max HP on kill). Upgrade paths: **Drain Rate** (+5%), **Kill Drain** (+5%).

#### LaserBeam projectile — overkill_amp parameter

`LaserBeam.__init__` now accepts `overkill_amp=1.0`. The overkill tier calculation is updated to:
`tier = max(1, int((effective_damage - target_health) × overkill_amp) // full_health)`

---

## 2026-05-05

### Drone Variant System — All Five Drone Types Now Have Five Variants

Every drone type now presents a variant selection screen when added. The player chooses one of five platform types per drone; the choice is permanent for that drone's lifetime.

#### Variant selection flow

- When a drone is earned at a level milestone the player sees a variant select screen before the drone is added
- If the drone type has only one platform class the screen is bypassed (the single variant is applied automatically)
- On banishment, variant selection still appears — the chosen platform's keyword and specific upgrade paths determine what transfers

#### Explosive drone variants (4 new)

All fire from the drone and deal AoE blast damage through `RocketHitAOE`. Each uses a `_detonated` flag (not `alive()`) to guard re-entry across the update cycle.

| Variant | Platform | Behavior |
|---------|----------|----------|
| Rocket | `ExplosivePlatform` | Self-propelled; explodes on impact (unchanged) |
| Fuse bomb | `FuseBombPlatform` | Placed at player position; countdown timer; large blast radius; never collides until it detonates |
| Grenade | `GrenadePlatform` | Lobbed toward target with arc; timer-based detonation |
| Homing missile | `HomingMissilePlatform` | Rotates velocity toward target up to `turn_rate` deg/s each frame |
| Proximity mine | `ProximityMinePlatform` | Placed at player position; stationary; detonates when any object enters `trigger_radius` |

#### Kinetic drone variants (4 new)

| Variant | Platform | Behavior |
|---------|----------|----------|
| Kinetic | `KineticPlatform` | Single fast round with knockback (unchanged) |
| Bouncer | `BouncerPlatform` | Deflects off targets; upgradeable bounce count |
| Buckshot | `BuckshotPlatform` | Wide cone of pellets; upgradeable pellet count |
| Cannonball | `CannonballPlatform` | Heavy, slow, high-damage; no pierce |
| Needle slug | `NeedleSlugPlatform` | High-velocity piercing round; upgradeable pierce count |

#### Slayer drone variants (4 new; drone renamed from LaserDrone)

`LaserDrone` → `SlayerDrone`. Design identity: the boss killer — sustained single-target damage plus overkill.

| Variant | Platform | Behavior |
|---------|----------|----------|
| Laser | `LaserPlatform` | Hitscan beam; overkill on elimination (unchanged) |
| Breach | `BreachPlatform` | Ignores a portion of target defense |
| Cascade | `CascadePlatform` | Amplifies overkill burst radius |
| Finisher | `FinisherPlatform` | Bonus damage proportional to target's missing HP |
| Overcharge | `OverchargePlatform` | Charges over time; releases devastating burst |

#### Debuff drone variants (4 new; drone renamed from PlasmaDrone)

`PlasmaDrone` → `DebuffDrone`. Design identity: the force multiplier — applies mechanical states that make everything else hit harder.

| Variant | Platform | Behavior |
|---------|----------|----------|
| Burn | `BurnPlatform` | Plasma bolt; stacking DoT (unchanged, was `PlasmaPlatform`) |
| Contagion | `ContagionPlatform` | DoT that spreads to nearby enemies on target death |
| Corrode | `CorrodePlatform` | Reduces target defense; all incoming damage hits harder |
| Mark | `MarkPlatform` | Tags target; next hit from any source deals amplified damage |
| Slow | `SlowPlatform` | Reduces target move speed and fire rate for a duration |

#### Sentinel drone variants (4 new)

`SentinelDrone` previously had one variant (Shield). It now has five. All sentinel variants bypass the standard `fire()` / targeting loop — they use `sentinel_update(drone, dt)` instead, a per-frame callback on the platform that receives the drone as an argument.

| Variant | Platform | Behavior |
|---------|----------|----------|
| Shield | `SentinelPlatform` | Creates and repairs a damage-absorbing shield (unchanged) |
| Decoy | `DecoyPlatform` | Deploys a `Decoy` entity at the player's position; enemies retarget it while active (6 s on, 8 s cooldown) |
| Evasion | `EvasionPlatform` | Sets `player.evasion_chance` each frame; `player.damaged()` rolls this chance to negate a hit entirely |
| Heal | `HealPlatform` | On activation converts lives to a health bar (`max_health = max_lives × 10`); heals +1 HP every 15 s |
| Resource boost | `ResourceBoostPlatform` | Generates 2 essence every 8 s passively |

#### Player health mode

Normally the player operates on a lives system (3 lives, invulnerability window after each hit). Choosing the Heal sentinel activates health mode:

- `player.uses_health = True`; `player.max_health = max_lives × 10`; `player.health = max_health`
- In health mode `player.damaged()` decrements `health` by the damage value directly — no invulnerability window, no blink
- Heart HUD switches: fill ratio = `current_health / max_health`; center label = `max_health` (not current count)
- All other sentinel variants, and the default game, use the lives system unchanged

#### Evasion dodge

`player.evasion_chance` (default 0.0) checked in `player.damaged()` before the lives-mode damage path. `EvasionPlatform.sentinel_update()` sets this to `C.EVASION_CHANCE` (0.20) each frame. The chance stacks with shop upgrades (`+0.05` per buy).

#### Decoy entity (`entities/decoy.py`)

New `CircleShape` subclass. Drawn as a plum-colored circle. Does not collide with anything. Base `Enemy.acquire_target()` and `KineticEnemy.acquire_target()` check `game.decoy` and retarget the decoy when one is active and alive. `DecoyPlatform` manages the decoy's lifecycle directly via `kill()`; `game.decoy` is set to `None` on expiry or cooldown.

#### Sentinel platform refactor

`WeaponsPlatform` base now has `sentinel_update(drone, dt)` — default no-op. `SentinelPlatform`'s shield logic moved from `SentinelDrone.shield_sentinel()` into `SentinelPlatform.sentinel_update(drone, dt)`. `SentinelDrone.update()` calls `self.platform.sentinel_update(self, dt)`. The drone still holds the shield state attributes (`player_shield`, `shield_max_health`, `shield_repair_timer_base`, etc.) so `game.py apply_upgrade` and the platform can read them via the drone arg.

---

## 2026-04-30

### Pixel Art Sprite — Player Ship

The player ship now renders using a pixel art sprite (`assets/images/Player.png`) instead of the hand-drawn triangle polygon.

- **Sprite loaded once** — `Player._sprite` is a class variable; `_load_sprite()` fires on first `__init__` and is a no-op thereafter
- **Scaled to collision size** — image is scaled to `PLAYER_RADIUS * 2` (52 × 52 px) so the visible ship matches the physics hitbox
- **Rotation matched to heading** — each frame the sprite is rotated with `pygame.transform.rotate(sprite, -self.rotation + 180)` to align with the ship's forward direction
- **Blink preserved** — during the damage invulnerability window the sprite is hidden on off-beats (same flash rhythm as the old polygon)
- **Exhaust port detail removed** — the static silver port squares that flanked the triangle hull are gone; the sprite carries that visual detail; particle exhaust effects (`ShipExhaustVE`) are unchanged
- Sets up the asset pipeline: future sprites for asteroids, enemies, and drones can follow the same load-once, scale-to-radius, blit-rotated pattern

---

## 2026-04-27

### Enemy Combat Pass — Friendly Fire, Rocket Splash, Laser Lock-On Rewrite

#### Friendly fire — all enemy projectiles now damage other enemies

Previously enemy projectiles were silently filtered out of enemy collision checks, so enemies could never hurt each other. That filter has been removed. All enemy-fired projectiles (kinetic, plasma, rocket) now apply damage to any enemy they collide with, same as player projectiles do. This enables emergent moments where the player can maneuver enemies into harming each other.

#### Player rocket — direct hits and AoE now damage enemies

The explosive rocket fired by the player's `ExplosiveDrone` can now hit enemy ships on direct contact, and enemies caught within the `ROCKET_HIT_RADIUS` blast take `ROCKET_HIT_DAMAGE` splash damage. Score and XP from any enemy killed by a rocket (direct or AoE) are attributed correctly and reported to the HUD/experience system.

#### Enemy rocket — visual blast radius + multi-target AoE

The `ExplosiveEnemy`'s rocket now:
- Triggers a `RocketHitExplosionVE` explosion with a visible ring outline (`ROCKET_HIT_RING_COLOR` orange, `ROCKET_HIT_RING_DURATION` 0.28 s) that clearly communicates the danger radius to the player
- Deals AoE splash damage to asteroids, other enemies, and the player if they are within blast radius — enemy rockets were previously harmless on AoE
- Added `ring_color / ring_duration / ring_max_alpha / ring_line_width` layer to `BaseExplosion` so any future explosion type can show an expanding ring independently of the base and overlay layers

#### Enemy kinetic projectile — tuned for readability

- Speed reduced from 900 → 550 px/s so the projectile is more visible and more avoidable
- Radius increased from 3 → 6 px so it reads clearly against the background

#### Laser enemy — lock-on rewrite

The laser's firing behavior has been completely corrected:

- **Ship rotation follows the lock** — once the lock-on is acquired (1 s before firing), the enemy ship immediately turns to face the locked position and holds that aim for the entire warn window; the crosshair and ship nose now both point at the same spot, giving the player a clear read
- **Direction from locked position, not ship facing** — previously the ray used the ship's current forward vector, causing it to fire in the wrong direction if the ship had drifted; it now fires along the exact line from the enemy toward the locked-on coordinate regardless of how the ship ends up oriented
- **No distance cap** — the old code stopped the ray at the locked position; the ray now extends to the screen edge so objects that have stepped into the line of fire after the lock was set are correctly struck
- **Checks all collidable objects** — the ray now tests asteroids, all other enemy ships, and the player; previously only asteroids were considered; the closest object along the ray takes the damage; if nothing is on the line the beam draws to the screen edge (a genuine miss)
- **Score and XP routing** — enemy kills from the laser route score to the HUD and XP to the experience system directly from `_fire_laser_at`; player hits update lives and trigger game-over correctly

---

## 2026-04-25 (2)

### Laser Enemy & Explosive Enemy — Two New Enemy Types

Added `LaserEnemy` and `ExplosiveEnemy`, bringing the enemy roster to four types.

#### Laser Enemy

- **Triangular hull** — equilateral-ish triangle (40 × 32) pointed forward; body color is dodger blue to read instantly against all other ships; the nose tip IS the emitter tip
- **Embedded laser emitter** — the `LaserPlatform` charge triangle is drawn directly into the nose of the hull in world space (no surface/blit), scaling ~45% of the half-hull dimensions; it cycles through the same INDIGO → LASER_RED charge gradient as the player's LaserDrone
- **Mirror movement** — tries to stay on the opposite side of the screen from the player (reflecting through the screen center); because its speed (65 px/s) is far below the player's max (450 px/s) it will never keep pace perfectly; if the distance to the player exceeds 550 px the enemy gives up mirroring and follows the player directly to close the gap; asteroid avoidance active throughout
- **Always aims at the player** — rotates to face the player's current position every frame
- **Lock-on crosshair** — when the fire timer reaches ≤ 1.0 s, the crosshair snaps to the player's position at that moment (locked, does not track); the crosshair fades from translucent red (alpha 40) to fully opaque red (alpha 255) over the 1.0 s window, drawn as crossing lines + outer circle; the player has a full second to dodge
- **Firing behavior** — when the timer hits zero the laser fires along the ray from the enemy toward the locked position; if any asteroid intersects that ray between enemy and locked position, the closest one (to the enemy) is struck; if nothing is in the way the beam draws to the screen edge and deals no damage — the player escaped
- **Fire rate** — 8.0 s total cycle with a 1.0 s crosshair window; slow, telegraphed, and dangerous
- **Stats** — 45 HP, 35 XP, 150 score, speed 65

#### Explosive Enemy

- **Square hull** — uses `rect_corners()` with equal hull_width and hull_length (30 × 30); body color is dark orange
- **`ExplosivePlatform` at the nose** — fires rockets with full AoE explosion; direct hits on the player damage normally; AoE hits nearby asteroids; fire rate 3.5 s, range 300 px, projectile speed 380 px/s
- **Cluster-seeking movement** — each frame scores every target (player + all asteroids) by counting how many other targets fall within rocket explosion radius (70 px) of that position; moves toward whichever anchor has the highest density; avoids asteroids in transit; encourages the player to spread out rather than staying in a tight area
- **Stats** — 50 HP, 35 XP, 150 score, speed 75

#### Spawner

- `EnemySpawner._pick_enemy_class()` now draws from all four types equally: `PlasmaEnemy`, `KineticEnemy`, `LaserEnemy`, `ExplosiveEnemy`

---

## 2026-04-25

### Kinetic Enemy — Second Enemy Type

Added `KineticEnemy`, a wide-bodied gunship that hunts asteroids rather than the player.

- **Wide hull** — hull is wider than it is long (48 × 22), giving it a squat disc silhouette; body color is copper to distinguish it from PlasmaEnemy's steel gray; forward-swept triangular fins flare from the front corners
- **Weapons platform as nose** — `KineticPlatform` mounts at the front of the ship, making it the visual nose; fires small, fast kinetic rounds colored danger red (matching the enemy projectile convention)
- **Asteroid hunting** — moves toward the largest asteroid on screen; fires at it when within weapon range; when the largest is out of range, fires at the nearest asteroid instead while navigating around non-target asteroids and the player
- **Player threat override** — if the player enters `KINETIC_ENEMY_PLAYER_THREAT_RADIUS` (220 px), the enemy switches to targeting and moving toward the player until the player exits range
- **Fire rate** — 2.0 s cooldown, much slower than the player's kinetic drone (0.12 s) but much faster than PlasmaEnemy (10.0 s); projectile speed 900 px/s
- **Stats** — 35 HP, 25 XP, speed 95; balanced as a level-one threat comparable to PlasmaEnemy
- **`KineticPlatform` extended** — added optional `projectile_color` param so the enemy's kinetic rounds render in danger red rather than the default drone silver
- **`EnemySpawner` updated** — now randomly picks between `PlasmaEnemy` and `KineticEnemy` each spawn via `_pick_enemy_class()`; both types still receive elemental assignment at the same 35% rate

All notable changes, additions, and updates to the game are recorded here.
Entries are never removed — only appended. Each entry is dated and summarizes what changed.

---

## 2026-04-21

### Plasma Burn on Enemies — Bug Fixes & Visual

Three bugs fixed that together meant plasma burn had never actually worked against enemy ships:

- **Burn was never applied on direct hits** — the collision system called `enemy.damaged()` + `projectile.kill()` directly, bypassing `Plasma.on_hit()` entirely. Fixed: `CollisionSystem.handle_enemy_collisions` now applies a `PlasmaBurnSTE` after any hit from a `Plasma` projectile (or any projectile with the `"burn"` ability from banishment)
- **Burn effects never ticked on enemies** — `Enemy.update()` was not calling `update_gameplay_effects(dt)` or `update_outline_pulse(dt)`, so effects accumulated silently and the pulse flash timer never ran. Both calls added
- **Lethal burn tick would crash on enemies** — `PlasmaBurnSTE.update()` did `total_score += score` but `Enemy.damaged()` returns a `(score, xp)` tuple while `Asteroid.damaged()` returns a plain int. Fixed with a defensive unpack

### Plasma Burn Stacking

Plasma burn effects now **stack independently** — each projectile that lands owns its own timer and ticks separately. Previously all burns on a single target merged into one (taking max duration, max damage, min tick rate). Stacking is controlled by a new `burn_stack_limit` attribute on `CircleShape` (default `None` = unlimited). Asteroids and basic enemies have no stack limit. Future enemy types can cap stacks by setting `burn_stack_limit` to a number, which causes overflow to merge into the oldest stack.

The `PlasmaBurnSTE` class carries a `stackable = True` flag; the base `SingleTargetEffect` defaults to `stackable = False` (merge behavior unchanged for all other effect types).

### Enemy Visual — Burn Flash & Elemental Outline

- **Plasma burn flash on enemies** — when a burn ticks, the enemy's entire hull (and wings on PlasmaEnemy) flashes to the plasma burn color for `PLASMA_BURN_FLASH_DURATION`, then returns to its body color. Uses the same `pulse_outline` / `get_outline_color` mechanism that asteroids use for their outline flash, applied to the polygon fill instead
- **Elemental glow on wings** — PlasmaEnemy wings now receive the same `draw_elemental_glow_poly` treatment as the hull when the enemy is elemental; previously the wings rendered plain even on elemental ships
- **Wider elemental ring** — the colored ring in `draw_elemental_glow_poly` widened from 3 px to 5 px for better readability against the hull fill

---

## 2026-04-20

### Plasma Burn Upgrade Path

Plasma Drone now has a dedicated, four-slot upgrade path that rewards investment in the burn mechanic rather than duplicating generic stat upgrades.

- **Burn duration extended** — plasma burn now lasts 3.1 seconds (up from 1.6s) at a base tick rate of once per second, dealing 3 ticks of damage to start
- **Burn Tick Rate upgrade** — each purchase reduces the tick interval by 0.05s, letting the burn deal damage more frequently within the same 3.1-second window; stacks with repeated purchases
- **Burn Spread upgrade** — gives burning targets a 10% chance (per purchase) to spread their burn to any object they physically collide with; the spread burn starts a fresh 3.1-second timer on the new target and inherits the full damage-per-tick, tick rate, and spread chance of the original
- Spread checks fire on asteroid–enemy collisions in both directions: a burning asteroid can ignite an enemy that runs into it, and a burning enemy can ignite an asteroid it hits
- The PlasmaDrone upgrade menu now shows **Damage +15%**, **Fire Rate +12%**, **Burn Ticks +**, and **Spread Chance +10%** — the burn-specific slots replace the old generic second slot to keep player choices clear and meaningful
- **Burn Ticks + (diminishing returns)** — first purchase reduces tick interval by 0.15s (biggest jump); each subsequent purchase tapers the reduction by 0.01s, flooring at 0.05s per purchase; tick rate itself is hard-floored at 0.01s; earlier upgrades matter most
- **Upgrade inheritance** — any drone that gains an ability through banishment now shows that ability's full upgrade set in the Technomancer shop; e.g. a PlasmaDrone that inherits Impact from a banished KineticDrone gets Kinetic Mass and Projectile Speed added to its six-slot upgrade list; LaserDrone inheriting Impact gets Kinetic Mass but not Projectile Speed (LaserBeam is hitscan, speed is irrelevant)

---

## 2026-04-18

### Enemy Ships

Enemy ships now enter the field and actively hunt the player — the first intelligent hostile threat alongside the asteroid field.

- **Enemies spawn on a timer** and close directly on the player; contact deals collision damage
- **Plasma Enemy** — the first named enemy type: a ranged gunship that pursues the player and fires burning plasma bolts; same burn DoT mechanic as the Plasma drone, but aimed at you
- **Elemental enemies** — 35% of enemy spawns are assigned a random element, making them resistant or vulnerable to your infused drones' element; matchup awareness now matters
- Enemy ships render as **rectangular hulls with type-specific wing geometry** — each enemy class has a distinct silhouette; the Plasma Enemy has swept-back delta wings and a nose-mounted cannon
- **Enemy projectiles are danger red** — immediately distinguishable from player and drone fire; elemental enemy projectiles keep their element's color ring on top of the red base
- Enemy body color is **neutral steel gray** so elemental glows read cleanly without a competing default color

### Player Color Update

Player ship color changed to **hull green** — reads clearly against black and is visually distinct from enemy ships, projectiles, and all five element colors.

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
