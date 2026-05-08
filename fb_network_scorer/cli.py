"""
Command Line Interface for Facebook Network Scorer.

Supports:
  fb-network-scorer <export_root> [--output <output_dir>]
  fb-network-scorer doctor <export_root>
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

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging with timestamps and levels."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_doctor(export_root: Path) -> None:
    """
    Run diagnostic checks on the export directory.
    Validates structure and presence of expected data without scanning private content.
    """
    logger.info("=" * 60)
    logger.info("Facebook Network Scorer - DOCTOR")
    logger.info("Export root: %s", export_root)
    logger.info("=" * 60)

    if not export_root.exists():
        logger.error("[FAIL] Export root does not exist: %s", export_root)
        sys.exit(1)
    
    logger.info("[PASS] Export root exists.")

    # Check friends
    friends_path = export_root / "connections" / "friends" / "your_friends.json"
    if friends_path.exists():
        logger.info("[PASS] Friends data found.")
    else:
        logger.warning("[WARN] Friends data missing (%s).", friends_path.relative_to(export_root))

    # Check messages
    inbox_dir = export_root / "your_facebook_activity" / "messages" / "inbox"
    if inbox_dir.exists():
        logger.info("[PASS] Message inbox found.")
    else:
        logger.warning("[WARN] Message inbox missing (%s).", inbox_dir.relative_to(export_root))

    # Check comments & reactions
    activity_dir = export_root / "your_facebook_activity" / "comments_and_reactions"
    if activity_dir.exists():
        logger.info("[PASS] Comments & reactions data found.")
    else:
        logger.warning("[WARN] Comments & reactions data missing (%s).", activity_dir.relative_to(export_root))

    # Check profile info
    profile_path = export_root / "personal_information" / "profile_information" / "profile_information.json"
    if profile_path.exists():
        logger.info("[PASS] Profile information found.")
    else:
        logger.warning("[WARN] Profile information missing. Auto-detection may rely on comments.")

    logger.info("=" * 60)
    logger.info("Doctor check complete. If you see warnings, the scorer will still run but may have limited accuracy.")


def run_scorer(args: argparse.Namespace) -> None:
    """Run the main scoring pipeline."""
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
    if not friends:
        logger.warning("No current friends found in export. Network cleanup classification will be skipped.")
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


def main() -> None:
    setup_logging()

    # Handle 'doctor' command seamlessly without requiring a 'score' subparser
    if len(sys.argv) >= 2 and sys.argv[1] == "doctor":
        if len(sys.argv) < 3:
            logger.error("Usage: fb-network-scorer doctor <export_root>")
            sys.exit(1)
        export_root = Path(sys.argv[2]).resolve()
        run_doctor(export_root)
        return

    # Standard scorer argument parsing
    parser = argparse.ArgumentParser(
        description="Facebook Network Connection Scorer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Reads a Facebook "Download Your Information" export and scores
the strength of each friend connection based on real interaction signals.

Quiet tools for noisy systems. Local-first. Privacy-safe.

Commands:
  <export_root>            Run the scorer on the specified directory
  doctor <export_root>     Validate the export directory structure

Output files:
  fb_friend_score.csv      - All contacts with scores
  keep.csv                 - Active, multi-channel connections
  review.csv               - Weak or unclear connections
  stale_connections.csv    - Dormant/drifted connections
  unknown_no_signal.csv    - Insufficient data to classify
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
    run_scorer(args)
