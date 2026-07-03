#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_no2.py
Extrai o NO2 troposferico medio de 2024 (Sentinel-5P / S5P-PAL, L3 anual) sobre
os 15 portos do Port Traffic Explorer + 2 corredores maritimos (Gibraltar e
Dover), comparando cada porto com um background regional em anel.

Entrada:  /tmp/no2_2024.nc  (S5P-PAL, s5p-l3grd-no2-tropospheric-001-year-2024)
Saida:    data.json (medias por porto, background, razao de realce)
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from netCDF4 import Dataset

NC = "/tmp/no2_2024.nc"
HERE = Path(__file__).resolve().parent

# lon, lat (mesmos portos do explorer) + corredores
ALVOS = {
    "Rotterdam":      (4.05, 51.98),
    "Antwerp-Bruges": (3.85, 51.35),
    "Hamburg":        (9.90, 53.53),
    "Bremerhaven":    (8.52, 53.58),
    "Valencia":       (-0.30, 39.44),
    "Algeciras":      (-5.40, 36.10),
    "Barcelona":      (2.17, 41.34),
    "Piraeus":        (23.60, 37.93),
    "Marseille":      (5.33, 43.32),
    "HAROPA":         (0.12, 49.47),
    "Genova":         (8.90, 44.39),
    "Gioia Tauro":    (15.90, 38.44),
    "Sines":          (-8.88, 37.94),
    "Constanta":      (28.68, 44.13),
    "Gdansk":         (18.70, 54.42),
    "Strait of Gibraltar": (-5.60, 35.95),
    "Strait of Dover":     (1.45, 50.95),
}
CORREDORES = {"Strait of Gibraltar", "Strait of Dover"}
URBANOS = {"Rotterdam", "Antwerp-Bruges", "Hamburg", "Valencia", "Barcelona",
           "Piraeus", "Marseille", "Genova", "HAROPA"}

R_PORTO = 0.15    # meia-janela do porto (graus) ~ 15 km
R_BG1, R_BG2 = 0.6, 1.2   # anel de background (60-120 km)

ds = Dataset(NC)
# localiza variaveis (nomes do produto PAL)
print("variaveis:", list(ds.variables.keys())[:20])
lats = ds.variables["latitude"][:]
lons = ds.variables["longitude"][:]
var_name = None
for cand in ["tropospheric_NO2_column_number_density",
             "nitrogendioxide_tropospheric_column"]:
    if cand in ds.variables:
        var_name = cand
        break
if var_name is None:
    var_name = [v for v in ds.variables
                if "no2" in v.lower() or "nitrogen" in v.lower()][0]
print("usando variavel:", var_name)
v = ds.variables[var_name]

def media_caixa(lon0, lat0, r_in, r_out=None):
    """media na caixa (r_out=None) ou no anel r_in..r_out"""
    r = r_out if r_out else r_in
    i0, i1 = np.searchsorted(lats, [lat0 - r, lat0 + r])
    j0, j1 = np.searchsorted(lons, [lon0 - r, lon0 + r])
    bloco = v[0, i0:i1, j0:j1] if v.ndim == 3 else v[i0:i1, j0:j1]
    bloco = np.ma.masked_invalid(bloco)
    if r_out:  # anel: mascara o miolo
        la = lats[i0:i1][:, None]; lo = lons[j0:j1][None, :]
        miolo = (np.abs(la - lat0) < r_in) & (np.abs(lo - lon0) < r_in)
        bloco = np.ma.masked_where(miolo, bloco)
    return float(bloco.mean()) if bloco.count() else None

res = []
for nome, (lon, lat) in ALVOS.items():
    porto = media_caixa(lon, lat, R_PORTO)
    bg = media_caixa(lon, lat, R_BG1, R_BG2)
    if porto is None or bg is None or bg <= 0:
        continue
    res.append({
        "name": nome,
        "kind": ("lane" if nome in CORREDORES else
                 "urban" if nome in URBANOS else "clean"),
        "no2_port": porto,
        "no2_background": bg,
        "enhancement_pct": round((porto / bg - 1) * 100, 1),
    })

# normaliza unidades para 1e15 molec/cm2 (fator tipico: mol/m2 -> x6.02214e19/1e15)
unit = getattr(v, "units", "?")
fator = 6.02214e19 / 1e15 if "mol" in unit and "m-2" in unit.replace("/", "-") else 1.0
for r in res:
    r["no2_port_1e15"] = round(r["no2_port"] * fator, 2)
    r["no2_background_1e15"] = round(r["no2_background"] * fator, 2)
    del r["no2_port"], r["no2_background"]

res.sort(key=lambda x: -x["enhancement_pct"])
payload = {
    "meta": {
        "source": "Copernicus Sentinel-5P TROPOMI, S5P-PAL L3 yearly grid, "
                  "tropospheric NO2 column, 2024 annual mean",
        "units": "1e15 molecules/cm2",
        "method": f"port = mean in ±{R_PORTO}° box; background = ring "
                  f"{R_BG1}–{R_BG2}°; enhancement = port/background - 1",
        "native_units": unit,
    },
    "targets": res,
}
(HERE / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8")
for r in res:
    print(f"{r['name']:22} {r['kind']:6} porto={r['no2_port_1e15']:6.2f} "
          f"bg={r['no2_background_1e15']:6.2f}  +{r['enhancement_pct']}%")
