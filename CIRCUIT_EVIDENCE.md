# Version 1 escape circuit: evidence and scope

## Selected pathway

Version 1 will model the bilateral, direct pathway:

```text
looming visual stimulus
   ├── angular expansion velocity -> LC4 ──┐
   └── angular size              -> LPLC2 ─┴──> DNp01 (Giant Fiber)
                                                   ↓
                                          rapid takeoff pathway
```

This is a deliberately narrow model of the rapid Giant-Fiber-mediated escape
component. It is not a model of every visually evoked fly escape.

## Biological evidence

- Ache et al. (2019) reconstructed direct LC4 and LPLC2 synapses onto the
  Giant Fiber. Their physiology and silencing experiments support LC4 as an
  angular-expansion-velocity input and LPLC2 as the angular-size input. They
  found LPLC2 necessary for the Giant-Fiber-mediated response and modeled the
  GF as integrating the two features.
- von Reyn et al. (2017) identified LC4 as an input conveying predator approach
  information and showed that the Giant Fiber integrates visual features while
  selecting and timing a fast escape motor program.
- Sorkac et al. (2023) independently recovered LC4 and LPLC2 as presynaptic
  partners of the Giant Fiber with retrograde transsynaptic tracing.
- Fotowat et al. (2009) showed an important limitation: visually evoked escape
  can use at least two descending pathways and does not universally require the
  Giant Fibers. Accordingly, DNp01 output in this project means activation of a
  **rapid GF pathway**, not a complete biological decision to escape.

## MaleCNS v1.0 result

Queried from neuPrint dataset `male-cns:v1.0` on 2026-09-19. All selected
LC4/LPLC2 cells connect to the ipsilateral DNp01, and all three selected types
have `acetylcholine` as their MaleCNS consensus neurotransmitter annotation.

| Source | Side | Target body ID | Connected cells | Direct synapses | Range per cell |
|---|---:|---:|---:|---:|---:|
| LC4 | right | 10001 | 55 | 2,580 | 21–67 |
| LPLC2 | right | 10001 | 91 | 2,220 | 1–59 |
| LC4 | left | 10010 | 71 | 3,782 | 30–86 |
| LPLC2 | left | 10010 | 94 | 2,642 | 2–64 |

Totals: 126 LC4 cells, 185 LPLC2 cells, 2 DNp01 cells, 311 direct edges, and
11,224 detected synapses.

The left/right count asymmetry is a property of this reconstructed specimen and
must not be interpreted as a universal biological asymmetry without additional
evidence.

## Modeling boundaries

- Synapse counts are structural measurements, not firing rates or calibrated
  physiological gains.
- The neural model normalizes these counts, but that normalization and
  every activation threshold will be explicitly labeled as simulation choices.
- Neurotransmitter identities are predictions/consensus annotations and do not
  supply synaptic time constants, receptor composition, or gap-junction data.
- The default game mode computes the angular size and angular expansion
  velocity of a constant-size virtual object approaching at constant speed.
  The exact visual response curves and behavior state transitions remain
  approximations. A standardized fixed-pulse mode is retained only for circuit
  debugging.

## Implemented simulation

`neural_model.py` loads the four bilateral synapse totals from
`data/escape_connection_summary.csv`. For each side, DNp01 drive is the
synapse-count-weighted mean of LC4 and LPLC2 activity. Activity follows a
first-order leaky update with a 55 ms simulation time constant, and escape is
active when either DNp01 reaches 0.10. Lesioned inputs remain in the
normalization denominator, so disabling a class removes its contribution
instead of rescaling the remaining class to full strength.

`looming.py` models a circular object approaching at constant virtual speed.
LC4 receives normalized angular expansion velocity. LPLC2 receives a Gaussian
angular-size response centered at 60°; this captures the form reported in the
literature but its width and normalization are modeling parameters. Fast and
slow trials use 500 and 200 mm/s respectively, with a 20 mm object radius.

`behavior.py` exposes wandering, postural preparation, leg extension/jump,
airborne, and recovery phases. Fast velocity-dominated responses produce a
rapid GF-like takeoff; slower size-dominated responses produce a prepared
long-mode approximation. The 55 ms neural time constant, 0.10 DNp01 threshold,
feature normalizations, preparation durations, and movement speeds are
transparent simulation parameters, not values measured from MaleCNS.

## Sources

- Ache et al. (2019), *Neural Basis for Looming Size and Velocity Encoding in
  the Drosophila Giant Fiber Escape Pathway*:
  https://doi.org/10.1016/j.cub.2019.01.079
- von Reyn et al. (2017), *Feature Integration Drives Probabilistic Behavior in
  the Drosophila Escape Response*:
  https://doi.org/10.1016/j.neuron.2017.05.036
- Sorkaç et al. (2023), *retro-Tango enables versatile retrograde circuit
  tracing in Drosophila*:
  https://doi.org/10.7554/eLife.85041
- Fotowat et al. (2009), *A novel neuronal pathway for visually guided escape
  in Drosophila melanogaster*:
  https://doi.org/10.1152/jn.00073.2009
- Card and Dickinson (2008), *Visually mediated motor planning in the escape
  response of Drosophila*:
  https://doi.org/10.1016/j.cub.2008.07.094
- Card and Dickinson (2008), *Performance trade-offs in the flight initiation
  of Drosophila*:
  https://doi.org/10.1242/jeb.012682
- MaleCNS data access and downloads:
  https://male-cns.janelia.org/download/
- neuPrint dataset explorer:
  https://neuprint.janelia.org/?dataset=male-cns%3Av1.0
