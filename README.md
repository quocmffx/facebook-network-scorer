# facebook-network-scorer

[English](README.md) | [Tiếng Việt](README.vi.md)

Score your Facebook social graph based on real interaction signals.

Quiet tools for noisy systems. Local-first and privacy-safe.

Analyzes a Facebook / Meta **"Download Your Information"** JSON export and produces per-friend scores using:

- **Signal strength** - messages, comments, reactions weighted by channel
- **Noise filtering** - one-sided spam, short tags, page reactions
- **Time decay** - exponential decay with configurable half-life
- **Context drift** - detects connections that have gone stale over time
- **Bidirectional scoring** - rewards genuine two-way conversations

## Quick start

```bash
pip install -r requirements.txt
fb-network-scorer /path/to/facebook-export --output ./scored_output
```

Or check the integrity of your export data:

```bash
fb-network-scorer doctor /path/to/facebook-export
```

*(Note: The `doctor` command only verifies directory paths and metadata. It does not scan the contents of your private messages).*

## Export Facebook Data

Before running the scorer you need a Facebook JSON export.

See **[docs/export-facebook-data.md](docs/export-facebook-data.md)** for the full step-by-step guide covering:

- Which categories to select (Friends, Messages, Comments, Reactions, ...)
- Format settings (JSON, Low quality, date range)
- Privacy boundaries and what to never commit

## Output

| File | Description |
|---|---|
| `current_friends_scored.csv` | All current friends with scores |
| `current_friends_keep.csv` | Active, multi-channel connections |
| `current_friends_review.csv` | Weak or ambiguous connections |
| `current_friends_stale.csv` | Dormant / drifted connections |
| `unknown_no_signal.csv` | Insufficient data to classify |
| `non_friend_contacts.csv` | Pages, groups, non-friend contacts |

## Project structure

```
fb_network_scorer/
  __init__.py       # Package metadata
  __main__.py       # CLI entry point wrapper
  cli.py            # CLI argument parsing
  config.py         # All tunable scoring parameters
  models.py         # Data structures
  parser.py         # Facebook JSON parser (handles mojibake)
  scorer.py         # Scoring engine with time decay + context drift
  exporter.py       # CSV export with classification splits

examples/
  sample_export/    # Fake data for testing

docs/
  export-facebook-data.md   # Facebook export guide
  vi/                       # Vietnamese documentation
```

## Privacy Boundaries

> **Warning:** Privacy boundaries are absolute. Never commit real Facebook export data, real CSV outputs, or real names to this repository.

Your personal data remains strictly on your local machine. There is no cloud service, no upload flow, and data never leaves your device. The `.gitignore` is configured to exclude Facebook exports and scorer output by default.

Read more in [docs/privacy.md](docs/privacy.md).

## License

[MIT](LICENSE)

## Links

- Homepage: [greenjade.net](https://greenjade.net)
