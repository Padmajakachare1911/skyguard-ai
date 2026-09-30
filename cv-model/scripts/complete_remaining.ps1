# Regenerate CV track reports after training (from repo root).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)

$Py = if (Test-Path ".\.venv-gpu\Scripts\python.exe") { ".\.venv-gpu\Scripts\python.exe" } else { "python" }

& $Py cv-model\scripts\record_val_metrics.py --model cv-model/models/full_v1/best.pt --data cv-model/datasets/merged/data.yaml --title "Week 4 — full_v1" --issue "#32" --out cv-model/reports/week4_full_v1_metrics.md
& $Py cv-model\scripts\record_val_metrics.py --model cv-model/models/full_v2/best.pt --data cv-model/datasets/merged/data.yaml --title "Week 5 — full_v2" --issue "#39" --out cv-model/reports/week5_full_v2_metrics.md
& $Py cv-model\scripts\hard_conditions_eval.py --model cv-model/models/full_v2/best.pt --out cv-model/reports/week5_hard_conditions_metrics.md

Push-Location cv-model
& $Py -m inference.infer_live --model models/full_v2/best.pt --source datasets/proxy/construction_sample.mp4 --no-display --max-seconds 30 --output reports/live_violations.jsonl
& $Py -m inference.eval_footage --model models/full_v2/best.pt --images datasets/merged/test/images --labels datasets/merged/test/labels --report reports/week9_fp_fn_summary.md --csv reports/week9_fp_fn.csv
& $Py -m inference.infer_pi --video datasets/proxy/construction_sample.mp4 --model models/full_v2/best.pt --gps stub --imgsz 416
& $Py -m inference.run_matrix --config datasets/proxy/matrix_config.json --model models/full_v2/best.pt
& $Py -m pytest tests/ -v
Pop-Location

Write-Host "Reports refreshed under cv-model/reports/" -ForegroundColor Green
