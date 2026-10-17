# Attributing the FY2026 Federal Deficit to the 2025 Reconciliation Act

Working paper and replication code. How much of the FY2026 U.S. federal deficit, and of its increase over FY2025, traces to the 2025 reconciliation act (P.L. 119-21)? Sources: Treasury, CBO, JCT and BEA.

Read it at https://amandoti.win/fy26-deficit.html

## Contents

| Path | What it is |
|---|---|
| `paper.md` | Source text of the paper |
| `paper.pdf` | PDF version |
| `model/fy26_model.py` | Model: recomputes every result and chart |
| `inputs_sourced.csv` | Every input with its source and page or table reference |
| `results.json` | Model output |
| `charts/` | Figures used in the paper |

## Reproduce

```bash
pip install matplotlib
python3 model/fy26_model.py
```

The script rewrites `results.json`, `inputs_sourced.csv` and `charts/`, and stops with an error if the bridge does not sum to the FY2026 deficit. Inputs are copied from the cited CBO, JCT, Treasury and BEA publications and are listed with their sources in `inputs_sourced.csv`.

## License

Text and charts: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code: MIT, see `LICENSE`.

Copyright 2026 ncx, amandoti.win.
