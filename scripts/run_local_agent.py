"""
Run the agent locally while the Windows VM runs on Azure.
Usage:
    python run_local_agent.py --exp_name experiment_1
    python run_local_agent.py --exp_name experiment_1 --instance_ip 1.2.3.4
    python run_local_agent.py --exp_name experiment_1 --all_workers   # parallel, all workers

Prerequisites:
  - Azure job already submitted with vm_only=true (via run_azure.py --vm_only true)
  - AZURE_INSTANCE_IP set in config.json, or passed via --instance_ip
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
from multiprocessing import Process
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR / ".."
DEFAULT_PEM = REPO_ROOT / "MatToolBench.pem"
DEFAULT_CLIENT_DIR = REPO_ROOT / "src" / "mattoolbench-container" / "client"


def wait_for_port(host: str, port: int, timeout: int = 600) -> bool:
    """Poll until port is reachable or timeout (seconds)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = socket.create_connection((host, port), timeout=2)
            s.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            print(f"  Waiting for {host}:{port} ...")
            time.sleep(5)
    return False


def get_instance_ip_from_sdk(azure_config: dict, instance_name: str):
    """Try to auto-detect SSH IP from Azure ML SDK."""
    try:
        from azure.ai.ml import MLClient
        from azure.identity import DefaultAzureCredential
        ml_client = MLClient(
            DefaultAzureCredential(),
            azure_config["AZURE_SUBSCRIPTION_ID"],
            azure_config["AZURE_ML_RESOURCE_GROUP"],
            azure_config["AZURE_ML_WORKSPACE_NAME"],
        )
        ci = ml_client.compute.get(instance_name)
        # SDK v2: services dict
        if hasattr(ci, "services") and ci.services:
            for key in ("SSH", "ssh"):
                svc = ci.services.get(key)
                if svc and hasattr(svc, "endpoint"):
                    return svc.endpoint
        # SDK v2: connectivity_endpoints
        if hasattr(ci, "connectivity_endpoints"):
            ep = ci.connectivity_endpoints
            if hasattr(ep, "public_ip_address"):
                return ep.public_ip_address
    except Exception as e:
        print(f"  Auto-detect IP failed: {e}")
    return None


def _loopback_ip(worker_id: int) -> str:
    """Return a unique loopback IP for each worker (127.0.0.1, 127.0.0.2, …).

    The entire 127.0.0.0/8 block is valid loopback on Linux, so each worker
    can bind its SSH tunnel to a different IP and avoid port-5000 conflicts.
    """
    return f"127.0.0.{worker_id + 1}"


def run_single_worker(worker_id: int, exp: dict, args, azure_config: dict):
    """SSH-tunnel + local agent for one worker. Safe to call in a subprocess."""
    local_ip = _loopback_ip(worker_id)
    tag = f"[Worker {worker_id}]"

    # ── Resolve Azure instance IP ─────────────────────────────────────────────
    instance_ips = azure_config.get("AZURE_INSTANCE_IPS", [])
    instance_ip = (
        args.instance_ip
        or (instance_ips[worker_id] if worker_id < len(instance_ips) else None)
    )
    if not instance_ip:
        instance_name = f"w{worker_id}{exp['exp_name']}"
        print(f"{tag} No instance IP provided, trying Azure ML SDK for '{instance_name}'...")
        instance_ip = get_instance_ip_from_sdk(azure_config, instance_name)

    if not instance_ip:
        print(
            f"{tag} ERROR: Cannot determine instance IP.\n"
            f"  Option 1: Add AZURE_INSTANCE_IPS list to config.json (index = worker_id)\n"
            f"  Option 2: Pass --instance_ip <ip>"
        )
        sys.exit(1)

    print(f"{tag} Azure instance: {instance_ip}:{args.ssh_port}  (local {local_ip})")

    # ── Start SSH tunnel (bound to worker-specific loopback IP) ───────────────
    pem = str(Path(args.pem_path).resolve())
    tunnel_cmd = [
        "ssh",
        "-i", pem,
        "-p", str(args.ssh_port),
        "-L", f"{local_ip}:5000:localhost:5000",
        "-L", f"{local_ip}:7200:localhost:7200",
        "-N",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        f"azureuser@{instance_ip}",
    ]
    print(f"{tag} Starting SSH tunnel...")
    tunnel = subprocess.Popen(tunnel_cmd)

    try:
        # ── Wait for Windows VM ───────────────────────────────────────────────
        print(f"{tag} Waiting for Windows VM on {local_ip}:5000 (up to 10 min)...")
        if not wait_for_port(local_ip, 5000, timeout=600):
            print(f"{tag} ERROR: Timed out waiting for VM. Is the Azure job running with vm_only=true?")
            sys.exit(1)

        print(f"{tag} VM is ready! Starting local agent...\n")

        # ── Run local agent ───────────────────────────────────────────────────
        agent_cmd = [
            sys.executable, "run.py",
            "--emulator_ip",        local_ip,
            "--agent_name",         exp.get("agent", "auto"),
            "--model",              exp.get("model_name", "qwen3.5-27b"),
            "--som_origin",         exp.get("som_origin", "oss"),
            "--a11y_backend",       exp.get("a11y_backend", "uia"),
            "--num_workers",        str(exp.get("num_workers", 1)),
            "--worker_id",          str(worker_id),
            "--result_dir",         args.result_dir,
            "--test_all_meta_path", exp.get("json_name", "evaluation_examples_windows/origin.json"),
            "--origin_mode",        exp.get("origin_mode", "script"),
        ]
        subprocess.run(agent_cmd, cwd=str(DEFAULT_CLIENT_DIR))

    finally:
        print(f"\n{tag} Shutting down SSH tunnel...")
        tunnel.terminate()
        tunnel.wait()
        print(f"{tag} Done.")


def main():
    parser = argparse.ArgumentParser(description="Run local agent against Azure-hosted VM.")
    parser.add_argument("--experiments_json", default=str(SCRIPT_DIR / "experiments.json"))
    parser.add_argument("--exp_name", default="experiment_1", help="Key in experiments.json")
    parser.add_argument("--instance_ip", default=None, help="Azure instance public IP (overrides config.json)")
    parser.add_argument("--ssh_port", type=int, default=50000, help="SSH port on Azure instance (default: 50000)")
    parser.add_argument("--pem_path", default=str(DEFAULT_PEM), help="Path to .pem SSH key")
    parser.add_argument("--worker_id", type=int, default=0, help="Worker index (ignored when --all_workers is set)")
    parser.add_argument("--result_dir", default="./results")
    parser.add_argument("--all_workers", action="store_true",
                        help="Launch ALL workers in parallel (num_workers from experiments.json)")
    args = parser.parse_args()

    # ── Load configs ──────────────────────────────────────────────────────────
    with open(REPO_ROOT / "config.json") as f:
        azure_config = json.load(f)
    with open(args.experiments_json) as f:
        experiments = json.load(f)

    exp = experiments[args.exp_name]

    if args.all_workers:
        # ── Parallel mode: spawn one process per worker ───────────────────────
        num_workers = exp.get("num_workers", 1)
        print(f"Launching {num_workers} workers in parallel...")
        procs = []
        for wid in range(num_workers):
            p = Process(target=run_single_worker, args=(wid, exp, args, azure_config))
            p.start()
            procs.append(p)
        for p in procs:
            p.join()
        print("All workers finished.")
    else:
        # ── Single-worker mode (original behaviour) ───────────────────────────
        run_single_worker(args.worker_id, exp, args, azure_config)


if __name__ == "__main__":
    main()
