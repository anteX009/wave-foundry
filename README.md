# Wave Foundry

Wave Foundry is a small procedural mesh generator for Blender and 3D printing.

It lets you create organic cylinder and square-based forms, preview them in a simple 3D interface, and export them as `.obj` files.

## Features

- Procedural 3D shape generation
- Cylinder and square base shapes
- Editable base width, base depth, and height
- Organic deformation filters:
  - Kymothea Flow
  - Harmonic Flow
  - Perlin Flux
- 3D preview with wireframe overlay
- Mini front, side, and top previews
- OBJ export for Blender and slicers
- Automatic export file names
- Lightweight Tkinter interface

## Requirements

- Python 3.10 or newer
- Tkinter
- Optional: `noise` for the real Perlin Flux filter

On macOS, Tkinter usually comes with the official Python installer from python.org.

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/wave-foundry.git
cd wave-foundry
```

Install optional dependencies:

```bash
pip3 install -r requirements.txt
```

## Run

From the project folder:

```bash
python3 src/wave_foundry.py
```

If the file is on your Desktop:

```bash
cd ~/Desktop/wave-foundry
python3 src/wave_foundry.py
```

## Exporting for Blender

Click `export obj`.

Then open Blender:

```text
File -> Import -> Wavefront (.obj)
```

## Exporting for 3D printing

The exported `.obj` is oriented for slicers using a vertical object orientation.

Recommended workflow:

1. Export `.obj` from Wave Foundry.
2. Import into Blender.
3. Inspect scale and orientation.
4. Export from Blender as `.stl` if your slicer prefers STL.

## Controls

### Shape

- `cylinder`: round or oval base
- `square`: square or rectangular base

### Base dimensions

- `base_width`: width of the base
- `base_depth`: depth of the base
- `height`: vertical height

Set `base_width` and `base_depth` to the same value for a perfect cylinder or square.

### Filters

#### Kymothea Flow

The main organic water-like surface filter.

Best for:
- soft flowing deformations
- bottle-like surfaces
- long vertical liquid shapes

#### Harmonic Flow

A trigonometric procedural wave system.

Best for:
- stable abstract waves
- clean organic modulation
- fast generation

#### Perlin Flux

Uses real Perlin noise if the `noise` package is installed.

Best for:
- less predictable organic surfaces
- natural irregularity
- noise-driven forms

Install support with:

```bash
pip3 install noise
```

## Project structure

```text
wave-foundry/
├── src/
│   └── wave_foundry.py
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

## License

MIT License.
