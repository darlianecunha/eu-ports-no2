# Seen From Space — NO₂ over Europe's Ports (Sentinel-5P, 2024)

Satellite analysis of **tropospheric NO₂ over 15 major European ports and 2 shipping lanes**,
from the Copernicus Sentinel-5P (TROPOMI) 2024 annual-mean grid produced by the ESA S5P-PAL
service. Each target is compared with its regional background: how much more NO₂ hangs over a
port than over the surrounding region?

## Headline findings (2024 annual mean)

| Finding | Value |
|---|---|
| Strait of Gibraltar (open sea, no city) | **+53.5%** NO₂ vs background — the shipping lane, visible from orbit |
| Strongest port away from cities | Algeciras: **+59.6%** |
| Strongest metropolitan port region | Piraeus/Athens: +232% (ships + city + industry) |
| Cleanest maritime signals | Algeciras, Gdansk, Constanta, Gioia Tauro, Bremerhaven, Sines |

Targets are grouped into three settings so the reader does not over-attribute: **away from
cities** (signal mostly maritime/port), **metropolitan** (city traffic and industry contribute),
and **shipping lanes** (no city at all).

## Files

| File | Purpose |
|---|---|
| `index.html` | The site (chart + full table + method) |
| `data.json` | Extracted values consumed by the page |
| `extract_v2.py` | Extraction script (netCDF4 + numpy) |
| `process_no2.py` | First version, kept for reference |

## Reproducing

1. Download the yearly L3 tropospheric NO₂ grid from the
   [S5P-PAL data portal](https://data-portal.s5p-pal.com/) (STAC API, product
   `s5p-l3grd-no2-tropospheric-001-year-*`, ~1.4 GB, no registration).
2. `pip install netCDF4 numpy`, adjust the file path in `extract_v2.py`, run it.
3. Serve locally (`python3 -m http.server`) or deploy to Vercel (framework: Other).

## Method & caveats

- Grid: 8192 × 16384 global (~0.022°), 2024 annual mean, tropospheric NO₂ column.
- Port value = mean in a ±0.15° box (~15 km); background = ring 0.6–1.2° (~60–120 km);
  enhancement = port/background − 1. Units converted from µmol/m² to 10¹⁵ molecules/cm².
- NO₂ has many sources; metropolitan enhancements must not be read as ship-only. Negative
  values are possible when the region around a port is more polluted than the port itself
  (Genova against the industrial Po basin).
- NO₂ is a co-emitted combustion tracer, not CO₂: it serves as an independent, space-based
  check on activity-based emission estimates such as those in the companion projects.

## Author

**Darliane Ribeiro Cunha, PhD**.
Research: maritime decarbonisation, port sustainability analytics, SDG implementation.

## Licence

Contains modified Copernicus Sentinel data (2024), processed by S5P-PAL. Analysis and site:
CC-BY 4.0.
