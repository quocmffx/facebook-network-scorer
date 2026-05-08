"""
Main entry point for Facebook Network Scorer.

Usage:
    python -m fb_network_scorer <export_root> [--output <output_dir>]

Example:
    python -m fb_network_scorer . --output ./output
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from .config import ScoringConfig
from .exporter import export_all
from .parser import (
    detect_owner_name,
    parse_comments,
    parse_friends,
    parse_messages,
    parse_reactions,
)
from .scorer import ScoringEngine


def setup_logging() -> None:
    """Configure logging with timestamps and levels."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Facebook Network Connection Scorer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Reads a Facebook "Download Your Information" export and scores
the strength of each friend connection based on real interaction signals.

Output files:
  fb_friend_score.csv    - All contacts with scores
  keep.csv               - Active, multi-channel connections
  review.csv             - Weak or unclear connections
  stale_connections.csv  - Dormant/drifted connections
  unknown_no_signal.csv  - Insufficient data to classify
        """,
    )
    parser.add_argument(
        "export_root",
        type=Path,
        help="Path to Facebook export root directory",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output directory for CSV files (default: <export_root>/scored_output)",
    )
    args = parser.parse_args()

    export_root: Path = args.export_root.resolve()
    output_dir: Path = args.output or (export_root / "scored_output")

    if not export_root.exists():
        logger.error("Export root does not exist: %s", export_root)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Facebook Network Scorer")
    logger.info("Export root: %s", export_root)
    logger.info("Output dir:  %s", output_dir)
    logger.info("=" * 60)

    start_time = time.monotonic()

    # Step 1: Detect owner
    owner_name = detect_owner_name(export_root)
    if owner_name:
        logger.info("Detected account owner: %s", owner_name)
    else:
        logger.warning("Could not auto-detect owner name. Message scoring may be inaccurate.")

    config = ScoringConfig(owner_name=owner_name)
    engine = ScoringEngine(config)

    # Step 2: Parse friends
    logger.info("--- Parsing friends ---")
    friends = parse_friends(export_root)
    engine.ingest_friends(friends)

    # Step 3: Parse messages (streaming)
    logger.info("--- Parsing messages ---")
    msg_count = 0
    for thread in parse_messages(export_root):
        engine.ingest_messages(thread)
        msg_count += 1
        if msg_count % 10 == 0:
            logger.info("  Processed %d message threads...", msg_count)
    logger.info("  Total message threads processed: %d", msg_count)

    # Step 4: Parse comments
    logger.info("--- Parsing comments ---")
    comments = parse_comments(export_root)
    engine.ingest_comments(comments)

    # Step 5: Parse reactions
    logger.info("--- Parsing reactions ---")
    reactions = parse_reactions(export_root)
    engine.ingest_reactions(reactions)

    # Step 6: Compute scores
    logger.info("--- Computing scores ---")
    scores = engine.compute_scores()

    # Step 7: Export
    logger.info("--- Exporting results ---")
    export_all(scores, output_dir)

    elapsed = time.monotonic() - start_time
    logger.info("Done in %.1f seconds", elapsed)


if __name__ == "__main__":
    main()
