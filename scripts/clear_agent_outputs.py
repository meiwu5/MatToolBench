"""
Delete all blobs under agent_outputs/ in parallel.

Usage:
    python scripts/clear_agent_outputs.py
    python scripts/clear_agent_outputs.py --prefix agent_outputs/Experiment1
    python scripts/clear_agent_outputs.py --dry-run
"""

import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.storage.blob import BlobServiceClient

ACCOUNT_NAME = "YOUR_AZURE_STORAGE_ACCOUNT_HERE"
ACCOUNT_KEY  = "YOUR_AZURE_STORAGE_KEY_HERE"
CONTAINER    = "YOUR_AZURE_CONTAINER_HERE"
DEFAULT_PREFIX = "agent_outputs/"
MAX_WORKERS  = 32

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default=DEFAULT_PREFIX, help="Blob prefix to delete")
    parser.add_argument("--dry-run", action="store_true", help="List blobs without deleting")
    args = parser.parse_args()

    client = BlobServiceClient(
        account_url=f"https://{ACCOUNT_NAME}.blob.core.windows.net",
        credential=ACCOUNT_KEY,
    )
    container_client = client.get_container_client(CONTAINER)

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
