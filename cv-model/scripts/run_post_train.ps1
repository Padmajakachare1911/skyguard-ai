# Post-training reports and proxy evals (run after full_v2/best.pt exists).
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
$Py = Join-Path $Root ".venv-gpu\Scripts\python.exe"

if (-not (Test-Path "cv-model\models\full_v2\best.pt")) {
    Write-Error "Missing cv-model\models\full_v2\best.pt — finish training first."
}

& $Py cv-model\scripts\record_val_metrics.py `
    --model cv-model/models/full_v1/best.pt `
    --data cv-model/datasets/merged/data.yaml `
    --title "Week 4 — full_v1" --issue "#32" `
    --out cv-model/reports/week4_full_v1_metrics.md

& $Py cv-model\scripts\hard_conditions_eval.py `
    --model cv-model/models/full_v2/best.pt `
    --out cv-model/reports/week5_hard_conditions_metrics.md

& $Py -m cv-model.inference.infer_video `
    --video cv-model/datasets/proxy/construction_sample.mp4 `
    --model cv-model/models/full_v2/best.pt `
    --output cv-model/reports/sample_violations.jsonl `
    --annotated-out cv-model/reports/annotated_output.mp4

Push-Location cv-model
& $Py -m inference.infer_live `
    --model models/full_v2/best.pt `
    --source datasets/proxy/construction_sample.mp4 `
    --no-display --max-seconds 30 `
    --output reports/live_violations.jsonl

& $Py -m inference.eval_footage `
    --footage datasets/proxy/construction_sample.mp4 `
    --images datasets/merged/test/images `
    --labels datasets/merged/test/labels `
    --model models/full_v2/best.pt

& $Py -m inference.infer_pi `
    --video datasets/proxy/construction_sample.mp4 `
    --model models/full_v2/best.pt --gps stub --imgsz 416

& $Py -m inference.run_matrix `
    --config datasets/proxy/matrix_config.json `
    --model models/full_v2/best.pt

& $Py -m pytest tests/ -v
Pop-Location

Write-Host "Post-train pipeline finished." -ForegroundColor Green
