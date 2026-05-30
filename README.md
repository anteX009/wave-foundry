# Wave Foundry

Wave Foundry is a lightweight procedural 3D mesh generator for Blender and 3D printing.


## Preview

![Wave Foundry UI](assets/wave-foundry-ui.png)

## Requirements

- Python 3.10 or newer
- Tkinter
- Optional: `noise` for the Perlin Flux filter

## Install

```bash
pip3 install -r requirements.txt
```

## Run

```bash
python3 src/wave_foundry.py
```

Or:

```bash
./run.sh
```

## Blender import

Export an `.obj` file from Wave Foundry, then in Blender:

```text
File -> Import -> Wavefront (.obj)
```
