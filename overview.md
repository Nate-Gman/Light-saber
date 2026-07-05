# LS.py — Overview, Architecture & Physics

This document explains how `LS.py` is built and the real science behind every
number it computes. For how to run it, see [`README.md`](README.md).

---

## 1. Design philosophy: honest engineering, not a movie prop

`LS.py` is a **digital twin** in the engineering sense — a to-scale, physically
grounded model of a real device — applied to a fictional one. Its guiding rule:

> Every dimension is real (SI units). Every number on screen is *computed* from a
> real equation, never hard-coded. Every result is followed to its honest
> conclusion, **including the conclusions that prove a subsystem cannot work.**

The original brief ([`Projectgoal.md`](Projectgoal.md)) asked for a working
lightsaber. Rather than pretend, the twin separates the request into what real
physics **can** build (a diode-laser / photonic-crystal / plasma-channel cutting
tool with an internal chemical photon engine) and what it **cannot** (an
indefinitely rigid, swingable "solid-light" blade) — and it *quantifies the gap*
rather than assuming it away.

The architecture follows the two reference programs in `ReferenceCode/`
(`Main.py`, `GmansRunV1.17.py`): a single self-contained file with a `DIMS`/`PHYS`
spec at the top, a pure-Python software renderer, and a live physics engine.

---

## 2. File structure

`LS.py` is one file, organised into labelled sections:

| Section | Contents |
|---|---|
| **1 — Engineering spec** | `DIMS` (all geometry, mm) and `PHYS` (all material/physical constants). The single source of truth. |
| **1b — Materials** | `MATERIALS`: 9 real materials with looked-up thermophysical properties for the cut test. |
| **2 — Colours & theme** | Palette, plus `blackbody_rgb()` (real blackbody colour vs temperature). |
| **3 — Mini 3D engine** | Software renderer: `Mesh`, `Part`, primitive builders (`_solid_cylinder`, `_annulus`, `_box`, `_sphere`, `_torus`, `_helix_tube`, `_half_annulus`…), painter's-algorithm rasteriser with backface culling and flat shading. |
| **4 — Physics** | Optics, thermal, plasma, engine, and feasibility functions. |
| **4b — Photon-binding physics** | The "solid light" analysis (see §4). |
| **4c — Material-cutting physics** | The ablation energy-balance model (see §5). |
| **5 — Geometry** | `build_hilt()`, `build_engine_parts()`, `build_binding_showcase()`, `build_cut_test()`, `build_microcavity_showcase()`, `build_blade_mesh()`. |
| **6 — Renderer** | `Renderer`: orbit/pan/zoom camera, section cut, exploded view, hover-pick, part labels, blueprint projection helpers. |
| **7 — Application** | `App`: pygame event loop, 5 scenes, mouse-operable control panel, live HUD panels, scene-aware math overlay, blueprint overlay. |
| **8 — Selftest / reports / main** | `selftest()`, `print_feasibility()`, `print_cut_test()`, `legacy_report()`, `main()` with the CLI. |

The `DIMS`/`PHYS`/`MATERIALS` dicts at the top are the only place numbers are
authored; everything downstream is derived, so changing a spec value updates the
geometry, the physics, and the on-screen readouts consistently.

---

## 3. The device (what is buildable)

Built to scale in the hilt and inspectable in the viewer:

- **Emitter head** — collimating lens (f = 5 mm), the ~80 µm WS₂/CsPbBr₃
  **photonic-crystal microcavity** (shown at true scale in the hilt and at 2000×
  in the showcase scene), the 800 nm AlGaAs diode laser, TEC, and a radial
  heatsink.
- **Thermal-isolation stack** — HfC/ZrC crucible around the hot zone, a graphene
  spreader, primary + outer aerogel, a 30-layer MLI radiation barrier, the
  Ti-HfC shell, and ceramic/silicone grip pads. Modelled with real conduction
  (`multilayer_conduction_drop_k`) and the real N-shield MLI radiation formula
  (`mli_effective_emissivity`) — which the tool itself shows is negligible at
  grip temperatures and dominant only in the hot engine bay.
- **Internal chemical photon engine** — a combustion-heated blackbody emitter
  pumps a folded high-finesse slow-light delay-line cavity, cavity-dumped
  through a fast photonic-crystal shutter (the same mechanism as a Q-switched
  laser). Includes reactant cartridges, heat pipes, and a hilt-mounted radiator.
- **Plasma channel (blade)** — a ~7500 K ionized-air column, coloured by its
  real blackbody spectrum, formed on ignition.

---

## 4. Photon binding — "can slowed light become a solid?" (Section 4b)

This is the heart of the tool and the most-requested detail. Photons are
massless and non-interacting in vacuum; to bind them into a mass with stiffness
you need, **in sequence**, a mass, an interaction, a low enough temperature, and
crystalline order. `LS.py` computes each step with real physics:

1. **Mass from slow light** — `m = (E_photon/c²)·n_g`. A group index n_g = 50
   (real photonic-crystal / EIT slow light) gives an effective photon mass of
   1.38×10⁻³⁴ kg. Slowing the light literally makes it heavier.

2. **Interaction via a medium** — photons ignore each other in vacuum. The
   **Rydberg-EIT blockade** (`rydberg_blockade_radius_m`) is the strongest real
   photon-photon force — it produced actual bound photon pairs in the lab
   (Firstenberg et al., *Nature* 2013); the model reproduces the ~13 µm blockade
   radius. Alternatively a Kerr χ³ medium. The interaction sets a chemical
   potential (blueshift) µ ~ 3 meV.

3. **The "hold" (compressive stiffness)** — the interacting photon fluid has a
   speed of sound `c_s = √(µ/m)`, a healing length `ξ = ℏ/√(2mµ)`, and a **bulk
   modulus `B = µ·n`**. Result: **B ≈ 2.4 Pa — softer than air, ~10¹¹× softer
   than steel.** A 10 % squeeze pushes back with just 0.17 mN across the whole
   blade face.

4. **Holding resistance (superfluid dynamics)** — this is the physics of *how it
   responds to being pushed*:
   - **Landau critical velocity** `v_c = c_s ≈ 1865 km/s`. Any object slower
     than v_c sheds no excitations and passes through **frictionlessly** — a
     superfluid cannot grip a slow (25 m/s) sword swing.
   - **Deborah number** `De = τ_heal/τ_strike ≈ 10⁻¹¹ ≪ 1`. The fluid's healing
     time is sub-picosecond, so on any strike timescale it behaves as a
     **liquid** — it parts around the blade instead of stopping it. It cannot hit
     or be hit.

5. **Static shear (the parry)** — resisting a sideways block needs a shear
   modulus. A superfluid's static shear modulus is **exactly zero**. Only a
   **supersolid** (self-modulated crystal, ~1.8 µm period here — real, but only
   demonstrated at µm scale, cryogenically, in 1–2D) carries shear, and even an
   optimistic one falls short of a 100-lbf block by 2.6×10⁶×.

6. **Temperature ceiling** — binding survives only while `k_B·T < µ`, i.e. below
   `T_max = µ/k_B ≈ 35 K` (cryogenic). The built 7500 K plasma blade is **215×
   too hot**, so nothing binds in it at all.

**Conclusion:** every ingredient is real, but only microscopically,
cryogenically, with frictionless slip-through and zero parry strength — never a
warm, metre-scale, swingable solid blade. The binding cutaway scene (key 3)
visualises all of these zones.

---

## 5. Material cutting — the test mode (Section 4c)

The blade cuts the way any real high-power thermal source does: an **energy
balance at the ablation front**. The recession velocity is
`u = q_net / E_v`, where:

- `E_v = ρ·[c_p·(T_vap − T₀) + L_fusion + L_vaporization]` is the volumetric
  ablation energy of the material,
- `q_in = (1 − R)·σ·(T_plasma⁴ − T₀⁴)` is the radiative flux the plasma couples
  in (so the temperature slider drives cutting performance ∝ T⁴),
- `q_cond = k·(T_melt − T₀)/L_kerf` is the sideways conduction loss,
- `q_net = q_in − q_cond`.

The 9-material database (`MATERIALS`) uses real, looked-up properties, so the
results are genuine — and some are counterintuitive:

| Material | Result at 7500 K |
|---|---|
| flesh, wood, concrete | cut very fast |
| steel, titanium, durasteel | cut steadily (steel ~1.1 mm/s) |
| aluminium | cut **slowly** — high conductivity + 90 % reflectivity fight the cut |
| tungsten | slow — very high vaporization temperature |
| **diamond** | **cannot be cut** — k = 2200 W/m·K conducts heat away faster than the plasma supplies it |

Cycle materials with `,` / `.`. The cut-test scene (key 4) is a **live dynamic
simulation**: press `SPACE` / **RUN CUT** and the ablation depth is integrated
in real time at the true recession rate (accelerated 25× so a 100+ s cut is
watchable), the kerf deepens on screen, a depth/percent/time readout updates,
and it stops at breakthrough — while an uncuttable material simply stalls at
0 %. `python3 LS.py --cut [TEMP_K]` prints the whole table non-interactively.

---

## 6. Other physics subsystems

- **Blade power budget** — a 0.8 m × 30 mm channel at 7500 K radiates ~11 MW;
  a handheld diode laser is ~6×10⁵× short of sustaining it (the honest reason a
  continuously-glowing handheld blade is impossible).
- **Plasma column vs. focused spot** — a 10 W diode can ionise a focused 50 µm
  spot but is ~10⁵× below the air-breakdown threshold spread over a full
  30 mm column.
- **Chemical engine** — combustion → blackbody pump → cavity buildup (finesse,
  photon lifetime, slow-light enhancement) → cavity-dump. Energy-conserving:
  `E_dump = P_in·τ_eff`. Thermally limited to ~1.8 s bursts (the thermal buffer,
  not the fuel, is the real limit).
- **Aspirational polariton BEC** — the critical density for a metre-scale
  room-temperature condensate is computed and shown to exceed any demonstrated
  polariton density by ~10¹× (and far more at the required temperature).

---

## 7. Rendering & UI

- **Software renderer** — no GPU. `Renderer.render()` transforms each mesh into
  camera space, projects with a perspective focal length, sorts polygons by
  depth (painter's algorithm), culls backfaces, and flat-shades against a fixed
  light. Supports orbit/pan/zoom-at-cursor, section cut, hover picking, and
  part labels.
- **Exploded view (E)** — `_apply_exploded_layout()` authors a proper
  exploded-assembly layout from measured geometry: concentric shell/liner parts
  peel radially outward at staggered fan angles (revealing the nested thermal
  stack), and the internal components fan apart along the long axis in assembly
  order, so every part becomes individually visible.
- **Blueprint overlay (P)** — turns the live model into a real engineering
  schematic: an auto-generated **Bill of Materials** (every part's L × OD
  measured live from its geometry), a projected dimension chain
  (HEAD/GRIP/ENGINE/POMMEL), OAL/OD callouts with leader lines, and a title
  block.
- **Scene-aware readouts** — each scene shows the relevant live physics panel;
  the **M** overlay shows the matching derivation (binding proofs in scene 3,
  cutting proofs in scene 4, device proofs elsewhere), flowing into two columns
  when long.

---

## 8. Validation (why the numbers can be trusted)

1. **`--selftest`** — 36 assertions: geometry builds, all reports are finite,
   an offscreen render of all 5 scenes succeeds, and the full `App` (all scenes,
   both overlays, blueprint, every control) draws and hit-tests cleanly. Crucially
   it also asserts the *honest* physics inequalities — diamond uncuttable,
   aluminium slower than titanium, bound-photon fluid >10⁹× softer than steel,
   superfluid cannot parry, plasma too hot to bind.
2. **Independent cross-check** — every core equation reproduces the textbook
   value to **zero relative error** (photon energy, Stefan-Boltzmann, effective
   mass, speed of sound, healing length, bulk modulus, binding temperature,
   cavity finesse, ablation energy, Deborah number).
3. **OBJ export** — valid, watertight, true-scale Wavefront geometry, importable
   into Blender / FreeCAD / a 3D-print slicer (the hilt exports as 96 × 96 ×
   405.9 mm).

---

## 9. Extending it

Because `DIMS` / `PHYS` / `MATERIALS` are the single source of truth, the usual
extensions are one-liners plus a builder tweak:

- **New material** to cut → add a row to `MATERIALS` (real properties) and a
  colour to `MATERIAL_COLORS`.
- **Change the blade / hilt** → edit `DIMS`; geometry, physics, blueprint and
  readouts all follow.
- **New physics result** → add a function in Section 4/4b/4c, surface it in the
  relevant report/panel, and add a `check(...)` in `selftest()`.

Keep the discipline that makes the tool trustworthy: numbers are computed, not
asserted, and every claim is checkable.
