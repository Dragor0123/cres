# CRES

Calibrated Relational Episode Sampling for graph few-shot node classification.

Research code, work in progress. Not ready for use.

## Environment

- Python 3.10, PyTorch 2.4.1 (CUDA 12.4), PyTorch Geometric 2.8.1
- Datasets: Amazon-Clothing, Amazon-Electronics, DBLP (GPN-format `.mat` + edge list), placed under `data/` (not tracked)

## Layout

| Path | Contents |
|---|---|
| `cres/` | CRES implementation |
| `baselines/` | Baseline adapters and re-implementations |
| `splits/` | Fixed class splits and test episodes |
| `tools/` | Analysis scripts |
| `docs/register/` | Decision records and pre-registrations |
| `instructions/`, `reports/` | Work instructions and reports |

## Acknowledgements

Parts of the backbone are adapted from [TEG](https://github.com/sung-won-kim/TEG) (MIT) and [VISION](https://github.com/KEAML-JLU/VISION) (MIT). Source files carry attribution where code is adapted.