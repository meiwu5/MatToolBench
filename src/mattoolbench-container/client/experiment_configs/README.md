# Experiment Configs

All JSON files here are passed to `run.py` via `--config <file>`.

---

## Main Experiment — LLM Comparison

Tests different LLMs on the full MatToolBench across all task types (GUI, Origin, Code).
Run with: `bash scripts/run_main.sh`

| Config file                    | Model                  | Task set  |
|-------------------------------|------------------------|-----------|
| `main_gpt_5.json`            | GPT-4o                 | All tasks |
| `main_gpt_5_mini.json`       | GPT-4o-mini            | All tasks |
| `main_claude_sonnet_4_6.json` | Claude Sonnet 4.6      | All tasks |
| `main_qwen_max.json`          | Qwen-Max               | All tasks |
| `main_gemini_1.5_pro.json`    | Gemini 1.5 Pro         | All tasks |

---

## Ablation Study — Key Parameters

Uses GPT-4o as the backbone. Tests two key parameters.
Run with: `bash scripts/run_ablations.sh`

### Dimension 1 — Origin Template Script

Tests whether injecting a pre-written domain-specific script into the OriginAgent system
prompt improves task success on Origin plotting tasks.

| Config file                      | Setting                          |
|---------------------------------|----------------------------------|
| `ablation_origin_script.json`   | OriginAgent + template script    |
| `ablation_origin_noscript.json` | OriginAgent without script       |

### Dimension 2 — GUI Screen Parser (SoM mode)

Tests which screen-parsing strategy works best for materials-science GUI tasks.

| Config file                    | SoM mode    | Description                      |
|-------------------------------|-------------|----------------------------------|
| `ablation_gui_som_oss.json`   | `oss`       | OCR-only (default baseline)      |
| `ablation_gui_som_a11y.json`  | `a11y`      | Accessibility tree               |
| `ablation_gui_som_mixed.json` | `mixed-oss` | OCR + accessibility (merged)     |
| `ablation_gui_som_omni.json`  | `omni`      | OmniParser visual grounding      |
| `ablation_gui_som_no_omni.json` | `no_omni` | Raw screenshots + coordinate clicks |

---

## Notes

- `max_steps` implicitly controls how many self-correction rounds the CodeAgent can attempt
  (each failed execution + retry counts as one step). There is no separate `code_retries`
  parameter — agents use `max_steps` consistently across all agent types.
- `temperature: 0.0` is used for all main and ablation experiments to ensure reproducibility.
- Results are written to `./results/<config_name>/scores_summary.csv`.
- Aggregate results: `python scripts/print_results.py --prefix main_` or `--prefix ablation_`
