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

## Insight 3: Severe Under-population — Most matches are solitary
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

---

## 🛠️ Notable Edge Case Matches for Testing
These matches are highly valuable for testing the visualization tool's performance and robustness:

1. **⚔️ High Combat:** `b3550292-8f80-493a-a422-95c4e70f0a5e.nakama-0`
   - **Scenario:** Highest combat activity with **38 BotKill events**. 
   - **Test Case:** Verify marker overlay density and "Kills" checkbox visibility.

2. **👨‍👩‍👧‍👦 Maximum Density:** `fbbc5d02-dd79-42fb-bba5-d768023891c8.nakama-0`
   - **Scenario:** Peak concurrency with **16 unique entities**.
   - **Test Case:** Test **Autofocus** camera logic on a wide bounding box.

3. **🌪️ Storm Death:** `8c8aca2d-626d-4d99-ad69-8c02acee5256.nakama-0`
   - **Scenario:** Rare environmental death event (`KilledByStorm`).
   - **Test Case:** Confirm the **Purple Circle-Dot** marker appears at the precise end-of-life coordinates.

4. **👻 Ghost Match:** `9b982ee6-e84b-4133-93f6-16725fca348f.nakama-0`
   - **Scenario:** Extreme low-data edge case (**2 total events**).
   - **Test Case:** Ensure playback slider stability and error handling.

5. **🌍 Map Complexity:**
   - **Lockdown (Heavy Data):** `d0a38c30-d476-4305-857d-ece9e65f72e6.nakama-0` (1,216 events).
   - **AmbroseValley (Long Traversal):** `de5aa1ae-6246-4cfb-9941-adf5996ef678.nakama-0` (1,124 events).
   - **Test Case:** Test **x4.0 Speed** and **±10s Jump** buttons.
