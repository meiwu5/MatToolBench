"""
Sync Azure ML agent_outputs to a local folder.

Usage:
    python scripts/sync_results.py --local_dir ./results_local
    python scripts/sync_results.py --local_dir ./results_local --interval 60
    python scripts/sync_results.py --local_dir ./results_local --once   # single sync, no loop
    python scripts/sync_results.py --local_dir ./results_local --exp_name exp0  # filter by exp
    python scripts/sync_results.py --local_dir ./results_local --remote_path Experiment1/pyautogui/screenshot/claude-sonnet-4-6-cc/0
"""

import os
import json
import time
import argparse
import logging
from pathlib import Path

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


def sync_once(ws, local_dir: Path, exp_filter: str = None, remote_path: str = None, skip_screenshots: bool = False):
    client, container_name = get_blob_service_client(ws)
    container_client = client.get_container_client(container_name)

    if remote_path:
        # Strip leading/trailing slashes and build exact prefix
        prefix = REMOTE_BASE + "/" + remote_path.strip("/") + "/"
    else:
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

        # skip screenshots if requested
        if skip_screenshots and Path(rel_path).suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
            continue

        local_path = local_dir / rel_path

        # skip if local file already exists
        if local_path.exists():
            continue

        # If any ancestor path is a file (stale placeholder), remove it
        for parent in reversed(local_path.parents):
            if parent.is_file():
                logging.warning(f"Removing stale file that blocks directory creation: {parent}")
                parent.unlink()
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob_client = container_client.get_blob_client(blob.name)
        downloaded = False
        for attempt in range(1, 4):
            try:
                with open(local_path, "wb") as f:
                    data = blob_client.download_blob(max_concurrency=4)
                    data.readinto(f)
                downloaded = True
                break
            except Exception as e:
                local_path.unlink(missing_ok=True)
                if attempt < 3:
                    logging.warning(f"  Download attempt {attempt} failed for {rel_path}: {e}, retrying...")
                    time.sleep(2 ** attempt)
                else:
                    logging.error(f"  Failed to download {rel_path} after 3 attempts: {e}")
        if downloaded:
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
    parser.add_argument("--remote_path", default="", help="Only sync a specific sub-path under agent_outputs/ (e.g. Experiment1)")
    parser.add_argument("--skip_screenshots", action="store_true", help="Skip image files (png/jpg) to speed up sync")
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
    remote_path = args.remote_path or None

    if args.once:
        sync_once(ws, local_dir, exp_filter, remote_path, args.skip_screenshots)
        return

    logging.info(f"Starting continuous sync every {args.interval}s. Press Ctrl+C to stop.")
    while True:
        try:
            logging.info("Syncing...")
            sync_once(ws, local_dir, exp_filter, remote_path, args.skip_screenshots)
        except Exception as e:
            logging.error(f"Sync error: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
