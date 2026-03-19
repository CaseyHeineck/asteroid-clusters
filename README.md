# Looking to add more to the game to make it feel like a game, future objectives include:
* ~~Add a scoring system~~
    * ~~Created a score class that shows in top left corner of screen, not updating correctly~~ 
        * ~~Implement higher scoring for larger asteroids~~
            * Scoring is now handled in the display class
    - Have a small popup showing the amount being added to total when destructed
* ~~Implement multiple lives and respawning~~
    * ~~Show on screen how many lives the player has left~~
    * ~~respawning is now handled within the player class~~
    * ~~Implement a cooldown system so player does not die on respawn too quickly~~
        * ~~Feels like I should be close to getting this to work, respawn properly calls player method now~~
        * ~~player method doesn't properly flag if the player is still invulnberable around the time~~
            * ~~Abandoned invulnerable idea for respawn, respawn cooldown uses player update properly now~~
    * ~~Add visual effect to ship while respawn cooldown~~
* Add an explosion effect for the asteroids
* Add acceleration to the player movement
* Make the objects wrap around the screen instead of disappearing
* Add a background image
* Create different weapon types
* Make the asteroids lumpy instead of perfectly round
* Make the ship have a triangular hit box instead of a circular one
* Add a shield power-up
* Add a speed power-up
* Add bombs that can be dropped
