# Fly Connectome Escape Experiment

A Pygame experiment that presents a controlled expanding swatter, converts its
retinal angular size and expansion velocity into visual-neuron activity, and
routes that activity through a simplified circuit built from MaleCNS data.

The current milestone includes:

- a wandering fly;
- reproducible slow and fast virtual looming trials from either side;
- angular-size and angular-velocity visual features;
- a bilateral LC4/LPLC2 → DNp01 rate model using real synapse-count weights;
- visible postural preparation, leg extension, jump, and airborne phases;
- rapid GF-like and prepared long-mode outcomes;
- live visual and neural activity meters; and
- LC4, LPLC2, and DNp01 lesion controls.

The first real connectome extract is also available under `data/`. See
`CIRCUIT_EVIDENCE.md` for the biological evidence, important limitations, and
the exact MaleCNS v1.0 connectivity summary.

## Run it

```bash
conda activate flybrain
cd /home/saliha/Desktop/personal/projects/fly_connectome
python main.py
```

Press `Space` or click in the arena to start a looming trial. The swatter moves
toward the fly and expands, LC4/LPLC2 respond to its visual features, and the
fly progresses through observable preparation and takeoff phases if DNp01
reaches threshold.

Controls:

- `Space` or arena click: start/restart a trial;
- `A`, `D`: attack from the left or right;
- `S`, `F`: select slow or fast loom;
- `M`: switch between biological looming and fixed-pulse debug mode;
- `1`, `2`, `3`: toggle LC4, LPLC2, or DNp01 lesions;
- `R`: restore and reset the experiment;
- checkboxes: mouse-accessible versions of the lesion controls; and
- `Escape`: quit.

## Run tests

```bash
pytest -q
```

## Refresh the connectome extract

```bash
python fetch_connectome.py
```

## Scientific boundary

The topology, neuron IDs, and connection weights come from MaleCNS v1.0. The
looming geometry follows retinal angular size and angular expansion velocity;
the LC4/LPLC2 feature curves are literature-inspired approximations. Neural
dynamics, behavioral thresholds, posture timing, and takeoff physics remain
simplified modeling choices. DNp01 represents the rapid Giant-Fiber pathway,
not every escape pathway used by a biological fly. Fixed-pulse mode is retained
only as a circuit debugging tool.
