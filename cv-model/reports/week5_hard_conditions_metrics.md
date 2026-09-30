# Week 5 — Hard vs Clean Conditions

**Model:** `cv-model/models/full_v2/best.pt`

| Subset | Images (sampled) | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Clean (brightness > p35.0) | 825 | 0.942 | 0.831 | 0.883 |
| Hard (brightness ≤ p35.0) | 445 | 0.946 | 0.828 | 0.883 |

Hard subset uses darker test images as a proxy for low-light field conditions.
