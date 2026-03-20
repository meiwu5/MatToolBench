"""Script to run & evaluate agent-loop on a single example from the benchmark."""
import datetime
import json
import logging
import os
import re
import time
import traceback
from trajectory_recorder import TrajectoryRecorder

logger = logging.getLogger("desktopenv.experiment")


def _write_with_retry(path: str, content: str, retries: int = 5, delay: float = 0.5) -> None:
    """Write text to a file, retrying makedirs on Azure Blob Fuse visibility delays."""
    for attempt in range(retries):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return
        except FileNotFoundError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


# Open the JSON file
with open("./settings.json", "r") as file:
    # Load the JSON data from the file
    data = json.load(file)
time_limit = data["time_limit"]

def run_single_example(agent, env, example, max_steps, instruction, args, example_result_dir, scores):
    agent.reset()
    obs = env.reset(task_config=example)
    done = False
    step_idx = 0

    #env.controller.start_recording()
    start_time = datetime.datetime.now()

    # Initialize recorder, which will save the trajectory as a JSON & HTML in {example_result_dir}/traj.(jsonl,html)
    recorder = TrajectoryRecorder(example_result_dir)

    # Record initial state
    init_timestamp = start_time.strftime("%Y%m%d@%H%M%S")
    recorder.record_init(obs, example, init_timestamp)

    # Collect per-step execution logs for code tasks (appended to eval_detail.json)
    exec_history = []

    while not done and step_idx < max_steps:
        if obs is None:
            logger.error("Observation is None. Waiting a little to do next step.")
            time.sleep(5)
            step_idx += 1
            continue

        logger.info("Agent: Thinking...")
        response, actions, logs, computer_update_args = agent.predict(
            instruction,
            obs
        )

        # update the computer object, used by navi's action space
        if computer_update_args:
            env.controller.update_computer(**computer_update_args)
        
        # step environment with agent actions 
        for action in actions:
            # Capture the timestamp before executing the action
            action_timestamp = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")
            elapsed_timestamp = f"{datetime.datetime.now() - start_time}"
            logger.info("Step %d: %s", step_idx + 1, action)
            
            obs, reward, done, info = env.step(action, args.sleep_after_execution)

            logger.info("Reward: %.2f", reward)
            logger.info("Done: %s", done)

            # Feed execution result back to CodeAgent for self-correction.
            if hasattr(agent, 'handle_action_result'):
                exec_result = info.get("exec_result") or {}
                # Use message (HTTP error) or output (HTTP success) as raw text
                raw = (exec_result.get("message", "")
                       if exec_result.get("status") == "error"
                       else exec_result.get("output", ""))
                # Parse RETURNCODE / SCRIPT_STDOUT / SCRIPT_STDERR from printed output
                _m_rc  = re.search(r"RETURNCODE:\s*(-?\d+)", raw)
                _m_out = re.search(r"SCRIPT_STDOUT:\s*(.*?)(?=SCRIPT_STDERR:|RETURNCODE:|$)", raw, re.DOTALL)
                _m_err = re.search(r"SCRIPT_STDERR:\s*(.*?)(?=RETURNCODE:|$)", raw, re.DOTALL)
                returncode = int(_m_rc.group(1)) if _m_rc else (1 if exec_result.get("status") == "error" else 0)
                stdout = _m_out.group(1).strip() if _m_out else ""
                stderr = _m_err.group(1).strip() if _m_err else (raw if exec_result.get("status") == "error" else "")
                agent.handle_action_result(stdout, stderr, returncode)
                # Save per-step execution log so it is visible in results directory
                logs["exec_log"] = (
                    f"returncode: {returncode}\n"
                    f"stdout:\n{stdout}\n"
                    f"stderr:\n{stderr}"
                )
                # Accumulate for eval_detail.json
                exec_history.append({
                    "step": step_idx + 1,
                    "returncode": returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                })
            
            # Record step data
            recorder.record_step(
                obs, 
                logs,
                step_idx,
                action_timestamp,
                elapsed_timestamp,
                action,
                reward,
                done,
                info
            )

            if done:
                logger.info("The episode is done.")
                break
        # inc step counter
        step_idx += 1
    
    logger.info("Running evaluator(s)...")
    result = env.evaluate()
    logger.info("Result: %.2f", result)
    scores.append(result)

    # Clean up code-task output files on the VM after evaluation, so stale
    # results cannot produce false-positive scores on future runs of the same task.
    env.cleanup_code_outputs()

    _write_with_retry(os.path.join(example_result_dir, "result.txt"), f"{result}\n")

    # Save detailed evaluation log
    max_score = len(env.metric) if isinstance(env.metric, list) else 1
    precision = result / max_score if max_score > 0 else 0.0
    success_rate = 1 if result >= max_score else 0
    eval_log = {
        "task_id": example.get("id", "unknown"),
        "instruction": example.get("instruction", ""),
        "total_score": result,
        "max_score": max_score,
        "precision": round(precision, 4),
        "success_rate": success_rate,
        "subtasks": getattr(env, "evaluation_details", {}).get("subtasks", []),
        "timestamp": datetime.datetime.now().isoformat(),
        # Code-task execution history: one entry per step that ran code
        "exec_history": exec_history,
    }
    _write_with_retry(os.path.join(example_result_dir, "eval_detail.json"),
                      json.dumps(eval_log, ensure_ascii=False, indent=2))
    logger.info("Evaluation detail saved to eval_detail.json")

    # Record final results
    recorder.record_end(result, start_time)
    # env.controller.end_recording(os.path.join(example_result_dir, "recording.mp4"))