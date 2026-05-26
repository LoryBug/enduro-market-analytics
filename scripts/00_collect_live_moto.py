import csv
import importlib.util
import os
import time
from datetime import date, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COLLECTOR_PATH = PROJECT_ROOT / "scripts" / "00_collect_wayback_moto.py"

spec = importlib.util.spec_from_file_location("moto_collector", COLLECTOR_PATH)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def load_existing_rows():
    if not collector.OUTPUT_PATH.exists():
        return []
    with collector.OUTPUT_PATH.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main():
    rows = load_existing_rows()
    seen = {(row.get("snapshot_date"), row.get("url")) for row in rows}

    snapshot_date = os.getenv("LIVE_SNAPSHOT_DATE", date.today().isoformat())
    timestamp = datetime.fromisoformat(snapshot_date).strftime("%Y%m%d000000")

    targets = collector.expanded_target_urls()
    start_target = int(os.getenv("START_TARGET", "0"))
    max_targets = os.getenv("MAX_TARGETS")
    targets = targets[start_target:]
    if max_targets:
        targets = targets[: int(max_targets)]

    added = 0
    for offset, target_url in enumerate(targets, start=start_target):
        print(f"[{offset}] Live Moto.it page {target_url}", flush=True)
        try:
            page = collector.fetch_text(target_url, timeout=20, retries=1)
            live_rows = collector.parse_archive_page(page, timestamp, target_url, target_url)
            print(f"  {len(live_rows)} listings")
            for row in live_rows:
                row["snapshot_date"] = snapshot_date
                row["source"] = "moto.it-live"
                key = (row["snapshot_date"], row["url"])
                if key not in seen:
                    seen.add(key)
                    rows.append(row)
                    added += 1
            collector.save_rows(rows)
            time.sleep(0.8)
        except Exception as exc:
            print(f"  live fetch/parse failed: {exc}")

    collector.save_rows(rows)
    print(f"Added {added} live real rows")
    print(f"Saved {len(rows)} total real rows to {collector.OUTPUT_PATH}")


if __name__ == "__main__":
    main()
