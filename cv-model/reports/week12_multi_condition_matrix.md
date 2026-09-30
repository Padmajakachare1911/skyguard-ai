# SIMULATED/PROXY — not real flight data
## Multi-condition matrix

| Time | Lighting | Altitude | Occlusion | Violation | Clip | Result |
|---|---|---|---|---|---|---|
| midday | bright | low | none | no-helmet | `datasets\proxy\construction_sample.mp4` | PASS |
| midday | bright | low | none | no-vest | `datasets\proxy\construction_sample.mp4` | PASS |
| midday | bright | low | none | machinery-proximity | `datasets\proxy\construction_sample.mp4` | PASS |
| dusk | backlit | high | partial | person-down | `datasets\proxy\missing_dusk_clip.mp4` | NOT TESTED — no footage |
| morning | overcast | medium | none | restricted-zone-entry | `datasets\proxy\construction_sample.mp4` | FAIL (no detection) |
