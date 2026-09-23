# Merged dataset manifest (generated 2026-09-23)

Run `python cv-model/scripts/merge_datasets.py` to regenerate local copies (not committed — see `cv-model/.gitignore`).

## Split (seed=42, ratios 70/20/10)

| Split | Full 6-class | PPE v1 4-class |
|-------|-------------|----------------|
| train | 8,883 | 8,765 |
| val   | 2,538 | 2,504 |
| test  | 1,270 | 1,253 |
| **total images** | **12,691** | **12,522** |

## Label instances (full 6-class merge)

| Class | Instances |
|-------|-----------|
| helmet | 26,214 |
| no-helmet | 7,677 |
| vest | 6,265 |
| no-vest | 1,757 |
| person | 1,763 |
| machinery | 787 |

## YAML paths

- Week 2 MVP: `datasets/merged_ppe_v1/data.yaml`
- Week 4+ (machinery/person): `datasets/merged/data.yaml`
