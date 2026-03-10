# FRIB Cross Section Sensitivity

Visualizes the minimum measurable cross section for FRIB exotic beams on a chart of nuclides.

## Formula

```
σ_min = N_min / (Rate × target_thickness × beam_time)
```

| Parameter | Default |
|---|---|
| Target thickness | 10²⁰ atoms/cm² |
| Beam time | 1 week (604800 s) |
| Minimum counts (N_min) | 10⁵ |
| Rate range | 10⁴ – 10⁸ pps (clamped at upper end) |

Rates are from the **FRIB PAC3 (2024)** fast beam rate estimates, based on EPAX 3.01 (fragmentation) and LISE++ 3EER (in-flight fission).

## Files

| File | Description |
|---|---|
| `frib_gui.py` | Interactive GUI — adjust all parameters live |
| `frib_cross_section_sensitivity.py` | Static plot script |
| `FRIB_Rates.txt` | FRIB PAC3 beam rates (N, Z, pps) |

## Usage

**Interactive GUI:**
```bash
python frib_gui.py
```

**Static plot:**
```bash
python frib_cross_section_sensitivity.py
```

## Requirements

```bash
pip install numpy matplotlib pandas
```
