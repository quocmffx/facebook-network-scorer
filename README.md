# facebook-network-scorer

Score your Facebook social graph based on real interaction signals.

Analyzes a Facebook / Meta **"Download Your Information"** JSON export and produces per-friend scores using:

- **Signal strength** - messages, comments, reactions weighted by channel
- **Noise filtering** - one-sided spam, short tags, page reactions
- **Time decay** - exponential decay with configurable half-life
- **Context drift** - detects connections that have gone stale over time
- **Bidirectional scoring** - rewards genuine two-way conversations

## Quick start

```bash
pip install -r requirements.txt
python -m fb_network_scorer /path/to/facebook-export --output ./scored_output
```

## Export Facebook Data

Before running the scorer you need a Facebook JSON export.

See **[docs/export-facebook-data.md](docs/export-facebook-data.md)** for the full step-by-step guide covering:

- Which categories to select (Friends, Messages, Comments, Reactions, ...)
- Format settings (JSON, Low quality, date range)
- Privacy rules and what to never commit

## Output

| File | Description |
|---|---|
| `current_friends_scored.csv` | All current friends with scores |
| `current_friends_keep.csv` | Active, multi-channel connections |
| `current_friends_review.csv` | Weak or ambiguous connections |
| `current_friends_stale.csv` | Dormant / drifted connections |
| `non_friend_contacts.csv` | Pages, groups, non-friend contacts |

## Project structure

```
fb_network_scorer/
  __init__.py       # Package metadata
  __main__.py       # CLI entry point
  config.py         # All tunable scoring parameters
  parser.py         # Facebook JSON parser (handles mojibake)
  scorer.py         # Scoring engine with time decay + context drift
  exporter.py       # CSV export with classification splits

examples/
  sample_export/    # Fake data for testing
  sample_output/    # Example scored output

docs/
  export-facebook-data.md   # Facebook export guide
```

## Privacy

> **Warning:** Never commit real Facebook export data, real CSV outputs, or real names to this repository.

The `.gitignore` is configured to exclude Facebook exports and scorer output by default. See the [export guide](docs/export-facebook-data.md#privacy-checklist) for details.

## License

[MIT](LICENSE)

## Links

- Homepage: [greenjade.net](https://greenjade.net)
