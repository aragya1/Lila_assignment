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

## Insight 3: Severe Underutilization of 'GrandRift'
**What caught my eye in the data:**
The `GrandRift` map has extremely low engagement compared to the other two maps.

**Back it up:**
Out of the 89,000 total events, `AmbroseValley` accounts for ~68% of the data (61k events) and `Lockdown` accounts for ~24% (21k). `GrandRift` only accounts for **~7.6% (6,853 events)**. 

**Actionable Takeaways:**
- **Metrics affected:** Map Selection Rate, Matchmaking Queue Times.
- **Actionable items:**
  - If map selection is player-chosen, investigate why players are avoiding GrandRift (e.g., poor loot distribution, unpopular aesthetic, or performance issues).
  - If map selection is random (rotation), check the matchmaking server logic to ensure GrandRift is actually weighted correctly in the queue.
- **Why a level designer should care:** Significant development time goes into creating a map. If a map is being skipped or matches on it end extremely fast (resulting in fewer events), the map design needs an overhaul to make it as compelling as Ambrose Valley.
