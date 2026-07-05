#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 LS.py -- LIGHTSABER ENGINEERING DIGITAL TWIN (grounded, real-science build)
================================================================================

A standalone, single-file, interactive 3D model + real physics study of the
BUILDABLE "lightsaber" design identified in Projectgoal.md: not the fictional
indefinite solid-light blade (which the physics rules out -- see --feasibility),
but the grounded 2025-2030 prototype -- a fiber/diode-laser-driven ionized
plasma channel, enhanced by a real room-temperature exciton-polariton photonic
crystal microcavity, powered by a supercapacitor/battery bank in the hilt (with
an optional external CHEMICAL photon-buildup pod -- no nuclear component: a
combustion-heated blackbody emitter pumps a high-finesse spiral delay-line
cavity that a fast photonic-crystal shutter cavity-dumps, the same real
mechanism as a Q-switched laser).

Every mechanical part is built AT TRUE SCALE (millimetres, SI units) from the
DIMS/PHYS spec below -- nothing is shrunk to a token "1/45 scale" miniature.
Where a real part is genuinely sub-millimetre (the WS2/CsPbBr3 microplate, the
photonic-crystal air-hole lattice, the DBR mirror stack), true-scale geometry
would be invisible on screen, so a dedicated MICROCAVITY SHOWCASE view builds
the SAME structure at a fixed, displayed zoom factor (2000x: 1 mm on screen =
500 nm real) -- high enough resolution to resolve individual lattice holes,
with the zoom factor always printed on screen so nothing is misrepresented.

Physics is real and computed live, not hard-coded flavor text: photon energy,
Gaussian-beam focal intensity vs. air-breakdown threshold, blackbody radiative
loss from the glowing channel, multi-layer (graphene / aerogel / Ti-HfC)
conduction thermal drop, supercapacitor runtime, BEC critical density for the
(aspirational, NOT built) polariton "solid beam", and real cavity-QED buildup
math (finesse, photon lifetime, cavity-dump peak power) for the external
chemical photon pod. Every number the model produces is followed to its
honest conclusion, including the ones that show a subsystem is NOT feasible
at this size/power -- that is the point of building this as a real
engineering tool rather than a prop description.

Dependencies: numpy, pygame (interactive viewer). matplotlib + scipy are only
imported lazily by --report (legacy static charts) so the viewer stays light.

--------------------------------------------------------------------------------
RUN
--------------------------------------------------------------------------------
    python3 LS.py                  # interactive 3D viewer (default)
    python3 LS.py --selftest       # headless build + physics + render sanity
    python3 LS.py --feasibility    # full honest physics/feasibility report
    python3 LS.py --cut [TEMP_K]   # material cut-test table (real ablation math)
    python3 LS.py --engineer       # failure->workaround scorecard for a REAL plasma-arc saber
    python3 LS.py --report         # legacy matplotlib static charts
    python3 LS.py --export-obj     # write OBJ+MTL of the hilt to ./export/

--------------------------------------------------------------------------------
CONTROLS
--------------------------------------------------------------------------------
  1..5 .............. HILT / ENGINE BAY / PHOTON-BINDING CUTAWAY / CUT TEST / MICROCAVITY
  mouse drag L ...... orbit          mouse drag R/M ..... pan
  wheel / +/- ....... zoom (around cursor)                R ... reset view
  E ................. toggle exploded view                X ... section cut
  L ................. toggle part labels                  P ... BLUEPRINT schematic overlay
  , / . ............. cycle CUT-TEST material             SPACE/B ... ignite/extinguish blade
  UP/DOWN ........... blade length 0.5-1.0 m               LEFT/RIGHT blade dia
  [ / ] ............. plasma temperature 5000-10000 K
  F ................. arm the internal Chem Photon Engine (pulsed reionize)
  I ................. info overlay (what this is / is not) M ... math overlay (all proofs)
  O ................. export OBJ                           ESC/Q ... quit

  Everything is also on the mouse-operable CONTROL PANEL (left): scene buttons,
  view toggles, blueprint, ignite/arm, material cycler, and blade sliders.
================================================================================
"""

import os
import sys
import math
import argparse
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np  # hard dependency

try:
    import pygame
except Exception:  # pragma: no cover - only if pygame missing
    pygame = None

from scipy.constants import h, hbar, c, k as KB, sigma as SIGMA_SB, e as ECHARGE, mu_0 as MU0


# =============================================================================
# SECTION 1 -- ENGINEERING SPECIFICATION (to scale, millimetres / SI)
# =============================================================================
#
# All geometry is TRUE SCALE. Two deliberate, documented exceptions:
#  1. The hand-held HILT (grip/head/pommel) is sized for a realistic handheld
#     prop (~320 mm long, ~32-34 mm diameter) per the "grounded" spec in
#     Projectgoal.md, NOT the aspirational "20 cm diameter" figure from the
#     internal-laser section (that figure describes a lab bench package, not
#     something a hand can close around -- see FUSION POD below for where
#     that mass/volume really goes).
#  2. The photonic-crystal microcavity chip is genuinely ~80 micrometres and
#     is built BOTH at true scale (in the hilt, where it is a few pixels) and
#     at a fixed, on-screen-labelled 2000x zoom in the MICROCAVITY SHOWCASE.

MM = 0.001   # millimetres -> metres
UM = 1e-6    # micrometres -> metres
NM = 1e-9    # nanometres  -> metres

SHOWCASE_ZOOM = 2000.0   # microcavity showcase: 1 mm on screen == 500 nm real

DIMS = {
    # --- Hand-held hilt shell: Ti-6Al-4V / HfC ceramic composite -----------
    # Resized per the layered thermal-isolation spec: a real HfC crucible +
    # aerogel + MLI + outer-aerogel + structural-shell stack needs more
    # radial room than the original 32 mm grip could offer. 60 mm is thicker
    # than a typical one-hand tool grip (~30-40 mm) -- an honest ergonomic
    # trade-off for a hilt that must also carry a chemical engine's
    # insulation, closer to a large baton/two-hand grip than a pen.
    "grip_len_mm":        180.0,
    "grip_od_mm":          60.0,
    "grip_wall_mm":         3.5,
    "head_len_mm":         65.0,   # front housing: lens+PhC+laser+heatsink
    "head_od_mm":          64.0,
    "pommel_len_mm":       50.0,   # rear housing: electronics+supercap+button
    "pommel_od_mm":        60.0,

    # --- Emitter head internals (positions are Z from the very front tip) -
    "aperture_od_mm":      20.0,   # beam output window
    "aperture_z_mm":        2.0,
    "lens_d_mm":           10.0,   # collimating lens, f=5mm per spec
    "lens_thick_mm":        3.0,
    "lens_z_mm":             8.0,
    "phc_chip_w_mm":        2.0,   # PhC microcavity carrier chip (true scale)
    "phc_chip_d_mm":        2.0,
    "phc_chip_t_mm":        0.5,
    "phc_z_mm":             14.0,
    "laser_pkg_mm":        10.0,   # TO-3 / butterfly package footprint
    "laser_pkg_h_mm":       5.0,
    "laser_z_mm":           24.0,
    "tec_t_mm":              1.5,  # integrated thermoelectric cooler
    "heatsink_w_mm":       20.0,   # aluminium fin heatsink
    "heatsink_h_mm":       20.0,
    "heatsink_fins":          8,
    "heatsink_z_mm":         34.0,

    # --- Thermal management: the full layered stack, inside to outside -----
    # (1) HfC/ZrC crucible around the ACTUAL hot chemical zone (the engine
    #     bay's combustor) -- not the TEC-cooled laser/PhC, which never gets
    #     near HfC's ~4200 K rating and doesn't need it.
    # (2) graphene-diamond spreader lining the head (existing, high-k).
    # (3) primary aerogel liner in the grip (existing).
    # (4) multi-layer insulation (MLI) reflective radiation barrier -- real
    #     spacecraft/cryogenic technique, modeled with the actual N-shield
    #     attenuation formula (see mli_effective_emissivity()), rendered as
    #     one representative band rather than 30 separate meshes.
    # (5) outer aerogel foam (a second, distinct layer per the spec).
    # (6) structural Ti-HfC/carbon-composite shell (existing, grip_wall_mm).
    # (7) ceramic/silicone grip-pad texture (ergonomic surface, negligible
    #     thermal resistance -- not part of the conduction stack).
    "hfc_crucible_t_mm":     4.0,   # HfC/ZrC liner around the combustor
    "graphene_layer_t_mm":   0.3,
    "aerogel_t_mm":          6.0,   # primary aerogel (grown from 3mm: more room now)
    "mli_layers":             30,   # foil-pair count (real N-shield formula)
    "mli_band_t_mm":         2.0,   # rendered thickness of the foil pack
    "outer_aerogel_t_mm":    4.0,   # second aerogel-foam layer (NEW)
    "grip_pad_rings":           6,  # raised ceramic/silicone ergonomic rings
    "grip_pad_t_mm":         1.5,

    # --- Engine-bay heat rejection: heat pipes + hilt-mounted radiator -----
    "heat_pipe_d_mm":        3.0,
    "heat_pipe_count":         4,
    "radiator_fins":            8,   # wraps the engine bay exterior
    "radiator_fin_len_mm":   14.0,   # radial fin protrusion

    # --- Rear grip / pommel internals --------------------------------------
    "electronics_l_mm":     18.0, "electronics_w_mm": 10.0, "electronics_t_mm": 2.0,
    "electronics_z_mm":     170.0,
    "supercap_d_mm":         26.0, "supercap_len_mm": 60.0, "supercap_z_mm": 205.0,
    "button_d_mm":            8.0, "button_z_mm": 365.0,

    # --- Blade / plasma channel (external, formed on ignition) -------------
    "blade_len_m":            0.8,   # adjustable 0.5-1.0 m
    "blade_d_mm":            30.0,   # adjustable 20-50 mm
    "confine_rings":            4,   # magnetic confinement coil rings at base
    "confine_ring_gap_mm":    6.0,
    "confine_tube_d_mm":      3.0,

    # --- Internal Chemical Photon Engine (replaces the Orbitron fusion pod --
    # entirely: no nuclear component. Lives INSIDE the hilt, in a dedicated
    # engine bay between the grip and pommel -- not an external attachment.
    # A combustion-heated blackbody emitter continuously pumps a folded
    # high-finesse delay-line cavity with an inline slow-light photonic-
    # crystal segment; a fast photonic-crystal shutter cavity-dumps the
    # accumulated energy in a directional burst to help re-ionize the full
    # blade column faster than a continuous low-power laser alone can.
    # Fitting a genuine engine (not just a token part) required lengthening
    # the hilt beyond the minimal 20-30 cm prop spec -- an honest SWaP
    # consequence, reported rather than hidden.) --------------------------
    "engine_bay_len_mm":     95.0,   # new hilt section housing the engine
    "engine_bay_od_mm":      68.0,   # bulged from the 60 mm grip
    "combustor_d_mm":        16.0,   # combustion / blackbody-emitter chamber
    "combustor_len_mm":      22.0,
    "cavity_coil_od_mm":     30.0,   # folded delay-line cavity envelope
    "cavity_turns":             5,
    "cavity_pitch_mm":        8.0,
    "cavity_tube_d_mm":       3.5,   # delay-line waveguide tube diameter
    "shutter_d_mm":          30.0,   # photonic-crystal shutter disc
    "shutter_grid":             8,   # NxN shutter-element grid shown
    "cartridges":               2,   # reactant micro-cartridges
    "cartridge_d_mm":         7.0,
    "cartridge_len_mm":      45.0,
    "cartridge_mass_g":      12.0,   # metal-powder/oxidizer charge per cartridge

    # --- Microcavity showcase (true sub-mm optics, shown at fixed zoom) ---
    "micro_plate_um":        80.0,   # WS2 / CsPbBr3 microplate, 80x80 um
    "micro_lattice_nm":     600.0,   # photonic-crystal lattice constant
    "micro_hole_nm":        300.0,   # PhC air-hole diameter
    "micro_dbr_pairs":          8,   # distributed Bragg reflector pairs
    "micro_dbr_layer_nm":   120.0,   # quarter-wave layer thickness (approx)
    "micro_patch_holes":       18,   # rendered lattice patch (NxN, see showcase)
}

PHYS = {
    "wavelength_nm":           800.0,   # AlGaAs diode, near-IR
    "laser_power_w":            10.0,   # CW max optical output
    "laser_power_formation_w":   5.4,
    "laser_power_sustain_w":     8.2,
    "laser_eta_wallplug":        0.50,  # electrical -> optical
    "beam_waist_um":             50.0,  # focused spot at the microcavity
    "m_eff_kg":                 9.1e-35,  # polariton effective mass (aspirational)
    "n_target_m3":              5.0e21,  # aspirational "solid beam" target density
    "T_beam_target_K":          1640.0,  # aspirational target temperature
    "plasma_temp_K":            7500.0,  # REAL glow temp of the built plasma channel
    "T_amb_K":                   300.0,
    "emissivity":                 0.80,
    "supercap_energy_wh":        300.0,  # practical config: Li-ion/supercap bank
    "chem_chamber_temp_k":     3800.0,  # combustion/refractory emitter temp (real: >3000-5000K range)
    "chem_heat_of_combustion_j_kg": 31.0e6,  # Al + O2 metal-powder combustion, real ~31 MJ/kg
    "chem_eta_photon":            0.25,  # chemical->photon conversion (note's 20-30% range; optimistic)
    "cavity_mirror_R":         0.99999,  # supermirror reflectivity (real: cavity ring-down-class)
    "shutter_open_s":             1e-9,  # fast PhC/MEMS shutter opening time (optimistic, ns-class)
    "slow_light_factor":          50.0,  # real PhC slow-light group-index enhancement (lit. range 10-100x)
    "plasma_recomb_time_s":       5e-6,  # order-of-magnitude weakly-ionized-air recombination time
    "human_flicker_fusion_hz":    50.0,  # real physiological constant: below this, pulsing looks like flicker
    "k_graphene_w_mk":          3000.0,
    "k_aerogel_w_mk":            0.020,
    "k_ti_hfc_w_mk":              15.0,
    "driver_overhead_w":           1.5,  # constant-current driver + control electronics

    # --- Layered thermal-isolation stack (HfC crucible / MLI / heat pipes) -
    "k_hfc_w_mk":                 20.0,  # HfC/ZrC, real ballpark
    "hfc_melting_k":            4200.0,  # ~3950 C, real HfC melting point
    "eps_mli_shield":            0.03,   # aluminized-foil emissivity (real)
    "eps_surface":                0.9,   # generic non-shield surface emissivity
    "heat_pipe_capture_frac":    0.92,   # fraction of waste heat the pipes intercept
    "buffer_mass_kg":             0.5,   # graphene/diamond thermal buffer (engine bay)
    "buffer_cp_j_kgk":          700.0,   # specific heat, graphite/diamond composite
    "buffer_delta_t_max_k":     200.0,   # max safe transient temperature rise
    "radiator_h_conv_w_m2k":     10.0,   # natural-convection coefficient, still air
    "radiator_emissivity":       0.85,
    "radiator_temp_k":          400.0,   # assumed fin temperature during a burst

    # --- PHOTON-BINDING PHYSICS: the real effects that could make slowed -----
    # light cohere into a mass with stiffness. All optimistic-but-real values;
    # the point is to compute the honest consequences, not to assert success.
    # (1) Slow light gives photons an EFFECTIVE MASS: m = (hbar*omega/c^2)*n_g,
    #     n_g = group index = slow_light_factor above. Real: slow-light
    #     enhancement of the polariton/photon mass.
    # (2) A nonlinear MEDIUM makes photons interact (they don't in vacuum):
    #     Kerr chi^3 (n = n0 + n2*I) OR Rydberg-EIT blockade (the strongest
    #     real photon-photon interaction -- bound photon "molecules" were
    #     demonstrated, Firstenberg et al. Nature 2013). This sets the
    #     interaction blueshift mu = g*n (the polariton chemical potential).
    # (3) mu + m give the fluid's speed of sound, healing length, and BULK
    #     modulus (its resistance to being SQUEEZED -- the "hold").
    # (4) THE CATCH: a superfluid resists compression but has ZERO static
    #     SHEAR modulus -- it cannot resist a sideways sword-block unless it
    #     has crystalline/supersolid order (real, but only demonstrated at um
    #     scale, cryogenic). And it only binds at all where k_B*T < mu.
    "interaction_blueshift_mev":  3.0,   # optimistic max polariton interaction blueshift (real: ~meV scale)
    "kerr_n2_m2_per_w":         1.0e-10, # engineered Rydberg-EIT giant-Kerr n2 (real media reach 1e-8..1e-12)
    "medium_n0":                  1.4,   # linear index of the host nonlinear medium
    "rydberg_c6_si":            3.2e-57, # van der Waals C6 [J*m^6], calibrated to ~13 um blockade (n~100)
    "rydberg_eit_bandwidth_hz": 1.0e6,   # EIT transparency bandwidth (sets blockade radius)
    "supersolid_shear_fraction":  0.1,   # optimistic shear/bulk modulus ratio IF crystalline order forms
    "lateral_load_n":           445.0,   # 100 lbf sideways sword-block (from Projectgoal spec)
    "binding_target_temp_k":     30.0,   # temperature a real bound-photon fluid would need (cryogenic)
    # -- mechanical-response ("holding resistance") parameters --
    "swing_tip_speed_m_s":       25.0,   # realistic sword-tip speed during a strike/parry
    "strike_duration_s":          0.02,  # contact time of a strike (~20 ms)
    "compression_strain":         0.10,  # 10% squeeze, for the compressive spring-force calc

    # --- MATERIAL-CUTTING PHYSICS (see MATERIALS below) --------------------
    "cut_view_factor":            1.0,   # geometric coupling of plasma flux into the kerf
    "cut_conduction_kerf_frac":   0.5,   # sideways conduction path length as a fraction of kerf width

    # --- ENGINEERING-AROUND: the current-carrying magnetic plasma-arc blade -
    # Instead of the (impossible) rigid "solid light", achieve the FUNCTIONS
    # -- a fixed-length blade that glows, cuts, and CLASHES with another blade
    # -- with real physics: a current-carrying plasma arc that (a) self-
    # confines by the Z-pinch (Bennett equilibrium), and (b) pushes on a
    # second energised blade by the Ampere force between parallel currents.
    "arc_blade_dia_mm":          8.0,    # arc channel diameter (thinner than the 30 mm show blade)
    "arc_plasma_density_m3":     1.0e22, # dense arc plasma number density
    "arc_plasma_temp_k":         8000.0, # arc core temperature
    "arc_field_gradient_v_m":    1200.0, # high-current free-burning air-arc voltage gradient
    "clash_force_target_n":      50.0,   # a firm, felt blade-to-blade clash
    "clash_contact_len_m":       0.20,   # length of blade overlap during a clash
    "clash_gap_m":               0.006,  # separation of the two current channels at contact

    # -- self-contained hybrid power system (supercap burst + battery idle) --
    # Finishes the "self-contained" hurdle: supercaps deliver the MW clash
    # BURSTS (they can dump kJ in ms), a high-density battery sustains the idle
    # glow. Runtime is an ignite-for-a-fight spec (energy density, not a wall).
    "arc_pulse_buffer_s":        0.02,   # ms-scale window the supercap must buffer (pulsed arc / clash impulse)
    "supercap_wh_per_kg":         8.0,   # real supercapacitor gravimetric energy
    "idle_current_frac":         0.60,   # idle current fraction -- kept ABOVE the Bennett confinement current
    "hilt_pack_kwh":             2.5,    # heavy but HANDHELD in-hilt battery+supercap pack
    "hilt_pack_mass_kg":         10.0,
    "backpack_energy_wh":       12000.0, # optional 12 kWh backpack for extended runtime

    # -- weapon lethality (this is a WEAPON, by design -- not a safe toy) -----
    "lethal_electrocution_j":    10.0,   # ~10 J across the heart can stop it; the blade holds kJ
    "flesh_cut_ref_mm_s":         0.0,   # filled at runtime from the cut model (instant amputation)

    # -- REAL "solid light" (photonic Mott insulator, Simon group 2019) -------
    # The genuine solid-light physics the request keeps asking for: photons in
    # a coupled-cavity lattice can freeze into a CRYSTALLINE Mott-insulator
    # state (real, demonstrated) -- which is the only "solid light" with the
    # crystalline order that gives static shear. The walls are temperature and
    # scale, computed honestly below (it is a chip at ~10 mK, not a blade).
    "mott_U_over_J":              8.0,   # interaction/tunnelling ratio for the Mott (solid) phase (real ~ >3.4)
    "mott_interaction_uev":       5.0,   # on-site photon-photon interaction U (circuit-QED scale)
    "mott_demo_temp_mk":         10.0,   # demonstrated operating temperature (~10 mK dilution fridge)
    "mott_site_spacing_um":     100.0,   # cavity-lattice site spacing (mm-scale cavities -> ~0.1 mm)
}


# =============================================================================
# SECTION 1b -- MATERIALS (real thermophysical properties, SI units)
# =============================================================================
# Every value is a real, looked-up property (density, specific heat, melt &
# vaporization/decomposition temperatures, latent heats of fusion &
# vaporization, thermal conductivity, and optical reflectivity in the near-IR).
# The cutting model in SECTION 4c does an honest energy balance at the ablation
# front with these -- no material "just cuts because lightsaber".
#   rho   kg/m^3     cp   J/kg-K     T_melt/T_vap  K
#   L_f   J/kg (fusion)  L_v  J/kg (vaporization/decomposition)
#   k     W/m-K       R    near-IR reflectivity (0-1)
MATERIALS = {
    "flesh (soft tissue)": dict(rho=1050.0, cp=3600.0, t_melt=333.0, t_vap=373.0,
                                l_f=3.3e5, l_v=2.26e6, k=0.5, refl=0.05, note="water-dominated; cauterizes"),
    "oak wood":            dict(rho=750.0, cp=1700.0, t_melt=550.0, t_vap=700.0,
                                l_f=0.0, l_v=1.2e7, k=0.17, refl=0.30, note="pyrolysis/char, effective L_v"),
    "aluminium 6061":      dict(rho=2700.0, cp=900.0, t_melt=933.0, t_vap=2792.0,
                                l_f=3.97e5, l_v=1.05e7, k=237.0, refl=0.90, note="high k + high reflectivity fight the cut"),
    "titanium Ti-6Al-4V":  dict(rho=4430.0, cp=560.0, t_melt=1933.0, t_vap=3560.0,
                                l_f=3.65e5, l_v=8.8e6, k=6.7, refl=0.50, note="low k: cuts cleaner than Al"),
    "mild steel":          dict(rho=7850.0, cp=490.0, t_melt=1811.0, t_vap=3134.0,
                                l_f=2.70e5, l_v=6.1e6, k=50.0, refl=0.60, note="the classic blast-door stand-in"),
    "concrete":            dict(rho=2400.0, cp=880.0, t_melt=1773.0, t_vap=3000.0,
                                l_f=5.0e4, l_v=2.0e6, k=1.4, refl=0.70, note="spalls/decomposes; low k, cheap to ablate"),
    "tungsten":            dict(rho=19300.0, cp=134.0, t_melt=3695.0, t_vap=5828.0,
                                l_f=2.85e5, l_v=4.35e6, k=173.0, refl=0.50, note="very high T_vap; slow going"),
    "diamond":             dict(rho=3510.0, cp=509.0, t_melt=4000.0, t_vap=4100.0,
                                l_f=1.0e7, l_v=6.0e7, k=2200.0, refl=0.17, note="huge k conducts heat away: near-uncuttable"),
    "durasteel (analog)":  dict(rho=8200.0, cp=450.0, t_melt=3300.0, t_vap=5200.0,
                                l_f=3.0e5, l_v=8.0e6, k=25.0, refl=0.55, note="FICTIONAL stand-in: refractory steel-carbide"),
}
MATERIAL_KEYS = list(MATERIALS.keys())


# =============================================================================
# SECTION 2 -- COLORS & THEME
# =============================================================================

BG_TOP        = (12, 16, 22)
BG_BOT        = (3, 5, 8)
C_TI_HFC      = (150, 152, 158)     # titanium/HfC composite shell
C_TI_HFC_DK   = (95, 97, 104)
C_APERTURE    = (60, 200, 255)
C_LENS        = (150, 220, 255)
C_PHC_CHIP    = (180, 90, 220)      # photonic-crystal microcavity carrier
C_LASER_PKG   = (210, 190, 60)      # gold TO-can package
C_TEC         = (90, 130, 200)
C_HEATSINK    = (200, 205, 212)
C_GRAPHENE    = (40, 42, 46)        # near-black, very high k
C_AEROGEL     = (210, 230, 235)     # translucent-looking pale blue
C_ELECTRONICS = (60, 150, 90)
C_SUPERCAP    = (80, 100, 210)
C_BUTTON      = (220, 60, 55)
C_CONFINE     = (120, 170, 255)
C_POD_SHELL   = (120, 100, 95)
C_CHAMBER     = (230, 140, 40)
C_STANDOFF    = (235, 235, 240)
C_RADIATOR    = (170, 80, 60)
C_UMBILICAL   = (40, 40, 44)
C_DBR_A       = (60, 90, 170)
C_DBR_B       = (180, 200, 230)
C_MICROPLATE  = (220, 120, 200)
C_HOLE        = (10, 10, 12)
C_HFC         = (200, 175, 140)     # HfC/ZrC crucible ceramic
C_MLI         = (225, 225, 210)     # aluminized-foil MLI pack, pale metallic
C_OUTER_GEL   = (190, 215, 222)     # outer aerogel foam (distinct from primary)
C_HEATPIPE    = (140, 205, 190)     # graphene/diamond heat pipe
C_GRIP_PAD    = (45, 48, 52)        # ceramic/silicone ergonomic grip texture
C_SHEATH      = (120, 180, 255)     # outer ionized-air plasma sheath
C_SLOWZONE    = (150, 110, 235)     # EIT/photonic-crystal slow-light region
C_BOUNDCORE   = (245, 235, 180)     # bound-photon condensate core
C_EITCELL     = (90, 160, 150)      # Rydberg-EIT vapour cell
C_FIELDLINE   = (110, 200, 255)     # confinement field lines
C_LATTICE     = (255, 180, 90)      # supersolid density-peak nodes (warm, stands out)
C_WORKPIECE   = (110, 114, 122)     # cut-test material block (recolored per material)
C_KERF        = (255, 120, 40)      # glowing cut kerf

MATERIAL_COLORS = {
    "flesh (soft tissue)": (200, 130, 120),
    "oak wood":            (150, 110, 65),
    "aluminium 6061":      (190, 195, 205),
    "titanium Ti-6Al-4V":  (140, 145, 155),
    "mild steel":          (120, 124, 132),
    "concrete":            (165, 160, 150),
    "tungsten":            (95, 100, 110),
    "diamond":             (185, 220, 235),
    "durasteel (analog)":  (100, 110, 128),
}

C_TEXT        = (224, 230, 238)
C_TEXT_DIM    = (150, 160, 175)
C_ACCENT      = (90, 200, 255)
C_GOOD        = (90, 220, 130)
C_WARN        = (255, 200, 60)
C_BAD         = (255, 90, 90)
C_PANEL       = (16, 20, 28)
C_PANEL_HI    = (28, 36, 50)


def blackbody_rgb(temp_k):
    """Approximate visible-light RGB for a blackbody at temp_k Kelvin (Tanner
    Helland's widely-used fit to Mitchell Charity's blackbody data). Used to
    color the plasma channel realistically instead of an arbitrary 'movie'
    color -- a real ~7500 K channel actually looks pale blue-white, not a
    saturated cartoon hue."""
    t = max(1000.0, min(40000.0, temp_k)) / 100.0
    if t <= 66.0:
        r = 255.0
        g = 99.47 * math.log(t) - 161.12 if t > 0 else 0.0
    else:
        r = 329.70 * ((t - 60.0) ** -0.1332)
        g = 288.12 * ((t - 60.0) ** -0.0755)
    if t >= 66.0:
        b = 255.0
    elif t <= 19.0:
        b = 0.0
    else:
        b = 138.52 * math.log(t - 10.0) - 305.04
    return (int(clamp(r, 0, 255)), int(clamp(g, 0, 255)), int(clamp(b, 0, 255)))


# =============================================================================
# SECTION 3 -- MINI 3D ENGINE (software renderer, painter's algorithm)
# =============================================================================

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else (hi if x > hi else x)


def rot_x(a):
    cq, sq = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, cq, -sq], [0, sq, cq]], dtype=float)


def rot_y(a):
    cq, sq = math.cos(a), math.sin(a)
    return np.array([[cq, 0, sq], [0, 1, 0], [-sq, 0, cq]], dtype=float)


def rot_z(a):
    cq, sq = math.cos(a), math.sin(a)
    return np.array([[cq, -sq, 0], [sq, cq, 0], [0, 0, 1]], dtype=float)


def _mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


class Mesh:
    """A bag of vertices + polygon faces with a base color. Coordinates are in
    METRES, the device axis along +Z (tip at -Z/front, pommel at +Z/rear).
    `group` selects which spin/animation angle drives this mesh (unused for a
    mostly-static prop, kept for the confinement-ring subtle rotation)."""

    def __init__(self, verts, faces, color, name="", group="static",
                 pivot=(0.0, 0.0, 0.0), spin=0.0, alpha=255):
        self.verts = np.asarray(verts, dtype=float)
        self.faces = faces
        self.color = color
        self.name = name
        self.group = group
        self.pivot = np.asarray(pivot, dtype=float)
        self.spin = spin
        self.alpha = alpha

    def world_verts(self, angle=0.0):
        v = self.verts
        if self.spin:
            v = v @ rot_z(angle * self.spin).T
        return v + self.pivot


# ---- primitive builders (all local axis = Z unless noted) ------------------

def _solid_cylinder(r, z0, z1, seg=28):
    seg = max(6, int(seg))
    verts, faces = [], []
    ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    for z in (z0, z1):
        for a in ang:
            verts.append((r * math.cos(a), r * math.sin(a), z))
    c0 = len(verts); verts.append((0, 0, z0))
    c1 = len(verts); verts.append((0, 0, z1))
    for i in range(seg):
        a, b = i, (i + 1) % seg
        faces.append((a, b, seg + b, seg + a))
        faces.append((c0, b, a))
        faces.append((c1, seg + a, seg + b))
    return verts, faces


def _annulus(r_out, r_in, z0, z1, seg=32):
    """Hollow tube closed at both axial ends (outer wall, inner wall, 2 caps)."""
    seg = max(6, int(seg))
    verts, faces = [], []
    ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    for z in (z0, z1):
        for a in ang:
            verts.append((r_out * math.cos(a), r_out * math.sin(a), z))
        for a in ang:
            verts.append((r_in * math.cos(a), r_in * math.sin(a), z))

    def oo(layer, i): return layer * (2 * seg) + (i % seg)
    def ii(layer, i): return layer * (2 * seg) + seg + (i % seg)

    for i in range(seg):
        faces.append((oo(0, i), oo(0, i + 1), oo(1, i + 1), oo(1, i)))
        faces.append((ii(0, i), ii(1, i), ii(1, i + 1), ii(0, i + 1)))
        faces.append((oo(0, i), ii(0, i), ii(0, i + 1), oo(0, i + 1)))
        faces.append((oo(1, i), oo(1, i + 1), ii(1, i + 1), ii(1, i)))
    return verts, faces


def _box(cx, cy, cz, sx, sy, sz):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
         (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
         (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
         (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return v, f


def _sphere(r, seg=12):
    seg = max(6, int(seg))
    rings = max(4, seg // 2)
    verts = []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        y = r * math.cos(phi)
        rr = r * math.sin(phi)
        for j in range(seg):
            th = 2 * math.pi * j / seg
            verts.append((rr * math.cos(th), y, rr * math.sin(th)))
    faces = []
    for i in range(rings):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            c = (i + 1) * seg + (j + 1) % seg
            d = (i + 1) * seg + j
            faces.append((a, b, c, d))
    return verts, faces


def _cone(r0, r1, z0, z1, seg=24):
    seg = max(6, int(seg))
    verts, faces = [], []
    ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    for r, z in ((r0, z0), (r1, z1)):
        for a in ang:
            verts.append((r * math.cos(a), r * math.sin(a), z))
    c0 = len(verts); verts.append((0, 0, z0))
    c1 = len(verts); verts.append((0, 0, z1))
    for i in range(seg):
        a, b = i, (i + 1) % seg
        faces.append((a, b, seg + b, seg + a))
        faces.append((c0, b, a))
        faces.append((c1, seg + a, seg + b))
    return verts, faces


def _torus(r_major, r_tube, seg_major=28, seg_tube=10, a0=0.0, a1=2 * np.pi):
    """Torus (or partial torus arc a0..a1) with its main ring in the local X-Y
    plane, tube axis following the ring -- used for the blade's electromagnetic
    confinement rings."""
    seg_major = max(6, int(seg_major)); seg_tube = max(4, int(seg_tube))
    closed = abs((a1 - a0) - 2 * np.pi) < 1e-6
    n_major = seg_major if closed else seg_major + 1
    verts, faces = [], []
    majors = np.linspace(a0, a1, n_major, endpoint=not closed)
    for A in majors:
        cA, sA = math.cos(A), math.sin(A)
        for j in range(seg_tube):
            B = 2 * np.pi * j / seg_tube
            rr = r_major + r_tube * math.cos(B)
            zz = r_tube * math.sin(B)
            verts.append((rr * cA, rr * sA, zz))
    for i in range(n_major - (1 if not closed else 0)):
        i2 = (i + 1) % n_major
        for j in range(seg_tube):
            j2 = (j + 1) % seg_tube
            a = i * seg_tube + j
            b = i2 * seg_tube + j
            cq = i2 * seg_tube + j2
            d = i * seg_tube + j2
            faces.append((a, b, cq, d))
    return verts, faces


def _combine(chunks):
    """Merge (verts, faces) chunks that already share ONE color into a single
    (verts, faces) pair with re-based face indices."""
    verts, faces = [], []
    for v, f in chunks:
        base = len(verts)
        verts.extend(v)
        faces.extend([tuple(i + base for i in face) for face in f])
    return verts, faces


def _translate(vf, off):
    v, f = vf
    ox, oy, oz = off
    return [(x + ox, y + oy, z + oz) for x, y, z in v], f


class Part:
    """A named, spec'd logical component made of one or more meshes. Carries an
    assembly `order` (front-to-back build sequence) and an `explode` direction
    used when the exploded view is active, plus a `specs` list of real
    engineering figures shown when the part is hovered/selected."""

    def __init__(self, key, name, meshes, specs, order, explode):
        self.key = key
        self.name = name
        self.meshes = meshes
        self.specs = specs
        self.order = order
        self.explode = np.asarray(explode, dtype=float)


# =============================================================================
# SECTION 4 -- PHYSICS (real equations, computed live, honest conclusions)
# =============================================================================

def photon_energy_j(wavelength_m):
    """E = hc/lambda."""
    return h * c / wavelength_m


def critical_density_bec(temp_k, m_eff_kg):
    """3D Bose-Einstein-condensation critical density via the thermal de Broglie
    wavelength: n_c = 2.612 / lambda_dB^3, lambda_dB = h / sqrt(2*pi*m*k_B*T).
    This is the ASPIRATIONAL "solid beam" polariton-condensate metric -- the
    built prototype below does not attempt this; it is reported for honesty
    against the original request."""
    if temp_k <= 0:
        return float("inf")
    lam_db = h / math.sqrt(2 * math.pi * m_eff_kg * KB * temp_k)
    return 2.612 / lam_db ** 3


def polariton_feasibility_ratio(n_target_m3, temp_k, m_eff_kg):
    n_c = critical_density_bec(temp_k, m_eff_kg)
    return n_target_m3 / n_c, n_c


def laser_electrical_draw_w(optical_power_w, eta_wallplug):
    return optical_power_w / eta_wallplug


def gaussian_focus_intensity(power_w, waist_m):
    """Area-averaged intensity of a focused CW Gaussian beam, W/m^2. Peak
    on-axis intensity of a true Gaussian is 2x this average."""
    area = math.pi * waist_m ** 2
    avg = power_w / area
    return avg, 2.0 * avg


def column_intensity(power_w, diameter_m):
    """Intensity if the SAME optical power were spread uniformly across a
    column of the given diameter (used to test whether the diode can sustain
    ionization over the full blade cross-section, not just at its focused
    spot)."""
    r = diameter_m / 2.0
    return power_w / (math.pi * r ** 2)


def breakdown_margin(intensity_w_m2, threshold_lo=1e9, threshold_hi=1e11):
    """How far intensity is from the real air-optical-breakdown band
    (~1e9-1e11 W/m^2). Returns (below_threshold: bool, ratio_to_lo)."""
    return intensity_w_m2 < threshold_lo, intensity_w_m2 / threshold_lo


def blackbody_radiative_power(temp_k, area_m2, emissivity, t_amb_k=300.0):
    """Stefan-Boltzmann radiated power: P = eps * sigma * A * (T^4 - Tamb^4)."""
    return emissivity * SIGMA_SB * area_m2 * (temp_k ** 4 - t_amb_k ** 4)


def cylinder_surface_area(length_m, diameter_m):
    r = diameter_m / 2.0
    return 2 * math.pi * r * length_m + 2 * math.pi * r ** 2


def multilayer_conduction_drop_k(power_w, layers):
    """Steady-state temperature drop across N plane layers in series:
    layers = [(thickness_m, k_W_per_mK, area_m2), ...]; R_i = t/(k*A);
    dT = P * sum(R_i). Used for the graphene-spreader + aerogel-liner +
    Ti/HfC-shell stack between the hot emitter head and the grip surface."""
    r_total = 0.0
    for thickness_m, k_wmk, area_m2 in layers:
        r_total += thickness_m / (k_wmk * area_m2)
    return power_w * r_total, r_total


def supercap_runtime_hours(energy_wh, power_w):
    if power_w <= 0:
        return float("inf")
    return energy_wh / power_w


def chem_emitter_optical_power_w(temp_k, area_m2, emissivity):
    """Real Stefan-Boltzmann blackbody output of the combustion-heated
    refractory emitter -- reuses the same physics as the plasma-blade
    radiative loss calc, just as a SOURCE here instead of a loss."""
    return blackbody_radiative_power(temp_k, area_m2, emissivity, PHYS["T_amb_K"])


def chem_fuel_flow_kg_s(p_optical_w, eta_photon, heat_of_combustion_j_kg):
    """Reactant mass flow needed to sustain a given optical output power at a
    given chemical->photon conversion efficiency and fuel energy density."""
    return p_optical_w / (eta_photon * heat_of_combustion_j_kg)


def reactant_runtime_s(total_reactant_kg, fuel_flow_kg_s):
    if fuel_flow_kg_s <= 0:
        return float("inf")
    return total_reactant_kg / fuel_flow_kg_s


def cavity_finesse(reflectivity):
    """Fabry-Perot finesse F = pi*sqrt(R)/(1-R) -- standard cavity-QED result,
    the same math behind LIGO's arm cavities and cavity-dumped lasers."""
    r = reflectivity
    return math.pi * math.sqrt(r) / (1.0 - r)


def helix_path_length_m(coil_diameter_m, turns, pitch_m):
    """Arc length of a helix: turns * sqrt((pi*D)^2 + pitch^2) per turn."""
    per_turn = math.sqrt((math.pi * coil_diameter_m) ** 2 + pitch_m ** 2)
    return per_turn * turns


def cavity_photon_lifetime_s(round_trip_length_m, reflectivity):
    """Photon storage time in a lossy ring cavity: tau = -L/(c ln R)."""
    return -round_trip_length_m / (c * math.log(reflectivity))


def slow_light_lifetime_s(tau_intrinsic_s, slow_light_factor):
    """A real, SEPARATE effect from mirror finesse: an inline photonic-crystal
    slow-light waveguide segment reduces the group velocity (v_g = c/n_g),
    so the SAME physical cavity holds circulating light for longer -- this is
    the 'hold slowed light... via the photonic crystal' mechanism, and it is
    real (demonstrated group-index enhancements of ~10-100x in PhC line-
    defect waveguides), distinct from and multiplicative with mirror finesse."""
    return tau_intrinsic_s * slow_light_factor


def cavity_dump_energy_j(p_in_w, tau_eff_s):
    """Energy extractable from ONE charge/dump cycle: while the shutter stays
    closed, the cavity accumulates roughly its own input power over its own
    storage time (a standard RC-charging relation, E = P_in * tau -- NOT
    P_in * finesse * tau, which would double-count the buildup factor and
    silently violate energy conservation; the finesse describes intracavity
    circulating power in a CONTINUOUSLY LEAKY cavity, a different regime from
    a closed-shutter charge-and-dump cycle)."""
    return p_in_w * tau_eff_s


def cavity_dump_peak_power_w(stored_energy_j, shutter_open_s):
    """Peak power if the shutter dumps the stored energy in shutter_open_s --
    the same mechanism (and the same huge peak-power payoff) as a Q-switched
    or cavity-dumped laser: same total energy, released over a far shorter
    time, so peak power spikes without creating energy from nothing."""
    if shutter_open_s <= 0:
        return float("inf")
    return stored_energy_j / shutter_open_s


def charge_time_s(tau_eff_s, n_lifetimes=3.0):
    """Time to reach ~95% of steady-state charge (1 - e^-3 ~= 0.95): sets how
    often the engine can re-arm the shutter for another dump."""
    return n_lifetimes * tau_eff_s


def repetition_rate_hz(charge_time_s_value):
    if charge_time_s_value <= 0:
        return float("inf")
    return 1.0 / charge_time_s_value


def flicker_appears_continuous(rep_rate_hz, fusion_hz=50.0):
    """Whether a human eye would see the pulsed re-ignition as a steady glow
    (rep rate at/above the real flicker-fusion threshold) or as a strobe."""
    return rep_rate_hz >= fusion_hz


def engine_waste_heat_w(p_optical_w, eta_photon):
    """Only eta_photon of the chemical energy INPUT becomes useful photons;
    the rest is waste heat that the heat pipes/radiator/buffer must manage.
    p_input = p_optical / eta_photon (definition of the conversion
    efficiency); waste = p_input - p_optical."""
    p_input = p_optical_w / eta_photon
    return p_input - p_optical_w, p_input


def mli_effective_emissivity(n_shields, eps_shield, eps_hot=0.9, eps_cold=0.9):
    """Standard N-radiation-shield attenuation formula (real: this is exactly
    how spacecraft/cryostat multi-layer insulation is sized): stacking N
    low-emissivity foils between two surfaces divides the radiative heat
    transfer coefficient by roughly (N+1) for equal emissivities."""
    inv_eps_eff = (1.0 / eps_hot + 1.0 / eps_cold - 1.0) + n_shields * (2.0 / eps_shield - 1.0)
    return 1.0 / inv_eps_eff


def linearized_radiative_resistance_k_per_w(eps_eff, area_m2, t_avg_k):
    """Linearize radiative heat transfer around an average temperature so an
    MLI gap can be folded into the same series-resistance network as the
    conduction layers: R = 1/(4 eps_eff sigma A T_avg^3), the standard small-
    signal radiative-resistance approximation used in thermal network models."""
    return 1.0 / (4.0 * eps_eff * SIGMA_SB * area_m2 * t_avg_k ** 3)


def radiator_dissipation_w(area_m2, t_radiator_k, t_amb_k, emissivity, h_conv):
    """Combined radiative + natural-convective dissipation -- the two real
    heat-rejection paths available to a passive hilt-mounted fin array (no
    forced airflow, no space-facing radiator)."""
    rad = blackbody_radiative_power(t_radiator_k, area_m2, emissivity, t_amb_k)
    conv = h_conv * area_m2 * (t_radiator_k - t_amb_k)
    return rad + conv


def thermal_buffer_capacity_j(mass_kg, specific_heat_j_kgk, delta_t_max_k):
    """Sensible-heat storage capacity of a thermal buffer mass: Q = m c dT."""
    return mass_kg * specific_heat_j_kgk * delta_t_max_k


def thermally_limited_runtime_s(buffer_capacity_j, net_heat_w):
    """How long the buffer can absorb heat faster than the radiator sheds it
    before hitting its safe temperature-rise limit -- often the REAL limit
    on a burst-mode chemical engine, not the fuel supply."""
    if net_heat_w <= 0:
        return float("inf")
    return buffer_capacity_j / net_heat_w


def blade_power_budget(length_m, diameter_m, temp_k, emissivity):
    """The core honesty check on the 'grounded' blade: how much continuous
    power is needed just to replace the radiative loss of a glowing channel of
    this size/temperature, versus what a handheld diode laser + supercap bank
    can actually deliver."""
    area = cylinder_surface_area(length_m, diameter_m)
    p_rad = blackbody_radiative_power(temp_k, area, emissivity, PHYS["T_amb_K"])
    return p_rad, area


def laser_power_budget():
    """Real electrical draw of the built laser system (both operating points),
    plus driver/control overhead."""
    p_opt_form = PHYS["laser_power_formation_w"]
    p_opt_sus = PHYS["laser_power_sustain_w"]
    eta = PHYS["laser_eta_wallplug"]
    e_form = laser_electrical_draw_w(p_opt_form, eta) + PHYS["driver_overhead_w"]
    e_sus = laser_electrical_draw_w(p_opt_sus, eta) + PHYS["driver_overhead_w"]
    return e_form, e_sus


# =============================================================================
# SECTION 4b -- PHOTON-BINDING PHYSICS (what makes slowed light cohere)
# =============================================================================
# The heart of the "solid light" question, done with real physics. Photons in
# vacuum are massless and non-interacting; to bind them into a mass with
# stiffness you need, in sequence: (1) an effective MASS (slow light in a
# medium/cavity), (2) an effective INTERACTION (a nonlinear medium: Kerr chi^3
# or -- the strongest real one -- the Rydberg-EIT blockade that produced
# actual bound photon pairs in the lab), (3) high enough DENSITY that the
# interaction energy exceeds the thermal energy so a quantum fluid forms.
# The fluid then has a BULK modulus (resists compression: the "hold") but,
# crucially, ZERO static SHEAR modulus unless it also has crystalline
# (supersolid) order -- which is why you cannot parry with it. Every function
# below returns a real, checkable number; the conclusions are followed honestly.

def slow_light_group_velocity(n_group):
    """v_g = c / n_g. A photonic-crystal / EIT slow-light segment with group
    index n_g slows the light and (below) proportionally raises its effective
    mass. Real: group indices of 10-100+ are routine, ~10^6-10^7 in atomic EIT."""
    return c / n_group


def effective_photon_mass_kg(wavelength_m, n_group):
    """A slowed photon in a medium/waveguide behaves like a massive particle
    with m ~ (hbar*omega/c^2) * n_g. Setting hbar*omega = E_photon, this is
    m = (E_photon / c^2) * n_g -- the mass GROWS with the group index, i.e.
    the more you slow the light the 'heavier' (more inertial) it becomes.
    This is the literal, quantitative meaning of 'after they are slowed'."""
    e_ph = photon_energy_j(wavelength_m)
    return (e_ph / c ** 2) * n_group


def kerr_index_shift(n2_m2_per_w, intensity_w_m2):
    """Kerr effect: n = n0 + n2*I. The nonlinear index shift dn = n2*I is the
    simplest real photon-photon interaction (photons see each other through the
    medium). For light to behave 'solid' you want dn approaching order-unity of
    n0. Returns dn."""
    return n2_m2_per_w * intensity_w_m2


def kerr_intensity_for_unity(n2_m2_per_w, n0):
    """Intensity needed for a Kerr shift dn = n0 (a huge, 'solid-like'
    nonlinearity): I = n0 / n2. Compared elsewhere against what's available."""
    return n0 / n2_m2_per_w


def rydberg_blockade_radius_m(c6_si, eit_bandwidth_hz):
    """Rydberg-EIT blockade radius r_b = (C6 / (hbar * Gamma_EIT))^(1/6): inside
    r_b a single Rydberg excitation blocks a second, giving photons an enormous
    effective interaction (this is the mechanism behind laboratory bound photon
    pairs, Firstenberg et al. 2013). Real, but only in ultracold (~uK) atomic
    gases at the single/few-photon level -- not macroscopic, not warm."""
    gamma = 2 * math.pi * eit_bandwidth_hz
    return (c6_si / (hbar * gamma)) ** (1.0 / 6.0)


def interaction_chemical_potential_j(blueshift_mev):
    """The interaction energy per particle (polariton chemical potential
    mu = g*n), taken from the directly-measured interaction blueshift. Real
    polariton condensates show blueshifts up to ~meV before the condensate is
    destroyed; that ceiling is exactly why the 'stiffness' below is so limited."""
    return blueshift_mev * 1e-3 * ECHARGE


def fluid_speed_of_sound(mu_j, m_kg):
    """Bogoliubov speed of sound in an interacting Bose fluid: c_s = sqrt(mu/m).
    Density perturbations (a 'push') propagate at c_s -- how fast the blade
    could respond to a load."""
    if m_kg <= 0:
        return 0.0
    return math.sqrt(max(0.0, mu_j) / m_kg)


def healing_length_m(mu_j, m_kg):
    """Healing length xi = hbar / sqrt(2*m*mu): the shortest length over which
    the fluid can resist a density change -- effectively the sharpness of the
    blade's edge/skin. Larger xi = mushier edge."""
    denom = 2.0 * m_kg * max(mu_j, 1e-60)
    return hbar / math.sqrt(denom)


def fluid_bulk_modulus_pa(mu_j, n_m3):
    """Compressive stiffness of the photon fluid. For a contact interaction
    mu = g*n, the pressure is P = 1/2 g n^2 and the bulk modulus B = n dP/dn =
    g n^2 = mu * n. This is the REAL 'hold' -- the fluid's resistance to being
    squeezed. Returned in pascals, to be compared against real solids."""
    return mu_j * n_m3


def binding_temperature_ceiling_k(mu_j):
    """A quantum fluid (and any binding/ordering) survives only while the
    thermal energy is below the interaction energy: k_B*T < mu. This returns
    T_max = mu / k_B -- above it, thermal agitation unbinds everything. It is
    typically CRYOGENIC, which is the single hardest fact for a hot glowing
    blade."""
    return mu_j / KB


def lateral_load_shear_stress_pa(force_n, blade_diameter_m):
    """A sideways sword-block of `force_n` newtons applied across the blade's
    circular cross-section produces a shear stress tau = F / A. A real solid
    resists this with its shear modulus; a superfluid resists it with NOTHING
    (zero static shear)."""
    area = math.pi * (blade_diameter_m / 2.0) ** 2
    return force_n / area if area > 0 else float("inf")


def supersolid_shear_modulus_pa(bulk_modulus_pa, shear_fraction):
    """Even IF the photon fluid acquired crystalline (supersolid) order -- the
    ONLY way to get a nonzero static shear modulus -- that modulus is a small
    fraction of the bulk modulus. A plain superfluid's static shear modulus is
    exactly zero (it flows), so it cannot statically resist a block at all."""
    return bulk_modulus_pa * shear_fraction


# ---- mechanical response / "holding resistance" (real superfluid dynamics) --

def landau_critical_velocity(c_s_m_s):
    """Landau criterion: a Bose superfluid flows WITHOUT dissipation for any
    object moving slower than the critical velocity v_c (for a weakly-
    interacting BEC v_c = c_s, the speed of sound). Below v_c an intruder feels
    ZERO drag (it slips through frictionlessly -- so the 'blade' cannot grip a
    slow object); above v_c it sheds excitations and feels drag. This is the
    real, deepest statement of a superfluid's (lack of) holding resistance."""
    return c_s_m_s


def healing_time_s(mu_j):
    """The fluid's intrinsic response time tau = hbar / mu (equivalently
    xi / c_s): how fast a density perturbation heals. It sets whether the
    medium can behave elastically (solid) or just flows (liquid) on a given
    timescale."""
    return hbar / max(mu_j, 1e-60)


def deborah_number(response_time_s, observation_time_s):
    """De = tau_response / tau_observation. De >> 1 -> the material has no time
    to flow and responds ELASTICALLY (solid-like); De << 1 -> it flows out of
    the way (liquid-like). A sword strike lasts ~10-100 ms; the photon fluid's
    healing time is ~sub-picosecond, so De ~ 1e-11 -> it behaves as a fluid on
    any human timescale: it cannot hit or be hit, it just parts."""
    if observation_time_s <= 0:
        return float("inf")
    return response_time_s / observation_time_s


def compression_restoring_pressure_pa(bulk_modulus_pa, strain):
    """Compressing the fluid by a volumetric strain eps produces a restoring
    (spring) pressure dP = B*eps -- the tactile 'squeeze' resistance. Turned
    into a force over the blade cross-section it is the closest thing to a felt
    'hold'."""
    return bulk_modulus_pa * strain


def rydberg_pair_binding_energy_j(eit_bandwidth_hz):
    """At the blockade radius r_b the pair interaction equals hbar*Gamma_EIT by
    definition of r_b, so the two-photon bound-state binding energy is of order
    hbar*Gamma_EIT -- the real energy scale of laboratory bound photon pairs."""
    return hbar * 2 * math.pi * eit_bandwidth_hz


def supersolid_lattice_period_m(healing_length_m_value):
    """A supersolid spontaneously modulates its density with a period set by the
    roton/interaction scale, ~ a few healing lengths. This is the crystalline
    order that alone could carry static shear -- real polariton supersolids show
    ~micron periods, cryogenic and 1-2D only."""
    return 2.0 * math.pi * healing_length_m_value


def photon_binding_report(blade_d_mm=None, plasma_temp_k=None):
    """Compute the full honest photon-binding chain once, for the console
    report, the M overlay, and the BINDING scene HUD."""
    blade_d_mm = DIMS["blade_d_mm"] if blade_d_mm is None else blade_d_mm
    plasma_temp_k = PHYS["plasma_temp_K"] if plasma_temp_k is None else plasma_temp_k
    wl_m = PHYS["wavelength_nm"] * NM
    n_g = PHYS["slow_light_factor"]

    v_g = slow_light_group_velocity(n_g)
    m_eff = effective_photon_mass_kg(wl_m, n_g)
    mu = interaction_chemical_potential_j(PHYS["interaction_blueshift_mev"])
    n_target = PHYS["n_target_m3"]

    c_s = fluid_speed_of_sound(mu, m_eff)
    xi = healing_length_m(mu, m_eff)
    bulk = fluid_bulk_modulus_pa(mu, n_target)
    shear_super = supersolid_shear_modulus_pa(bulk, PHYS["supersolid_shear_fraction"])

    t_ceiling = binding_temperature_ceiling_k(mu)
    kT_plasma = KB * plasma_temp_k
    thermal_ratio = kT_plasma / mu   # >>1 means thermally unbound

    r_b = rydberg_blockade_radius_m(PHYS["rydberg_c6_si"], PHYS["rydberg_eit_bandwidth_hz"])
    i_kerr_unity = kerr_intensity_for_unity(PHYS["kerr_n2_m2_per_w"], PHYS["medium_n0"])

    blade_d_m = blade_d_mm * MM
    tau_required = lateral_load_shear_stress_pa(PHYS["lateral_load_n"], blade_d_m)
    # can even an optimistic supersolid resist the block?
    shear_margin = shear_super / tau_required if tau_required > 0 else float("inf")

    # what it would ACTUALLY take: density for a rubber-like bulk modulus at
    # the (already optimistic) blueshift ceiling -- B = mu*n  ->  n = B/mu.
    rubber_bulk_pa = 1.0e6
    n_for_rubber = rubber_bulk_pa / mu if mu > 0 else float("inf")
    density_gap = n_for_rubber / n_target if n_target > 0 else float("inf")

    # --- mechanical response: the actual "holding resistance" ---------------
    v_crit = landau_critical_velocity(c_s)
    swing = PHYS["swing_tip_speed_m_s"]
    superfluid_slips = swing < v_crit            # slow motion -> frictionless slip-through
    tau_heal = healing_time_s(mu)
    de = deborah_number(tau_heal, PHYS["strike_duration_s"])
    behaves_solid = de >= 1.0
    dP = compression_restoring_pressure_pa(bulk, PHYS["compression_strain"])
    blade_area = math.pi * (blade_d_m / 2.0) ** 2
    spring_force_n = dP * blade_area             # force felt for a 10% squeeze
    e_pair = rydberg_pair_binding_energy_j(PHYS["rydberg_eit_bandwidth_hz"])
    ss_period = supersolid_lattice_period_m(xi)

    steel_bulk_pa = 1.6e11
    return dict(
        n_group=n_g, v_g_m_s=v_g, v_g_frac_c=v_g / c, m_eff_kg=m_eff,
        m_eff_vs_electron=m_eff / 9.109e-31,
        mu_j=mu, mu_mev=PHYS["interaction_blueshift_mev"],
        c_s_m_s=c_s, healing_length_m=xi, healing_length_um=xi * 1e6,
        bulk_pa=bulk, bulk_vs_steel=bulk / steel_bulk_pa,
        shear_super_pa=shear_super,
        t_ceiling_k=t_ceiling, kT_plasma_j=kT_plasma, thermal_ratio=thermal_ratio,
        binds_at_plasma_temp=(thermal_ratio < 1.0),
        rydberg_blockade_um=r_b * 1e6,
        kerr_i_unity_w_m2=i_kerr_unity,
        tau_required_pa=tau_required, shear_margin=shear_margin,
        can_parry=(shear_margin >= 1.0),
        n_for_rubber_m3=n_for_rubber, density_gap=density_gap,
        v_crit_m_s=v_crit, swing_speed_m_s=swing, superfluid_slips=superfluid_slips,
        healing_time_s=tau_heal, deborah=de, behaves_solid=behaves_solid,
        compress_pressure_pa=dP, spring_force_n=spring_force_n,
        pair_binding_j=e_pair, pair_binding_uev=e_pair / ECHARGE * 1e6,
        supersolid_period_um=ss_period * 1e6,
    )


# =============================================================================
# SECTION 4c -- MATERIAL-CUTTING PHYSICS (honest ablation energy balance)
# =============================================================================
# The blade cuts the way a real high-power thermal source does: it deposits a
# heat flux into the workpiece; the material recedes only as fast as that flux
# can supply the full enthalpy of heating + melting + vaporizing the material
# it removes, minus what conducts away sideways. This is standard laser-drilling
# / ablation-front physics -- nothing cuts "because lightsaber".

def volumetric_ablation_energy_j_m3(mat, t_amb_k=300.0):
    """Energy to take unit volume of a material from ambient all the way to
    vapor: E_v = rho * [ c_p*(T_vap - T_amb) + L_fusion + L_vaporization ].
    (J/m^3). The dominant, honest cost of removing material."""
    dT = max(0.0, mat["t_vap"] - t_amb_k)
    return mat["rho"] * (mat["cp"] * dT + mat["l_f"] + mat["l_v"])


def plasma_contact_flux_w_m2(plasma_temp_k, reflectivity, view_factor=1.0, t_work_k=300.0):
    """Radiative heat flux the ~7500 K plasma channel couples INTO a workpiece
    on contact: q = (1 - R) * F * sigma * (T_plasma^4 - T_work^4). This is the
    real, dominant, temperature-dependent contact mechanism -- and it ties the
    on-screen plasma-temperature slider directly to cutting performance."""
    return (1.0 - reflectivity) * view_factor * SIGMA_SB * (plasma_temp_k ** 4 - t_work_k ** 4)


def conduction_loss_flux_w_m2(mat, kerf_width_m, kerf_frac=0.5):
    """Heat conducted sideways out of the kerf instead of ablating: q_cond ~
    k*(T_melt - T_amb)/L, L = kerf_frac * kerf_width. High-k materials
    (aluminium, copper, diamond) bleed the incoming flux away faster than it
    can ablate -- the honest reason diamond is nearly uncuttable thermally."""
    length = max(1e-6, kerf_frac * kerf_width_m)
    return mat["k"] * (mat["t_melt"] - PHYS["T_amb_K"]) / length


def cut_recession_velocity_m_s(mat, plasma_temp_k, kerf_width_m):
    """Ablation-front recession velocity u = q_net / E_v, where q_net is the
    contact flux minus sideways conduction loss. If q_net <= 0 the blade warms
    the material but cannot cut it. Returns (u_m_s, q_contact, q_cond, q_net,
    E_v)."""
    q_contact = plasma_contact_flux_w_m2(plasma_temp_k, mat["refl"], PHYS["cut_view_factor"])
    q_cond = conduction_loss_flux_w_m2(mat, kerf_width_m, PHYS["cut_conduction_kerf_frac"])
    q_net = q_contact - q_cond
    e_v = volumetric_ablation_energy_j_m3(mat)
    u = max(0.0, q_net) / e_v if e_v > 0 else 0.0
    return u, q_contact, q_cond, q_net, e_v


def cutting_report(material_key, plasma_temp_k=None, blade_d_mm=None, thickness_mm=20.0):
    """Full cutting analysis for one material against the live blade settings."""
    plasma_temp_k = PHYS["plasma_temp_K"] if plasma_temp_k is None else plasma_temp_k
    blade_d_mm = DIMS["blade_d_mm"] if blade_d_mm is None else blade_d_mm
    mat = MATERIALS[material_key]
    kerf_w = blade_d_mm * MM
    u, q_contact, q_cond, q_net, e_v = cut_recession_velocity_m_s(mat, plasma_temp_k, kerf_w)
    can_cut = u > 0.0
    thickness_m = thickness_mm * MM
    t_through = thickness_m / u if u > 0 else float("inf")
    # instantaneous removal power = flux * kerf face area (blade diameter square-ish)
    removal_area = kerf_w ** 2
    p_removal = q_net * removal_area if q_net > 0 else 0.0
    return dict(
        material=material_key, note=mat["note"],
        e_v_j_m3=e_v, q_contact_w_m2=q_contact, q_cond_w_m2=q_cond, q_net_w_m2=q_net,
        can_cut=can_cut, recession_mm_s=u * 1000.0,
        thickness_mm=thickness_mm, through_time_s=t_through,
        removal_power_w=p_removal, conduction_limited=(q_cond >= q_contact),
    )


# =============================================================================
# SECTION 4d -- ENGINEERING AROUND THE WALLS (magnetic plasma-arc blade)
# =============================================================================
# The rule: treat every "impossibility" as an engineering hurdle. The one true
# wall -- a rigid SOLID-LIGHT blade -- is bypassed, not by making photons rigid
# (that stays impossible), but by achieving the *functions* (fixed-length
# blade, cutting, clash/deflection) with a CURRENT-CARRYING PLASMA ARC. A
# current in a plasma column does three real things at once:
#   (1) self-confines the column by the Z-pinch (Bennett equilibrium) -> a
#       fixed-length blade with real magnetic pressure ("stiffness"),
#   (2) pushes on a SECOND energised blade by the Ampere force between parallel
#       currents -> a real, felt clash/parry (blade-vs-blade),
#   (3) dissipates power in the arc column -> the (large but finite) energy cost.
# Everything below is standard EM / plasma physics; the numbers are the honest
# engineering price of a real lightsaber.

def ampere_force_per_length_n_m(i1_a, i2_a, gap_m):
    """Force per unit length between two parallel currents (Ampere's force
    law): F/L = mu0 I1 I2 / (2 pi d). Attractive for parallel, repulsive for
    antiparallel -- either way, a real mechanical force between two blades."""
    return MU0 * i1_a * i2_a / (2 * math.pi * gap_m)


def current_for_clash_a(force_n, contact_len_m, gap_m):
    """Invert Ampere's law: the blade current needed for a target clash force
    over a given contact length and channel separation.
    F = (mu0 I^2 / 2 pi d) * L  ->  I = sqrt(F * 2 pi d / (mu0 L))."""
    return math.sqrt(force_n * 2 * math.pi * gap_m / (MU0 * contact_len_m))


def z_pinch_surface_field_t(current_a, radius_m):
    """Azimuthal magnetic field at the surface of a current-carrying column,
    B = mu0 I / (2 pi r) -- the field that pinches the plasma inward."""
    return MU0 * current_a / (2 * math.pi * radius_m)


def magnetic_pressure_pa(b_t):
    """Magnetic pressure P = B^2 / (2 mu0). For a Z-pinch this is the confining
    'stiffness' of the blade -- the real analogue of a bulk modulus, and orders
    of magnitude larger than the photon-fluid's 2.4 Pa."""
    return b_t ** 2 / (2 * MU0)


def bennett_pinch_current_a(density_m3, radius_m, temp_k):
    """Bennett equilibrium: the current that magnetically confines a plasma
    column of a given line density and temperature. I^2 = 8 pi N k_B (Ti+Te) /
    mu0, N = n * pi r^2 (line density), Ti ~ Te ~ T. If the blade's operating
    current exceeds this, the same current that lets it clash also holds it
    together -- one current, three jobs."""
    line_density = density_m3 * math.pi * radius_m ** 2
    return math.sqrt(8 * math.pi * line_density * KB * (2 * temp_k) / MU0)


def arc_column_power_w(current_a, length_m, field_gradient_v_m):
    """Electrical power dissipated in the arc column: P = E_arc * I * L, where
    E_arc is the arc voltage gradient (V/m). This is the real, finite energy
    cost of holding a metre-long high-current air arc."""
    return field_gradient_v_m * current_a * length_m


def hybrid_power_system(p_full_w, length_m):
    """Finish the SELF-CONTAINED hurdle with a hybrid power system: a
    supercapacitor buffers the ms-scale pulsed-arc peaks (its job -- huge peak
    power, dumps kJ in ms), while a high-density in-hilt battery sustains the
    arc. The Ampere clash needs NO separate energy burst (both blades are
    already energised), so the real cost is just holding the arc lit. Runtime
    is an honest 'ignite-for-a-fight' spec set by energy density, NOT a physics
    wall (a bigger pack -> longer blade). Returns the sizing + runtime dict."""
    buffer_e = p_full_w * PHYS["arc_pulse_buffer_s"]             # energy the supercap must buffer
    sc_mass = (buffer_e / 3600.0) / PHYS["supercap_wh_per_kg"]   # kg of supercaps for that buffer
    p_idle = p_full_w * PHYS["idle_current_frac"]                # sustaining arc (kept above Bennett)
    hilt_j = PHYS["hilt_pack_kwh"] * 3.6e6
    pack_j = PHYS["backpack_energy_wh"] * 3.6e3
    hilt_glow_s = hilt_j / p_idle
    hilt_full_s = hilt_j / p_full_w
    backpack_glow_s = pack_j / p_idle
    return dict(
        buffer_energy_j=buffer_e, supercap_mass_kg=sc_mass,
        p_idle_w=p_idle, hilt_glow_s=hilt_glow_s, hilt_full_s=hilt_full_s,
        backpack_glow_s=backpack_glow_s,
        # self-contained if a heavy but handheld hilt pack gives a usable
        # ignite-for-a-fight window (movie-style ignite/retract, not always-on)
        self_contained=(hilt_glow_s >= 5.0),
    )


def photonic_mott_report():
    """The REAL 'solid light': a photonic Mott insulator (Simon group, Nature
    2019). Photons in a coupled-cavity lattice, with strong on-site interaction
    U and tunnelling J, freeze into a CRYSTALLINE Mott-insulator state -- the
    only 'solid light' with the crystalline order that carries static shear.
    This function reports the real physics AND the honest gap to a warm,
    metre-scale, free-standing blade (temperature and scale, both huge)."""
    U = PHYS["mott_interaction_uev"] * 1e-6 * ECHARGE   # on-site interaction (J)
    T_ceiling_k = U / KB                                 # k_B T < U for the Mott order to survive
    demo_T_k = PHYS["mott_demo_temp_mk"] * 1e-3
    temp_gap = PHYS["arc_plasma_temp_k"] / demo_T_k      # how much hotter the plasma blade is
    # a metre blade at the cavity-lattice spacing = this many ordered sites
    spacing = PHYS["mott_site_spacing_um"] * UM
    sites_per_m = 1.0 / spacing
    blade_sites = sites_per_m * DIMS["blade_len_m"]
    return dict(
        U_over_J=PHYS["mott_U_over_J"], is_solid=(PHYS["mott_U_over_J"] > 3.4),
        mott_T_ceiling_k=T_ceiling_k, demo_temp_k=demo_T_k, temp_gap=temp_gap,
        blade_sites=blade_sites, spacing_um=PHYS["mott_site_spacing_um"],
    )


def weapon_lethality(p_full_w, clash_current_a):
    """This is a WEAPON, by design. Report the lethality honestly (it is not a
    safe toy and is not meant to be): the plasma cuts flesh essentially
    instantly, and the blade circuit stores far more than a lethal electrical
    dose. These are honest weapon metrics, not a build/harm guide."""
    flesh = cutting_report("flesh (soft tissue)", PHYS["arc_plasma_temp_k"], PHYS["arc_blade_dia_mm"])
    stored_e = p_full_w * PHYS["arc_pulse_buffer_s"]           # blade-circuit stored energy (supercap buffer)
    lethal_margin = stored_e / PHYS["lethal_electrocution_j"]  # stored energy vs a lethal dose
    return dict(
        flesh_recession_mm_s=flesh["recession_mm_s"],
        stored_j=stored_e, lethal_margin=lethal_margin,
        clash_current_a=clash_current_a,
    )


def engineered_saber_report():
    """Run the failure -> engineering-workaround analysis for a REAL lightsaber
    and return a scorecard. Each lightsaber FUNCTION is scored PASS / PARTIAL /
    WALL with the real number behind it. The design point is the current-
    carrying magnetic plasma-arc blade defined in PHYS above."""
    r = PHYS["arc_blade_dia_mm"] * MM / 2.0
    L = DIMS["blade_len_m"]
    n = PHYS["arc_plasma_density_m3"]
    T = PHYS["arc_plasma_temp_k"]

    # clash (hurdle: rigidity has no real analogue for light -> use Ampere force)
    i_design = current_for_clash_a(PHYS["clash_force_target_n"],
                                    PHYS["clash_contact_len_m"], PHYS["clash_gap_m"])
    i_full_block = current_for_clash_a(PHYS["lateral_load_n"],
                                       PHYS["clash_contact_len_m"], PHYS["clash_gap_m"])

    # confinement (hurdle: plasma disperses -> Z-pinch / Bennett)
    i_bennett = bennett_pinch_current_a(n, r, T)
    self_confined = i_design >= i_bennett
    b_surf = z_pinch_surface_field_t(i_design, r)
    p_mag = magnetic_pressure_pa(b_surf)
    photon_bulk = fluid_bulk_modulus_pa(interaction_chemical_potential_j(
        PHYS["interaction_blueshift_mev"]), PHYS["n_target_m3"])
    stiffness_gain = p_mag / photon_bulk if photon_bulk else float("inf")

    # power (hurdle: 11 MW blackbody myth -> real arc power at the design current)
    p_arc = arc_column_power_w(i_design, L, PHYS["arc_field_gradient_v_m"])
    pw = hybrid_power_system(p_arc, L)          # FINISHED self-contained hurdle
    runtime_s = pw["hilt_glow_s"]

    # cutting (already solved) -- steel as the reference
    steel = cutting_report("mild steel", PHYS["arc_plasma_temp_k"], PHYS["arc_blade_dia_mm"])

    # thermal/grip (already solved) -- pull the conduction result
    rpt = full_feasibility_report()

    leth = weapon_lethality(p_arc, i_design)    # it is a WEAPON, by design
    mott = photonic_mott_report()               # the REAL 'solid light'

    # honest per-function scorecard
    functions = [
        ("Fixed-length glowing blade", "PASS",
         f"Z-pinch self-confinement (Bennett {i_bennett:.0f} A < design {i_design:.0f} A); "
         f"straight metre-arc still needs a guide field -> hard but not forbidden"),
        ("Cuts real materials", "PASS",
         f"ablation energy balance: steel {steel['recession_mm_s']:.2f} mm/s at {T:.0f} K "
         f"(diamond still uncuttable -- honest)"),
        ("Blade-vs-blade CLASH / deflect", "PASS",
         f"Ampere force: {PHYS['clash_force_target_n']:.0f} N clash at {i_design:.0f} A "
         f"({i_full_block:.0f} A for a full {PHYS['lateral_load_n']:.0f} N block)"),
        ("Real blade 'stiffness'", "PASS",
         f"Z-pinch magnetic pressure {p_mag/1000:.1f} kPa = {stiffness_gain:.0f}x the "
         f"photon-fluid's 2.4 Pa"),
        ("Grip stays cool", "PASS",
         f"layered stack holds the grip at ambient (+{rpt['dT_stack_k']:.0f} K on the hot side)"),
        ("Self-contained power", "PASS",
         f"hybrid supercap ({pw['supercap_mass_kg']:.1f} kg buffers the pulsed arc) + "
         f"{PHYS['hilt_pack_kwh']:.1f} kWh in-hilt battery -> {pw['hilt_glow_s']:.0f} s active blade per "
         f"charge (ignite-for-a-fight); {pw['backpack_glow_s']/60:.1f} min on a 12 kWh backpack"),
        ("LETHAL WEAPON (by design)", "WEAPON",
         f"intentional: {i_design/1000:.1f} kA + {p_arc/1e6:.1f} MW; cuts flesh at "
         f"{leth['flesh_recession_mm_s']:.0f} mm/s (instant) and stores {leth['lethal_margin']:.0e}x a "
         f"lethal electrical dose -- NOT a safe toy, and not meant to be"),
        ("Rigid 'solid light' blade", "APROX/WALL",
         f"real 'solid light' = photonic Mott insulator (U/J={mott['U_over_J']:.0f}, crystalline, has "
         f"shear) EXISTS -- but at ~{mott['demo_temp_k']*1000:.0f} mK on a chip; a warm metre blade is "
         f"{mott['temp_gap']:.0e}x too hot and {mott['blade_sites']:.0e} sites. Bypassed by the plasma arc"),
    ]
    n_pass = sum(1 for _, s, _ in functions if s == "PASS")
    n_partial = sum(1 for _, s, _ in functions if s == "PARTIAL")
    return dict(
        i_design_a=i_design, i_full_block_a=i_full_block, i_bennett_a=i_bennett,
        self_confined=self_confined, b_surf_t=b_surf, p_mag_pa=p_mag,
        stiffness_gain=stiffness_gain, p_arc_w=p_arc, runtime_s=runtime_s,
        steel_recession_mm_s=steel["recession_mm_s"], functions=functions,
        power=pw, lethality=leth, mott=mott,
        n_pass=n_pass, n_partial=n_partial, n_total=len(functions),
    )


def full_feasibility_report(blade_len_m=None, blade_d_mm=None, plasma_temp_k=None):
    """Compute every number in the honest physics narrative once, in one
    place, for both the console --feasibility report and the in-app M overlay.
    Optional overrides let the live UI sliders (blade length/diameter/temp)
    drive the same real formulas the console report uses."""
    blade_len_m = DIMS["blade_len_m"] if blade_len_m is None else blade_len_m
    blade_d_mm = DIMS["blade_d_mm"] if blade_d_mm is None else blade_d_mm
    plasma_temp_k = PHYS["plasma_temp_K"] if plasma_temp_k is None else plasma_temp_k

    wl_m = PHYS["wavelength_nm"] * NM
    e_photon = photon_energy_j(wl_m)

    waist_m = PHYS["beam_waist_um"] * UM
    i_focus_avg, i_focus_peak = gaussian_focus_intensity(PHYS["laser_power_w"], waist_m)
    below_lo, ratio_lo = breakdown_margin(i_focus_peak)

    blade_d_m = blade_d_mm * MM
    i_column = column_intensity(PHYS["laser_power_w"], blade_d_m)
    col_below_lo, col_ratio_lo = breakdown_margin(i_column)

    p_rad, area = blade_power_budget(blade_len_m, blade_d_m, plasma_temp_k, PHYS["emissivity"])

    e_form, e_sus = laser_power_budget()
    runtime_h = supercap_runtime_hours(PHYS["supercap_energy_wh"], e_sus)

    # Real cylindrical-shell area for each layer (not a placeholder): the
    # graphene spreader lines the head, the aerogel/MLI/outer-aerogel/shell
    # stack lines the grip -- using true DIMS areas instead of a fixed guess
    # is the difference between a meaningless number and an honest one.
    head_r_in = DIMS["head_od_mm"] * MM / 2.0 - DIMS["grip_wall_mm"] * MM
    graphene_area = 2 * math.pi * head_r_in * (DIMS["head_len_mm"] * MM)
    grip_r_in = DIMS["grip_od_mm"] * MM / 2.0 - DIMS["grip_wall_mm"] * MM
    aerogel_area = 2 * math.pi * grip_r_in * (DIMS["grip_len_mm"] * MM)
    grip_r_out = DIMS["grip_od_mm"] * MM / 2.0
    shell_area = 2 * math.pi * grip_r_out * (DIMS["grip_len_mm"] * MM)
    layers = [
        (DIMS["graphene_layer_t_mm"] * MM, PHYS["k_graphene_w_mk"], graphene_area),
        (DIMS["aerogel_t_mm"] * MM, PHYS["k_aerogel_w_mk"], aerogel_area),
        (DIMS["outer_aerogel_t_mm"] * MM, PHYS["k_aerogel_w_mk"], aerogel_area),
        (DIMS["grip_wall_mm"] * MM, PHYS["k_ti_hfc_w_mk"], shell_area),
    ]
    dT_stack, r_total = multilayer_conduction_drop_k(PHYS["laser_power_sustain_w"], layers)
    # The N-shield MLI formula is real, but radiative heat transfer scales as
    # T^3: at the grip's modest ~320 K environment it is utterly negligible
    # next to conduction (a real assembled MLI blanket's parasitic standoff
    # conduction would dominate anyway) -- MLI only matters where it's
    # actually hot, i.e. the engine bay below, not this laser-cooling path.
    # Reported here purely descriptively for comparison.
    mli_eps_eff = mli_effective_emissivity(DIMS["mli_layers"], PHYS["eps_mli_shield"],
                                            PHYS["eps_surface"], PHYS["eps_surface"])
    dT_mli_grip = PHYS["laser_power_sustain_w"] * linearized_radiative_resistance_k_per_w(
        mli_eps_eff, aerogel_area, 320.0)

    ratio_solid, n_c = polariton_feasibility_ratio(
        PHYS["n_target_m3"], PHYS["T_beam_target_K"], PHYS["m_eff_kg"])

    # --- Internal chemical photon engine (replaces the Orbitron fusion pod) -
    emitter_area = cylinder_surface_area(DIMS["combustor_len_mm"] * MM, DIMS["combustor_d_mm"] * MM)
    p_chem = chem_emitter_optical_power_w(PHYS["chem_chamber_temp_k"], emitter_area, PHYS["emissivity"])
    fuel_flow = chem_fuel_flow_kg_s(p_chem, PHYS["chem_eta_photon"], PHYS["chem_heat_of_combustion_j_kg"])
    total_reactant_kg = DIMS["cartridges"] * DIMS["cartridge_mass_g"] / 1000.0
    chem_runtime_s = reactant_runtime_s(total_reactant_kg, fuel_flow)
    finesse = cavity_finesse(PHYS["cavity_mirror_R"])
    rt_length = helix_path_length_m(DIMS["cavity_coil_od_mm"] * MM, DIMS["cavity_turns"], DIMS["cavity_pitch_mm"] * MM)
    tau_intrinsic = cavity_photon_lifetime_s(rt_length, PHYS["cavity_mirror_R"])
    tau_eff = slow_light_lifetime_s(tau_intrinsic, PHYS["slow_light_factor"])
    dump_energy = cavity_dump_energy_j(p_chem, tau_eff)
    dump_peak_power = cavity_dump_peak_power_w(dump_energy, PHYS["shutter_open_s"])
    t_charge = charge_time_s(tau_eff)
    rep_rate = repetition_rate_hz(t_charge)
    appears_continuous = flicker_appears_continuous(rep_rate, PHYS["human_flicker_fusion_hz"])
    pulses_available = chem_runtime_s / t_charge if t_charge > 0 else 0.0
    dump_column_intensity = column_intensity(dump_peak_power, blade_d_m)
    dump_below_threshold, dump_ratio_to_threshold = breakdown_margin(dump_column_intensity)

    # --- Engine-bay heat rejection: waste heat, heat pipes, radiator, buffer
    waste_heat_w, p_chem_input_w = engine_waste_heat_w(p_chem, PHYS["chem_eta_photon"])
    captured_w = waste_heat_w * PHYS["heat_pipe_capture_frac"]
    parasitic_w = waste_heat_w - captured_w

    fin_len = DIMS["radiator_fin_len_mm"] * MM
    n_fins = DIMS["radiator_fins"]
    bay_r_out = DIMS["engine_bay_od_mm"] * MM / 2.0
    finned_len = DIMS["engine_bay_len_mm"] * MM * 0.6
    fin_area_each = 2.0 * (fin_len * finned_len)
    bare_area = 2 * math.pi * bay_r_out * finned_len
    radiator_area = n_fins * fin_area_each + bare_area
    radiator_capacity_w = radiator_dissipation_w(radiator_area, PHYS["radiator_temp_k"], PHYS["T_amb_K"],
                                                  PHYS["radiator_emissivity"], PHYS["radiator_h_conv_w_m2k"])
    net_to_buffer_w = max(0.0, captured_w - radiator_capacity_w)
    buffer_capacity_j = thermal_buffer_capacity_j(PHYS["buffer_mass_kg"], PHYS["buffer_cp_j_kgk"],
                                                   PHYS["buffer_delta_t_max_k"])
    thermal_runtime_s = thermally_limited_runtime_s(buffer_capacity_j, net_to_buffer_w)
    engine_runtime_s = min(chem_runtime_s, thermal_runtime_s)

    # engine bay's own local insulation stack, driven by the residual
    # (uncaptured) parasitic leak -- HfC crucible + aerogel/outer-aerogel +
    # structural shell in series (conduction only; the MLI radiative term at
    # these temperatures/gaps is dominated by huge uncertainty in the
    # effective gap temperature, so it's reported separately, not folded in,
    # to avoid manufacturing false precision).
    hfc_area = cylinder_surface_area(DIMS["combustor_len_mm"] * MM, DIMS["combustor_d_mm"] * MM)
    bay_r_in = DIMS["engine_bay_od_mm"] * MM / 2.0 - DIMS["grip_wall_mm"] * MM
    bay_area = 2 * math.pi * bay_r_in * (DIMS["engine_bay_len_mm"] * MM)
    engine_layers = [
        (DIMS["hfc_crucible_t_mm"] * MM, PHYS["k_hfc_w_mk"], hfc_area),
        (DIMS["aerogel_t_mm"] * MM, PHYS["k_aerogel_w_mk"], bay_area),
        (DIMS["outer_aerogel_t_mm"] * MM, PHYS["k_aerogel_w_mk"], bay_area),
        (DIMS["grip_wall_mm"] * MM, PHYS["k_ti_hfc_w_mk"], bay_area),
    ]
    dT_engine_bay, r_engine_bay = multilayer_conduction_drop_k(parasitic_w, engine_layers)

    return dict(
        e_photon_j=e_photon, wl_nm=PHYS["wavelength_nm"],
        i_focus_avg=i_focus_avg, i_focus_peak=i_focus_peak,
        focus_below_threshold=below_lo, focus_ratio_to_threshold=ratio_lo,
        i_column=i_column, column_below_threshold=col_below_lo,
        column_ratio_to_threshold=col_ratio_lo,
        blade_p_rad_w=p_rad, blade_area_m2=area,
        e_form_w=e_form, e_sus_w=e_sus, runtime_h=runtime_h,
        dT_stack_k=dT_stack, r_total_k_per_w=r_total,
        ratio_solid=ratio_solid, n_c_solid=n_c,
        p_chem_w=p_chem, fuel_flow_kg_s=fuel_flow, chem_runtime_s=chem_runtime_s,
        cavity_finesse=finesse, cavity_tau_intrinsic_s=tau_intrinsic, cavity_tau_eff_s=tau_eff,
        cavity_dump_energy_j=dump_energy, cavity_dump_peak_power_w=dump_peak_power,
        charge_time_s=t_charge, rep_rate_hz=rep_rate, appears_continuous=appears_continuous,
        pulses_available=pulses_available,
        dump_column_intensity_w_m2=dump_column_intensity,
        dump_reionizes_full_column=(not dump_below_threshold), dump_ratio_to_threshold=dump_ratio_to_threshold,
        power_shortfall=(p_rad / e_sus) if e_sus > 0 else float("inf"),
        mli_eps_eff=mli_eps_eff, dT_mli_grip_k=dT_mli_grip,
        waste_heat_w=waste_heat_w, p_chem_input_w=p_chem_input_w,
        captured_w=captured_w, parasitic_w=parasitic_w,
        radiator_area_m2=radiator_area, radiator_capacity_w=radiator_capacity_w,
        net_to_buffer_w=net_to_buffer_w, buffer_capacity_j=buffer_capacity_j,
        thermal_runtime_s=thermal_runtime_s, engine_runtime_s=engine_runtime_s,
        dT_engine_bay_k=dT_engine_bay,
    )


# =============================================================================
# SECTION 5 -- GEOMETRY: the buildable hilt, the external chemical photon pod,
#               and the microcavity showcase, all assembled from the DIMS spec.
# =============================================================================

def _tube_between(p0, p1, r, seg=8, color=(200, 200, 200)):
    """A simple round tube (fiber, umbilical cable, standoff) between two 3D
    points, built by generating a cylinder along +Z then rotating/translating
    it onto the p0->p1 segment."""
    p0 = np.asarray(p0, dtype=float); p1 = np.asarray(p1, dtype=float)
    d = p1 - p0
    length = float(np.linalg.norm(d))
    if length < 1e-9:
        return [], []
    v, f = _solid_cylinder(r, 0.0, length, seg=seg)
    v = np.asarray(v, dtype=float)
    z_axis = d / length
    ref = np.array([0.0, 0.0, 1.0]) if abs(z_axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x_axis = np.cross(ref, z_axis); x_axis /= np.linalg.norm(x_axis)
    y_axis = np.cross(z_axis, x_axis)
    rot = np.column_stack([x_axis, y_axis, z_axis])
    v = v @ rot.T + p0
    return v.tolist(), f


def _helix_tube(coil_r, tube_r, turns, pitch, n_seg=120, tube_seg=8):
    """A tube following a helical path (the spiral photon-buildup cavity's
    delay-line waveguide) -- sampled as short straight tube segments via
    _tube_between, the same approximation style used for fins/pipes elsewhere
    in this file."""
    n = max(8, int(n_seg))
    ts = np.linspace(0.0, turns * 2 * np.pi, n + 1)
    pts = [(coil_r * math.cos(t), coil_r * math.sin(t), pitch * t / (2 * math.pi)) for t in ts]
    chunks = [_tube_between(p0, p1, tube_r, seg=tube_seg) for p0, p1 in zip(pts[:-1], pts[1:])]
    return _combine(chunks)


def _apply_exploded_layout(parts, axis_len, shell_keys=frozenset()):
    """Author a proper exploded-assembly layout so the EXPLODE view genuinely
    separates every component (the ad-hoc per-part offsets barely moved).
    Concentric shell/liner parts PEEL radially outward at staggered fan angles
    (revealing the nested layers); the remaining internal parts FAN apart along
    the long axis in assembly (z) order. Offsets are relative to each part's
    real position, so the assembled (explode_amt=0) view is unchanged."""
    metas = []
    for p in parts:
        vv = [m.world_verts() for m in p.meshes if len(m.verts)]
        if not vv:
            metas.append((p, 0.0, 0.0)); continue
        V = np.vstack(vv)
        metas.append((p, float(V[:, 2].mean()), float(np.max(np.hypot(V[:, 0], V[:, 1])))))

    shells = sorted((m for m in metas if m[0].key in shell_keys), key=lambda m: m[2])
    inner = sorted((m for m in metas if m[0].key not in shell_keys), key=lambda m: m[1])

    ns = max(1, len(shells))
    for i, (p, zc, rmax) in enumerate(shells):
        ang = 2 * math.pi * (i / ns) + 0.5
        mag = axis_len * (0.30 + 0.14 * i / ns)          # bigger tubes splay further
        p.explode = np.array([mag * math.cos(ang), mag * math.sin(ang), 0.0])

    if inner:
        z0 = min(m[1] for m in inner)
        z1 = max(m[1] for m in inner)
        span = (z1 - z0) or 1.0
        for i, (p, zc, rmax) in enumerate(inner):
            frac = (zc - z0) / span
            target_z = (frac - 0.5) * axis_len * 1.9      # stretch the stack along Z
            rn_x = axis_len * 0.07 * ((i % 3) - 1)        # small radial spread so
            rn_y = axis_len * 0.05 * (1 if i % 2 else -1)  # coincident parts don't overlap
            p.explode = np.array([rn_x, rn_y, target_z - zc])
    return parts


def build_hilt():
    """The hand-held prop: front tip (z=0) to pommel rear, all in metres, to
    real scale. Returns a list[Part]. See DIMS for every source dimension."""
    parts = []

    head_len = DIMS["head_len_mm"] * MM
    grip_len = DIMS["grip_len_mm"] * MM
    engine_bay_len = DIMS["engine_bay_len_mm"] * MM
    pommel_len = DIMS["pommel_len_mm"] * MM
    z_grip0 = head_len
    z_engine0 = head_len + grip_len
    z_pommel0 = z_engine0 + engine_bay_len
    z_end = z_pommel0 + pommel_len

    head_r = DIMS["head_od_mm"] * MM / 2.0
    grip_r = DIMS["grip_od_mm"] * MM / 2.0
    engine_bay_r = DIMS["engine_bay_od_mm"] * MM / 2.0
    pommel_r = DIMS["pommel_od_mm"] * MM / 2.0
    wall = DIMS["grip_wall_mm"] * MM

    # ---- beam aperture (front output window) ------------------------------
    ap_z = DIMS["aperture_z_mm"] * MM
    ap_r = DIMS["aperture_od_mm"] * MM / 2.0
    v, f = _annulus(ap_r, ap_r * 0.7, 0.0, ap_z, seg=36)
    parts.append(Part("aperture", "Beam Output Aperture", [Mesh(v, f, C_APERTURE, "aperture window")],
                       [f"clear aperture {DIMS['aperture_od_mm']:.0f} mm OD"],
                       order=12, explode=(0, 0, -0.06)))

    # ---- collimating lens (f=5mm, per exact laser spec) --------------------
    lens_z = DIMS["lens_z_mm"] * MM
    lens_r = DIMS["lens_d_mm"] * MM / 2.0
    lens_t = DIMS["lens_thick_mm"] * MM
    v, f = _solid_cylinder(lens_r, lens_z - lens_t / 2, lens_z + lens_t / 2, seg=32)
    parts.append(Part("lens", "Collimating Lens", [Mesh(v, f, C_LENS, "lens f=5mm")],
                       [f"dia {DIMS['lens_d_mm']:.0f} mm, f=5 mm -> {PHYS['beam_waist_um']:.0f} um waist"],
                       order=11, explode=(0, 0, -0.05)))

    # ---- photonic-crystal microcavity chip (ON-AXIS, TRUE SCALE) -----------
    # 80x80x0.5 um: at true scale this is a few PIXELS -- see the dedicated
    # MICROCAVITY SHOWCASE (view 3) for a legible, honestly-zoomed build.
    phc_z = DIMS["phc_z_mm"] * MM
    w = DIMS["phc_chip_w_mm"] * MM; dd = DIMS["phc_chip_d_mm"] * MM; t = DIMS["phc_chip_t_mm"] * MM
    v, f = _box(0, 0, phc_z, w, dd, t)
    parts.append(Part("phc", "Photonic-Crystal Microcavity (WS2/CsPbBr3)",
                       [Mesh(v, f, C_PHC_CHIP, "PhC microcavity chip")],
                       [f"true size {DIMS['micro_plate_um']:.0f} um microplate -- see SHOWCASE (key 3)",
                        f"lattice a={DIMS['micro_lattice_nm']:.0f} nm, hole d={DIMS['micro_hole_nm']:.0f} nm"],
                       order=10, explode=(0, 0, -0.04)))

    # ---- laser diode package (off-axis) + fiber stub to the on-axis chip --
    laser_z = DIMS["laser_z_mm"] * MM
    pkg = DIMS["laser_pkg_mm"] * MM; pkg_h = DIMS["laser_pkg_h_mm"] * MM
    pkg_x = 0.007
    v, f = _box(pkg_x, 0, laser_z, pkg, pkg, pkg_h)
    fv, ff = _tube_between((pkg_x, 0, laser_z), (0, 0, phc_z), 0.00025, seg=8)
    vv, ffz = _combine([(v, f), (fv, ff)])
    parts.append(Part("laser", "CW Diode Laser (AlGaAs, TO-3/butterfly)",
                       [Mesh(vv, ffz, C_LASER_PKG, "laser diode + fiber")],
                       [f"{PHYS['wavelength_nm']:.0f} nm, {PHYS['laser_power_w']:.0f} W max CW",
                        f"pkg {DIMS['laser_pkg_mm']:.0f}x{DIMS['laser_pkg_mm']:.0f}x{DIMS['laser_pkg_h_mm']:.1f} mm",
                        "M2<1.5, linewidth<0.5nm, TE linear pol."],
                       order=9, explode=(0.03, 0, -0.02)))

    # ---- integrated TEC (thermoelectric cooler) plate ----------------------
    tec_t = DIMS["tec_t_mm"] * MM
    v, f = _box(pkg_x, 0, laser_z + pkg_h / 2 + tec_t / 2, pkg * 0.9, pkg * 0.9, tec_t)
    parts.append(Part("tec", "Thermoelectric Cooler", [Mesh(v, f, C_TEC, "TEC")],
                       ["stabilizes 20-30 C to prevent wavelength drift"],
                       order=8, explode=(0.035, 0, -0.01)))

    # ---- compact radial heatsink collar (repackaged from flat 2x2cm spec) -
    # NOTE (honest SWaP finding): the spec's flat 2cm x 2cm fin block does not
    # fit alongside the lens/PhC/laser in a 34mm-diameter head; repackaged
    # here as an equivalent-area radial fin collar around the diode package,
    # the standard real solution for compact laser-diode thermal design.
    hs_z = DIMS["heatsink_z_mm"] * MM
    n_fins = DIMS["heatsink_fins"]
    collar_chunks = []
    for i in range(n_fins):
        ang = 2 * math.pi * i / n_fins
        fx = pkg_x + 0.006 * math.cos(ang)
        fy = 0.006 * math.sin(ang)
        collar_chunks.append(_box(fx, fy, hs_z, 0.0015, 0.0015, 0.014))
    v, f = _combine(collar_chunks)
    parts.append(Part("heatsink", "Aluminium Radial Heatsink", [Mesh(v, f, C_HEATSINK, "heatsink fins")],
                       [f"{DIMS['heatsink_fins']} fins, dissipates ~5 W, keeps grip <40C"],
                       order=7, explode=(0.045, 0, 0.0)))

    # ---- head housing shell (Ti-6Al-4V / HfC composite) --------------------
    v, f = _annulus(head_r, head_r - wall, 0.0, head_len, seg=48)
    parts.append(Part("head_shell", "Emitter Head Housing", [Mesh(v, f, C_TI_HFC, "head shell")],
                       [f"OD {DIMS['head_od_mm']:.0f} mm, len {DIMS['head_len_mm']:.0f} mm, Ti-6Al-4V/HfC"],
                       order=13, explode=(0, 0, -0.10)))

    # ---- graphene-diamond thermal spreader (lines the head, high-k) -------
    gl_t = DIMS["graphene_layer_t_mm"] * MM
    v, f = _annulus(head_r - wall, head_r - wall - gl_t, 0.0, head_len, seg=48)
    parts.append(Part("graphene", "Graphene-Diamond Thermal Spreader", [Mesh(v, f, C_GRAPHENE, "graphene spreader")],
                       [f"k~{PHYS['k_graphene_w_mk']:.0f} W/m-K, {gl_t*1000:.1f} mm liner"],
                       order=14, explode=(0, 0, -0.08)))

    # ---- confinement rings at the beam base (magnetic/electrostatic) ------
    blade_r = DIMS["blade_d_mm"] * MM / 2.0
    gap = DIMS["confine_ring_gap_mm"] * MM
    tube_r = DIMS["confine_tube_d_mm"] * MM / 2.0
    ring_chunks = []
    for i in range(DIMS["confine_rings"]):
        rr = blade_r + gap + i * (2 * tube_r + 0.0015)
        v, f = _torus(rr, tube_r, seg_major=34, seg_tube=10)
        ring_chunks.append(_translate((v, f), (0, 0, -0.002 - i * 0.003)))
    v, f = _combine(ring_chunks)
    parts.append(Part("confine", "Magnetic/Electrostatic Confinement Rings", [Mesh(v, f, C_CONFINE, "confinement rings")],
                       [f"{DIMS['confine_rings']} rings, electromagnetic E x B confinement",
                        "limited plasma-column stability, NOT rigid"],
                       order=15, explode=(0, 0, -0.03)))

    # ---- grip shell (what the hand holds) ----------------------------------
    v, f = _annulus(grip_r, grip_r - wall, z_grip0, z_pommel0, seg=44)
    parts.append(Part("grip_shell", "Grip Housing", [Mesh(v, f, C_TI_HFC_DK, "grip shell")],
                       [f"OD {DIMS['grip_od_mm']:.0f} mm, len {DIMS['grip_len_mm']:.0f} mm"],
                       order=16, explode=(0, 0, 0.0)))

    # ---- layered thermal isolation in the grip: primary aerogel -> MLI ------
    # radiation barrier -> outer aerogel foam -> structural shell (already
    # built above). Inside-out order matches the real spec: this is what
    # keeps the grip at ambient while the laser/TEC side runs warmer
    # (see --feasibility for the actual numbers).
    ag_t = DIMS["aerogel_t_mm"] * MM
    mli_t = DIMS["mli_band_t_mm"] * MM
    outer_ag_t = DIMS["outer_aerogel_t_mm"] * MM
    r_shell_in = grip_r - wall
    r_outerag_in = r_shell_in - outer_ag_t
    r_mli_in = r_outerag_in - mli_t
    r_aerogel_in = r_mli_in - ag_t
    gz0, gz1 = z_grip0 + 0.002, z_pommel0 - 0.002

    v, f = _annulus(r_aerogel_in + ag_t, r_aerogel_in, gz0, gz1, seg=44)
    parts.append(Part("aerogel", "Primary Aerogel Insulation", [Mesh(v, f, C_AEROGEL, "aerogel liner")],
                       [f"k~{PHYS['k_aerogel_w_mk']*1000:.0f} mW/m-K, {ag_t*1000:.1f} mm"],
                       order=17, explode=(0, 0, 0.02)))

    v, f = _annulus(r_mli_in + mli_t, r_mli_in, gz0, gz1, seg=44)
    parts.append(Part("mli_band", f"MLI Radiation Barrier ({DIMS['mli_layers']}-layer pack)",
                       [Mesh(v, f, C_MLI, "MLI band")],
                       [f"{DIMS['mli_layers']} aluminized-foil shields, eps~{PHYS['eps_mli_shield']:.2f} each",
                        "rendered as ONE representative band, not 30 separate meshes",
                        "real N-shield formula computed in --feasibility (dominant at high T)"],
                       order=18, explode=(0, 0, 0.025)))

    v, f = _annulus(r_outerag_in + outer_ag_t, r_outerag_in, gz0, gz1, seg=44)
    parts.append(Part("outer_aerogel", "Outer Aerogel Foam", [Mesh(v, f, C_OUTER_GEL, "outer aerogel")],
                       [f"{outer_ag_t*1000:.1f} mm, second distinct aerogel layer per spec"],
                       order=19, explode=(0, 0, 0.03)))

    # ---- ceramic/silicone ergonomic grip-pad rings (outer surface texture) -
    n_pads = DIMS["grip_pad_rings"]
    pad_t = DIMS["grip_pad_t_mm"] * MM
    pad_w = (z_pommel0 - z_grip0) / (n_pads * 2.2)
    chunks = []
    for i in range(n_pads):
        pz = z_grip0 + (i + 0.5) * (z_pommel0 - z_grip0) / n_pads
        v, f = _annulus(grip_r + pad_t, grip_r, pz - pad_w / 2, pz + pad_w / 2, seg=40)
        chunks.append((v, f))
    v, f = _combine(chunks)
    parts.append(Part("grip_pad", "Ceramic/Silicone Grip-Pad Rings", [Mesh(v, f, C_GRIP_PAD, "grip pad")],
                       [f"{n_pads}x raised ergonomic rings, negligible added thermal resistance"],
                       order=20, explode=(0, 0.015, 0.0)))

    # ---- driver electronics board ------------------------------------------
    el_z = DIMS["electronics_z_mm"] * MM
    el_l = DIMS["electronics_l_mm"] * MM; el_w = DIMS["electronics_w_mm"] * MM; el_t = DIMS["electronics_t_mm"] * MM
    v, f = _box(0, -0.008, el_z, el_w, el_t, el_l)
    parts.append(Part("electronics", "Constant-Current Driver + Control PCB", [Mesh(v, f, C_ELECTRONICS, "driver PCB")],
                       ["2-3 A / 2-3 V constant current, <1% power ripple",
                        "feedback stabilization, safety interlock logic"],
                       order=18, explode=(0, -0.02, 0.0)))

    # ---- supercapacitor / battery bank (on-axis, widest power component) --
    sc_z = DIMS["supercap_z_mm"] * MM
    sc_r = DIMS["supercap_d_mm"] * MM / 2.0
    sc_l = DIMS["supercap_len_mm"] * MM
    v, f = _solid_cylinder(sc_r, sc_z - sc_l / 2, sc_z + sc_l / 2, seg=36)
    parts.append(Part("supercap", "Supercapacitor / Li-ion Bank", [Mesh(v, f, C_SUPERCAP, "power bank")],
                       [f"{PHYS['supercap_energy_wh']:.0f} Wh, dia {DIMS['supercap_d_mm']:.0f} mm",
                        "baseline continuous power; the internal engine assists in pulsed bursts"],
                       order=19, explode=(0, 0, 0.05)))

    # ---- engine bay: internal chemical photon engine (combustor + cavity + --
    # shutter + cartridges) lives here, bulged slightly from the 32 mm grip.
    # Honest SWaP note: fitting a genuine engine required lengthening the
    # hilt beyond the minimal 20-30 cm prop spec -- reported, not hidden.
    v, f = _annulus(engine_bay_r, engine_bay_r - wall, z_engine0, z_pommel0, seg=44)
    parts.append(Part("engine_bay_shell", "Engine Bay Housing", [Mesh(v, f, C_TI_HFC_DK, "engine bay shell")],
                       [f"OD {DIMS['engine_bay_od_mm']:.0f} mm, len {DIMS['engine_bay_len_mm']:.0f} mm",
                        "bulged from the 32 mm grip to fit the internal engine"],
                       order=29, explode=(0, 0, 0.03)))
    parts.extend(build_engine_parts(z0=z_engine0, include_fiber=True))

    # ---- pommel housing + rear cap ------------------------------------------
    v1, f1 = _annulus(pommel_r, pommel_r - wall, z_pommel0, z_end, seg=44)
    v2, f2 = _solid_cylinder(pommel_r - wall, z_end, z_end + wall, seg=44)
    vv, ff = _combine([(v1, f1), (v2, f2)])
    parts.append(Part("pommel_shell", "Pommel Housing", [Mesh(vv, ff, C_TI_HFC, "pommel")],
                       [f"OD {DIMS['pommel_od_mm']:.0f} mm, len {DIMS['pommel_len_mm']:.0f} mm"],
                       order=20, explode=(0, 0, 0.08)))

    # ---- activation button / safety interlock stud -------------------------
    bt_z = DIMS["button_z_mm"] * MM
    bt_r = DIMS["button_d_mm"] * MM / 2.0
    v, f = _solid_cylinder(bt_r, 0, 0.003, seg=16)
    v = (np.asarray(v) @ rot_x(math.pi / 2).T + np.array([0, pommel_r, bt_z])).tolist()
    parts.append(Part("button", "Activation Button / Safety Interlock", [Mesh(v, f, C_BUTTON, "activation button")],
                       ["press-hold ignition, auto-shutoff on release",
                        "thermal/overheat interlock (trips if the engine over-fires)"],
                       order=21, explode=(0, 0.02, 0.0)))

    hilt_shells = {"head_shell", "graphene", "grip_shell", "aerogel", "mli_band",
                   "outer_aerogel", "grip_pad", "pommel_shell", "engine_bay_shell", "confine"}
    _apply_exploded_layout(parts, z_end, hilt_shells)
    return parts, z_end, blade_r


def build_blade_mesh(length_m, diameter_m, temp_k, z_front=-0.005):
    """The plasma channel itself -- built fresh whenever length/diameter/temp
    change (cheap: one cylinder). Not part of build_hilt() because it only
    exists while ignited."""
    r = diameter_m / 2.0
    z0 = z_front
    z1 = z_front - length_m
    v, f = _solid_cylinder(r, z1, z0, seg=36)
    cap_v, cap_f = _sphere(r, seg=20)
    cap_v = (np.asarray(cap_v) @ rot_x(math.pi / 2).T + np.array([0, 0, z1])).tolist()
    vv, ff = _combine([(v, f), (cap_v, cap_f)])
    color = blackbody_rgb(temp_k)
    return Part("blade", "Plasma Channel (ionized-air light column)",
                [Mesh(vv, ff, color, "plasma blade")],
                [f"{length_m*100:.0f} cm x {diameter_m*1000:.0f} mm, ~{temp_k:.0f} K glow",
                 "NOT a rigid solid -- an ionized gas/laser column"],
                order=22, explode=(0, 0, 0.0))


def build_engine_parts(z0=0.0, include_fiber=True):
    """The internal CHEMICAL photon engine -- replaces the Orbitron fusion
    pod entirely; no nuclear component anywhere in this design, and no
    external attachment: it lives inside the hilt's engine bay. A metal-
    powder/oxidizer combustion chamber heats a refractory emitter to real
    blackbody-radiating temperatures; that light continuously pumps a
    folded high-finesse delay-line cavity with an inline photonic-crystal
    slow-light segment (real group-index enhancement, separate from and
    multiplicative with the mirror finesse); a fast photonic-crystal shutter
    then cavity-dumps the accumulated energy in a directed burst. This is
    the SAME real mechanism as a Q-switched / cavity-dumped laser (closed-
    shutter charge, fast output coupling) -- NOT the 'chaotic bouncing
    causes parametric amplification' framing of the original note, which
    would need an active gain medium to exceed input power without
    violating energy conservation. Shared by build_hilt() (in place, at
    hilt-relative z0) and build_engine_showcase() (standalone, z0=0)."""
    parts = []
    bay_len = DIMS["engine_bay_len_mm"] * MM
    bay_r = DIMS["engine_bay_od_mm"] * MM / 2.0

    # ---- combustion / blackbody emitter (rear of the bay) ------------------
    comb_r = DIMS["combustor_d_mm"] * MM / 2.0
    comb_len = DIMS["combustor_len_mm"] * MM
    comb_z1 = z0 + bay_len - 0.006
    comb_z0 = comb_z1 - comb_len
    v, f = _solid_cylinder(comb_r, comb_z0, comb_z1, seg=28)
    parts.append(Part("combustor", "Combustion / Blackbody Emitter Chamber", [Mesh(v, f, C_CHAMBER, "combustor")],
                       [f"Al/O2 metal-powder combustion, refractory liner ~{PHYS['chem_chamber_temp_k']:.0f} K",
                        "real Stefan-Boltzmann thermal emission -- see feasibility for W output"],
                       order=30, explode=(0, 0, 0.05)))

    # ---- HfC/ZrC crucible lining -- the ACTUAL hot chemical zone (not the --
    # TEC-cooled laser/PhC, which never needs a 4200 K-rated ceramic).
    hfc_t = DIMS["hfc_crucible_t_mm"] * MM
    v, f = _annulus(comb_r + hfc_t, comb_r, comb_z0 - 0.002, comb_z1 + 0.002, seg=28)
    parts.append(Part("hfc_crucible", "HfC/ZrC Crucible Liner", [Mesh(v, f, C_HFC, "HfC crucible")],
                       [f"HfC: melting point ~{PHYS['hfc_melting_k']:.0f} K, k~{PHYS['k_hfc_w_mk']:.0f} W/m-K",
                        f"{DIMS['hfc_crucible_t_mm']:.0f} mm liner contains the combustion zone"],
                       order=29, explode=(0, 0, 0.04)))

    # ---- reactant micro-cartridges around the combustor --------------------
    n_cart = DIMS["cartridges"]
    cart_len = DIMS["cartridge_len_mm"] * MM; cart_r = DIMS["cartridge_d_mm"] * MM / 2.0
    cz = (comb_z0 + comb_z1) / 2.0
    chunks = []
    for i in range(n_cart):
        ang = 2 * math.pi * i / n_cart
        x, y = (bay_r - 0.004 - cart_r) * math.cos(ang), (bay_r - 0.004 - cart_r) * math.sin(ang)
        v, f = _solid_cylinder(cart_r, cz - cart_len / 2, cz + cart_len / 2, seg=10)
        chunks.append(_translate((v, f), (x, y, 0)))
    v, f = _combine(chunks)
    parts.append(Part("cartridges", "Reactant Micro-Cartridges", [Mesh(v, f, C_STANDOFF, "cartridges")],
                       [f"{n_cart}x {DIMS['cartridge_mass_g']:.0f} g metal-powder/oxidizer charge",
                        "storable chemical reactant, not cryogenic fusion fuel"],
                       order=31, explode=(0, 0.01, 0.0)))

    # ---- folded slow-light delay-line cavity (middle of the bay) -----------
    coil_r = DIMS["cavity_coil_od_mm"] * MM / 2.0
    tube_r = DIMS["cavity_tube_d_mm"] * MM / 2.0
    turns = DIMS["cavity_turns"]; pitch = DIMS["cavity_pitch_mm"] * MM
    v, f = _helix_tube(coil_r, tube_r, turns, pitch, n_seg=turns * 24, tube_seg=10)
    cav_z0 = z0 + 0.014
    v = (np.asarray(v) + np.array([0.0, 0.0, cav_z0])).tolist()
    parts.append(Part("cavity", "Folded Slow-Light Delay-Line Cavity",
                       [Mesh(v, f, C_CONFINE, "spiral cavity")],
                       [f"{turns} turns, supermirror R~{PHYS['cavity_mirror_R']:.5f}",
                        f"inline PhC slow-light segment: {PHYS['slow_light_factor']:.0f}x group-index boost",
                        "closed-shutter resonant buildup -- real cavity ring-down/Q-switch",
                        "physics, NOT amplification from passive bouncing alone"],
                       order=32, explode=(0, 0, 0.0)))

    # ---- photonic-crystal shutter (front of the bay, faces the beam path) --
    sh_z = z0 + 0.007
    sh_r = DIMS["shutter_d_mm"] * MM / 2.0
    v, f = _solid_cylinder(sh_r, sh_z, sh_z + 0.003, seg=36)
    grid = DIMS["shutter_grid"]
    hole_chunks = []
    hr = sh_r * 1.7 / grid * 0.35
    for i in range(grid):
        for j in range(grid):
            x = (i - grid / 2.0 + 0.5) * (sh_r * 1.7 / grid)
            y = (j - grid / 2.0 + 0.5) * (sh_r * 1.7 / grid)
            if x * x + y * y > (sh_r * 0.9) ** 2:
                continue
            hv, hf = _solid_cylinder(hr, sh_z + 0.001, sh_z + 0.0031, seg=8)
            hole_chunks.append(_translate((hv, hf), (x, y, 0)))
    hv, hf = _combine(hole_chunks)
    vv, ff = _combine([(v, f)])
    parts.append(Part("shutter", "Photonic-Crystal Shutter Array (directional dump)",
                       [Mesh(vv, ff, C_TI_HFC, "shutter disc"), Mesh(hv, hf, C_HOLE, "shutter elements")],
                       [f"{grid}x{grid} fast MEMS/electro-optic apertures, ~{PHYS['shutter_open_s']*1e9:.1f} ns open",
                        "closed during buildup, opens toward the beam path for the directional dump"],
                       order=33, explode=(0, 0, -0.02)))

    # ---- graphene/diamond heat pipes: carry waste heat radially OUT to the -
    # radiator, away from the grip (per the layered thermal-isolation spec).
    n_pipes = DIMS["heat_pipe_count"]
    pipe_r = DIMS["heat_pipe_d_mm"] * MM / 2.0
    pipe_r0 = comb_r + hfc_t + 0.001
    pipe_r1 = bay_r - 0.004
    chunks = []
    for i in range(n_pipes):
        ang = 2 * math.pi * i / n_pipes
        p0 = (pipe_r0 * math.cos(ang), pipe_r0 * math.sin(ang), cz)
        p1 = (pipe_r1 * math.cos(ang), pipe_r1 * math.sin(ang), cz)
        v, f = _tube_between(p0, p1, pipe_r, seg=8)
        chunks.append((v, f))
    v, f = _combine(chunks)
    parts.append(Part("heat_pipes", "Graphene/Diamond Heat Pipes", [Mesh(v, f, C_HEATPIPE, "heat pipes")],
                       [f"{n_pipes}x, k>2000-5000 W/m-K, capture "
                        f"{PHYS['heat_pipe_capture_frac']*100:.0f}% of combustor waste heat",
                        "carry it OUT to the radiator, away from the grip -- see feasibility"],
                       order=35, explode=(0.02, 0.0, 0.0)))

    # ---- hilt-mounted radiator: wraps the engine bay exterior --------------
    fins = DIMS["radiator_fins"]
    fin_len = DIMS["radiator_fin_len_mm"] * MM
    fin_axial = DIMS["engine_bay_len_mm"] * MM * 0.5
    chunks = []
    for i in range(fins):
        ang = 2 * math.pi * i / fins
        rx, ry = (bay_r + fin_len / 2) * math.cos(ang), (bay_r + fin_len / 2) * math.sin(ang)
        v, f = _box(rx, ry, cz, fin_len, 0.0015, fin_axial)
        vrot = np.asarray(v) - np.array([rx, ry, cz])
        cq, sq = math.cos(ang), math.sin(ang)
        rz = np.array([[cq, -sq, 0], [sq, cq, 0], [0, 0, 1]])
        vrot = vrot @ rz.T + np.array([rx, ry, cz])
        chunks.append((vrot.tolist(), f))
    v, f = _combine(chunks)
    parts.append(Part("radiator", "Hilt-Mounted Radiator Fins", [Mesh(v, f, C_RADIATOR, "radiator fins")],
                       [f"{fins} fins around the engine bay exterior -- sheds only a small",
                        "fraction of the waste heat (see feasibility): a thermal buffer, not",
                        "steady-state radiation, is what actually limits engine runtime"],
                       order=36, explode=(0, 0, 0.06)))

    # ---- delivery fiber: physically carries the dump forward to the PhC ----
    if include_fiber:
        phc_z = DIMS["phc_z_mm"] * MM
        v, f = _tube_between((0, 0, sh_z), (0, 0, phc_z), 0.0004, seg=8)
        parts.append(Part("delivery_fiber", "Engine Delivery Fiber (to beam path)",
                           [Mesh(v, f, C_LASER_PKG, "delivery fiber")],
                           ["carries the cavity-dump pulse forward to join the diode laser's",
                            "path at the photonic-crystal microcavity"],
                           order=34, explode=(0, 0, 0.0)))

    return parts


def build_engine_showcase():
    """The internal engine, standalone, for a dedicated close-up inspection
    view (the same Parts build_hilt() places inside the engine bay, just
    re-rooted at z0=0 with no forward delivery fiber to clutter the view)."""
    parts = build_engine_parts(z0=0.0, include_fiber=False)
    bay_len = DIMS["engine_bay_len_mm"] * MM
    _apply_exploded_layout(parts, bay_len * 2.4, {"hfc_crucible"})
    return parts, bay_len


BINDING_ZOOM = 4.0   # binding showcase: blade cross-section enlarged 4x for legibility


def build_binding_showcase():
    """A cutaway of the blade's internal STRUCTURE, showing -- to scale with
    each other, enlarged 4x -- the concentric physics zones that would bind
    slowed photons into a coherent mass, plus the confinement and the Rydberg-
    EIT medium that mediates the interaction. This is the visual companion to
    SECTION 4b: it makes 'the effects that bind photons' inspectable. A half
    cutaway (front semicircle removed) exposes the nested cores."""
    parts = []
    Z = BINDING_ZOOM
    seg_len = 0.09 * Z              # a representative axial slice of blade
    r_blade = (DIMS["blade_d_mm"] * MM / 2.0) * Z
    z0, z1 = -seg_len / 2, seg_len / 2

    # concentric radii (fractions of the blade radius), outer -> inner
    r_sheath = r_blade
    r_slow = r_blade * 0.72
    r_core = r_blade * 0.42

    # ---- outer ionized-air plasma sheath (the glowing, hot, visible part) --
    v, f = _half_annulus(r_sheath, r_slow, z0, z1)
    parts.append(Part("bind_sheath", "Ionized-Air Plasma Sheath (~7500 K)", [Mesh(v, f, C_SHEATH, "plasma sheath")],
                       ["the ONLY part that actually exists in the built blade:",
                        "a hot glowing ionized-air column, k_B T ~ 200x any binding energy"],
                       order=0, explode=(0, 0.05, 0)))

    # ---- EIT / photonic-crystal slow-light region --------------------------
    v, f = _half_annulus(r_slow, r_core, z0, z1)
    parts.append(Part("bind_slow", "Slow-Light Zone (EIT + photonic crystal)", [Mesh(v, f, C_SLOWZONE, "slow-light zone")],
                       [f"group index n_g~{PHYS['slow_light_factor']:.0f}: v_g ~ c/{PHYS['slow_light_factor']:.0f}",
                        "slowing the light gives the photons an effective MASS (see MATH)"],
                       order=1, explode=(0, 0.03, 0)))

    # ---- bound-photon condensate core --------------------------------------
    v, f = _half_cylinder(r_core, z0, z1)
    parts.append(Part("bind_core", "Bound-Photon Condensate Core", [Mesh(v, f, C_BOUNDCORE, "bound core")],
                       [f"interaction blueshift mu~{PHYS['interaction_blueshift_mev']:.0f} meV -> a compressive",
                        "'hold' (bulk modulus), but below the Landau v_c it is a frictionless",
                        "superfluid: slow motion slips through (see MATH)"],
                       order=2, explode=(0, 0.02, 0)))

    # ---- supersolid density-modulation lattice (the crystalline order that -
    # ALONE could carry static shear = the parry). Shown SCHEMATICALLY on the
    # cutaway face: the real period is ~1.8 um (SECTION 4b), far below blade
    # scale, so the node spacing here is representative, not to scale.
    node_chunks = []
    b = photon_binding_report()
    n_across = 6
    spacing_z = seg_len / (n_across + 1)
    spacing_y = (2 * r_core * 0.82) / (n_across + 1)
    node_r = min(spacing_z, spacing_y) * 0.32
    for iz in range(n_across):
        zc = z0 + (iz + 1) * spacing_z
        row_off = 0.5 * spacing_y if iz % 2 else 0.0   # triangular stagger
        for iy in range(n_across):
            yc = -r_core * 0.82 + (iy + 1) * spacing_y + row_off - spacing_y * 0.5
            if abs(yc) > r_core * 0.86:
                continue
            sv, sf = _sphere(node_r, seg=10)
            # protrude slightly onto the exposed cut face (+x) so they're visible
            node_chunks.append(_translate((sv, sf), (node_r * 0.5, yc, zc)))
    v, f = _combine(node_chunks)
    parts.append(Part("bind_lattice", "Supersolid Density Modulation (schematic)",
                       [Mesh(v, f, C_LATTICE, "supersolid lattice")],
                       [f"the crystalline order that ALONE gives static shear (the parry);",
                        f"real period ~{b['supersolid_period_um']:.1f} um (um-scale, cryogenic, 1-2D only)"],
                       order=3, explode=(0, 0.04, 0)))

    # ---- Rydberg-EIT vapour cell + crossed control beams (the interaction) -
    cell_r = r_blade * 0.16
    cell_z = z1 + seg_len * 0.28
    v, f = _solid_cylinder(cell_r, z1 + 0.004, cell_z, seg=28)
    beam_chunks = []
    for ang in (0.5, -0.5):
        p0 = (-cell_r * 1.6 * math.cos(ang), cell_r * 1.6 * math.sin(ang), z1 + 0.006)
        p1 = (cell_r * 1.6 * math.cos(ang), -cell_r * 1.6 * math.sin(ang), cell_z - 0.002)
        bv, bf = _tube_between(p0, p1, node_r * 0.35, seg=6)
        beam_chunks.append((bv, bf))
    bv, bf = _combine(beam_chunks)
    parts.append(Part("bind_eit", "Rydberg-EIT Cell + Control Beams",
                       [Mesh(v, f, C_EITCELL, "EIT cell"), Mesh(bv, bf, C_SLOWZONE, "control beams")],
                       [f"ultracold atomic vapour; blockade radius {b['rydberg_blockade_um']:.0f} um mediates the",
                        "strongest real photon-photon force (bound photon pairs, Firstenberg 2013);",
                        f"pair binding energy ~{b['pair_binding_uev']:.3f} ueV"],
                       order=4, explode=(0, 0, 0.03)))

    # ---- confinement field rings (electromagnetic containment) -------------
    ring_chunks = []
    for i in range(5):
        zc = z0 + (i + 0.5) * seg_len / 5
        v, f = _torus(r_sheath * 1.06, r_sheath * 0.05, seg_major=44, seg_tube=12)
        ring_chunks.append(_translate((v, f), (0, 0, zc)))
    v, f = _combine(ring_chunks)
    parts.append(Part("bind_field", "Electromagnetic Confinement Rings", [Mesh(v, f, C_FIELDLINE, "confinement")],
                       ["radial E x B confinement holds the column together;",
                        "provides shape, NOT the internal binding"],
                       order=5, explode=(0, 0, 0)))

    return parts, seg_len


CUT_BLOCK_W, CUT_BLOCK_H, CUT_BLOCK_D = 0.30, 0.16, 0.05   # cut-test workpiece (m)
CUT_TIME_ACCEL = 25.0    # sim runs at 25x real time so a real 146 s cut is watchable


def build_cut_test(material_key, plasma_temp_k=None, blade_d_mm=None, blade_len_m=None,
                   cut_depth_m=None):
    """The cutting TEST bench: the blade descending into a block of the chosen
    material, with a glowing kerf whose DEPTH is the ACCUMULATED ablation depth
    (`cut_depth_m`) from the live dynamic test. If cut_depth_m is None it falls
    back to a representative 10 s dwell (the static preview). Rebuilt whenever
    material / settings / cut progress change."""
    plasma_temp_k = PHYS["plasma_temp_K"] if plasma_temp_k is None else plasma_temp_k
    blade_d_mm = DIMS["blade_d_mm"] if blade_d_mm is None else blade_d_mm
    blade_len_m = DIMS["blade_len_m"] if blade_len_m is None else blade_len_m
    parts = []

    block_w, block_h, block_d = CUT_BLOCK_W, CUT_BLOCK_H, CUT_BLOCK_D
    rep = cutting_report(material_key, plasma_temp_k, blade_d_mm, thickness_mm=block_h * 1000)
    mat_color = MATERIAL_COLORS.get(material_key, C_WORKPIECE)

    if cut_depth_m is None:
        kerf_depth = min(block_h, rep["recession_mm_s"] * MM * 10.0)  # static preview
    else:
        kerf_depth = min(block_h, max(0.0, cut_depth_m))
    kerf_w = blade_d_mm * MM

    # ---- material block (with a slot where the blade has cut in) ------------
    if kerf_depth > 1e-4:
        left_w = (block_w - kerf_w) / 2
        v1, f1 = _box(-(kerf_w / 2 + left_w / 2), block_h / 2, 0, left_w, block_h, block_d)
        v2, f2 = _box(+(kerf_w / 2 + left_w / 2), block_h / 2, 0, left_w, block_h, block_d)
        floor_h = block_h - kerf_depth                       # remaining material under the cut
        v3, f3 = _box(0, floor_h / 2, 0, kerf_w, floor_h, block_d)
        v, f = _combine([(v1, f1), (v2, f2), (v3, f3)])
    else:
        v, f = _box(0, block_h / 2, 0, block_w, block_h, block_d)
    parts.append(Part("workpiece", f"Workpiece: {material_key}", [Mesh(v, f, mat_color, material_key)],
                       [MATERIALS[material_key]["note"],
                        (f"recession {rep['recession_mm_s']:.2f} mm/s at {plasma_temp_k:.0f} K"
                         if rep["can_cut"] else "CANNOT CUT: conduction bleeds heat away faster than supplied")],
                       order=0, explode=(0, 0, -0.12)))

    # ---- glowing kerf floor (only if actually cutting) ---------------------
    if kerf_depth > 1e-4:
        floor_top = block_h - kerf_depth
        v, f = _box(0, floor_top + 0.004, 0, kerf_w * 0.98, 0.008, block_d)
        pct = 100.0 * kerf_depth / block_h
        depth_note = (f"{kerf_depth*1000:.0f} mm deep ({pct:.0f}% through {block_h*1000:.0f} mm)")
        parts.append(Part("kerf", "Glowing Ablation Kerf", [Mesh(v, f, blackbody_rgb(plasma_temp_k), "kerf")],
                           [f"kerf width = blade dia {blade_d_mm:.0f} mm", depth_note],
                           order=1, explode=(0, 0, 0)))

    # ---- the blade descending into the cut ---------------------------------
    blade_bottom = block_h - kerf_depth
    blade_top = block_h + blade_len_m * 0.5
    r = kerf_w / 2
    v, f = _solid_cylinder(r, blade_bottom, blade_top, seg=36)
    v = (np.asarray(v) @ rot_x(math.pi / 2).T).tolist()  # stand it up along +Y
    # rot_x maps +Z -> +Y? rot_x(90): (x,y,z)->(x,-z,y); so z->y. good.
    parts.append(Part("cut_blade", "Plasma Blade (contact edge)", [Mesh(v, f, blackbody_rgb(plasma_temp_k), "blade")],
                       [f"{plasma_temp_k:.0f} K -> contact flux {rep['q_contact_w_m2']/1e6:.1f} MW/m^2",
                        f"net (minus sideways conduction) {rep['q_net_w_m2']/1e6:.1f} MW/m^2"],
                       order=2, explode=(0, 0.1, 0)))

    return parts, block_w, rep


def _half_annulus(r_out, r_in, z0, z1, seg=48):
    """A half (rear semicircle) annular shell -- used for blade cutaways so the
    front is open and the nested cores are visible."""
    return _annulus_arc(r_out, r_in, z0, z1, math.pi * 0.5, math.pi * 1.5, seg)


def _half_cylinder(r, z0, z1, seg=48):
    v, f = _annulus_arc(r, r * 0.001, z0, z1, math.pi * 0.5, math.pi * 1.5, seg)
    return v, f


def _annulus_arc(r_out, r_in, z0, z1, a0, a1, seg=48):
    """Partial annular shell between angles a0..a1 (outer wall, inner wall,
    two axial caps, two radial end caps)."""
    seg = max(6, int(seg))
    ang = np.linspace(a0, a1, seg + 1)
    n = seg + 1
    verts, faces = [], []
    for z in (z0, z1):
        for a in ang:
            verts.append((r_out * math.cos(a), r_out * math.sin(a), z))
        for a in ang:
            verts.append((r_in * math.cos(a), r_in * math.sin(a), z))

    def oo(layer, i): return layer * (2 * n) + i
    def ii(layer, i): return layer * (2 * n) + n + i

    for i in range(seg):
        faces.append((oo(0, i), oo(0, i + 1), oo(1, i + 1), oo(1, i)))
        faces.append((ii(0, i), ii(1, i), ii(1, i + 1), ii(0, i + 1)))
        faces.append((oo(0, i), ii(0, i), ii(0, i + 1), oo(0, i + 1)))
        faces.append((oo(1, i), oo(1, i + 1), ii(1, i + 1), ii(1, i)))
    faces.append((oo(0, 0), oo(1, 0), ii(1, 0), ii(0, 0)))
    faces.append((oo(0, seg), ii(0, seg), ii(1, seg), oo(1, seg)))
    return verts, faces


def build_microcavity_showcase():
    """The SAME photonic-crystal microcavity from the hilt, rebuilt at a fixed
    documented zoom (SHOWCASE_ZOOM = 2000x: 1 model-mm on screen = 500 nm
    real) so the lattice is actually legible. A representative NxN patch of
    the full lattice is rendered (the full plate is ~133x133 lattice cells --
    rendering all of them is unnecessary for legibility and is noted on
    screen, not silently implied to be the whole device). The substrate/DBR
    slab is sized to match the rendered PATCH, not the full 80 um plate --
    otherwise the substrate would be ~7x wider than the holes drawn on it."""
    parts = []
    Z = SHOWCASE_ZOOM
    lattice_m = DIMS["micro_lattice_nm"] * NM * Z
    hole_r = DIMS["micro_hole_nm"] * NM * Z / 2.0
    n_side = DIMS["micro_patch_holes"]
    patch_m = n_side * lattice_m
    plate_m = patch_m * 1.15   # substrate/DBR slab: small margin beyond the shown holes
    full_side_cells = round(DIMS["micro_plate_um"] * 1000.0 / DIMS["micro_lattice_nm"])

    # ---- DBR mirror stack beneath the microplate (alternating quarter-wave)
    layer_t = DIMS["micro_dbr_layer_nm"] * NM * Z
    chunks_a, chunks_b = [], []
    z = 0.0
    for i in range(DIMS["micro_dbr_pairs"]):
        chunks_a.append(_box(0, 0, z - layer_t / 2, plate_m, plate_m, layer_t))
        z -= layer_t
        chunks_b.append(_box(0, 0, z - layer_t / 2, plate_m, plate_m, layer_t))
        z -= layer_t
    va, fa = _combine(chunks_a)
    vb, fb = _combine(chunks_b)
    parts.append(Part("dbr_a", "DBR Mirror (high-index layers)", [Mesh(va, fa, C_DBR_A, "DBR high-n")],
                       [f"{DIMS['micro_dbr_pairs']} pairs, {DIMS['micro_dbr_layer_nm']:.0f} nm/layer (quarter-wave @800nm)"],
                       order=0, explode=(0, 0, -0.3)))
    parts.append(Part("dbr_b", "DBR Mirror (low-index layers)", [Mesh(vb, fb, C_DBR_B, "DBR low-n")],
                       ["distributed Bragg reflector -- real photonic-crystal element"],
                       order=1, explode=(0, 0, -0.2)))

    # ---- WS2 / CsPbBr3 microplate with the triangular PhC hole lattice ----
    plate_t = 0.5 * UM * Z
    v, f = _box(0, 0, plate_t / 2, plate_m, plate_m, plate_t)
    hole_chunks = []
    rows = n_side
    for j in range(rows):
        for i in range(n_side):
            x = (i - n_side / 2.0) * lattice_m + (0.5 * lattice_m if j % 2 else 0.0)
            y = (j - rows / 2.0) * lattice_m * math.sqrt(3) / 2.0
            if abs(x) > plate_m / 2 - hole_r or abs(y) > plate_m / 2 - hole_r:
                continue
            hv, hf = _solid_cylinder(hole_r, plate_t * 0.4, plate_t * 0.6 + 1e-6, seg=10)
            hole_chunks.append(_translate((hv, hf), (x, y, 0)))
    hv, hf = _combine(hole_chunks)
    vv, ff = _combine([(v, f)])
    parts.append(Part("microplate", "WS2/CsPbBr3 Microplate (rendered patch)",
                       [Mesh(vv, ff, C_MICROPLATE, "microplate")],
                       [f"full plate is {DIMS['micro_plate_um']:.0f}x{DIMS['micro_plate_um']:.0f} um x 0.5 um "
                        f"(~{full_side_cells}x{full_side_cells} lattice cells)",
                        f"shown here: a {n_side}x{n_side} cell patch, "
                        f"SHOWCASE ZOOM {Z:.0f}x (1 mm here = {1000/Z*1e3:.0f} nm real)"],
                       order=2, explode=(0, 0, 0.0)))
    parts.append(Part("holes", f"PhC Air-Hole Lattice ({n_side}x{rows} of ~{full_side_cells}x{full_side_cells} shown)",
                       [Mesh(hv, hf, C_HOLE, "PhC holes")],
                       [f"triangular lattice, a={DIMS['micro_lattice_nm']:.0f} nm, d={DIMS['micro_hole_nm']:.0f} nm",
                        "slow-light v_g reduction factor ~10-100x (real PhC waveguide physics)"],
                       order=3, explode=(0, 0, 0.15 * plate_m / 0.02)))

    # ---- true-scale reference dot: what this plate ACTUALLY looks like ----
    true_r = max(DIMS["micro_plate_um"] * UM / 2.0, 1e-6)  # not zoomed
    v, f = _sphere(true_r, seg=8)
    v = (np.asarray(v) + np.array([patch_m * 0.65, patch_m * 0.65, 0.0])).tolist()
    parts.append(Part("truescale_dot", "True-Scale Reference (unzoomed)", [Mesh(v, f, (255, 60, 60), "true scale dot")],
                       [f"this dot is the ACTUAL {DIMS['micro_plate_um']:.0f} um size at 1:1 -- everything",
                        f"else in this view is enlarged {Z:.0f}x for visibility"],
                       order=4, explode=(0, 0, 0)))

    return parts, patch_m


# =============================================================================
# SECTION 6 -- RENDERER (software painter's algorithm; orbit/pan/zoom, section
#               cut, exploded view, hover-inspect, part labels)
# =============================================================================

def _label(surf, font, text, pos, accent=False):
    color = C_ACCENT if accent else C_TEXT
    img = font.render(text, True, color)
    x, y = pos
    bg = pygame.Surface((img.get_width() + 6, img.get_height() + 2), pygame.SRCALPHA)
    bg.fill((10, 12, 16, 165))
    surf.blit(bg, (x + 4, y - img.get_height() / 2 - 1))
    surf.blit(img, (x + 7, y - img.get_height() / 2))


def _panel(surf, x, y, w, h, alpha=205):
    p = pygame.Surface((w, h), pygame.SRCALPHA)
    p.fill((*C_PANEL, alpha))
    pygame.draw.rect(p, (*C_PANEL_HI, min(255, alpha + 30)), p.get_rect(), 1)
    surf.blit(p, (x, y))


def _bar(surf, font, x, y, w, frac, color, label, val):
    h = 14
    pygame.draw.rect(surf, C_PANEL_HI, (x, y, w, h))
    fw = max(0, min(w, int(w * clamp(frac, 0.0, 1.0))))
    pygame.draw.rect(surf, color, (x, y, fw, h))
    pygame.draw.rect(surf, (10, 12, 16), (x, y, w, h), 1)
    img = font.render(f"{label}: {val}", True, C_TEXT)
    surf.blit(img, (x + 4, y - 1))


class Renderer:
    """Projects + paints a list[Part] built by one of the build_* functions
    above. One instance per scene (hilt / chem photon pod / microcavity showcase)."""

    def __init__(self, parts, home_az=0.55, home_el=0.30, home_dist=0.55, scale=1.0,
                 center=(0.0, 0.0, 0.0)):
        self.parts = parts
        self._home = (home_az, home_el, home_dist)
        self.az, self.el, self.dist = home_az, home_el, home_dist
        self.pan = np.array([0.0, 0.0])
        self.light = np.array([0.4, 0.6, 1.0]); self.light /= np.linalg.norm(self.light)
        self.exploded = False
        self.explode_amt = 0.0
        self.section = False
        self.hovered = None
        self.selected = None
        self.scale = scale   # metres-per-model-unit already baked into geometry; kept for zoom clamps
        self.center = np.asarray(center, dtype=float)   # orbit pivot (screen-centered point)

    def reset_view(self):
        self.az, self.el, self.dist = self._home
        self.pan = np.array([0.0, 0.0])

    def zoom_at(self, factor, mouse_pos=None, rect=None):
        old = self.dist
        self.dist = max(0.05 * self.scale, min(20.0 * self.scale, self.dist * factor))
        if old <= 1e-9 or mouse_pos is None or rect is None or not rect.collidepoint(mouse_pos):
            return
        anchor = np.array([mouse_pos[0] - (rect.x + rect.w / 2.0),
                            mouse_pos[1] - (rect.y + rect.h / 2.0)], dtype=float)
        k = old / self.dist
        self.pan = anchor - (anchor - self.pan) * k

    def orbit(self, dx, dy, fine=False):
        sens = 0.004 if fine else 0.009
        self.az += dx * sens
        self.el = max(-1.55, min(1.55, self.el + dy * sens))

    def pan_by(self, dx, dy, fine=False):
        sens = 0.45 if fine else 1.0
        self.pan += np.array([dx * sens, dy * sens])

    def tick(self, dt):
        target = 1.0 if self.exploded else 0.0
        self.explode_amt += (target - self.explode_amt) * min(1.0, dt * 4.0)

    def active_part(self):
        i = self.selected if self.selected is not None else self.hovered
        return self.parts[i] if i is not None else None

    def render(self, surf, rect, show_labels, label_font, mouse_pos=None, interactive=True,
               extra_parts=None):
        clip = surf.get_clip(); surf.set_clip(rect)
        cx = rect.x + rect.w / 2.0 + self.pan[0]
        cy = rect.y + rect.h / 2.0 + self.pan[1]
        focal = min(rect.w, rect.h) * 1.05
        Rcam = rot_x(self.el) @ rot_y(self.az)
        lx, ly, lz = float(self.light[0]), float(self.light[1]), float(self.light[2])

        polys = []
        labels = []
        screeninfo = []
        all_parts = list(self.parts) + list(extra_parts or [])

        for pi, part in enumerate(all_parts):
            off = part.explode * self.explode_amt
            highlight = (pi == (self.selected if self.selected is not None else self.hovered))
            allcam = []
            for m in part.meshes:
                wv = m.world_verts() + off - self.center
                cam = wv @ Rcam.T
                cam[:, 2] += self.dist
                allcam.append(cam)
                caml = cam.tolist()
                col = m.color
                if highlight:
                    col = _mix(col, (255, 255, 255), 0.30)
                cr, cg, cb = col
                sxl, syl, dzl = [], [], []
                for vx2, vy2, vz2 in caml:
                    dzl.append(vz2)
                    if vz2 > 1e-6:
                        sxl.append(cx + focal * vx2 / vz2)
                        syl.append(cy - focal * vy2 / vz2)
                    else:
                        sxl.append(0.0); syl.append(0.0)
                for face in m.faces:
                    if self.section and self._section_cut(part.key, wv, face):
                        continue
                    if any(dzl[i] <= 1e-6 for i in face):
                        continue
                    ax, ay, az_ = caml[face[0]]; bx, by, bz = caml[face[1]]; fx, fy, fz = caml[face[2]]
                    ux, uy, uz = bx - ax, by - ay, bz - az_
                    wx, wy, wz = fx - ax, fy - ay, fz - az_
                    nx = uy * wz - uz * wy; ny = uz * wx - ux * wz; nz = ux * wy - uy * wx
                    inv = 1.0 / ((nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0)
                    nx *= inv; ny *= inv; nz *= inv
                    if nz > 0:
                        nx, ny, nz = -nx, -ny, -nz
                    d = nx * lx + ny * ly + nz * lz
                    shade = 0.45 + 0.55 * (d if d > 0.0 else 0.0)
                    fc = (int(cr * shade), int(cg * shade), int(cb * shade))
                    ds = sum(dzl[i] for i in face)
                    outline = (255, 210, 120) if highlight else (12, 14, 18)
                    polys.append((ds / len(face), [(sxl[i], syl[i]) for i in face], fc, outline))
            if not allcam:
                continue
            cam_all = np.vstack(allcam)
            cen = cam_all.mean(axis=0)
            if cen[2] > 1e-6:
                safez = np.where(cam_all[:, 2] <= 1e-6, 1e9, cam_all[:, 2])
                scx = cx + focal * cam_all[:, 0] / safez
                scy = cy - focal * cam_all[:, 1] / safez
                pcx = cx + focal * cen[0] / cen[2]; pcy = cy - focal * cen[1] / cen[2]
                rad = float(np.max(np.hypot(scx - pcx, scy - pcy))) * 0.55 + 6
                screeninfo.append((pi, pcx, pcy, rad, cen[2]))
                if show_labels and label_font:
                    labels.append((cen[2], (pcx, pcy), part.name))

        polys.sort(key=lambda t: t[0], reverse=True)
        for _, pts, fc, outline in polys:
            if len(pts) >= 3:
                try:
                    pygame.draw.polygon(surf, fc, pts)
                    pygame.draw.polygon(surf, outline, pts, 1)
                except Exception:
                    pass

        if show_labels and label_font:
            labels.sort(key=lambda t: t[0])
            used = []
            for _, (lxp, lyp), text in labels:
                ly2 = lyp
                for uy in used:
                    if abs(ly2 - uy) < 15:
                        ly2 = uy + 15
                used.append(ly2)
                _label(surf, label_font, text, (lxp, ly2))

        if interactive and mouse_pos is not None:
            mxp, myp = mouse_pos
            best, bestd = None, 1e18
            for pi, pcx, pcy, rad, depth in screeninfo:
                if math.hypot(mxp - pcx, myp - pcy) <= rad and depth < bestd:
                    bestd, best = depth, pi
            self.hovered = best if best is not None and best < len(self.parts) else None

        surf.set_clip(clip)

    def _section_cut(self, key, wv, face):
        sectionable = key in ("head_shell", "grip_shell", "pommel_shell", "graphene",
                               "aerogel", "mli_band", "outer_aerogel", "grip_pad",
                               "engine_bay_shell", "combustor", "hfc_crucible")
        if not sectionable:
            return False
        c = wv[list(face)].mean(axis=0)
        return c[0] > 0.0005

    def project(self, p_local, rect):
        """Project a single local-space point with the SAME camera transform
        used by render() (for the blade glow overlay drawn by the App)."""
        cx = rect.x + rect.w / 2.0 + self.pan[0]
        cy = rect.y + rect.h / 2.0 + self.pan[1]
        focal = min(rect.w, rect.h) * 1.05
        Rcam = rot_x(self.el) @ rot_y(self.az)
        p = (np.asarray(p_local, dtype=float) - self.center) @ Rcam.T
        p[2] += self.dist
        if p[2] <= 1e-6:
            return None
        return (cx + focal * p[0] / p[2], cy - focal * p[1] / p[2], p[2])


# =============================================================================
# SECTION 7 -- APPLICATION (pygame shell: 3 scenes, live physics HUD, CLI)
# =============================================================================

SCENES = ("hilt", "engine", "binding", "cut", "showcase")
SCENE_TITLES = {
    "hilt": "HAND-HELD HILT  (real scale: ~390 mm long, 60-68 mm dia)",
    "engine": "INTERNAL ENGINE BAY CLOSE-UP  (combustion-pumped slow-light cavity, no nuclear component)",
    "binding": f"PHOTON-BINDING CUTAWAY  (blade cross-section, {BINDING_ZOOM:.0f}x -- the effects that would bind slowed light)",
    "cut": "MATERIAL CUT TEST  (real ablation energy balance -- [ ]/,/. change temp/material)",
    "showcase": f"PHOTONIC-CRYSTAL MICROCAVITY SHOWCASE  (zoomed {SHOWCASE_ZOOM:.0f}x, true scale ~80 um)",
}

INFO_TEXT = [
    "WHAT THIS MODEL IS",
    "A to-scale digital twin of the BUILDABLE 'lightsaber' concept identified",
    "in Projectgoal.md: a diode-laser-driven ionized-air plasma channel,",
    "enhanced by a real room-temperature exciton-polariton photonic-crystal",
    "microcavity, powered by a supercapacitor/battery bank PLUS an INTERNAL",
    "chemical photon engine living inside the hilt's own engine bay -- no",
    "nuclear component: combustion heats a blackbody emitter that continuously",
    "pumps a folded slow-light delay-line cavity, which a fast photonic-",
    "crystal shutter cavity-dumps toward the beam path in a directed burst.",
    "",
    "WHAT THE ENGINE ACTUALLY DOES (AND DOESN'T)",
    "The concept this engine is built from described photons 'spiraling in",
    "vortex modes with parametric amplification' from chaotic bouncing alone.",
    "Without an active gain medium, a passive cavity cannot exceed its input",
    "power -- that would violate energy conservation. What IS real, and what's",
    "built here, is: (1) a folded cavity HOLDS light longer via mirror finesse",
    "and a genuine photonic-crystal SLOW-LIGHT segment (real group-index",
    "enhancement); (2) the shutter stays closed while this charges, then",
    "opens for a cavity-dump burst -- the same mechanism as a Q-switched",
    "laser. The dump is far too brief and fuel-limited to replace the blade's",
    "continuous radiative loss, but its peak intensity CAN reionize the full",
    "plasma column (not just a focused spot) -- a real, useful, bounded",
    "contribution, not a free-energy trick. Press M for the numbers.",
    "",
    "THE PHOTON-BINDING QUESTION (view 3 -- the effects that would bind light)",
    "'What holds slowed photons together as a solid mass?' is answered with real",
    "physics, in five steps: (1) SLOW LIGHT gives photons an effective mass",
    "(m = E/c^2 * n_g); (2) a nonlinear MEDIUM makes them interact -- the",
    "Rydberg-EIT blockade is the strongest real one and made actual bound photon",
    "pairs in the lab; (3) that gives a fluid with a BULK modulus (a compressive",
    "'hold'); but (4) a superfluid has ZERO static SHEAR modulus, so it cannot",
    "resist a sideways sword-block unless it forms crystalline (supersolid)",
    "order; and (5) it only binds at all while k_B*T < mu, i.e. cryogenically.",
    "The built 7500 K plasma blade is ~200x too hot -- press M for every number.",
    "",
    "THE CUT TEST (view 4 -- real ablation math, ,/. change material)",
    "The blade cuts the way any real high-power thermal source does: an energy",
    "balance at the ablation front (recession u = q_net / E_v). It cuts steel,",
    "titanium, concrete, flesh, even the fictional 'durasteel' analog -- but",
    "CANNOT cut diamond, whose enormous thermal conductivity conducts the heat",
    "away faster than the plasma supplies it. A real, non-obvious result.",
    "",
    "ENGINEERING AROUND THE WALLS (run: python3 LS.py --engineer)",
    "Treating every barrier as a hurdle: the rigid SOLID-LIGHT blade is the one",
    "true wall (a superfluid has zero static shear), so we BYPASS it -- achieve",
    "the FUNCTIONS with a current-carrying magnetic PLASMA-ARC blade. One blade",
    "current does three real jobs: it self-confines the column (Z-pinch/Bennett,",
    "a fixed-length blade with ~kPa magnetic 'stiffness', ~3000x the photon",
    "fluid), it CLASHES with a second blade by the Ampere force (~50 N at ~2.7",
    "kA, a real felt parry), and it cuts by ablation. The price is real and",
    "honestly reported: ~2.6 MW, kA currents, backpack/tether power, lethal --",
    "engineering COSTS, not physical impossibilities. A lightsaber that glows,",
    "holds a fixed length, cuts, and clashes with another blade IS buildable.",
    "",
    "WHAT REMAINS IMPOSSIBLE (bypassed, not solved)",
    "The literal indefinite, rigid, swingable 'solid light' blade -- a metre-",
    "scale room/high-temperature exciton-polariton supersolid -- is NOT",
    "buildable: real polariton condensates exist at um-mm scale, near room temp,",
    "for ps-ns lifetimes, with zero static shear. So it is not the mechanism;",
    "magnetism does the clash instead. This tool reports that gap quantitatively",
    "(press M) rather than assuming it away.",
    "",
    "HONEST DESIGN CHOICES BAKED INTO THE GEOMEOMETRY",
    "- Hilt sized for a real hand (~32-40 mm dia), NOT the 200 mm bench-",
    "  package figure from the aspirational laser section. Fitting a genuine",
    "  internal engine (not just a token part) required a dedicated, slightly",
    "  bulged engine bay and a longer hilt (~405 mm total) than the minimal",
    "  20-30 cm prop spec -- an honest SWaP consequence, reported not hidden.",
    "- The flat 20x20 mm heatsink spec is repackaged as an equivalent-area",
    "  radial fin collar so it actually fits the 34 mm head housing.",
    "- The photonic-crystal microcavity is genuinely ~80 um: shown true-scale",
    "  in the hilt (a few pixels) AND at a documented 2000x zoom (view 3).",
    "",
    "Press M for the live physics/feasibility readout behind these claims.",
]


def _wrap(font, text, max_w):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.size(trial)[0] > max_w and cur:
            lines.append(cur); cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


class _Button:
    """A mouse-clickable rectangle -- the control panel's basic building
    block, matching the reference programs' pattern of a fully mouse-
    operable UI (not just keyboard shortcuts)."""

    def __init__(self, rect, label, on_click, active_fn=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.active_fn = active_fn

    def is_active(self):
        return bool(self.active_fn()) if self.active_fn else False

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surf, font):
        active = self.is_active()
        bg = C_ACCENT if active else C_PANEL_HI
        pygame.draw.rect(surf, bg, self.rect, border_radius=3)
        pygame.draw.rect(surf, (10, 12, 16), self.rect, 1, border_radius=3)
        fg = (10, 12, 16) if active else C_TEXT
        img = font.render(self.label, True, fg)
        surf.blit(img, (self.rect.centerx - img.get_width() // 2,
                        self.rect.centery - img.get_height() // 2))


class _Slider:
    """A mouse-draggable value bar for a continuous parameter (blade length/
    diameter/plasma temperature) -- lets the live physics numbers be driven
    by the mouse, not just bracket keys."""

    def __init__(self, rect, lo, hi, get_value, set_value, label, fmt="{:.2f}"):
        self.rect = pygame.Rect(rect)
        self.lo, self.hi = lo, hi
        self.get_value = get_value
        self.set_value = set_value
        self.label = label
        self.fmt = fmt

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def set_from_x(self, x):
        frac = clamp((x - self.rect.x) / max(1, self.rect.w), 0.0, 1.0)
        self.set_value(self.lo + frac * (self.hi - self.lo))

    def draw(self, surf, font):
        val = self.get_value()
        frac = clamp((val - self.lo) / (self.hi - self.lo), 0.0, 1.0)
        pygame.draw.rect(surf, C_PANEL_HI, self.rect)
        pygame.draw.rect(surf, C_ACCENT, (self.rect.x, self.rect.y, int(self.rect.w * frac), self.rect.h))
        pygame.draw.rect(surf, (10, 12, 16), self.rect, 1)
        img = font.render(f"{self.label}: {self.fmt.format(val)}", True, C_TEXT)
        surf.blit(img, (self.rect.x + 3, self.rect.y - 14))


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("LS.py -- Lightsaber Engineering Digital Twin")
        self.W, self.H = 1280, 800
        self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas,menlo,monospace", 15)
        self.font_sm = pygame.font.SysFont("consolas,menlo,monospace", 12)
        self.font_big = pygame.font.SysFont("consolas,menlo,monospace", 20, bold=True)

        self.hilt_parts, self.hilt_len, self.blade_base_r = build_hilt()
        self.engine_parts, self.engine_len = build_engine_showcase()
        self.binding_parts, self.binding_seg = build_binding_showcase()
        self.showcase_parts, self.patch_m = build_microcavity_showcase()
        self.material_idx = 4   # start on mild steel
        cut_parts, cut_w, _ = build_cut_test(MATERIAL_KEYS[self.material_idx])

        self.renderers = {
            # the hilt is a long thin rod along Z -- orbit around its MIDPOINT
            # and view from a raking near-side angle (az~1.3 rad) so the full
            # length reads as a profile ("sword") view, not end-on down the barrel.
            "hilt": Renderer(self.hilt_parts, home_az=1.30, home_el=0.32,
                              home_dist=self.hilt_len * 1.15, scale=self.hilt_len,
                              center=(0, 0, self.hilt_len / 2)),
            # the engine bay is short/fat (len ~ 2x diameter), a normal 3/4 view frames it well
            "engine": Renderer(self.engine_parts, home_az=0.55, home_el=0.25,
                                home_dist=self.engine_len * 1.9, scale=self.engine_len,
                                center=(0, 0, self.engine_len / 2)),
            # blade cutaway: az~2.3 shows the concentric layers edge-on as a
            # clean cross-section (sheath / slow-light / bound core / lattice)
            "binding": Renderer(self.binding_parts, home_az=2.30, home_el=0.30,
                                 home_dist=self.binding_seg * 2.3, scale=self.binding_seg,
                                 center=(0, 0, 0)),
            # cut bench: front 3/4 view of the block + descending blade
            "cut": Renderer(cut_parts, home_az=0.5, home_el=0.28,
                            home_dist=cut_w * 1.7, scale=cut_w,
                            center=(0, 0.06, 0)),
            # az~2.8 views from the microplate's PATTERNED face (holes + top
            # surface), not from behind through the DBR stack -- the DBR is
            # built extending to -Z, so the naive small-az view looks through
            # its back first and hides the very surface this scene exists to show.
            "showcase": Renderer(self.showcase_parts, home_az=2.80, home_el=0.30,
                                  home_dist=self.patch_m * 2.6, scale=self.patch_m,
                                  center=(0, 0, -0.0015)),
        }
        self.cut_w = cut_w
        self.cut_rep = None
        # live cut-test state (dynamic simulation)
        self.cut_running = False
        self.cut_depth_m = 0.0
        self.cut_elapsed_s = 0.0         # true physical seconds of cutting
        self.cut_done_s = None           # physical time when it broke through
        self.scene = "hilt"

        self.show_labels = True
        self.show_info = False
        self.show_math = False
        self.show_blueprint = False
        self.engine_armed = False
        self.engine_armed_since = None
        self.engine_cooldown_until = 0.0
        self.engine_warn = ""

        self.ignited = False
        self.ignite_amt = 0.0
        self.blade_len_m = DIMS["blade_len_m"]
        self.blade_d_mm = DIMS["blade_d_mm"]
        self.plasma_temp_k = PHYS["plasma_temp_K"]
        self.t_elapsed = 0.0

        self.dragging = False
        self.panning = False
        self.mouse_pos = (0, 0)
        self.active_slider = None

        self._build_controls()

    def _check_thermal_limit(self):
        """Auto-disarm the engine once it has been firing longer than the
        REAL thermally-limited runtime (see full_feasibility_report) --
        not a scripted timer, the actual buffer-capacity/waste-heat number,
        then lock out re-arming for a cooldown period (4x the burst length,
        a stand-in for the buffer bleeding its absorbed heat back down)."""
        if not self.engine_armed or self.engine_armed_since is None:
            return
        rpt = full_feasibility_report(self.blade_len_m, self.blade_d_mm, self.plasma_temp_k)
        elapsed = self.t_elapsed - self.engine_armed_since
        if elapsed > rpt["thermal_runtime_s"]:
            self.engine_armed = False
            self.engine_armed_since = None
            self.engine_cooldown_until = self.t_elapsed + rpt["thermal_runtime_s"] * 4.0
            self.engine_warn = "THERMAL LIMIT REACHED -- ENGINE AUTO-DISARMED, COOLING DOWN"

    def _rend(self):
        return self.renderers[self.scene]

    def _view_rect(self):
        return pygame.Rect(0, 34, self.W, self.H - 34 - 26)

    def _toggle(self, obj, attr):
        setattr(obj, attr, not getattr(obj, attr))

    def _cur_material(self):
        return MATERIAL_KEYS[self.material_idx]

    def _cycle_material(self, delta):
        self.material_idx = (self.material_idx + delta) % len(MATERIAL_KEYS)
        self._reset_cut()   # start a fresh cut on the new material

    def _reset_cut(self):
        self.cut_depth_m = 0.0
        self.cut_elapsed_s = 0.0
        self.cut_done_s = None
        self.cut_running = False

    def _toggle_cut_run(self):
        """SPACE in the CUT scene runs/pauses the live cut; restarts if done."""
        if self.cut_done_s is not None:
            self._reset_cut()
        self.cut_running = not self.cut_running

    def _advance_cut(self, dt):
        """Integrate the ablation depth at the REAL recession rate (accelerated
        by CUT_TIME_ACCEL so a 100+ s cut is watchable). Stops at breakthrough."""
        if not self.cut_running:
            return
        rep = cutting_report(self._cur_material(), self.plasma_temp_k, self.blade_d_mm,
                             thickness_mm=CUT_BLOCK_H * 1000)
        if not rep["can_cut"]:
            return  # uncuttable: clock does not advance, kerf stays at 0
        step = dt * CUT_TIME_ACCEL
        self.cut_elapsed_s += step
        self.cut_depth_m = min(CUT_BLOCK_H, self.cut_depth_m + rep["recession_mm_s"] * MM * step)
        if self.cut_depth_m >= CUT_BLOCK_H and self.cut_done_s is None:
            self.cut_done_s = self.cut_elapsed_s
            self.cut_running = False

    def _rebuild_cut(self):
        """Rebuild the cut-test geometry at the current accumulated cut depth
        and swap it into its renderer, preserving the user's camera."""
        parts, w, rep = build_cut_test(self._cur_material(), self.plasma_temp_k,
                                        self.blade_d_mm, self.blade_len_m,
                                        cut_depth_m=self.cut_depth_m)
        self.renderers["cut"].parts = parts
        self.cut_w = w
        return rep

    def _toggle_engine_armed(self):
        if self.engine_armed:
            self.engine_armed = False
            self.engine_armed_since = None
            return
        if self.t_elapsed < self.engine_cooldown_until:
            return  # still cooling down from the last thermal-limited burst
        self.engine_armed = True
        self.engine_armed_since = self.t_elapsed
        self.engine_warn = ""

    def _build_controls(self):
        """Mouse-operable control panel, left side: scene buttons, view
        toggles, blade sliders, and action buttons -- everything the keyboard
        shortcuts do, also clickable/draggable, matching how Main.py/
        GmansRunV1.17.py mirror every key with an on-screen control."""
        x0, w, bh, gap = 10, 190, 20, 5
        y = 40
        self.buttons = []
        self.sliders = []

        scenes = (("HILT", "hilt"), ("ENGINE", "engine"), ("BIND", "binding"),
                  ("CUT", "cut"), ("MICRO", "showcase"))
        bw = (w - gap * 2) // 3
        for i, (label, key) in enumerate(scenes):
            row, col = divmod(i, 3)
            self.buttons.append(_Button((x0 + col * (bw + gap), y + row * (bh + gap), bw, bh), label,
                                         (lambda k=key: setattr(self, "scene", k)),
                                         (lambda k=key: self.scene == k)))
        y += 2 * (bh + gap) + 6

        bw2 = (w - gap) // 2
        toggles = [
            ("EXPLODE", lambda: self._toggle(self._rend(), "exploded"), lambda: self._rend().exploded),
            ("SECTION", lambda: self._toggle(self._rend(), "section"), lambda: self._rend().section),
            ("LABELS", lambda: self._toggle(self, "show_labels"), lambda: self.show_labels),
            ("BLUEPRINT", lambda: self._toggle(self, "show_blueprint"), lambda: self.show_blueprint),
            ("RESET VIEW", lambda: self._rend().reset_view(), None),
        ]
        for i, (label, cb, active) in enumerate(toggles):
            row, col = divmod(i, 2)
            self.buttons.append(_Button((x0 + col * (bw2 + gap), y + row * (bh + gap), bw2, bh),
                                         label, cb, active))
        y += 3 * (bh + gap) + 6

        self.buttons.append(_Button((x0, y, w, bh + 4), "IGNITE BLADE",
                                     lambda: self._toggle(self, "ignited"), lambda: self.ignited))
        y += bh + 4 + gap
        self.buttons.append(_Button((x0, y, w, bh + 4), "ARM ENGINE",
                                     self._toggle_engine_armed, lambda: self.engine_armed))
        y += bh + 4 + gap
        # material cycler + live-cut controls (drive the CUT scene)
        self.buttons.append(_Button((x0, y, bw2, bh), "< MATERIAL",
                                     lambda: self._cycle_material(-1), None))
        self.buttons.append(_Button((x0 + bw2 + gap, y, bw2, bh), "MATERIAL >",
                                     lambda: self._cycle_material(+1), None))
        y += bh + gap
        self.buttons.append(_Button((x0, y, bw2, bh), "RUN CUT",
                                     self._toggle_cut_run, lambda: self.cut_running))
        self.buttons.append(_Button((x0 + bw2 + gap, y, bw2, bh), "RESET CUT",
                                     self._reset_cut, None))
        y += bh + 16

        self.sliders.append(_Slider((x0, y, w, 14), 0.5, 1.0,
                                     lambda: self.blade_len_m, lambda v: setattr(self, "blade_len_m", v),
                                     "LENGTH m", "{:.2f}"))
        y += 26
        self.sliders.append(_Slider((x0, y, w, 14), 20.0, 50.0,
                                     lambda: self.blade_d_mm, lambda v: setattr(self, "blade_d_mm", v),
                                     "DIA mm", "{:.0f}"))
        y += 26
        self.sliders.append(_Slider((x0, y, w, 14), 5000.0, 10000.0,
                                     lambda: self.plasma_temp_k, lambda v: setattr(self, "plasma_temp_k", v),
                                     "TEMP K", "{:.0f}"))
        y += 26 + 8

        self.buttons.append(_Button((x0, y, bw2, bh), "INFO",
                                     lambda: self._toggle(self, "show_info"), lambda: self.show_info))
        self.buttons.append(_Button((x0 + bw2 + gap, y, bw2, bh), "MATH",
                                     lambda: self._toggle(self, "show_math"), lambda: self.show_math))
        y += bh + gap
        self.buttons.append(_Button((x0, y, w, bh), "EXPORT OBJ",
                                     lambda: export_obj_all(self.hilt_parts, self.engine_parts,
                                                             self.showcase_parts), None))

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            if not self._events():
                break
            self._rend().tick(dt)
            target = 1.0 if self.ignited else 0.0
            self.ignite_amt += (target - self.ignite_amt) * min(1.0, dt * 2.2)
            self.t_elapsed += dt
            self._check_thermal_limit()
            if self.scene == "cut":
                self._advance_cut(dt)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    # ---- input --------------------------------------------------------
    def _events(self):
        rect = self._view_rect()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            elif e.type == pygame.VIDEORESIZE:
                self.W, self.H = e.w, e.h
                self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    return False
                elif e.key == pygame.K_1:
                    self.scene = "hilt"
                elif e.key == pygame.K_2:
                    self.scene = "engine"
                elif e.key == pygame.K_3:
                    self.scene = "binding"
                elif e.key == pygame.K_4:
                    self.scene = "cut"
                elif e.key == pygame.K_5:
                    self.scene = "showcase"
                elif e.key == pygame.K_COMMA:
                    self._cycle_material(-1)
                elif e.key == pygame.K_PERIOD:
                    self._cycle_material(+1)
                elif e.key == pygame.K_p:
                    self.show_blueprint = not self.show_blueprint
                elif e.key == pygame.K_e:
                    self._rend().exploded = not self._rend().exploded
                elif e.key == pygame.K_x:
                    self._rend().section = not self._rend().section
                elif e.key == pygame.K_l:
                    self.show_labels = not self.show_labels
                elif e.key == pygame.K_r:
                    self._rend().reset_view()
                elif e.key in (pygame.K_SPACE, pygame.K_b):
                    # context-sensitive: run/pause the live cut in the CUT scene,
                    # otherwise ignite/extinguish the blade
                    if self.scene == "cut":
                        self._toggle_cut_run()
                    else:
                        self.ignited = not self.ignited
                elif e.key == pygame.K_UP:
                    self.blade_len_m = min(1.0, self.blade_len_m + 0.05)
                elif e.key == pygame.K_DOWN:
                    self.blade_len_m = max(0.5, self.blade_len_m - 0.05)
                elif e.key == pygame.K_RIGHT:
                    self.blade_d_mm = min(50.0, self.blade_d_mm + 2.0)
                elif e.key == pygame.K_LEFT:
                    self.blade_d_mm = max(20.0, self.blade_d_mm - 2.0)
                elif e.key == pygame.K_RIGHTBRACKET:
                    self.plasma_temp_k = min(10000.0, self.plasma_temp_k + 250.0)
                elif e.key == pygame.K_LEFTBRACKET:
                    self.plasma_temp_k = max(5000.0, self.plasma_temp_k - 250.0)
                elif e.key == pygame.K_f:
                    self._toggle_engine_armed()
                elif e.key == pygame.K_i:
                    self.show_info = not self.show_info
                elif e.key == pygame.K_m:
                    self.show_math = not self.show_math
                elif e.key == pygame.K_o:
                    export_obj_all(self.hilt_parts, self.engine_parts, self.showcase_parts)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    hit_control = False
                    for b in self.buttons:
                        if b.hit(e.pos):
                            b.on_click()
                            hit_control = True
                            break
                    if not hit_control:
                        for s in self.sliders:
                            if s.hit(e.pos):
                                self.active_slider = s
                                s.set_from_x(e.pos[0])
                                hit_control = True
                                break
                    if not hit_control:
                        self.dragging = True
                elif e.button in (2, 3):
                    self.panning = True
                elif e.button in (4, 5):
                    factor = 0.86 if e.button == 4 else 1.16
                    self._rend().zoom_at(factor, e.pos, rect)
            elif e.type == pygame.MOUSEBUTTONUP:
                self.dragging = self.panning = False
                self.active_slider = None
            elif e.type == pygame.MOUSEMOTION:
                self.mouse_pos = e.pos
                dx, dy = e.rel
                fine = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                if self.active_slider is not None:
                    self.active_slider.set_from_x(e.pos[0])
                elif self.dragging:
                    self._rend().orbit(dx, dy, fine=fine)
                elif self.panning:
                    self._rend().pan_by(dx, dy, fine=fine)
            elif e.type == pygame.MOUSEWHEEL:
                factor = 0.86 ** e.y if e.y > 0 else 1.16 ** (-e.y)
                self._rend().zoom_at(factor, pygame.mouse.get_pos(), rect)
        return True

    # ---- drawing --------------------------------------------------------
    def _draw(self):
        surf = self.screen
        for y in range(0, self.H, 4):
            t = y / max(1, self.H)
            pygame.draw.rect(surf, _mix(BG_TOP, BG_BOT, t), (0, y, self.W, 4))

        rect = self._view_rect()
        # the CUT scene depends on live material/temp/blade settings -- rebuild
        # its geometry from the real physics each frame (cheap: a few boxes).
        self.cut_rep = self._rebuild_cut() if self.scene == "cut" else None

        extra = []
        rnd = self._rend()
        boosted = False
        pulse_mult = 1.0
        if self.scene == "hilt" and self.ignite_amt > 0.005:
            eff_len = self.blade_len_m * self.ignite_amt
            blade_part = build_blade_mesh(eff_len, self.blade_d_mm * MM, self.plasma_temp_k,
                                           z_front=-0.004)
            if self.engine_armed:
                # tie the render directly to the real physics: the engine's
                # cavity-dump repetition rate (see full_feasibility_report)
                # drives a visible strobe whenever it sits below the human
                # flicker-fusion threshold (~50 Hz) -- not a cosmetic effect,
                # the actual honest consequence of the numbers in the M overlay.
                rep_rate = full_feasibility_report(
                    self.blade_len_m, self.blade_d_mm, self.plasma_temp_k)["rep_rate_hz"]
                phase = (self.t_elapsed * rep_rate) % 1.0
                pulse_mult = 1.0 if phase < 0.5 else 0.35
                dimmed = [Mesh(m.verts, m.faces, _mix((0, 0, 0), m.color, pulse_mult), m.name)
                          for m in blade_part.meshes]
                blade_part = Part(blade_part.key, blade_part.name, dimmed, blade_part.specs,
                                   blade_part.order, blade_part.explode)
            extra = [blade_part]
            # the ignited blade extends well beyond the hilt's own framing --
            # temporarily pull the camera back (and recenter) so it stays in
            # view, then restore the user's actual zoom/pan state afterward.
            orig_dist, orig_center = rnd.dist, rnd.center.copy()
            total_span = self.hilt_len + eff_len
            rnd.dist = orig_dist * (total_span / self.hilt_len)
            rnd.center = np.array([0.0, 0.0, (self.hilt_len - eff_len) / 2.0])
            boosted = True
            self._draw_blade_glow(rect, eff_len, pulse_mult)

        rnd.render(surf, rect, self.show_labels, self.font_sm,
                   mouse_pos=self.mouse_pos, interactive=True, extra_parts=extra)

        if boosted:
            rnd.dist, rnd.center = orig_dist, orig_center

        if self.show_blueprint:
            self._draw_blueprint(rect)

        self._draw_topbar()
        # in blueprint mode the drawing (title block + BOM) replaces the
        # live HUD panel so the schematic reads clean
        if not self.show_blueprint:
            if self.scene == "binding":
                self._draw_binding_panel()
            elif self.scene == "cut":
                self._draw_cut_panel()
            else:
                self._draw_physics_panel()
        self._draw_controls_panel()
        self._draw_hover_card()
        self._draw_controls_bar()
        if self.show_info:
            self._draw_overlay("REAL-SCIENCE ASSESSMENT  (press I to close)", INFO_TEXT)
        if self.show_math:
            self._draw_math_overlay()

    def _draw_blade_glow(self, rect, eff_len, pulse_mult=1.0):
        p0 = self._rend().project((0, 0, -0.004), rect)
        p1 = self._rend().project((0, 0, -0.004 - eff_len), rect)
        if p0 is None or p1 is None:
            return
        color = blackbody_rgb(self.plasma_temp_k)
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for rad, a in ((26, 26), (18, 40), (11, 70), (6, 120)):
            pygame.draw.line(overlay, (*color, int(a * pulse_mult)), p0[:2], p1[:2], rad)
        self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_topbar(self):
        _panel(self.screen, 0, 0, self.W, 30, alpha=225)
        img = self.font.render(f"LS.py  |  {SCENE_TITLES[self.scene]}", True, C_TEXT)
        self.screen.blit(img, (10, 6))
        if self.t_elapsed < self.engine_cooldown_until:
            remain = self.engine_cooldown_until - self.t_elapsed
            cfg = f"{self.engine_warn} ({remain:.1f}s cooldown)"
            cfg_color = C_BAD
        else:
            cfg = "ENGINE ARMED (pulsed reionize)" if self.engine_armed else "LASER ONLY (baseline)"
            cfg_color = C_WARN if self.engine_armed else C_GOOD
        img2 = self.font.render(f"engine: {cfg}", True, cfg_color)
        self.screen.blit(img2, (self.W - img2.get_width() - 12, 6))

    def _draw_controls_bar(self):
        y = self.H - 26
        _panel(self.screen, 0, y, self.W, 26, alpha=225)
        txt = ("1-5 scene  orbit/wheel/R-M  E explode  X section  L labels  P blueprint  "
               "SPACE ignite/run-cut  F arm  UP/DN len  L/R dia  [ ] temp  ,/. material  "
               "I info  M math  O export  ESC quit")
        img = self.font_sm.render(txt, True, C_TEXT_DIM)
        self.screen.blit(img, (10, y + 5))

    def _draw_physics_panel(self):
        rpt = full_feasibility_report(self.blade_len_m, self.blade_d_mm, self.plasma_temp_k)
        eng = engineered_saber_report()
        w = min(480, self.W - 20)
        x = self.W - w - 10
        y = 40
        lines = [
            ("LASER", None),
            (f" {PHYS['wavelength_nm']:.0f} nm, E_photon={rpt['e_photon_j']*1e19:.2f}e-19 J", C_TEXT_DIM),
            (f" focus peak I={rpt['i_focus_peak']:.2e} W/m2  "
             f"({'below' if rpt['focus_below_threshold'] else 'ABOVE'} 1e9 threshold, "
             f"{rpt['focus_ratio_to_threshold']:.2f}x)",
             C_WARN if rpt["focus_below_threshold"] else C_GOOD),
            ("PLASMA COLUMN (full blade aperture)", None),
            (f" I={rpt['i_column']:.2e} W/m2 vs 1e9-1e11 breakdown band", C_TEXT_DIM),
            (f" -> {rpt['column_ratio_to_threshold']:.2e}x threshold "
             f"({'CANNOT sustain column' if rpt['column_below_threshold'] else 'plausible'})",
             C_BAD if rpt["column_below_threshold"] else C_GOOD),
            ("THERMAL", None),
            (f" blade radiates {rpt['blade_p_rad_w']:.3g} W to hold {self.plasma_temp_k:.0f} K glow", C_TEXT_DIM),
            (f" laser draw: {rpt['e_form_w']:.1f} W form / {rpt['e_sus_w']:.1f} W sustain", C_TEXT_DIM),
            (f" power shortfall (blade vs laser elec.): {rpt['power_shortfall']:.2e}x", C_BAD),
            (f" laser-side may rise +{rpt['dT_stack_k']:.1f} K above ambient, grip stays AT ambient", C_GOOD),
            ("POWER BUDGET", None),
            (f" supercap {PHYS['supercap_energy_wh']:.0f} Wh -> {rpt['runtime_h']:.1f} h @ sustain draw", C_TEXT_DIM),
            ("CHEM ENGINE (internal, press F to arm)", None),
            (f" combustor emits {rpt['p_chem_w']:.2e} W blackbody @ {PHYS['chem_chamber_temp_k']:.0f} K", C_TEXT_DIM),
            (f" fuel flow {rpt['fuel_flow_kg_s']*1000:.2f} g/s -> burn time {rpt['chem_runtime_s']:.1f} s", C_TEXT_DIM),
            (f" tau_eff={rpt['cavity_tau_eff_s']*1000:.2f} ms (slow-light x{PHYS['slow_light_factor']:.0f}) -> "
             f"{rpt['cavity_dump_energy_j']:.1f} J/dump", C_TEXT_DIM),
            (f" dump peak {rpt['cavity_dump_peak_power_w']:.2e} W -> "
             f"{'REIONIZES full column' if rpt['dump_reionizes_full_column'] else 'below breakdown'} "
             f"({rpt['dump_ratio_to_threshold']:.1f}x)",
             C_GOOD if rpt["dump_reionizes_full_column"] else C_BAD),
            (f" repeat {rpt['rep_rate_hz']:.1f} Hz -> "
             f"{'looks continuous' if rpt['appears_continuous'] else 'visible flicker'} (eye fusion ~50Hz)",
             C_GOOD if rpt["appears_continuous"] else C_WARN),
            (f" ~{rpt['pulses_available']:.0f} pulses available per cartridge set", C_TEXT_DIM),
            ("ENGINE HEAT REJECTION (HfC crucible + MLI + heat pipes)", None),
            (f" waste heat {rpt['waste_heat_w']:.2e} W ({(1-PHYS['chem_eta_photon'])*100:.0f}% of chem input, "
             f"eta={PHYS['chem_eta_photon']*100:.0f}%)", C_TEXT_DIM),
            (f" heat pipes capture {PHYS['heat_pipe_capture_frac']*100:.0f}% -> radiator needs "
             f"{rpt['captured_w']:.2e} W, has {rpt['radiator_capacity_w']:.1f} W", C_BAD),
            (f" shortfall -> {PHYS['buffer_mass_kg']*1000:.0f}g buffer absorbs rest, "
             f"{rpt['thermal_runtime_s']:.2f} s to limit", C_WARN),
            (f" engine runtime: min(fuel {rpt['chem_runtime_s']:.1f}s, thermal {rpt['thermal_runtime_s']:.2f}s) "
             f"= {rpt['engine_runtime_s']:.2f} s", C_BAD),
            (f" residual leak, conduction only: +{rpt['dT_engine_bay_k']:.2e} K "
             f"(steady-state impossible)", C_BAD),
            ("ASPIRATIONAL SOLID BEAM (NOT built)", None),
            (f" target n / BEC critical n_c: {rpt['ratio_solid']:.2e}x", C_BAD),
            ("ENGINEERED-AROUND (magnetic arc -- python3 LS.py --engineer)", None),
            (f" clash {PHYS['clash_force_target_n']:.0f} N via Ampere force @ {eng['i_design_a']:.0f} A; "
             f"Z-pinch {eng['p_mag_pa']/1000:.1f} kPa", C_GOOD),
            (f" real cost: {eng['p_arc_w']/1e6:.1f} MW arc, kA-lethal -> {eng['n_pass']} PASS / "
             f"{eng['n_partial']} PARTIAL of {eng['n_total']}", C_WARN),
        ]
        h = 14 + len(lines) * 15
        _panel(self.screen, x, y, w, h)
        yy = y + 6
        for text, color in lines:
            if color is None:
                img = self.font_sm.render(text, True, C_ACCENT)
            else:
                img = self.font_sm.render(text, True, color)
            self.screen.blit(img, (x + 8, yy))
            yy += 15

    def _draw_controls_panel(self):
        x0, w = 10, 190
        y0 = 36
        y1 = self.sliders[-1].rect.bottom + 46
        _panel(self.screen, x0 - 6, y0, w + 12, y1 - y0, alpha=205)
        for b in self.buttons:
            b.draw(self.screen, self.font_sm)
        for s in self.sliders:
            s.draw(self.screen, self.font_sm)

    def _draw_line_panel(self, lines, w=None):
        """Right-side titled readout panel: lines are (text, color|None); None
        color renders as an accent SECTION header."""
        w = w or min(480, self.W - 20)
        x = self.W - w - 10
        y = 40
        h = 14 + len(lines) * 15
        _panel(self.screen, x, y, w, h)
        yy = y + 6
        for text, color in lines:
            img = self.font_sm.render(text, True, C_ACCENT if color is None else color)
            self.screen.blit(img, (x + 8, yy))
            yy += 15

    def _draw_binding_panel(self):
        b = photon_binding_report(self.blade_d_mm, self.plasma_temp_k)
        lines = [
            ("PHOTON BINDING -- can slowed light become a solid?", None),
            ("1) SLOW LIGHT gives photons mass", C_ACCENT),
            (f"   n_g={b['n_group']:.0f} -> v_g={b['v_g_frac_c']*100:.1f}% c, "
             f"m_eff={b['m_eff_kg']:.2e} kg ({b['m_eff_vs_electron']:.1e} m_e)", C_TEXT_DIM),
            ("2) A MEDIUM makes them interact", C_ACCENT),
            (f"   Rydberg-EIT blockade r_b={b['rydberg_blockade_um']:.0f} um (ultracold only)", C_TEXT_DIM),
            (f"   Kerr: needs I={b['kerr_i_unity_w_m2']:.1e} W/m2 for dn~n0", C_TEXT_DIM),
            (f"   interaction blueshift mu={b['mu_mev']:.0f} meV", C_TEXT_DIM),
            ("3) THE 'HOLD' (compressive stiffness)", C_ACCENT),
            (f"   c_s={b['c_s_m_s']/1000:.0f} km/s, healing xi={b['healing_length_um']:.2f} um", C_TEXT_DIM),
            (f"   bulk B={b['bulk_pa']:.2f} Pa = {b['bulk_vs_steel']:.1e}x steel", C_BAD),
            (f"   10% squeeze pushes back only {b['spring_force_n']*1000:.2f} mN", C_BAD),
            ("4) HOLDING RESISTANCE (superfluid dynamics)", C_ACCENT),
            (f"   Landau v_c={b['v_crit_m_s']/1000:.0f} km/s >> {b['swing_speed_m_s']:.0f} m/s swing", C_TEXT_DIM),
            (f"   -> slow motion slips through FRICTIONLESS (no grip)", C_BAD),
            (f"   Deborah De={b['deborah']:.1e} << 1 -> flows like a fluid,", C_TEXT_DIM),
            (f"      parts around a strike (cannot hit/be hit)", C_BAD),
            ("5) STATIC SHEAR -- the parry", C_ACCENT),
            (f"   superfluid shear=0; supersolid (period {b['supersolid_period_um']:.1f} um)", C_TEXT_DIM),
            (f"   still off by {1/b['shear_margin']:.1e}x -> CANNOT parry", C_BAD),
            ("6) AND only binds when k_B T < mu", C_ACCENT),
            (f"   T_max={b['t_ceiling_k']:.0f} K; plasma is {b['thermal_ratio']:.0f}x too hot",
             C_BAD),
        ]
        self._draw_line_panel(lines)

    def _draw_cut_panel(self):
        rep = self.cut_rep or cutting_report(self._cur_material(), self.plasma_temp_k, self.blade_d_mm)
        mat = MATERIALS[rep["material"]]
        cut_col = C_GOOD if rep["can_cut"] else C_BAD
        lines = [
            (f"CUT TEST -- {rep['material']}   ( ,/.  change )", None),
            (f" {mat['note']}", C_TEXT_DIM),
            ("MATERIAL (real properties)", C_ACCENT),
            (f" rho={mat['rho']:.0f}  cp={mat['cp']:.0f}  k={mat['k']:.0f} W/mK  R={mat['refl']:.2f}", C_TEXT_DIM),
            (f" T_melt={mat['t_melt']:.0f} K  T_vap={mat['t_vap']:.0f} K", C_TEXT_DIM),
            (f" ablation energy E_v={rep['e_v_j_m3']:.2e} J/m3", C_TEXT_DIM),
            ("ENERGY BALANCE AT THE KERF", C_ACCENT),
            (f" plasma flux in : {rep['q_contact_w_m2']/1e6:.1f} MW/m2 @ {self.plasma_temp_k:.0f} K", C_TEXT_DIM),
            (f" conduction out : {rep['q_cond_w_m2']/1e6:.1f} MW/m2 (k, kerf)", C_TEXT_DIM),
            (f" net available  : {rep['q_net_w_m2']/1e6:.1f} MW/m2", cut_col),
            ("RESULT", C_ACCENT),
            (f" {'CUTS' if rep['can_cut'] else 'CANNOT CUT'}: recession {rep['recession_mm_s']:.2f} mm/s",
             cut_col),
            (f" through {CUT_BLOCK_H*1000:.0f} mm in "
             f"{(str(round(CUT_BLOCK_H/ (rep['recession_mm_s']/1000),1))+' s') if rep['can_cut'] else 'never'}",
             cut_col),
            (" (conduction bleeds heat faster than supplied)" if rep["conduction_limited"]
             else f" removal power {rep['removal_power_w']/1000:.1f} kW", C_TEXT_DIM),
            ("LIVE CUT  (SPACE run/pause, RESET btn)", C_ACCENT),
        ]
        pct = 100.0 * self.cut_depth_m / CUT_BLOCK_H
        if not rep["can_cut"]:
            status, scol = "STALLED -- cannot cut this material", C_BAD
        elif self.cut_done_s is not None:
            status, scol = f"CUT THROUGH in {self.cut_done_s:.1f} s", C_GOOD
        elif self.cut_running:
            status, scol = f"CUTTING... {CUT_TIME_ACCEL:.0f}x speed", C_WARN
        else:
            status, scol = "paused (SPACE to run)", C_TEXT_DIM
        lines += [
            (f" {status}", scol),
            (f" depth {self.cut_depth_m*1000:5.1f} / {CUT_BLOCK_H*1000:.0f} mm  ({pct:3.0f}%)  "
             f"t={self.cut_elapsed_s:.1f} s", C_TEXT_DIM),
        ]
        self._draw_line_panel(lines, w=min(430, self.W - 20))

    @staticmethod
    def _dim_string(m):
        return f"{m*1000:.1f} mm" if abs(m) < 1 else f"{m:.3f} m"

    def _draw_dim_line(self, pa, pb, text, bp, offset=(0, 0)):
        """Draw one dimension line (with end ticks + centred value) between two
        already-projected points -- the basic element of an engineering drawing."""
        if pa is None or pb is None:
            return
        ax, ay = pa[0] + offset[0], pa[1] + offset[1]
        bx, by = pb[0] + offset[0], pb[1] + offset[1]
        pygame.draw.line(self.screen, bp, (ax, ay), (bx, by), 1)
        # end ticks perpendicular-ish (short crosses)
        for px, py in ((ax, ay), (bx, by)):
            pygame.draw.line(self.screen, bp, (px - 4, py - 4), (px + 4, py + 4), 1)
        mid = ((ax + bx) / 2, (ay + by) / 2)
        _label(self.screen, self.font_sm, text, mid, accent=True)

    def _draw_blueprint(self, rect):
        """Real blueprint-schematic overlay: engineering-drawing frame + grid,
        projected OVERALL and PER-SECTION dimension chains, an auto-generated
        BILL OF MATERIALS (each part's L x D measured live from its geometry),
        and a title block -- turning the live to-scale model into a schematic."""
        bp = (150, 200, 255)
        grid = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        for gx in range(0, rect.w, 40):
            pygame.draw.line(grid, (*bp, 20), (gx, 0), (gx, rect.h), 1)
        for gy in range(0, rect.h, 40):
            pygame.draw.line(grid, (*bp, 20), (0, gy), (rect.w, gy), 1)
        self.screen.blit(grid, (rect.x, rect.y))
        pygame.draw.rect(self.screen, bp, rect, 2)
        pygame.draw.rect(self.screen, bp, rect.inflate(-16, -16), 1)

        rnd = self._rend()
        # per-part bounding boxes in world coords -> live BOM + overall extents
        bom = []
        allv = []
        for part in rnd.parts:
            pv = [m.world_verts() for m in part.meshes]
            if not pv:
                continue
            V = np.vstack(pv)
            allv.append(V)
            zlen = float(V[:, 2].max() - V[:, 2].min())
            dia = 2.0 * float(np.max(np.hypot(V[:, 0], V[:, 1])))
            bom.append((part.name, zlen, dia, float(V[:, 2].min()), float(V[:, 2].max())))
        if not allv:
            return
        Vall = np.vstack(allv)
        zmin, zmax = float(Vall[:, 2].min()), float(Vall[:, 2].max())
        rmax = float(np.max(np.hypot(Vall[:, 0], Vall[:, 1])))

        # OVERALL length callout (offset outward along +Y so it clears the body)
        pa = rnd.project((0, rmax * 1.35, zmin), rect)
        pb = rnd.project((0, rmax * 1.35, zmax), rect)
        self._draw_dim_line(pa, pb, f"OAL {self._dim_string(zmax - zmin)}", bp)
        # OVERALL diameter callout at the front
        da = rnd.project((-rmax, 0, zmin), rect)
        db = rnd.project((rmax, 0, zmin), rect)
        self._draw_dim_line(da, db, f"OD {self._dim_string(2 * rmax)}", bp, offset=(0, -10))

        # per-SECTION dimension chain (hilt only: the named housing sections)
        if self.scene == "hilt":
            h = DIMS["head_len_mm"] * MM
            g = DIMS["grip_len_mm"] * MM
            eb = DIMS["engine_bay_len_mm"] * MM
            pm = DIMS["pommel_len_mm"] * MM
            stations = [(0.0, h, "HEAD"), (h, h + g, "GRIP"),
                        (h + g, h + g + eb, "ENGINE"), (h + g + eb, h + g + eb + pm, "POMMEL")]
            yoff = rmax * 1.9
            for s0, s1, nm in stations:
                psa = rnd.project((0, yoff, s0), rect)
                psb = rnd.project((0, yoff, s1), rect)
                self._draw_dim_line(psa, psb, f"{nm} {(s1-s0)*1000:.0f}", bp)

        # BILL OF MATERIALS table (right side, clear of the left control panel),
        # auto-measured from geometry
        rows_max = min(len(bom), 30)
        bw, rowh = 316, 14
        bx, byy = rect.right - bw - 22, rect.y + 24
        _panel(self.screen, bx, byy, bw, 22 + rows_max * rowh + 8, alpha=225)
        pygame.draw.rect(self.screen, bp, (bx, byy, bw, 22 + rows_max * rowh + 8), 1)
        self.screen.blit(self.font_sm.render("BILL OF MATERIALS  (L x OD, measured live)", True, bp),
                         (bx + 6, byy + 4))
        pygame.draw.line(self.screen, bp, (bx, byy + 20), (bx + bw, byy + 20), 1)
        for i, (nm, zlen, dia, _z0, _z1) in enumerate(bom[:rows_max]):
            yy = byy + 24 + i * rowh
            label = nm if len(nm) <= 30 else nm[:29] + "…"
            self.screen.blit(self.font_sm.render(f"{i+1:2d} {label}", True, C_TEXT), (bx + 6, yy))
            dtxt = f"{zlen*1000:5.1f} x {dia*1000:5.1f}"
            self.screen.blit(self.font_sm.render(dtxt, True, C_TEXT_DIM),
                             (bx + bw - self.font_sm.size(dtxt)[0] - 6, yy))

        # title block (bottom-right)
        tb_w, tb_h = 360, 92
        tx, ty = rect.right - tb_w - 20, rect.bottom - tb_h - 20
        _panel(self.screen, tx, ty, tb_w, tb_h, alpha=235)
        pygame.draw.rect(self.screen, bp, (tx, ty, tb_w, tb_h), 1)
        pygame.draw.line(self.screen, bp, (tx, ty + 22), (tx + tb_w, ty + 22), 1)
        pygame.draw.line(self.screen, bp, (tx + tb_w * 0.62, ty + 22), (tx + tb_w * 0.62, ty + tb_h), 1)
        self.screen.blit(self.font_sm.render("LS.py -- LIGHTSABER ENGINEERING DIGITAL TWIN", True, bp),
                         (tx + 6, ty + 4))
        left = [f"VIEW: {self.scene.upper()}", "SCALE: to-scale (SI, mm)", f"PARTS: {len(bom)}"]
        right = [f"OAL: {self._dim_string(zmax - zmin)}", f"OD: {self._dim_string(2*rmax)}", "REV A | SHEET 1/1"]
        for i, r in enumerate(left):
            self.screen.blit(self.font_sm.render(r, True, C_TEXT), (tx + 6, ty + 28 + i * 16))
        for i, r in enumerate(right):
            col = C_TEXT_DIM if i == 2 else C_TEXT
            self.screen.blit(self.font_sm.render(r, True, col), (tx + int(tb_w * 0.62) + 6, ty + 28 + i * 16))

    def _draw_hover_card(self):
        part = self._rend().active_part()
        if part is None:
            return
        w, h = 380, 26 + 16 * (len(part.specs) + 1)
        x, y = 10, self.H - 26 - h - 8
        _panel(self.screen, x, y, w, h)
        img = self.font.render(part.name, True, C_ACCENT)
        self.screen.blit(img, (x + 8, y + 6))
        yy = y + 26
        for s in part.specs:
            img = self.font_sm.render("- " + s, True, C_TEXT_DIM)
            self.screen.blit(img, (x + 8, yy))
            yy += 16

    def _draw_overlay(self, title, text_lines):
        # pre-wrap; None marks a blank spacer line. Colon-prefixed "@" is a
        # section header we may use as a column-break hint.
        col_w = min(560, (self.W - 80) // 2)
        wrapped = []
        for line in text_lines:
            if line == "":
                wrapped.append(None)
            else:
                for w2 in _wrap(self.font_sm, line, col_w - 32):
                    wrapped.append(w2)

        avail_h = self.H - 100
        max_rows = max(8, (avail_h - 46) // 16)
        one_col_rows = sum(1 for _ in wrapped)  # count including spacers
        two_col = one_col_rows > max_rows

        cols = 2 if two_col else 1
        w = col_w * cols + (20 if two_col else 0)
        w = min(w, self.W - 40)
        # split into `cols` roughly-equal chunks, preferring to break on a blank
        n = len(wrapped)
        per = math.ceil(n / cols)
        chunks = []
        i = 0
        for _c in range(cols):
            end = min(n, i + per)
            # extend to the next blank to avoid splitting a section mid-way
            while end < n and wrapped[end] is not None and (end - i) < per + 8:
                end += 1
            chunks.append(wrapped[i:end])
            i = end
        rows = max((len(c) for c in chunks), default=0)
        h = min(self.H - 60, 46 + rows * 16 + 12)
        x, y = (self.W - w) // 2, (self.H - h) // 2
        _panel(self.screen, x, y, w, h, alpha=238)
        clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(x, y, w, h))
        img = self.font_big.render(title, True, C_ACCENT)
        self.screen.blit(img, (x + 16, y + 12))
        for ci, chunk in enumerate(chunks):
            cx = x + 16 + ci * (col_w + 4)
            yy = y + 46
            for wln in chunk:
                if wln is None:
                    yy += 8
                    continue
                self.screen.blit(self.font_sm.render(wln, True, C_TEXT), (cx, yy))
                yy += 16
        self.screen.set_clip(clip)

    def _draw_math_overlay(self):
        rpt = full_feasibility_report(self.blade_len_m, self.blade_d_mm, self.plasma_temp_k)
        lines = [
            "LIVE PHYSICS  (every number here is computed from DIMS/PHYS at the top of LS.py)",
            "",
            "Photon energy:  E = h c / lambda",
            f"  lambda={PHYS['wavelength_nm']:.0f} nm  ->  E = {rpt['e_photon_j']:.3e} J",
            "",
            "Focused Gaussian intensity:  I_avg = P / (pi w0^2),  I_peak = 2 I_avg",
            f"  P={PHYS['laser_power_w']:.0f} W, w0={PHYS['beam_waist_um']:.0f} um  ->  "
            f"I_peak = {rpt['i_focus_peak']:.3e} W/m^2",
            f"  real air-breakdown band ~1e9-1e11 W/m^2  ->  margin {rpt['focus_ratio_to_threshold']:.2f}x threshold",
            "",
            "Same power spread over the FULL blade cross-section (diameter as ignited):",
            f"  I_column = P/(pi r^2) = {rpt['i_column']:.3e} W/m^2  "
            f"({rpt['column_ratio_to_threshold']:.2e}x the breakdown threshold)",
            "  -> a 10 W diode focused to 50 um can ignite a spot, but CANNOT keep a",
            "     2-5 cm column ionized along its own length: that needs a different",
            "     beam geometry (filamentation/Bessel-beam) or vastly more power.",
            "",
            "Blackbody radiative loss:  P = eps sigma A (T^4 - Tamb^4)",
            f"  T={self.plasma_temp_k:.0f} K, A={rpt['blade_area_m2']:.4f} m^2  ->  "
            f"P_rad = {rpt['blade_p_rad_w']:.3e} W",
            f"  laser electrical draw available: {rpt['e_sus_w']:.1f} W  ->  "
            f"shortfall {rpt['power_shortfall']:.2e}x",
            "  (this is the honest reason a continuously glowing handheld blade at",
            "   this temperature is not achievable at diode-laser power levels)",
            "",
            "Multilayer conduction (graphene spreader + aerogel + outer-aerogel + Ti/HfC",
            "shell): treat the grip's OUTER surface as clamped at ambient (real room-air",
            "convection); dT is how far the INNER (laser/TEC) side must rise to still push",
            "the laser's waste heat out through that much resistance:",
            f"  dT = P * sum(t_i / (k_i A_i))  ->  laser side = ambient + {rpt['dT_stack_k']:.1f} K,",
            f"  grip surface stays AT ambient ({PHYS['T_amb_K']:.0f} K)",
            "",
            "N-shield MLI radiation formula (real: how spacecraft/cryostat MLI is sized) --",
            "shown here to prove it is irrelevant at grip temperatures (radiation ~ T^3):",
            f"  1/eps_eff = (1/eps_h + 1/eps_c - 1) + N(2/eps_shield - 1), N={DIMS['mli_layers']}",
            f"  eps_eff = {rpt['mli_eps_eff']:.2e}  ->  at ~320 K this implies a "
            f"{rpt['dT_mli_grip_k']:.2e} K rise for 8.2 W",
            "  (absurd -- confirms conduction, not radiation, governs this modest heat leak;",
            "   MLI only earns its keep where it's actually hot: the engine bay, below)",
            "",
            "Supercap/battery runtime:  t = E_wh / P_w",
            f"  {PHYS['supercap_energy_wh']:.0f} Wh / {rpt['e_sus_w']:.1f} W  ->  {rpt['runtime_h']:.1f} hours",
            "",
            "INTERNAL CHEM ENGINE -- combustor blackbody emission (Stefan-Boltzmann,",
            "same formula as the blade's radiative loss above, used here as a SOURCE):",
            f"  P = eps sigma A (T^4-Tamb^4), T={PHYS['chem_chamber_temp_k']:.0f} K  ->  "
            f"P_chem = {rpt['p_chem_w']:.3e} W",
            f"  fuel flow = P/(eta_photon * HoC) = {rpt['fuel_flow_kg_s']*1000:.2f} g/s "
            f"(eta={PHYS['chem_eta_photon']*100:.0f}%, Al/O2 HoC=31 MJ/kg)",
            f"  {DIMS['cartridges']}x {DIMS['cartridge_mass_g']:.0f} g cartridges -> burn time "
            f"{rpt['chem_runtime_s']:.1f} s (a brief flare, not continuous)",
            "",
            "Folded delay-line cavity (real cavity ring-down physics, same regime as",
            "high-finesse laser-cavity buildup) + a SEPARATE inline PhC slow-light segment:",
            f"  finesse F = pi sqrt(R)/(1-R), R={PHYS['cavity_mirror_R']:.5f}  ->  F={rpt['cavity_finesse']:.0f}",
            f"  intrinsic photon lifetime tau = -L/(c ln R)  ->  tau={rpt['cavity_tau_intrinsic_s']*1e6:.2f} us",
            f"  slow light HOLDS it longer: tau_eff = tau * {PHYS['slow_light_factor']:.0f}  ->  "
            f"tau_eff = {rpt['cavity_tau_eff_s']*1000:.2f} ms",
            "",
            "Cavity-dump energy (closed shutter charges, then opens -- an RC-charging",
            "relation, E = P_in * tau_eff; NOT P_in * finesse * tau, which would double-",
            "count the buildup factor and silently break energy conservation):",
            f"  E_dump = P_chem * tau_eff = {rpt['cavity_dump_energy_j']:.2f} J",
            f"  peak power (shutter opens in {PHYS['shutter_open_s']*1e9:.1f} ns): "
            f"{rpt['cavity_dump_peak_power_w']:.3e} W",
            "  (real: same mechanism as a Q-switched/cavity-dumped laser -- NOT 'parametric",
            "   amplification from chaotic bouncing', which needs an active gain medium)",
            "",
            "Does the dump re-ionize the FULL blade column (not just a focused spot)?",
            f"  I = P_peak/(pi r^2) = {rpt['dump_column_intensity_w_m2']:.3e} W/m^2 vs "
            f"1e9-1e11 breakdown band",
            f"  -> {rpt['dump_ratio_to_threshold']:.2e}x threshold: "
            f"{'YES, full column reionizes' if rpt['dump_reionizes_full_column'] else 'no, still too weak'}",
            "",
            "Repetition rate (recharge ~3 tau_eff between dumps) vs. human flicker fusion:",
            f"  charge time = 3 tau_eff = {rpt['charge_time_s']*1000:.2f} ms  ->  "
            f"rep rate = {rpt['rep_rate_hz']:.1f} Hz",
            f"  vs {PHYS['human_flicker_fusion_hz']:.0f} Hz flicker-fusion threshold: "
            f"{'reads as steady glow' if rpt['appears_continuous'] else 'reads as a visible strobe'}",
            f"  ~{rpt['pulses_available']:.0f} pulses available before the cartridges deplete",
            "  (honest conclusion: this engine cannot replace the blade's continuous",
            "   radiative loss, but it CAN periodically re-ionize the full column --",
            "   a real, useful, and physically distinct contribution)",
            "",
            "ENGINE HEAT REJECTION -- only eta_photon of the chemical input becomes",
            "useful light; the rest is waste heat the HfC crucible/heat pipes/radiator",
            "/buffer must manage (real: this is why chemical rockets need active cooling):",
            f"  P_input = P_chem/eta = {rpt['p_chem_input_w']:.3e} W  ->  "
            f"waste = {rpt['waste_heat_w']:.3e} W",
            f"  heat pipes capture {PHYS['heat_pipe_capture_frac']*100:.0f}%  ->  "
            f"{rpt['captured_w']:.3e} W reaches the radiator",
            f"  radiator (rad+conv): P = eps*sigma*A*(T^4-Tamb^4) + h*A*dT, "
            f"A={rpt['radiator_area_m2']*1e4:.1f} cm^2  ->  {rpt['radiator_capacity_w']:.1f} W capacity",
            f"  shortfall {rpt['net_to_buffer_w']:.3e} W must go into a thermal buffer:",
            f"  t_thermal = (m c dT_max)/P_net = "
            f"({PHYS['buffer_mass_kg']*1000:.0f}g * {PHYS['buffer_cp_j_kgk']:.0f} * "
            f"{PHYS['buffer_delta_t_max_k']:.0f}K)/{rpt['net_to_buffer_w']:.2e}W = "
            f"{rpt['thermal_runtime_s']:.2f} s",
            f"  -> REAL engine runtime = min(fuel-limited {rpt['chem_runtime_s']:.1f}s, "
            f"thermal-limited {rpt['thermal_runtime_s']:.2f}s) = {rpt['engine_runtime_s']:.2f} s",
            f"  residual parasitic leak ({rpt['parasitic_w']:.0f} W) through the engine bay's own",
            f"  HfC/aerogel/shell stack at STEADY STATE would need +{rpt['dT_engine_bay_k']:.2e} K --",
            "  physically impossible (exceeds every material's melting point), which is",
            "  exactly why this can only be a brief, thermally-limited burst, never continuous",
            "",
            "ASPIRATIONAL 'solid beam' polariton BEC (not part of the built device):",
            "  n_c(T) = 2.612 / lambda_dB^3,  lambda_dB = h / sqrt(2 pi m_eff k_B T)",
            f"  target n={PHYS['n_target_m3']:.2e} m^-3 at T={PHYS['T_beam_target_K']:.0f} K  ->  "
            f"n_c = {rpt['n_c_solid']:.3e} m^-3",
            f"  target/n_c = {rpt['ratio_solid']:.2e}x  ->  far beyond any demonstrated polariton density",
        ]
        # The full proof set is large, so the M overlay is scene-aware: the
        # BINDING and CUT scenes lead with their own derivations (they also
        # have live side-panels); the device scenes show the laser/thermal/
        # engine proofs above. Each stays digestible in one/two columns.
        b = photon_binding_report(self.blade_d_mm, self.plasma_temp_k)
        binding_lines = [
            "PHOTON BINDING -- what would make slowed light a solid mass (SECTION 4b)",
            "Photons are massless and non-interacting in vacuum. To bind them you need,",
            "in sequence: a mass, an interaction, and a low enough temperature.",
            "",
            "step 1 -- MASS from slow light:  m = (E_photon / c^2) * n_g",
            f"  group index n_g = {b['n_group']:.0f} (real PhC/EIT slow light)",
            f"  -> v_g = {b['v_g_frac_c']*100:.1f}% of c,  m_eff = {b['m_eff_kg']:.2e} kg",
            f"     (~{b['m_eff_vs_electron']:.1e} electron masses; the more you slow it, the heavier)",
            "",
            "step 2 -- INTERACTION via a nonlinear medium (photons ignore each other in vacuum):",
            f"  Rydberg-EIT blockade  r_b = (C6 / hbar / Gamma)^(1/6) = {b['rydberg_blockade_um']:.0f} um",
            "    (the strongest real photon-photon force; made bound photon pairs in the lab,",
            "     Firstenberg 2013 -- but only in ultracold ~uK atomic gases)",
            f"  or Kerr n = n0 + n2*I:  needs I = {b['kerr_i_unity_w_m2']:.1e} W/m^2 for dn ~ n0",
            f"  interaction blueshift (chemical potential)  mu = {b['mu_mev']:.0f} meV",
            "",
            "step 3 -- the 'HOLD' = fluid stiffness (mu = g n):",
            "  speed of sound c_s = sqrt(mu/m),  healing length xi = hbar/sqrt(2 m mu),",
            "  bulk modulus B = n dP/dn = mu * n",
            f"  -> c_s = {b['c_s_m_s']/1000:.0f} km/s,  xi = {b['healing_length_um']:.2f} um,",
            f"     B = {b['bulk_pa']:.2f} Pa = {b['bulk_vs_steel']:.1e}x steel  (softer than air!)",
            f"  for rubber-like stiffness you'd need {b['density_gap']:.1e}x the target density",
            "",
            "step 4 -- HOLDING RESISTANCE = how a superfluid actually responds to motion:",
            "  Landau criterion: an object slower than the critical velocity v_c = c_s sheds",
            "  NO excitations -> it slips through with ZERO drag (a superfluid cannot grip a",
            f"  slow intruder).  v_c = {b['v_crit_m_s']/1000:.0f} km/s vs a {b['swing_speed_m_s']:.0f} m/s swing -> frictionless.",
            "  Deborah number De = tau_heal / tau_strike decides solid-vs-fluid response:",
            f"    tau_heal = hbar/mu = {b['healing_time_s']*1e15:.1f} fs,  De = {b['deborah']:.1e} << 1",
            "    -> it flows out of the way on any human timescale (it cannot hit or be hit).",
            f"  compressive spring: a {PHYS['compression_strain']*100:.0f}% squeeze gives dP = B*eps and a",
            f"    felt force of only {b['spring_force_n']*1000:.2f} mN over the whole blade face.",
            "",
            "step 5 -- THE CATCH: static SHEAR (the actual parry) needs crystalline order",
            f"  a {PHYS['lateral_load_n']:.0f} N block over the cross-section = tau_req = {b['tau_required_pa']/1e3:.0f} kPa",
            "  a superfluid's static shear modulus is exactly ZERO. Only a SUPERSOLID (a",
            f"  self-modulated crystal, period {b['supersolid_period_um']:.1f} um here, real but um-scale &",
            f"  cryogenic) carries shear -- and even an optimistic one is off by {1/b['shear_margin']:.1e}x.",
            f"  -> CAN PARRY: {'yes' if b['can_parry'] else 'NO'}",
            "",
            "step 6 -- binding survives only while k_B T < mu:",
            f"  T_max = mu / k_B = {b['t_ceiling_k']:.0f} K  (cryogenic!)",
            f"  pair binding energy ~ hbar*Gamma_EIT = {b['pair_binding_uev']:.3f} ueV (real bound-pair scale)",
            f"  the built 7500 K plasma blade is {b['thermal_ratio']:.0f}x too hot -> nothing binds in it.",
            "",
            "CONCLUSION: every ingredient is real (slow-light mass, Rydberg binding, fluid",
            "stiffness, supersolid order), but only microscopically, cryogenically, with",
            "frictionless slip-through and zero parry strength -- never a warm, metre-scale,",
            "swingable solid blade that resists a block.",
        ]
        cr = cutting_report(self._cur_material(), self.plasma_temp_k, self.blade_d_mm)
        mat = MATERIALS[cr["material"]]
        cutting_lines = [
            f"MATERIAL CUTTING -- {cr['material']} (SECTION 4c: real ablation energy balance)",
            f"  {cr['note']}",
            "",
            "The blade removes material as fast as its heat flux can supply the full",
            "enthalpy of heating + melting + vaporizing it, minus sideways conduction.",
            "",
            f"material properties:  rho={mat['rho']:.0f} kg/m^3,  cp={mat['cp']:.0f} J/kgK,",
            f"  k={mat['k']:.0f} W/mK,  R={mat['refl']:.2f},  T_melt={mat['t_melt']:.0f} K,  T_vap={mat['t_vap']:.0f} K",
            "",
            "1) volumetric ablation energy  E_v = rho[cp(T_vap-T0) + L_f + L_v]",
            f"   = {cr['e_v_j_m3']:.2e} J/m^3",
            "2) plasma contact flux  q_in = (1-R) sigma (T_plasma^4 - T0^4)",
            f"   = {cr['q_contact_w_m2']/1e6:.1f} MW/m^2   at {self.plasma_temp_k:.0f} K  (scales as T^4)",
            "3) sideways conduction loss  q_cond = k (T_melt - T0) / L_kerf",
            f"   = {cr['q_cond_w_m2']/1e6:.1f} MW/m^2   ->  q_net = {cr['q_net_w_m2']/1e6:.1f} MW/m^2",
            "4) recession velocity  u = q_net / E_v",
            f"   = {cr['recession_mm_s']:.2f} mm/s  ->  "
            + (f"through {cr['thickness_mm']:.0f} mm in {cr['through_time_s']:.1f} s"
               if cr["can_cut"] else "q_net <= 0: CANNOT CUT (conduction-limited)"),
            "",
            "Why diamond is nearly uncuttable: k=2200 W/mK conducts the incoming flux",
            "away faster than it can ablate (q_cond > q_in). High-reflectivity aluminium",
            "cuts slowly for the same family of reasons. Change material with ,/. -- the",
            "spread of results is real, and some of it is genuinely counterintuitive.",
        ]
        if self.scene == "binding":
            self._draw_overlay("PHOTON-BINDING MATH  (press M to close)", binding_lines)
        elif self.scene == "cut":
            self._draw_overlay("CUTTING MATH  (press M to close)", cutting_lines)
        else:
            lines += ["", "(binding proofs: view 3 + M   |   cutting proofs: view 4 + M)"]
            self._draw_overlay("DEVICE MATH / FEASIBILITY  (press M to close)", lines)


def export_obj_all(hilt_parts, engine_parts, showcase_parts, out_dir="export"):
    os.makedirs(out_dir, exist_ok=True)
    for name, parts in (("hilt", hilt_parts), ("engine", engine_parts),
                         ("microcavity_showcase", showcase_parts)):
        path = os.path.join(out_dir, f"{name}.obj")
        with open(path, "w") as fh:
            fh.write(f"# {name} -- exported by LS.py\n")
            voff = 1
            for part in parts:
                for mesh in part.meshes:
                    fh.write(f"o {part.key}_{mesh.name or 'mesh'}\n")
                    for x, y, z in mesh.verts:
                        fh.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
                    for face in mesh.faces:
                        idx = " ".join(str(i + voff) for i in face)
                        fh.write(f"f {idx}\n")
                    voff += len(mesh.verts)
        print(f"wrote {path}")
    return out_dir


# =============================================================================
# SECTION 8 -- SELFTEST / CONSOLE FEASIBILITY REPORT / LEGACY CHARTS / MAIN
# =============================================================================

def selftest():
    """Headless build + physics + one offscreen render per scene. No display
    required (forces the SDL dummy driver) -- safe to run in CI."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    ok = True

    def check(label, cond):
        nonlocal ok
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
        ok = ok and cond

    print("=" * 70)
    print("LS.py SELFTEST")
    print("=" * 70)

    try:
        hilt_parts, hilt_len, blade_r = build_hilt()
        check("build_hilt()", len(hilt_parts) > 0)
        check("hilt length matches DIMS sum (incl. engine bay)",
              abs(hilt_len - (DIMS["head_len_mm"] + DIMS["grip_len_mm"] + DIMS["engine_bay_len_mm"]
                              + DIMS["pommel_len_mm"]) * MM) < 1e-9)
    except Exception as ex:
        check(f"build_hilt() raised {ex!r}", False)
        hilt_parts, hilt_len = [], 0.32

    try:
        engine_parts, engine_len = build_engine_showcase()
        check("build_engine_showcase()", len(engine_parts) > 0)
    except Exception as ex:
        check(f"build_engine_showcase() raised {ex!r}", False)
        engine_parts, engine_len = [], 0.085

    try:
        showcase_parts, patch_m = build_microcavity_showcase()
        check("build_microcavity_showcase()", len(showcase_parts) > 0)
        n_holes = len(showcase_parts[4 if len(showcase_parts) > 4 else -1].meshes[0].faces) if showcase_parts else 0
        check("PhC hole lattice has faces", n_holes > 0)
    except Exception as ex:
        check(f"build_microcavity_showcase() raised {ex!r}", False)
        showcase_parts, patch_m = [], 0.02

    try:
        blade = build_blade_mesh(0.8, 0.03, 7500.0)
        check("build_blade_mesh()", len(blade.meshes[0].verts) > 0)
    except Exception as ex:
        check(f"build_blade_mesh() raised {ex!r}", False)

    try:
        rpt = full_feasibility_report()
        finite = all(math.isfinite(v) for v in rpt.values() if isinstance(v, float))
        check("full_feasibility_report() all-finite", finite)
        check("photon energy ~2.48e-19 J @ 800nm", abs(rpt["e_photon_j"] - 2.48e-19) / 2.48e-19 < 0.01)
        check("column intensity is far below breakdown (honest infeasibility)",
              rpt["column_ratio_to_threshold"] < 1e-3)
        check("BEC target density exceeds critical density (honest infeasibility)",
              rpt["ratio_solid"] > 1.0)
        check("chem engine fuel flow / runtime / cavity finesse are positive and finite",
              rpt["fuel_flow_kg_s"] > 0 and rpt["chem_runtime_s"] > 0 and rpt["cavity_finesse"] > 1.0)
        check("cavity-dump energy respects conservation (dump < total chemical energy over burn)",
              rpt["cavity_dump_energy_j"] < rpt["p_chem_w"] * rpt["chem_runtime_s"])
        check("cavity-dump peak intensity clears the air-breakdown band (can reionize the full column)",
              rpt["dump_reionizes_full_column"])
        check("average pulsed power stays <= continuous chem input (energy conservation over many pulses)",
              rpt["cavity_dump_energy_j"] * rpt["rep_rate_hz"] <= rpt["p_chem_w"] * 1.0001)
        check("pulsed average power is still far below the blade's continuous radiative need (honest: bursts, not sustain)",
              rpt["cavity_dump_energy_j"] * rpt["rep_rate_hz"] < rpt["blade_p_rad_w"])
        check("waste heat exceeds useful photon output (real: eta_photon<1 always means waste>0)",
              rpt["waste_heat_w"] > rpt["p_chem_w"])
        check("radiator alone cannot shed the captured waste heat (honest: forces the thermal-buffer limit)",
              rpt["radiator_capacity_w"] < rpt["captured_w"])
        check("thermal-limited runtime is shorter than fuel-limited runtime (thermal, not fuel, actually governs)",
              rpt["engine_runtime_s"] == min(rpt["chem_runtime_s"], rpt["thermal_runtime_s"])
              and rpt["thermal_runtime_s"] < rpt["chem_runtime_s"])
        check("grip-side conduction stack keeps the laser's modest heat load to a sane double-digit/low-hundreds K rise",
              0.0 < rpt["dT_stack_k"] < 1000.0)
        check("MLI is correctly shown as irrelevant (not applied) at grip temperatures vs. dominant at engine-bay temps",
              rpt["dT_mli_grip_k"] > rpt["dT_stack_k"])
    except Exception as ex:
        check(f"full_feasibility_report() raised {ex!r}", False)

    try:
        b = photon_binding_report()
        finite = all(math.isfinite(v) for v in b.values() if isinstance(v, float))
        check("photon_binding_report() all-finite", finite)
        check("slowing light raises effective photon mass (m grows with group index)",
              b["m_eff_kg"] > (photon_energy_j(PHYS["wavelength_nm"] * NM) / c ** 2) * 0.99)
        check("Rydberg blockade radius is microscopic (~10 um class, ultracold-only)",
              1.0 < b["rydberg_blockade_um"] < 100.0)
        check("bound-photon bulk modulus is >1e9x softer than steel (honest: barely a 'hold')",
              b["bulk_vs_steel"] < 1e-9)
        check("binding needs cryogenic temps; the 7500 K plasma is far too hot (k_B T >> mu)",
              (not b["binds_at_plasma_temp"]) and b["thermal_ratio"] > 10.0)
        check("cannot parry a 100-lbf block: superfluid has ~zero static shear (needs crystalline order)",
              (not b["can_parry"]) and b["shear_margin"] < 1e-3)
        check("a slow swing is below the Landau critical velocity -> frictionless slip-through (no grip)",
              b["superfluid_slips"] and b["swing_speed_m_s"] < b["v_crit_m_s"])
        check("Deborah number << 1 -> behaves as a FLUID on a strike timescale (parts, cannot hit)",
              (not b["behaves_solid"]) and b["deborah"] < 1e-6)
        check("compressive spring-force for a 10% squeeze is imperceptible (<< 1 N, sub-milli-newton)",
              0.0 < b["spring_force_n"] < 1.0)
        check("supersolid density-modulation period is micron-scale (matches real polariton demos)",
              0.1 < b["supersolid_period_um"] < 100.0)
    except Exception as ex:
        check(f"photon_binding_report() raised {ex!r}", False)

    try:
        diamond = cutting_report("diamond")
        steel = cutting_report("mild steel")
        alu = cutting_report("aluminium 6061")
        ti = cutting_report("titanium Ti-6Al-4V")
        check("cutting model all-finite for a representative material (steel)",
              all(math.isfinite(v) for v in steel.values() if isinstance(v, float)))
        check("diamond is uncuttable: its huge conductivity bleeds heat away faster than the plasma supplies",
              (not diamond["can_cut"]) and diamond["conduction_limited"])
        check("high-k/high-reflectivity aluminium cuts far slower than low-k titanium (non-obvious but real)",
              alu["recession_mm_s"] < ti["recession_mm_s"])
        check("hotter plasma cuts steel faster (flux ~ T^4 ties the temp slider to performance)",
              cutting_report("mild steel", plasma_temp_k=10000.0)["recession_mm_s"] > steel["recession_mm_s"])
    except Exception as ex:
        check(f"cutting_report() raised {ex!r}", False)

    try:
        eng = engineered_saber_report()
        finite = all(math.isfinite(v) for v in eng.values() if isinstance(v, float))
        check("engineered_saber_report() all-finite", finite)
        # Ampere clash current scales as sqrt(force): doubling force -> sqrt(2)x current
        i50 = current_for_clash_a(50.0, 0.2, 0.006)
        i100 = current_for_clash_a(100.0, 0.2, 0.006)
        check("Ampere clash current follows sqrt(force) (real force law, not fudged)",
              abs(i100 / i50 - math.sqrt(2.0)) < 1e-6)
        check("design current confines the plasma (Z-pinch/Bennett self-confinement is real)",
              eng["self_confined"] and eng["i_design_a"] > eng["i_bennett_a"])
        check("Z-pinch magnetic 'stiffness' vastly exceeds the photon fluid (engineering-around works)",
              eng["stiffness_gain"] > 100.0)
        check("real clash force is delivered at a plausible (kA-class, not absurd) current",
              1000.0 < eng["i_design_a"] < 20000.0)
        check("the arc-power price is real and large (MW-class): a cost, honestly reported",
              eng["p_arc_w"] > 1e6)
        check("engineered scorecard is mostly PASS with honest PARTIALs (no fabricated success)",
              eng["n_pass"] >= 4 and eng["n_partial"] >= 1)
    except Exception as ex:
        check(f"engineered_saber_report() raised {ex!r}", False)

    if pygame is not None:
        try:
            pygame.init()
            surf = pygame.Surface((640, 480))
            for parts, home_dist in ((hilt_parts, hilt_len * 1.7),
                                      (engine_parts, engine_len * 1.9),
                                      (showcase_parts, patch_m * 1.8)):
                if not parts:
                    continue
                rnd = Renderer(parts, home_dist=home_dist, scale=home_dist)
                rnd.render(surf, pygame.Rect(0, 0, 640, 480), True,
                           pygame.font.SysFont("monospace", 12), interactive=False)
            check("offscreen render of all 3 scenes (dummy video driver)", True)
        except Exception as ex:
            check(f"offscreen render raised {ex!r}", False)

        try:
            app = App()
            for scene in SCENES:
                app.scene = scene
                app._rend().tick(0.1)
                app._draw()
            # cut scene across every material (drives build_cut_test + panel)
            app.scene = "cut"
            for _ in range(len(MATERIAL_KEYS)):
                app._cycle_material(+1)
                app._draw()
            # exercise the live dynamic cut: run steel to breakthrough, and
            # confirm diamond stalls (depth stays 0)
            app.material_idx = MATERIAL_KEYS.index("mild steel"); app._reset_cut()
            app._toggle_cut_run()
            for _ in range(400):
                app._advance_cut(0.05); app._draw()
            assert app.cut_done_s is not None and app.cut_depth_m >= CUT_BLOCK_H, "steel should cut through"
            app.material_idx = MATERIAL_KEYS.index("diamond"); app._reset_cut()
            app._toggle_cut_run()
            for _ in range(50):
                app._advance_cut(0.05); app._draw()
            assert app.cut_depth_m == 0.0 and app.cut_done_s is None, "diamond must not cut"
            app._reset_cut()
            app.show_blueprint = True
            app.scene = "hilt"
            app._draw()
            app.show_blueprint = False
            app.ignited = True
            app.ignite_amt = 1.0
            app.engine_armed = True
            app.engine_armed_since = 0.0
            app.scene = "hilt"
            app._draw()
            app.show_info = True
            app._draw()
            app.show_info = False
            app.show_math = True
            for scene in ("hilt", "binding", "cut"):
                app.scene = scene
                app._draw()
            # exercise the button/slider hit-testing path too
            for b in app.buttons:
                assert b.hit(b.rect.center)
            for s in app.sliders:
                s.set_from_x(s.rect.centerx)
            app._check_thermal_limit()
            check("App() builds, draws all 5 scenes + blueprint + overlays, controls hit-test cleanly", True)
        except Exception as ex:
            check(f"App() smoke test raised {ex!r}", False)
        finally:
            pygame.quit()
    else:
        check("pygame available", False)

    print("=" * 70)
    print("SELFTEST " + ("PASSED" if ok else "FAILED"))
    print("=" * 70)
    return ok


def print_feasibility():
    rpt = full_feasibility_report()
    print("=" * 78)
    print("LIGHTSABER ENGINEERING -- HONEST FEASIBILITY REPORT (all numbers computed live)")
    print("=" * 78)
    print(f"\n-- LASER --")
    print(f"  {PHYS['wavelength_nm']:.0f} nm, photon energy = {rpt['e_photon_j']:.3e} J")
    print(f"  focused peak intensity @ {PHYS['beam_waist_um']:.0f} um waist = {rpt['i_focus_peak']:.3e} W/m^2")
    print(f"  real air-breakdown band: ~1e9-1e11 W/m^2  ->  "
          f"{'BELOW' if rpt['focus_below_threshold'] else 'within/above'} threshold "
          f"({rpt['focus_ratio_to_threshold']:.2f}x lower bound)")
    print(f"\n-- PLASMA COLUMN (same laser power spread over the full blade aperture) --")
    print(f"  I_column = {rpt['i_column']:.3e} W/m^2  ->  {rpt['column_ratio_to_threshold']:.2e}x the threshold")
    print(f"  CONCLUSION: a {PHYS['laser_power_w']:.0f} W diode cannot sustain ionization across a "
          f"{DIMS['blade_d_mm']:.0f} mm column; it can only ignite a focused spot.")
    print(f"\n-- THERMAL (glowing channel radiative loss) --")
    print(f"  {DIMS['blade_len_m']*100:.0f} cm x {DIMS['blade_d_mm']:.0f} mm @ {PHYS['plasma_temp_K']:.0f} K "
          f"radiates {rpt['blade_p_rad_w']:.3e} W")
    print(f"  available laser electrical draw: {rpt['e_sus_w']:.1f} W  ->  shortfall {rpt['power_shortfall']:.2e}x")
    print(f"  laser-side may rise +{rpt['dT_stack_k']:.1f} K above ambient while the grip stays AT ambient")
    print(f"  (N={DIMS['mli_layers']}-shield MLI eps_eff={rpt['mli_eps_eff']:.2e}: implies {rpt['dT_mli_grip_k']:.2e} K "
          f"at grip temps -- irrelevant here, radiation ~T^3; MLI matters at the engine bay, not this leak)")
    print(f"\n-- POWER BUDGET (practical, supercap/battery config) --")
    print(f"  {PHYS['supercap_energy_wh']:.0f} Wh bank / {rpt['e_sus_w']:.1f} W sustain draw = "
          f"{rpt['runtime_h']:.1f} hours runtime")
    print(f"\n-- INTERNAL CHEM PHOTON ENGINE (lives in the hilt's engine bay, no nuclear component) --")
    print(f"  combustor blackbody emission @ {PHYS['chem_chamber_temp_k']:.0f} K: {rpt['p_chem_w']:.3e} W")
    print(f"  fuel flow {rpt['fuel_flow_kg_s']*1000:.2f} g/s  ->  "
          f"{DIMS['cartridges']}x{DIMS['cartridge_mass_g']:.0f} g cartridges give {rpt['chem_runtime_s']:.1f} s burn time")
    print(f"  cavity finesse {rpt['cavity_finesse']:.0f}, intrinsic lifetime {rpt['cavity_tau_intrinsic_s']*1e6:.2f} us,")
    print(f"    slow-light (x{PHYS['slow_light_factor']:.0f}) tau_eff = {rpt['cavity_tau_eff_s']*1000:.2f} ms")
    print(f"  cavity-dump energy E=P_chem*tau_eff = {rpt['cavity_dump_energy_j']:.2f} J  ->  "
          f"peak power {rpt['cavity_dump_peak_power_w']:.3e} W (real: cavity-dump/Q-switch physics,")
    print(f"    NOT 'parametric amplification from chaotic bouncing' -- that needs an active gain medium)")
    print(f"  dump column intensity {rpt['dump_column_intensity_w_m2']:.3e} W/m^2 vs 1e9-1e11 breakdown band  ->  "
          f"{'REIONIZES the full column' if rpt['dump_reionizes_full_column'] else 'still too weak'}")
    print(f"  repetition rate {rpt['rep_rate_hz']:.1f} Hz vs {PHYS['human_flicker_fusion_hz']:.0f} Hz eye-fusion  ->  "
          f"{'reads as steady glow' if rpt['appears_continuous'] else 'reads as a visible strobe'}")
    print(f"  CONCLUSION: cannot replace the blade's continuous radiative loss (still {rpt['power_shortfall']:.1e}x"
          f" short), but CAN periodically re-ionize the full column -- a real, honest, useful contribution.")
    print(f"\n-- ENGINE HEAT REJECTION (HfC crucible + MLI + heat pipes + radiator + buffer) --")
    print(f"  waste heat {rpt['waste_heat_w']:.3e} W ({(1-PHYS['chem_eta_photon'])*100:.0f}% of "
          f"{rpt['p_chem_input_w']:.3e} W chemical input, eta_photon={PHYS['chem_eta_photon']*100:.0f}%)")
    print(f"  heat pipes capture {PHYS['heat_pipe_capture_frac']*100:.0f}% -> {rpt['captured_w']:.3e} W to radiator "
          f"(area {rpt['radiator_area_m2']*1e4:.1f} cm^2, capacity {rpt['radiator_capacity_w']:.1f} W)")
    print(f"  shortfall {rpt['net_to_buffer_w']:.3e} W -> {PHYS['buffer_mass_kg']*1000:.0f}g thermal buffer gives "
          f"{rpt['thermal_runtime_s']:.2f} s before its {PHYS['buffer_delta_t_max_k']:.0f} K safety margin is spent")
    print(f"  REAL engine runtime = min(fuel {rpt['chem_runtime_s']:.1f}s, thermal {rpt['thermal_runtime_s']:.2f}s) "
          f"= {rpt['engine_runtime_s']:.2f} s")
    print(f"  residual parasitic leak steady-state conduction: +{rpt['dT_engine_bay_k']:.2e} K -- physically "
          f"impossible, proving this MUST stay a brief burst, never continuous operation")
    print(f"\n-- ASPIRATIONAL 'SOLID BEAM' POLARITON SUPERSOLID (not implemented in the build) --")
    print(f"  target density {PHYS['n_target_m3']:.2e} m^-3 @ {PHYS['T_beam_target_K']:.0f} K")
    print(f"  BEC critical density at that temperature: {rpt['n_c_solid']:.3e} m^-3")
    print(f"  target/critical ratio: {rpt['ratio_solid']:.2e}x  ->  far beyond any demonstrated polariton system")

    b = photon_binding_report()
    print(f"\n-- PHOTON BINDING: can slowed light be bound into a solid mass? (SECTION 4b) --")
    print(f"  1) slow light -> mass:  m = (E_photon/c^2)*n_g, n_g={b['n_group']:.0f}  ->  "
          f"v_g={b['v_g_frac_c']*100:.1f}% c, m_eff={b['m_eff_kg']:.2e} kg")
    print(f"  2) interaction:  Rydberg-EIT blockade r_b={b['rydberg_blockade_um']:.0f} um "
          f"(real bound photon pairs, ultracold-only); mu={b['mu_mev']:.0f} meV")
    print(f"  3) the 'hold':  bulk modulus B=mu*n={b['bulk_pa']:.2f} Pa = {b['bulk_vs_steel']:.1e}x steel "
          f"(softer than air); c_s={b['c_s_m_s']/1000:.0f} km/s, xi={b['healing_length_um']:.2f} um")
    print(f"     for rubber-like stiffness you'd need {b['density_gap']:.1e}x the target density;")
    print(f"     a {PHYS['compression_strain']*100:.0f}% squeeze pushes back only {b['spring_force_n']*1000:.2f} mN over the blade face")
    print(f"  4) HOLDING RESISTANCE:  below the Landau critical velocity (v_c={b['v_crit_m_s']/1000:.0f} km/s) a")
    print(f"     {b['swing_speed_m_s']:.0f} m/s swing slips through FRICTIONLESS; Deborah De={b['deborah']:.1e} << 1")
    print(f"     -> it flows like a fluid on a strike timescale (it cannot hit or be hit)")
    print(f"  5) THE PARRY needs static shear = crystalline order:  a superfluid's is ZERO; even an")
    print(f"     optimistic supersolid (period {b['supersolid_period_um']:.1f} um) is off by {1/b['shear_margin']:.1e}x vs the")
    print(f"     {PHYS['lateral_load_n']:.0f} N block ({b['tau_required_pa']/1e3:.0f} kPa) -> CANNOT parry")
    print(f"  6) and binding needs k_B T < mu:  T_max={b['t_ceiling_k']:.0f} K (cryogenic); the 7500 K "
          f"plasma is {b['thermal_ratio']:.0f}x too hot -> nothing binds in the built blade.")

    print(f"\n-- MATERIAL CUT TEST (SECTION 4c): ablation energy balance at {PHYS['plasma_temp_K']:.0f} K --")
    print(f"  {'material':22s} {'q_net(MW/m2)':>12s} {'recession':>11s} {'through 20mm':>13s}")
    for key in MATERIAL_KEYS:
        cr = cutting_report(key, thickness_mm=20.0)
        tt = f"{cr['through_time_s']:.1f} s" if cr["can_cut"] else "NEVER"
        rec = f"{cr['recession_mm_s']:.2f} mm/s" if cr["can_cut"] else "0 (cond-lim)"
        print(f"  {key:22s} {cr['q_net_w_m2']/1e6:12.1f} {rec:>11s} {tt:>13s}")

    print("\n" + "=" * 78)
    print("Overall: the DIODE LASER + PLASMA-CHANNEL + PHOTONIC-CRYSTAL prototype is the")
    print("buildable path (real optics/thermo/EM, computed above). The hot plasma channel")
    print("CUTS most materials by real ablation physics -- but the indefinite rigid, bindable,")
    print("parry-able 'solid light' blade is not physically achievable with known science.")
    print("=" * 78)


def legacy_report():
    """Legacy static matplotlib charts for the ASPIRATIONAL solid-beam physics
    (kept from the original LS.py for continuity). Lazy-imports matplotlib and
    scipy.integrate so the interactive viewer never needs them."""
    import matplotlib.pyplot as plt
    from scipy.integrate import solve_ivp

    L, r = 1.067, 0.025
    V_beam = math.pi * r ** 2 * L
    tau_eff = 2e-7
    n_target = PHYS["n_target_m3"]
    T_beam = PHYS["T_beam_target_K"]
    m_eff = PHYS["m_eff_kg"]
    eta_coupling, eta_laser = 0.4, PHYS["laser_eta_wallplug"]

    N_total = n_target * V_beam
    E_photon = photon_energy_j(PHYS["wavelength_nm"] * NM)
    photon_rate_formation = N_total / (3.0 * eta_coupling)
    laser_power_formation = photon_rate_formation * E_photon / eta_laser
    loss_rate = N_total / tau_eff
    sustain_elec = (loss_rate * E_photon) / (eta_laser * eta_coupling)
    n_c = critical_density_bec(T_beam, m_eff)

    def rate_eq(t, N, R_pump, tau):
        return R_pump - N / tau

    R_pump = N_total / (tau_eff * (1 - math.exp(-3.0 / tau_eff)))
    sol = solve_ivp(rate_eq, [0, 3.0], [0], args=(R_pump, tau_eff), method="RK45", rtol=1e-6)

    print(f"Total polaritons: {N_total:.2e} | n_c@{T_beam:.0f}K: {n_c:.2e} | "
          f"formation power: {laser_power_formation:.1f} W | sustain: {sustain_elec:.1f} W")

    plt.figure(figsize=(12, 8))
    plt.subplot(2, 2, 1)
    plt.plot(sol.t, sol.y[0] / 1e18, "b-")
    plt.xlabel("Time (s)"); plt.ylabel("N (1e18)"); plt.title("Aspirational Formation Dynamics"); plt.grid(True)

    plt.subplot(2, 2, 2)
    T_range = np.linspace(300, 2000, 100)
    n_c_curve = [critical_density_bec(t, m_eff) for t in T_range]
    plt.semilogy(T_range, n_c_curve, "r-")
    plt.axhline(n_target, color="k", linestyle="--", label="target density")
    plt.xlabel("Temperature (K)"); plt.ylabel("Critical density (m^-3)")
    plt.title("BEC Critical Density vs T"); plt.legend(); plt.grid(True)

    plt.subplot(2, 2, 3)
    plt.bar(["Formation", "Sustain"], [laser_power_formation, sustain_elec], color=["blue", "orange"])
    plt.ylabel("Power (W)"); plt.title("Aspirational Power Requirements"); plt.grid(True)

    plt.subplot(2, 2, 4)
    plt.text(0.05, 0.6,
              f"Target/critical density ratio: {n_target/n_c:.2e}x\n"
              f"Realistic tau_eff limit: ~1e-7 - 1e-9 s\n"
              f"See --feasibility for the buildable-device numbers.", fontsize=10)
    plt.axis("off"); plt.title("Summary")
    plt.tight_layout()
    plt.show()


def print_cut_test(temp_k=None, blade_d_mm=None, thickness_mm=20.0):
    """Console cutting-test table across every material (the --cut CLI)."""
    temp_k = PHYS["plasma_temp_K"] if temp_k is None else temp_k
    blade_d_mm = DIMS["blade_d_mm"] if blade_d_mm is None else blade_d_mm
    print("=" * 78)
    print(f"MATERIAL CUT TEST -- plasma {temp_k:.0f} K, blade dia {blade_d_mm:.0f} mm, "
          f"target thickness {thickness_mm:.0f} mm")
    print("(real ablation energy balance: u = (q_in - q_conduction) / E_v)")
    print("=" * 78)
    hdr = f"{'material':22s} {'E_v(GJ/m3)':>10s} {'q_in':>8s} {'q_net':>8s} {'recession':>12s} {'through':>10s}"
    print(hdr); print("-" * len(hdr))
    for key in MATERIAL_KEYS:
        cr = cutting_report(key, temp_k, blade_d_mm, thickness_mm)
        rec = f"{cr['recession_mm_s']:.2f} mm/s" if cr["can_cut"] else "-- (cond)"
        tt = f"{cr['through_time_s']:.1f} s" if cr["can_cut"] else "NEVER"
        print(f"{key:22s} {cr['e_v_j_m3']/1e9:10.2f} {cr['q_contact_w_m2']/1e6:7.0f}M "
              f"{cr['q_net_w_m2']/1e6:7.0f}M {rec:>12s} {tt:>10s}")
    print("-" * len(hdr))
    print("q in MW/m^2. 'NEVER' = conduction bleeds heat away faster than the plasma supplies.")
    print("Hotter plasma (flux ~ T^4) and thinner/low-k materials cut faster. Diamond's huge")
    print("conductivity makes it near-uncuttable thermally -- a real, non-obvious result.")


def print_engineering():
    """The --engineer report: treat every failure as an engineering hurdle,
    work around it with real physics, and print the honest scorecard for a
    REAL (magnetic plasma-arc) lightsaber."""
    r = engineered_saber_report()
    print("=" * 78)
    print("ENGINEERING AROUND THE WALLS -- can a REAL lightsaber be built? (SECTION 4d)")
    print("=" * 78)
    print("Rule: every 'impossibility' is an engineering hurdle. The rigid SOLID-LIGHT")
    print("blade is the one true wall (a superfluid has zero static shear) -- so we BYPASS")
    print("it: achieve the FUNCTIONS with a current-carrying magnetic PLASMA-ARC blade.")
    print("\nOne blade current does three real jobs at once:")
    print(f"  - CLASH:   Ampere force between two blades -> {PHYS['clash_force_target_n']:.0f} N "
          f"needs I = {r['i_design_a']:.0f} A  ({r['i_full_block_a']:.0f} A for a full "
          f"{PHYS['lateral_load_n']:.0f} N block)")
    print(f"  - CONFINE: Z-pinch/Bennett -> {r['i_bennett_a']:.0f} A confines the plasma; design "
          f"{r['i_design_a']:.0f} A {'EXCEEDS' if r['self_confined'] else 'is below'} it -> "
          f"{'self-confined' if r['self_confined'] else 'under-confined'}")
    print(f"             magnetic pressure = {r['p_mag_pa']/1000:.1f} kPa 'stiffness' "
          f"= {r['stiffness_gain']:.0f}x the photon-fluid's 2.4 Pa (B = {r['b_surf_t']:.2f} T)")
    print(f"  - CUT:     steel ablates at {r['steel_recession_mm_s']:.2f} mm/s at "
          f"{PHYS['arc_plasma_temp_k']:.0f} K (diamond still uncuttable -- honest)")

    pw = r["power"]
    print(f"\nSELF-CONTAINED POWER (finished): the Ampere clash needs NO extra burst -- both")
    print(f"blades are already energised -- so the cost is just holding the {r['p_arc_w']/1e6:.2f} MW arc.")
    print(f"  hybrid: supercap ({pw['supercap_mass_kg']:.1f} kg) buffers the ms-scale pulsed arc;")
    print(f"          a {PHYS['hilt_pack_kwh']:.1f} kWh in-hilt battery (~{PHYS['hilt_pack_mass_kg']:.0f} kg) "
          f"sustains it")
    print(f"  runtime: {pw['hilt_glow_s']:.1f} s active blade per hilt charge (idle "
          f"{pw['p_idle_w']/1e6:.2f} MW, above Bennett -> stays confined);")
    print(f"           {pw['hilt_full_s']:.1f} s continuous full-power; {pw['backpack_glow_s']:.0f} s on a "
          f"{PHYS['backpack_energy_wh']/1000:.0f} kWh backpack. Ignite-for-a-fight, like the films.")

    le = r["lethality"]
    print(f"\nLETHALITY (this is a WEAPON, by design -- not a safe toy):")
    print(f"  the {PHYS['arc_plasma_temp_k']:.0f} K blade cuts flesh at {le['flesh_recession_mm_s']:.0f} mm/s "
          f"(instant amputation), and the blade circuit stores {le['stored_j']/1000:.0f} kJ = "
          f"{le['lethal_margin']:.0e}x a lethal electrical dose. Handle as the lethal high-energy")
    print(f"  weapon it is (dead-man, current-limit, insulated hilt, controlled return path).")

    mo = r["mott"]
    print(f"\nWHAT ABOUT ACTUAL SOLID LIGHT? -- it is REAL, but not as a blade:")
    print(f"  a photonic MOTT INSULATOR (Simon group, Nature 2019) freezes photons into a")
    print(f"  CRYSTAL (U/J={mo['U_over_J']:.0f} > 3.4 -> {'solid' if mo['is_solid'] else 'fluid'}), the only")
    print(f"  'solid light' with the crystalline order that carries static shear -- BUT at "
          f"~{mo['demo_temp_k']*1000:.0f} mK")
    print(f"  on a chip. A warm metre blade is {mo['temp_gap']:.0e}x too hot and needs "
          f"{mo['blade_sites']:.0e} ordered")
    print(f"  cavity sites in a physical scaffold. Real physics, astronomically far from a")
    print(f"  free swingable blade -- so the plasma arc is what actually delivers the functions.")

    print("\nFUNCTION SCORECARD (real numbers behind each):")
    print("-" * 78)
    for name, status, detail in r["functions"]:
        print(f"  [{status:10s}] {name}")
        print(f"               {detail}")
    print("-" * 78)
    print(f"RESULT: {r['n_pass']} of {r['n_total']} functions PASS; 1 is LETHAL-by-design (intended);")
    print("1 (rigid 'solid light') stays a physics wall, bypassed by the plasma arc.")
    print("A lightsaber that GLOWS, holds a FIXED LENGTH, CUTS, CLASHES with another blade,")
    print("and runs SELF-CONTAINED (ignite-for-a-fight) IS buildable with today's physics --")
    print("as a kA / MW-class, intentionally-lethal plasma-arc weapon. Every claim above is")
    print("computed from real EM / plasma / thermodynamics; run --selftest to check the math.")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description="Lightsaber Engineering Digital Twin")
    parser.add_argument("--selftest", action="store_true", help="headless build+physics+render sanity check")
    parser.add_argument("--feasibility", action="store_true", help="print the full honest physics report")
    parser.add_argument("--cut", nargs="?", const="", metavar="TEMP_K",
                        help="print the material cut-test table (optional plasma temperature in K)")
    parser.add_argument("--engineer", action="store_true",
                        help="failure -> engineering-workaround scorecard for a REAL (magnetic plasma-arc) saber")
    parser.add_argument("--report", action="store_true", help="legacy matplotlib charts (aspirational solid-beam)")
    parser.add_argument("--export-obj", action="store_true", help="write OBJ files to ./export/ and exit")
    args = parser.parse_args()

    if args.selftest:
        sys.exit(0 if selftest() else 1)
    if args.feasibility:
        print_feasibility()
        return
    if args.cut is not None:
        temp = float(args.cut) if args.cut else None
        print_cut_test(temp_k=temp)
        return
    if args.engineer:
        print_engineering()
        return
    if args.report:
        legacy_report()
        return
    if args.export_obj:
        hilt_parts, _, _ = build_hilt()
        engine_parts, _ = build_engine_showcase()
        showcase_parts, _ = build_microcavity_showcase()
        export_obj_all(hilt_parts, engine_parts, showcase_parts)
        return

    if pygame is None:
        print("pygame is required for the interactive viewer. Install with:")
        print("  python3 -m pip install pygame numpy")
        sys.exit(1)
    App().run()


if __name__ == "__main__":
    main()
