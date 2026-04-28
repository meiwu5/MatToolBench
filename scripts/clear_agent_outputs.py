"""
Delete all blobs under agent_outputs/ in parallel.

Usage:
    python scripts/clear_agent_outputs.py
    python scripts/clear_agent_outputs.py --prefix agent_outputs/Experiment1
    python scripts/clear_agent_outputs.py --dry-run

Reads AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY, and AZURE_STORAGE_CONTAINER
from config.json at the repository root.
"""

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from azure.storage.blob import BlobServiceClient

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_PREFIX = "azureml"
MAX_WORKERS = 32

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def load_config() -> dict:
    cfg_path = REPO_ROOT / "config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"config.json not found at {cfg_path}")
    with open(cfg_path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default=DEFAULT_PREFIX, help="Blob prefix to delete")
    parser.add_argument("--dry-run", action="store_true", help="List blobs without deleting")
    args = parser.parse_args()

    cfg = load_config()
    account_name = cfg["AZURE_STORAGE_ACCOUNT"]
    account_key = cfg["AZURE_STORAGE_KEY"]
    container = cfg["AZURE_STORAGE_CONTAINER"]

    client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=account_key,
    )
    container_client = client.get_container_client(container)

    logging.info(f"Listing blobs under '{args.prefix}' ...")
    blobs = [b.name for b in container_client.list_blobs(name_starts_with=args.prefix)]
    logging.info(f"Found {len(blobs)} blobs.")

    if not blobs:
        return

    if args.dry_run:
        for name in blobs:
            print(name)
        return

    deleted = 0
    failed = 0

    def delete_blob(name):
        container_client.delete_blob(name)
        return name

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(delete_blob, name): name for name in blobs}
        for future in as_completed(futures):
            try:
                future.result()
                deleted += 1
                if deleted % 100 == 0:
                    logging.info(f"  Deleted {deleted}/{len(blobs)} ...")
            except Exception as e:
                failed += 1
                logging.error(f"Failed to delete {futures[future]}: {e}")

    logging.info(f"Done. Deleted {deleted}, failed {failed}.")


if __name__ == "__main__":
    main()
