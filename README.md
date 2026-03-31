# Looking to add more to the game to make it feel like a game, future objectives include:
* ~~Add a scoring system~~
    * ~~Created a score class that shows in top left corner of screen, not updating correctly~~ 
        * ~~Implement higher scoring for larger asteroids~~
            * Scoring is now handled in the display class
    - Have a small popup showing the amount being added to total when destructed
    * ~~Added health to each asteroid dependent on its size~~
        * ~~Shows a health bar on the asteroid when the asteroid is damaged~~
            * Now scars appear on the asteroid when damaged
* ~~Implement multiple lives and respawning~~
    * ~~Show on screen how many lives the player has left~~
    * ~~respawning is now handled within the player class~~
    * ~~Implement a cooldown system so player does not die on respawn too quickly~~
        * ~~Feels like I should be close to getting this to work, respawn properly calls player method now~~
        * ~~player method doesn't properly flag if the player is still invulnberable around the time~~
            * ~~Abandoned invulnerable idea for respawn, respawn cooldown uses player update properly now~~
    * ~~Add visual effect to ship while respawn cooldown~~
* ~~Add an explosion effect for the asteroids~~
    * Add detail and specialization for each kind of explosion
* ~~Add acceleration to the player movement~~
    * ~~Added boost and strafe functionality to player movement~~
* ~~Make the objects wrap around the screen instead of disappearing~~
    * Projectiles that miss still go off screen
* Add a background image
* ~~Make the asteroids lumpy instead of perfectly round~~
* ~~Make the ship have a triangular hit box instead of a circular one~~
* ~~Create different weapon types~~
* ~~Add a shield power-up~~
* Add bombs that can be dropped
## Shaping the future of the game:
* ~~Having Start Game Menu~~
    * Add settings/options button
        * Add customizable settings
    * Add upgrade menus
        * Various different branching upgrade possibilities
    * Add index/reference menus
* Game should play much more like a avoid the obstacle type game
    * As acceleration is added along with gravitational like forces, movement will become a huge gameplay factor
* Implement drones for automatic mining/destroying of asteroids
    * Want to add drops from asteroid destruction
        * Some kind of fuel to either use or trade
        * Some kind of ore 
        * Experience
    * Use a limited drone amount structure
        * Have five different types of drones
            * Medium range, medium RoF, medium damage, maybe called blaster
            * Medium range, high RoF, low damage, maybe called minigun
            * High range, low RoF, high damage, maybe called eliminator
            * Varied medium range, varied low RoF, high damage with splash, maybe called explosive
            * Targets player or immediate player area, varied RoF, aids player, maybe called defender
        * Start with one drone deployed each run, and after a certain amount of levels allow the player to add more drones
            * For example, after levels 5, 10, 15, and 20, then all drones can be deployed
                * Levels in between or after can be used to improve and upgrade each drone itself
                    * Potentially even player movement, or asteroid behavior
* Map exploration per run
    * In gameplay that is inspired by Stand Survivors
        * Start in a random asteroid field where the player can warp around the edges of that screen
        * After player collects certain amount of currency, can unlock a warp to a new screen
* ~~Having Game End Screen~~
    * Fix program so that if you start a new game it doesn't crash