"""
Sync Azure ML agent_outputs to a local folder.

Usage:
    python scripts/sync_results.py --local_dir ./results_local
    python scripts/sync_results.py --local_dir ./results_local --interval 60
    python scripts/sync_results.py --local_dir ./results_local --once   # single sync, no loop
    python scripts/sync_results.py --local_dir ./results_local --exp_name exp0  # filter by exp
"""

import os
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

from azureml.core import Workspace, Datastore
from azureml.core.authentication import AzureCliAuthentication
from azure.storage.blob import BlobServiceClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

REMOTE_BASE = "agent_outputs"


def load_config():
    config_path = Path(__file__).parent.parent / "config.json"
    with config_path.open("r") as f:
        return json.load(f)


def get_blob_service_client(ws):
    datastore = Datastore.get(ws, "workspaceblobstore")
    account_name = datastore.account_name
    account_key = datastore.account_key
    container_name = datastore.container_name
    url = f"https://{account_name}.blob.core.windows.net"
    client = BlobServiceClient(account_url=url, credential=account_key)
    return client, container_name


def sync_once(ws, local_dir: Path, exp_filter: str = None):
    client, container_name = get_blob_service_client(ws)
    container_client = client.get_container_client(container_name)

    prefix = REMOTE_BASE + "/"
    blobs = list(container_client.list_blobs(name_starts_with=prefix))

    if exp_filter:
        blobs = [b for b in blobs if exp_filter in b.name]

    new_count = 0
    for blob in blobs:
        # relative path after agent_outputs/
        rel_path = blob.name[len(prefix):]

        # skip directory marker blobs (empty blobs with no file extension, or trailing slash)
        if not rel_path or rel_path.endswith("/") or (blob.size == 0 and "." not in Path(rel_path).name):
            continue

        local_path = local_dir / rel_path

        # skip if local file is already up-to-date
        if local_path.exists():
            local_mtime = datetime.utcfromtimestamp(local_path.stat().st_mtime)
            # blob.last_modified is timezone-aware; make naive for comparison
            blob_mtime = blob.last_modified.replace(tzinfo=None)
            if local_mtime >= blob_mtime and local_path.stat().st_size == blob.size:
                continue

        # If any ancestor path is a file (stale placeholder), remove it
        for parent in reversed(local_path.parents):
            if parent.is_file():
                logging.warning(f"Removing stale file that blocks directory creation: {parent}")
                parent.unlink()
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob_client = container_client.get_blob_client(blob.name)
        with open(local_path, "wb") as f:
            data = blob_client.download_blob()
            data.readinto(f)
        new_count += 1
        logging.info(f"  Downloaded: {rel_path}")

    logging.info(f"Sync complete — {new_count} new/updated file(s), {len(blobs)} total blobs checked.")
    return new_count


def main():
    parser = argparse.ArgumentParser(description="Sync Azure ML results to local folder.")
    parser.add_argument("--local_dir", default="./results_local", help="Local destination folder")
    parser.add_argument("--interval", type=int, default=30, help="Sync interval in seconds (default: 30)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--exp_name", default="", help="Filter blobs by experiment name")
    args = parser.parse_args()

    local_dir = Path(args.local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Local results dir: {local_dir.resolve()}")

    config = load_config()
    cli_auth = AzureCliAuthentication()
    ws = Workspace(
        subscription_id=config["AZURE_SUBSCRIPTION_ID"],
        resource_group=config["AZURE_ML_RESOURCE_GROUP"],
        workspace_name=config["AZURE_ML_WORKSPACE_NAME"],
        auth=cli_auth,
    )
    logging.info(f"Connected to workspace: {ws.name}")

    exp_filter = args.exp_name or None

    if args.once:
        sync_once(ws, local_dir, exp_filter)
        return

    logging.info(f"Starting continuous sync every {args.interval}s. Press Ctrl+C to stop.")
    while True:
        try:
            logging.info("Syncing...")
            sync_once(ws, local_dir, exp_filter)
        except Exception as e:
            logging.error(f"Sync error: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
