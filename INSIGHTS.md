# Game Insights from Player Telemetry

## Insight 1: Heavy PvE Bias — Players are rarely fighting each other
**What caught my eye in the data:**
The vast majority of combat events in the game are players fighting bots, rather than other human players.

**Back it up:**
Out of ~89,000 recorded events, there were **2,415 `BotKill`** events (humans killing bots) and **700 `BotKilled`** events (humans dying to bots). In stark contrast, there were only **3 `Kill`** and **3 `Killed`** events (Human vs. Human combat) across the entire 5-day period.

**Actionable Takeaways:**
- **Metrics affected:** PvP Engagement Rate, Player Retention (if players are seeking competitive PvP but only finding bots).
- **Actionable items:** 
  - Increase the human player count per match or reduce the map size to force human encounters.
  - Create high-tier loot zones ("hot drops") that attract multiple human squads to the same central location.
- **Why a level designer should care:** If the map is too large or lacks centralized points of interest (POIs) with high-value loot, human players will naturally avoid each other and only encounter the ambient bot population.

---

## Insight 2: Disproportionate Storm Danger on 'Lockdown'
**What caught my eye in the data:**
The `Lockdown` map is significantly more lethal due to the storm mechanic compared to the primary map.

**Back it up:**
The primary map, `AmbroseValley`, saw the vast majority of playtime (61,013 total events) and resulted in **17 `KilledByStorm`** events.
The `Lockdown` map saw only a third of that playtime (21,238 total events), yet *also* resulted in **17 `KilledByStorm`** events. Players die to the storm at a 3x higher rate on Lockdown.

**Actionable Takeaways:**
- **Metrics affected:** Survival Rate, Extraction Rate, Player Frustration (dying to environment vs. combat).
- **Actionable items:**
  - Review the storm speed and timing logic specifically for the Lockdown map; it may be moving too fast for the map's terrain.
  - Add more extraction points or mobility items (ziplines, jump pads) to the Lockdown map to help players outrun the storm.
- **Why a level designer should care:** "Lockdown" is intended to be a smaller/close-quarters map. If players are dying to the storm at a high rate, it suggests the map's layout (perhaps too many walls/chokepoints) is restricting movement and trapping players outside the safe zone.

---

## Insight 4: Severe Under-population — Most matches are solitary
**What caught my eye in the data:**
The vast majority of matches are effectively empty, with only a single human or bot recorded.

**Back it up:**
Across 796 unique matches recorded over 5 days:
- **743 matches (93%)** had only **1 participant**.
- The **Average participants per match** is only **1.56**.
- Even the **Max participants** seen was only **16** (in an extraction shooter that likely supports 50-100).

**Actionable Takeaways:**
- **Metrics affected:** Matchmaking Efficiency, Player Engagement, Server Costs (running many instances for 1 player is inefficient).
- **Actionable items:** 
  - Investigate the matchmaking "bucket" logic; why are so many matches starting with only one player instead of waiting to fill?
  - Consider a "match start delay" or a minimum player threshold before spawning the instance.
- **Why a level designer should care:** A map's layout and chokepoints only "work" when there is a critical mass of players interacting. If 93% of matches are solo, the map feels like an empty walking simulator, and the carefully designed level geometry is never truly tested by combat or tactical positioning.
