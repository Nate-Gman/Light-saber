# LS.py — Lightsaber Engineering Digital Twin

A single-file, interactive 3D **engineering digital twin** of a lightsaber, built
to real scale with a live physics engine. Every dimension is SI, every number on
screen is computed from real equations, and every conclusion is followed
honestly — including the ones that prove a subsystem *cannot* work.

It is not a movie prop. It is an honest engineering study of **what is buildable
(a diode-laser / photonic-crystal / plasma-channel cutting tool) and what is
not (an indefinitely rigid, swingable "solid-light" blade)** — with the physics
to back up both answers.

![status](https://img.shields.io/badge/selftest-36%2F36%20passing-brightgreen)
![physics](https://img.shields.io/badge/physics-cross--checked%20vs%20textbook-blue)

---

## Quick start

```bash
python3 -m pip install numpy scipy pygame      # dependencies
python3 LS.py                                   # launch the interactive 3D viewer
```

No GPU, CAD library, or internet connection required — the renderer is a
self-contained pure-Python software rasteriser (numpy + pygame).

### Command-line modes

| Command | What it does |
|---|---|
| `python3 LS.py` | Interactive 3D viewer (default) |
| `python3 LS.py --selftest` | Headless build + physics + render sanity (36 checks) |
| `python3 LS.py --feasibility` | Full honest physics/feasibility report to the console |
| `python3 LS.py --cut [TEMP_K]` | Material cut-test table (real ablation math) |
| `python3 LS.py --export-obj` | Write `hilt.obj`, `engine.obj`, `microcavity_showcase.obj` to `./export/` |
| `python3 LS.py --report` | Legacy matplotlib charts (aspirational solid-beam physics) |

The exported `.obj` files are standard Wavefront geometry at true SI scale
(the hilt is 96 × 96 × 405.9 mm), importable into Blender / FreeCAD / a
3D-print slicer.

---

## The five scenes

Switch with keys **1–5** or the on-screen scene buttons.

| Key | Scene | Shows |
|---|---|---|
| **1** | **Hilt** | The whole hand-held device to scale (~390 mm long, 60–68 mm dia): emitter head, diode laser, photonic-crystal microcavity, thermal-isolation stack, internal chemical photon engine, power bank, grip. |
| **2** | **Engine bay** | Close-up of the internal chemical photon engine (combustor, reactant cartridges, folded slow-light delay-line cavity, photonic-crystal shutter, heat pipes, radiator). |
| **3** | **Photon-binding cutaway** | The blade's internal physics zones — plasma sheath, slow-light region, bound-photon core, supersolid density-modulation lattice, Rydberg-EIT cell, confinement rings — the visual companion to *"what would bind slowed light into a solid?"* |
| **4** | **Cut test** | A **live cutting simulation** — press `SPACE` (or **RUN CUT**) and the blade actually ablates into the block at the real recession rate (accelerated 25×), the kerf deepens with a live depth/percent/time readout, and it stops at breakthrough. Cycle materials with `,` / `.`; **RESET CUT** to restart. Uncuttable materials (diamond) stall at 0 %. |
| **5** | **Microcavity showcase** | The genuinely ~80 µm WS₂/CsPbBr₃ photonic-crystal microcavity, shown at a documented 2000× zoom so the lattice is legible. |

---

## Controls

```
1..5 .......... switch scene            mouse drag L .... orbit
mouse wheel ... zoom (around cursor)    drag R/M ........ pan
R ............. reset view              E ............... exploded view
X ............. section cut             L ............... part labels
P ............. BLUEPRINT schematic overlay (BOM + dimensions + title block)
SPACE / B ..... ignite / extinguish the plasma blade
F ............. arm the internal chemical photon engine (pulsed reionize)
UP / DOWN ..... blade length 0.5–1.0 m  LEFT / RIGHT .... blade diameter
[ / ] ......... plasma temperature 5000–10000 K
, / . ......... cycle cut-test material
I ............. info overlay            M ............... math / proofs overlay
O ............. export OBJ              ESC / Q ......... quit
```

Everything is also on the **mouse-operable control panel** (left): scene
buttons, view toggles, blueprint, ignite/arm, material cycler, and blade
sliders.

Press **M** in any scene for the live math overlay — it is scene-aware
(binding proofs in scene 3, cutting proofs in scene 4, device proofs
elsewhere).

---

## What the physics says (honest bottom line)

The tool computes all of this live; press **M** or run `--feasibility`.

**Buildable (real, grounded):**
- An 800 nm diode laser feeding a real room-temperature exciton-polariton
  photonic-crystal microcavity.
- A hot (~7500 K) ionized-air **plasma channel** that genuinely **cuts** most
  materials by real ablation physics — steel at ~1.1 mm/s, and it cannot cut
  diamond, whose enormous thermal conductivity bleeds heat away faster than the
  plasma supplies it.
- An internal **chemical photon engine** (combustion-pumped high-finesse cavity,
  cavity-dumped like a Q-switched laser) that can briefly re-ionize the full
  blade column — thermally limited to ~1.8 s bursts.
- A multi-layer thermal stack (HfC crucible / aerogel / 30-layer MLI / heat
  pipes) that keeps the grip at ambient.

**Not buildable (the fictional part), proven quantitatively:**
- A continuously glowing metre-scale blade needs ~11 MW of radiated power — a
  handheld diode laser is ~6×10⁵× short.
- "Solid light" would need slowed photons bound into a fluid. Every ingredient
  is real — slow-light effective mass, the Rydberg-EIT blockade (13 µm, made
  actual bound photon pairs in the lab), fluid stiffness — but the resulting
  "hold" is a **bulk modulus of ~2.4 Pa (softer than air, ~10¹¹× softer than
  steel)**, it offers **zero static shear** (a superfluid flows — it cannot
  parry a block), it **slips through frictionlessly** below the Landau critical
  velocity, it **behaves as a fluid** on any strike timescale (Deborah number
  ~10⁻¹¹), and it only binds at all below ~35 K — the 7500 K plasma is 215× too
  hot.

See [`overview.md`](overview.md) for the architecture and the full physics
breakdown.

---

## Verification

The build is validated three ways:

1. **`--selftest`** — 36 checks covering geometry build, every physics report,
   an offscreen render of all scenes, and a full `App` UI smoke test. Also
   asserts the *honest* inequalities (e.g. diamond is uncuttable, the bound
   photon fluid is >10⁹× softer than steel, a superfluid cannot parry).
2. **Independent physics cross-check** — every core equation (photon energy,
   Stefan-Boltzmann flux, effective photon mass, speed of sound, healing
   length, bulk modulus, binding temperature, cavity finesse, ablation energy,
   Deborah number) reproduces the textbook value to zero relative error.
3. **OBJ export** — produces valid, watertight, correctly-scaled Wavefront
   geometry usable in real CAD / 3D-printing tools.

```bash
python3 LS.py --selftest      # -> "SELFTEST PASSED" (36/36)
```

---

## Requirements

- Python 3.9+
- `numpy`, `scipy`, `pygame` (interactive viewer); `matplotlib` only for
  the legacy `--report` charts.

## Files

```
LS.py            the entire program (single file, ~3700 lines)
Projectgoal.md   the original design brief this twin is built from
ReferenceCode/   the two reference programs (Main.py, GmansRunV1.17.py) whose
                 architecture this follows
README.md        this file
overview.md      architecture + full physics breakdown
```
