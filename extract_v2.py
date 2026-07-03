#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extração otimizada: lê UMA vez o recorte da Europa e calcula em memória."""
import json
import numpy as np
from netCDF4 import Dataset
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALVOS = {
    "Rotterdam": (4.05, 51.98), "Antwerp-Bruges": (3.85, 51.35),
    "Hamburg": (9.90, 53.53), "Bremerhaven": (8.52, 53.58),
    "Valencia": (-0.30, 39.44), "Algeciras": (-5.40, 36.10),
    "Barcelona": (2.17, 41.34), "Piraeus": (23.60, 37.93),
    "Marseille": (5.33, 43.32), "HAROPA": (0.12, 49.47),
    "Genova": (8.90, 44.39), "Gioia Tauro": (15.90, 38.44),
    "Sines": (-8.88, 37.94), "Constanta": (28.68, 44.13),
    "Gdansk": (18.70, 54.42),
    "Strait of Gibraltar": (-5.60, 35.95), "Strait of Dover": (1.45, 50.95),
}
CORREDORES = {"Strait of Gibraltar", "Strait of Dover"}
URBANOS = {"Rotterdam", "Antwerp-Bruges", "Hamburg", "Valencia", "Barcelona",
           "Piraeus", "Marseille", "Genova", "HAROPA"}
R_P, R_B1, R_B2 = 0.15, 0.6, 1.2

ds = Dataset("/tmp/no2_2024.nc")
lats = ds.variables["latitude"][:]
lons = ds.variables["longitude"][:]
v = ds.variables["tropospheric_NO2_column_number_density"]
unit = getattr(v, "units", "?")
print("grade:", len(lats), "x", len(lons), "| unidade:", unit, "| dims:", v.shape, flush=True)

i0, i1 = np.searchsorted(lats, [33.0, 57.0])
j0, j1 = np.searchsorted(lons, [-11.0, 31.0])
print("recorte:", i1 - i0, "x", j1 - j0, flush=True)
sub = v[0, i0:i1, j0:j1] if v.ndim == 3 else v[i0:i1, j0:j1]
sub = np.ma.masked_invalid(np.asarray(sub, dtype="float64"))
sla, slo = lats[i0:i1], lons[j0:j1]
print("recorte carregado, células válidas:", int(sub.count()), flush=True)

def caixa(lon0, lat0, r_in, r_out=None):
    r = r_out if r_out else r_in
    a0, a1 = np.searchsorted(sla, [lat0 - r, lat0 + r])
    b0, b1 = np.searchsorted(slo, [lon0 - r, lon0 + r])
    bloco = sub[a0:a1, b0:b1]
    if r_out:
        la = sla[a0:a1][:, None]; lo = slo[b0:b1][None, :]
        bloco = np.ma.masked_where(
            (np.abs(la - lat0) < r_in) & (np.abs(lo - lon0) < r_in), bloco)
    return float(bloco.mean()) if bloco.count() else None

# conversão para 1e15 moléculas/cm²: µmol/m² x 6.02214e17 molec/µmol / 1e4 cm²/m² / 1e15
if unit.strip().lower().startswith("umol"):
    fator = 6.02214e17 / 1e4 / 1e15      # = 0.0602214
elif unit.strip().lower().startswith("mol"):
    fator = 6.02214e23 / 1e4 / 1e15
else:
    fator = 1.0
res = []
for nome, (lon, lat) in ALVOS.items():
    p = caixa(lon, lat, R_P)
    b = caixa(lon, lat, R_B1, R_B2)
    if p is None or b is None or b <= 0:
        continue
    res.append({
        "name": nome,
        "kind": ("lane" if nome in CORREDORES else
                 "urban" if nome in URBANOS else "clean"),
        "no2_port_1e15": round(p * fator, 2),
        "no2_background_1e15": round(b * fator, 2),
        "enhancement_pct": round((p / b - 1) * 100, 1),
    })
res.sort(key=lambda x: -x["enhancement_pct"])
payload = {
    "meta": {
        "source": "Copernicus Sentinel-5P TROPOMI, S5P-PAL L3 yearly grid, "
                  "tropospheric NO2 column, 2024 annual mean",
        "units": "1e15 molecules/cm2", "native_units": unit,
        "method": f"port = ±{R_P}° box (~15 km); background = ring "
                  f"{R_B1}–{R_B2}° (~60–120 km); enhancement = port/background - 1",
    },
    "targets": res,
}
(HERE / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8")
for r in res:
    print(f"{r['name']:22} {r['kind']:6} porto={r['no2_port_1e15']:6.2f} "
          f"bg={r['no2_background_1e15']:6.2f}  +{r['enhancement_pct']}%")
print("FIM", flush=True)
