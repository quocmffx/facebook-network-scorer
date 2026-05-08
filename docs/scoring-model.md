# Scoring Model

The Facebook Network Scorer uses a multi-channel algorithm to calculate the interaction strength between you and your connections. 

## Channels and Weights

Interactions are parsed and weighted according to their value:
- **Direct Messages:** The strongest signal of a real connection.
- **Comments:** Moderate signal. Comments longer than a certain threshold carry more weight than short tags.
- **Reactions:** Weakest signal, representing low-friction engagement (likes, loves).

## Key Concepts

### Bidirectional Scoring
The algorithm rewards genuine two-way conversations. A conversation where both parties participate equally will receive a significant bonus multiplier. Heavily one-sided spam or monologues are penalized.

### Time Decay
All signals decay over time using an exponential decay function. An interaction from yesterday is worth significantly more than an interaction from 5 years ago.

### Context Drift
When you stop interacting with someone entirely, their context drift penalty increases over time. This helps push historical connections into the `stale_connections.csv` list, allowing you to focus on the people you still talk to today.
