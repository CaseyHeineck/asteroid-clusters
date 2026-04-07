# Changelog

All notable changes to this project are documented here. Entries are added manually when commits are made, referencing the commit message for detail.

---

## [Unreleased]

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
