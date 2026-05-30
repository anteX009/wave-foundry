#!/usr/bin/env python3
"""
Terminal Formas Organicas - version estable con Ribs como filtro.

Ejecutar:
    python3 terminal_formas_organicas_ribs_stable.py

Opcional para Perlin Flux:
    pip3 install noise
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from math import sin, cos, pi, atan2
from datetime import datetime
import random

try:
    from noise import pnoise3
    HAS_NOISE = True
except Exception:
    HAS_NOISE = False


UI_GREEN = "#e8e8e8"
UI_GREEN_LIGHT = "#ffffff"
UI_GREEN_DARK = "#5f5f5f"
BG = "black"

FONT = ("Courier New", 11)
FONT_SMALL = ("Courier New", 10)
FONT_TITLE = ("Courier New", 14)


def safe_name(value):
    return str(value).replace(".", "p").replace("-", "m")


def nombre_sugerido(params):
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return (
        f"{params['forma']}"
        f"_{params['filtro'].replace(' ', '_')}"
        f"_ancho{safe_name(params['ancho_base'])}"
        f"_largo{safe_name(params['largo_base'])}"
        f"_h{safe_name(params['altura'])}"
        f"_seed{safe_name(params['semilla'])}"
        f"_{stamp}.obj"
    )


def crear_capas(ondas, detalle, semilla):
    random.seed(int(semilla))
    capas = []
    for _ in range(max(1, int(ondas))):
        capas.append({
            "freq_theta": random.randint(2, 10),
            "freq_z": random.uniform(2.0, 13.0) * detalle,
            "fase": random.uniform(0, 2 * pi),
            "amp": random.uniform(0.25, 1.0),
            "tipo": random.choice(["sin", "cos"]),
        })
    return capas


def harmonic_flow(theta, nz, params, capas):
    deform = 0.0
    for capa in capas:
        valor = theta * capa["freq_theta"] + nz * capa["freq_z"] + params["torsion"] * nz * 2.5 + capa["fase"]
        deform += (sin(valor) if capa["tipo"] == "sin" else cos(valor)) * capa["amp"]

    deform = deform / len(capas) * params["intensidad"]
    flujo = sin(theta * 2 + nz * 9 + params["torsion"]) * params["intensidad"] * 0.35
    micro = sin(theta * 17 + nz * 21) * params["intensidad"] * 0.08
    borde = sin(theta * 5 + params["semilla"]) * params["borde"]
    return deform + flujo + micro + borde


def perlin_flux(theta, nz, params):
    if not HAS_NOISE:
        return sin(theta * 5 + nz * 9 + params["semilla"]) * params["intensidad"] * 0.5

    scale = params["noise_scale"]
    x = cos(theta) * scale
    y = sin(theta) * scale
    z = nz * scale

    n = pnoise3(
        x, y, z,
        octaves=max(1, int(params["octaves"])),
        persistence=params["persistence"],
        lacunarity=params["lacunarity"],
        repeatx=1024,
        repeaty=1024,
        repeatz=1024,
        base=int(params["semilla"]),
    )

    flow = sin(theta * params["flow"] + nz * 8.0 + params["torsion"]) * 0.25
    borde = sin(theta * 5 + params["semilla"]) * params["borde"] * 0.5
    return (n + flow) * params["intensidad"] + borde


def kymothea_flow(theta, nz, params, capas):
    intensity = params["intensidad"]
    main = (
        sin(theta * 3.0 + nz * 1.4 + params["torsion"] * 0.7 + params["semilla"] * 0.011) * 0.95
        + sin(theta * 5.0 - nz * 2.2 + 1.4) * 0.55
        + cos(theta * 2.0 + nz * 3.1 - 0.8) * 0.42
    )

    lens = 0.0
    centers = [
        (0.18, 0.34, 3.2, 1.00),
        (0.43, 0.58, 4.1, -0.75),
        (0.68, 0.44, 2.7, 0.85),
        (0.82, 0.70, 3.8, -0.65),
    ]

    for angle_c, z_c, spread_t, amp in centers:
        dtheta = abs((theta / (2 * pi) - angle_c + 0.5) % 1.0 - 0.5)
        dz = abs(nz - z_c)
        oval = max(0.0, 1.0 - dtheta * spread_t * 2.0 - dz * 3.0)
        oval = oval * oval * (3.0 - 2.0 * oval)
        lens += oval * amp

    drift = sin(nz * pi * 1.7 + theta * 1.1) * 0.28
    ribbon = sin(theta * 7.0 + sin(nz * pi * 2.0) * 2.3) * 0.16
    vertical_mask = min(1.0, max(0.0, sin(pi * nz) * 1.25))

    return (main + lens + drift + ribbon) * intensity * 0.78 * vertical_mask + params["borde"] * 0.18 * sin(theta * 4.0)


def rib_wave(t, count, softness):
    """
    Acanalado suave. Devuelve -1..1.
    t representa la posición local dentro de una cara.
    """
    wave = 0.5 + 0.5 * cos(2.0 * pi * count * t)
    exponent = max(0.55, 2.3 - softness * 1.7)
    return (wave ** exponent) * 2.0 - 1.0


def ribs_offset_for_base(base_x, base_y, params):
    if strength <= 0:
        return 0.0, 0.0

    half_w = max(0.001, params["ancho_base"] / 2.0)
    half_d = max(0.001, params["largo_base"] / 2.0)

    if params["forma"] == "square":
        # Detecta cara y aplica estría en la normal de esa cara.
        if abs(abs(base_x) - half_w) <= abs(abs(base_y) - half_d):
            t = (base_y / (2.0 * half_d)) + 0.5
            normal_x = 1.0 if base_x >= 0 else -1.0
            return normal_x * rib_wave(t, count, softness) * strength, 0.0

        t = (base_x / (2.0 * half_w)) + 0.5
        normal_y = 1.0 if base_y >= 0 else -1.0
        return 0.0, normal_y * rib_wave(t, count, softness) * strength

    # Cilindro/elipse.
    theta = atan2(base_y / half_d, base_x / half_w)
    t = (theta / (2.0 * pi)) % 1.0
    rib = rib_wave(t, count, softness)

    nx = base_x / (half_w * half_w)
    ny = base_y / (half_d * half_d)
    length = (nx * nx + ny * ny) ** 0.5 or 1.0
    return (nx / length) * rib * strength, (ny / length) * rib * strength



def vertical_groove_wave(t, count, width, roundness):
    """
    Muescas verticales suaves.
    t es coordenada local 0..1 dentro de cada cara o alrededor del cilindro.
    Devuelve -1..0: siempre entra hacia dentro, no crea picos hacia fuera.
    """
    phase = (t * count) % 1.0
    d = abs(phase - 0.5) * 2.0

    # width controla cuánto ocupa la muesca dentro de cada repetición.
    groove = max(0.0, 1.0 - d / max(0.001, width))
    groove = groove ** max(0.1, roundness)

    # Perfil con fondo redondeado, parecido a acanalado de vidrio/plástico.
    return -groove


def vertical_grooves_offset(base_x, base_y, params):
    """
    Filtro Vertical Grooves.

    En cuadrado:
    - las muescas se calculan por cara
    - cada cara tiene líneas verticales rectas
    - el desplazamiento va hacia dentro de la normal de la cara

    En cilindro:
    - las muescas siguen la circunferencia
    """
    if depth <= 0:
        return 0.0, 0.0


    half_w = max(0.001, params["ancho_base"] / 2.0)
    half_d = max(0.001, params["largo_base"] / 2.0)

    if params["forma"] == "square":
        # Cara derecha/izquierda: repetición a lo largo de Y.
        if abs(abs(base_x) - half_w) <= abs(abs(base_y) - half_d):
            t = (base_y / (2.0 * half_d)) + 0.5
            normal_x = 1.0 if base_x >= 0 else -1.0
            groove = vertical_groove_wave(t, count, width, roundness)
            return normal_x * groove * depth, 0.0

        # Cara frontal/trasera: repetición a lo largo de X.
        t = (base_x / (2.0 * half_w)) + 0.5
        normal_y = 1.0 if base_y >= 0 else -1.0
        groove = vertical_groove_wave(t, count, width, roundness)
        return 0.0, normal_y * groove * depth

    # Cilindro/elipse: muescas alrededor de la sección.
    theta_local = atan2(base_y / half_d, base_x / half_w)
    t = (theta_local / (2.0 * pi)) % 1.0
    groove = vertical_groove_wave(t, count, width, roundness)

    nx = base_x / (half_w * half_w)
    ny = base_y / (half_d * half_d)
    length = (nx * nx + ny * ny) ** 0.5 or 1.0

    return (nx / length) * groove * depth, (ny / length) * groove * depth



def generar_vertices(params, preview=False):
    half_w = params["ancho_base"] / 2.0
    half_d = params["largo_base"] / 2.0

    if preview:
        sr = max(96, min(int(params["segmentos_radiales"]), 220))
        sh = max(40, min(int(params["segmentos_altura"]), 160))
    else:
        sr = max(24, int(params["segmentos_radiales"]))
        sh = max(24, int(params["segmentos_altura"]))

    capas = crear_capas(params["ondas"], params["detalle"], params["semilla"])
    vertices = []

    for i in range(sh + 1):
        z = params["altura"] * (i / sh)
        nz = z / params["altura"]

        for j in range(sr):
            theta = 2 * pi * (j / sr)

            if params["forma"] == "cylinder":
                base_x = half_w * cos(theta)
                base_y = half_d * sin(theta)

            elif params["forma"] == "square" and params["filtro"] in ["Ribs", "Vertical Grooves"]:
                # Recorrido uniforme por cada cara. Esto es clave para que las rayas
                # se apliquen a las caras como en la lámpara de referencia.
                face_steps = sr // 4
                face = j // face_steps
                k = j % face_steps
                u = k / face_steps

                if face == 0:
                    base_x = half_w
                    base_y = -half_d + 2.0 * half_d * u
                elif face == 1:
                    base_x = half_w - 2.0 * half_w * u
                    base_y = half_d
                elif face == 2:
                    base_x = -half_w
                    base_y = half_d - 2.0 * half_d * u
                else:
                    base_x = -half_w + 2.0 * half_w * u
                    base_y = -half_d

            else:
                c = cos(theta)
                s = sin(theta)
                t = 1.0 / max(abs(c), abs(s))
                base_x = half_w * c * t
                base_y = half_d * s * t

            if params["filtro"] == "Kymothea Flow":
                deform = kymothea_flow(theta, nz, params, capas)
            elif params["filtro"] == "Harmonic Flow":
                deform = harmonic_flow(theta, nz, params, capas)
            elif params["filtro"] == "Perlin Flux":
                deform = perlin_flux(theta, nz, params)
            else:
                deform = 0.0

            x = base_x + deform * cos(theta)
            y = base_y + deform * sin(theta)

            vertices.append((x, y, z))

    faces = []
    for i in range(sh):
        for j in range(sr):
            a = i * sr + j
            b = i * sr + ((j + 1) % sr)
            c = (i + 1) * sr + ((j + 1) % sr)
            d = (i + 1) * sr + j
            faces.append((a, b, c, d))

    return vertices, faces, sr, sh


def exportar_obj(params, path):
    vertices, faces, _, _ = generar_vertices(params, preview=False)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# OBJ formas organicas procedurales\n")
        f.write("# Units: millimeters\n")
        f.write(f"# Shape: {params['forma']}\n")
        f.write(f"# Filter: {params['filtro']}\n")
        f.write("s 1\n")

        # Export vertical para slicers que interpretan Y como eje vertical:
        # interno: X,Y,Z -> export: X,Z,-Y
        for x, y, z in vertices:
            f.write(f"v {x:.6f} {z:.6f} {-y:.6f}\n")

        for a, b, c, d in faces:
            f.write(f"f {a+1} {b+1} {c+1} {d+1}\n")

    return len(vertices), len(faces)


class TerminalButton(tk.Canvas):
    def __init__(self, master, text, command, width=170, height=30):
        super().__init__(master, width=width, height=height, bg=BG, highlightthickness=0)
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.hover = False
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", self.enter)
        self.bind("<Leave>", self.leave)
        self.draw()

    def enter(self, event=None):
        self.hover = True
        self.draw()

    def leave(self, event=None):
        self.hover = False
        self.draw()

    def draw(self):
        self.delete("all")
        color = UI_GREEN_LIGHT if self.hover else UI_GREEN
        self.create_rectangle(1, 1, self.width - 2, self.height - 2, outline=color, width=1)
        self.create_text(self.width / 2, self.height / 2, text=self.text, fill=color, font=FONT)


class EllipsisMenuButton(tk.Canvas):
    def __init__(self, master, app, width=36, height=30):
        super().__init__(master, width=width, height=height, bg=BG, highlightthickness=0)
        self.app = app
        self.width = width
        self.height = height
        self.hover = False
        self.menu = tk.Menu(self, tearoff=0, bg=BG, fg=UI_GREEN, activebackground=UI_GREEN_DARK, activeforeground=UI_GREEN_LIGHT)
        self.menu.add_command(label="reset default values", command=self.app.reset_defaults)
        self.bind("<Button-1>", self.open_menu)
        self.bind("<Enter>", self.enter)
        self.bind("<Leave>", self.leave)
        self.draw()

    def enter(self, event=None):
        self.hover = True
        self.draw()

    def leave(self, event=None):
        self.hover = False
        self.draw()

    def open_menu(self, event):
        self.menu.tk_popup(self.winfo_rootx(), self.winfo_rooty() + self.height)

    def draw(self):
        self.delete("all")
        color = UI_GREEN_LIGHT if self.hover else UI_GREEN
        self.create_rectangle(1, 1, self.width - 2, self.height - 2, outline=color, width=1)
        self.create_text(self.width / 2, self.height / 2 - 1, text="...", fill=color, font=FONT)


class TabButton(tk.Canvas):
    def __init__(self, master, app, value, width=160, height=36):
        super().__init__(master, width=width, height=height, bg=BG, highlightthickness=0)
        self.app = app
        self.value = value
        self.width = width
        self.height = height
        self.hover = False
        self.bind("<Button-1>", self.select)
        self.bind("<Enter>", self.enter)
        self.bind("<Leave>", self.leave)
        self.draw()

    def select(self, event=None):
        self.app.forma.set(self.value)
        self.app.draw_shape_tabs()
        self.app.safe_refresh()

    def enter(self, event=None):
        self.hover = True
        self.draw()

    def leave(self, event=None):
        self.hover = False
        self.draw()

    def draw_icon(self, cx, cy, color):
        if self.value == "cylinder":
            self.create_oval(cx - 6, cy - 5, cx + 6, cy + 1, outline=color, width=1)
            self.create_line(cx - 6, cy - 2, cx - 6, cy + 7, fill=color)
            self.create_line(cx + 6, cy - 2, cx + 6, cy + 7, fill=color)
            self.create_oval(cx - 6, cy + 4, cx + 6, cy + 10, outline=color, width=1)
        else:
            self.create_rectangle(cx - 6, cy - 5, cx + 6, cy + 7, outline=color, width=1)

    def draw(self):
        self.delete("all")
        selected = self.app.forma.get() == self.value
        color = UI_GREEN_LIGHT if self.hover else UI_GREEN
        dim = UI_GREEN if selected else UI_GREEN_DARK
        self.create_line(0, self.height - 2, self.width, self.height - 2, fill=dim, width=2 if selected else 1)
        self.draw_icon(28, 16, color if selected else dim)
        self.create_text(self.width / 2 + 6, self.height / 2, text=self.value, fill=color if selected else dim, font=FONT)


class TerminalSlider(tk.Canvas):
    def __init__(self, master, variable, min_v, max_v, step, callback, width=220, height=24):
        super().__init__(master, width=width, height=height, bg=BG, highlightthickness=0)
        self.variable = variable
        self.min_v = min_v
        self.max_v = max_v
        self.step = step
        self.callback = callback
        self.width = width
        self.height = height
        self.bind("<Button-1>", self.set_value)
        self.bind("<B1-Motion>", self.set_value)
        self.variable.trace_add("write", lambda *args: self.draw())
        self.draw()

    def set_value(self, event):
        left = 12
        right = self.width - 12
        x = max(left, min(right, event.x))
        t = (x - left) / (right - left)
        value = self.min_v + t * (self.max_v - self.min_v)
        if self.step:
            value = round(value / self.step) * self.step
        if isinstance(self.variable, tk.IntVar):
            value = int(round(value))
        self.variable.set(value)
        self.callback()

    def draw(self):
        self.delete("all")
        left = 12
        right = self.width - 12
        y = self.height / 2
        try:
            value = float(self.variable.get())
        except Exception:
            value = self.min_v
        value = max(self.min_v, min(self.max_v, value))
        t = (value - self.min_v) / (self.max_v - self.min_v)
        knob_x = left + t * (right - left)
        self.create_line(left, y, right, y, fill=UI_GREEN_DARK, width=2)
        self.create_line(left, y, knob_x, y, fill=UI_GREEN, width=2)
        self.create_rectangle(knob_x - 5, y - 8, knob_x + 5, y + 8, outline=UI_GREEN, fill=BG)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Wave Foundry")
        root.configure(bg=BG)
        root.geometry("1320x820")

        self.angle_x = -0.55
        self.angle_z = 0.75
        self.drag_last = None

        self.params = {
            "ancho_base": tk.DoubleVar(value=100),
            "largo_base": tk.DoubleVar(value=100),
            "altura": tk.DoubleVar(value=120),
            "ondas": tk.IntVar(value=8),
            "intensidad": tk.DoubleVar(value=6),
            "detalle": tk.DoubleVar(value=2),
            "torsion": tk.DoubleVar(value=1),
            "borde": tk.DoubleVar(value=0.0),
            "segmentos_radiales": tk.IntVar(value=160),
            "segmentos_altura": tk.IntVar(value=90),
            "semilla": tk.IntVar(value=12),
            "noise_scale": tk.DoubleVar(value=2.5),
            "octaves": tk.IntVar(value=4),
            "persistence": tk.DoubleVar(value=0.5),
            "lacunarity": tk.DoubleVar(value=2.0),
            "flow": tk.DoubleVar(value=4.0),
        }

        self.default_values = {k: v.get() for k, v in self.params.items()}
        self.forma = tk.StringVar(value="cylinder")
        self.filtro = tk.StringVar(value="Kymothea Flow")
        self.default_forma = "cylinder"
        self.default_filtro = "Kymothea Flow"

        self.ranges = {
            "ancho_base": (20, 250, 1),
            "largo_base": (20, 250, 1),
            "altura": (20, 250, 1),
            "ondas": (1, 24, 1),
            "intensidad": (0, 20, 0.1),
            "detalle": (0.2, 6, 0.1),
            "torsion": (-5, 5, 0.1),
            "borde": (0, 15, 0.1),
            "segmentos_radiales": (24, 360, 1),
            "segmentos_altura": (24, 260, 1),
            "semilla": (1, 999, 1),
            "noise_scale": (0.2, 10, 0.1),
            "octaves": (1, 8, 1),
            "persistence": (0.1, 1.0, 0.05),
            "lacunarity": (1.0, 5.0, 0.1),
            "flow": (0, 16, 0.1),
        }

        self.control_rows = {}
        self.build_ui()

        for var in self.params.values():
            var.trace_add("write", lambda *args: self.safe_refresh())

        self.root.after(100, self.refresh)

    def build_ui(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True)

        left_wrap = tk.Frame(outer, bg=BG, width=560)
        left_wrap.pack(side="left", fill="y")
        left_wrap.pack_propagate(False)

        right = tk.Frame(outer, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=16, pady=16)

        tk.Label(left_wrap, text="> wave foundry", fg=UI_GREEN, bg=BG, font=FONT_TITLE).pack(anchor="w", padx=10, pady=(14, 14))

        self.controls_canvas = tk.Canvas(left_wrap, bg=BG, highlightthickness=0, width=560)
        self.controls_canvas.pack(side="left", fill="both", expand=True)

        self.controls_frame = tk.Frame(self.controls_canvas, bg=BG)
        self.controls_window = self.controls_canvas.create_window((0, 0), window=self.controls_frame, anchor="nw")
        self.controls_frame.bind("<Configure>", lambda e: self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox("all")))
        self.controls_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        tabs = tk.Frame(self.controls_frame, bg=BG)
        tabs.pack(fill="x", padx=8, pady=(0, 14))

        self.shape_tabs = [
            TabButton(tabs, self, "cylinder", width=265),
            TabButton(tabs, self, "square", width=265),
        ]
        self.shape_tabs[0].pack(side="left", padx=(0, 6))
        self.shape_tabs[1].pack(side="left")

        filtro_frame = tk.Frame(self.controls_frame, bg=BG)
        filtro_frame.pack(fill="x", padx=8, pady=(0, 12))

        tk.Label(filtro_frame, text="filter", fg=UI_GREEN, bg=BG, font=FONT, width=14, anchor="w").pack(side="left")
        self.filter_menu = tk.OptionMenu(
            filtro_frame,
            self.filtro,
            "Kymothea Flow",
            "Harmonic Flow",
            "Perlin Flux",
            command=lambda e: self.on_filter_change(),
        )
        self.filter_menu.config(bg=BG, fg=UI_GREEN, activebackground=BG, activeforeground=UI_GREEN_LIGHT, highlightthickness=1, highlightbackground=UI_GREEN, relief="flat", font=FONT, width=28)
        self.filter_menu["menu"].config(bg=BG, fg=UI_GREEN, activebackground=UI_GREEN_DARK, activeforeground=UI_GREEN_LIGHT)
        self.filter_menu.pack(side="left", fill="x", expand=True)

        for key in [
            "ancho_base",
            "largo_base",
            "altura",
            "ondas",
            "intensidad",
            "detalle",
            "torsion",
            "borde",
            "segmentos_radiales",
            "segmentos_altura",
            "semilla",
            "noise_scale",
            "octaves",
            "persistence",
            "lacunarity",
            "flow",
        ]:
            self.add_control(self.controls_frame, key)

        right_header = tk.Frame(right, bg=BG)
        right_header.pack(fill="x")

        tk.Label(right_header, text="> 3d preview", fg=UI_GREEN, bg=BG, font=FONT_TITLE).pack(side="left", anchor="w")
        EllipsisMenuButton(right_header, self, width=36, height=30).pack(side="right", anchor="e", padx=(8, 0))
        TerminalButton(right_header, "exportar obj", self.exportar, width=170, height=30).pack(side="right", anchor="e")

        self.canvas = tk.Canvas(right, width=760, height=710, bg=BG, highlightthickness=1, highlightbackground=UI_GREEN)
        self.canvas.pack(fill="both", expand=True, pady=(8, 0))

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)

        self.on_filter_change()

    def on_mousewheel(self, event):
        self.controls_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def reset_defaults(self):
        for key, value in self.default_values.items():
            self.params[key].set(value)
        self.forma.set(self.default_forma)
        self.filtro.set(self.default_filtro)
        self.on_filter_change()
        self.refresh()

    def draw_shape_tabs(self):
        for tab in self.shape_tabs:
            tab.draw()

    def on_filter_change(self):
        f = self.filtro.get()
        perlin_keys = ["noise_scale", "octaves", "persistence", "lacunarity", "flow"]

        for key in perlin_keys:
            row = self.control_rows.get(key)
            if row:
                (row.pack if f == "Perlin Flux" else row.pack_forget)(fill="x", padx=8, pady=4) if f == "Perlin Flux" else row.pack_forget()
        self.safe_refresh()

    def add_control(self, parent, key):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", padx=8, pady=4)
        self.control_rows[key] = row

        display_names = {
            "ancho_base": "base_width",
            "largo_base": "base_depth",
            "altura": "height",
            "ondas": "waves",
            "intensidad": "intensity",
            "detalle": "detail",
            "torsion": "twist",
            "borde": "rim",
            "segmentos_radiales": "radial_segments",
            "segmentos_altura": "height_segments",
            "semilla": "seed",
            "noise_scale": "noise_scale",
            "octaves": "octaves",
            "persistence": "persistence",
            "lacunarity": "lacunarity",
            "flow": "flow",
        }

        tk.Label(row, text=display_names.get(key, key), fg=UI_GREEN, bg=BG, font=FONT, width=26, anchor="w").pack(side="left")
        min_v, max_v, step = self.ranges[key]
        slider = TerminalSlider(row, self.params[key], min_v, max_v, step, self.safe_refresh, width=245)
        slider.pack(side="left", padx=(0, 8))

        entry = tk.Entry(row, textvariable=self.params[key], bg=BG, fg=UI_GREEN, insertbackground=UI_GREEN, font=FONT, relief="flat", width=11, highlightthickness=1, highlightbackground=UI_GREEN, highlightcolor=UI_GREEN_LIGHT)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self.safe_refresh())
        entry.bind("<FocusOut>", lambda e: self.safe_refresh())

    def get_params(self):
        data = {k: v.get() for k, v in self.params.items()}
        data["forma"] = self.forma.get()
        data["filtro"] = self.filtro.get()
        return data

    def start_drag(self, event):
        self.drag_last = (event.x, event.y)

    def drag(self, event):
        if self.drag_last is None:
            return
        lx, ly = self.drag_last
        self.angle_z += (event.x - lx) * 0.01
        self.angle_x += (event.y - ly) * 0.01
        self.drag_last = (event.x, event.y)
        self.refresh()

    def safe_refresh(self):
        try:
            self.draw_shape_tabs()
            self.refresh()
        except Exception:
            pass

    def project(self, point, scale, cx, cy, altura):
        x, y, z = point
        z -= altura / 2
        cz = cos(self.angle_z)
        sz = sin(self.angle_z)
        x, y = x * cz - y * sz, x * sz + y * cz
        cxr = cos(self.angle_x)
        sxr = sin(self.angle_x)
        y, z = y * cxr - z * sxr, y * sxr + z * cxr
        dist = 420
        factor = dist / (dist - z)
        return cx + x * scale * factor, cy - y * scale * factor, z

    def draw_mini_views(self, vertices):
        if not vertices:
            return
        w = int(self.canvas.winfo_width() or 760)
        h = int(self.canvas.winfo_height() or 710)
        box_w, box_h, gap, margin = 78, 78, 8, 14
        total_w = box_w * 3 + gap * 2
        x0 = w - total_w - margin
        y0 = h - box_h - margin

        views = [
            ("front", lambda v: (v[0], v[2])),
            ("side", lambda v: (v[1], v[2])),
            ("top", lambda v: (v[0], v[1])),
        ]

        for idx, (label, mapper) in enumerate(views):
            bx = x0 + idx * (box_w + gap)
            by = y0
            self.canvas.create_rectangle(bx, by, bx + box_w, by + box_h, outline=UI_GREEN_DARK, width=1)
            pts = [mapper(v) for v in vertices]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            span_x = max(max_x - min_x, 0.001)
            span_y = max(max_y - min_y, 0.001)
            scale = min((box_w - 18) / span_x, (box_h - 22) / span_y)
            step = max(1, len(pts) // 220)
            for px, py in pts[::step]:
                sx = bx + box_w / 2 + (px - (min_x + max_x) / 2) * scale
                sy = by + box_h / 2 - (py - (min_y + max_y) / 2) * scale + 4
                self.canvas.create_rectangle(sx, sy, sx + 1, sy + 1, outline=UI_GREEN, fill=UI_GREEN)
            self.canvas.create_text(bx + 5, by + 5, anchor="nw", text=label, fill=UI_GREEN, font=("Courier New", 8))

    def refresh(self):
        self.canvas.delete("all")
        params = self.get_params()
        vertices, faces, sr, sh = generar_vertices(params, preview=True)

        w = int(self.canvas.winfo_width() or 760)
        h = int(self.canvas.winfo_height() or 710)
        cx, cy = w / 2, h / 2
        max_xy = max(params["ancho_base"], params["largo_base"]) + params["intensidad"] * 4
        max_dim = max(max_xy, params["altura"])
        scale = min(w, h) * 0.50 / max_dim

        projected = [self.project(v, scale, cx, cy, params["altura"]) for v in vertices]
        sortable = []
        for face in faces:
            avg_z = sum(projected[idx][2] for idx in face) / 4
            sortable.append((avg_z, face))
        sortable.sort(key=lambda x: x[0])

        for avg_z, face in sortable:
            pts = []
            for idx in face:
                pts.extend([projected[idx][0], projected[idx][1]])
            shade = int(max(45, min(210, 115 + avg_z * 0.8)))
            color = f"#{shade:02x}{shade:02x}{shade:02x}"
            self.canvas.create_polygon(pts, fill=color, outline=UI_GREEN_DARK)

        for i in range(0, sh + 1, 6):
            pts = []
            for j in range(sr + 1):
                idx = i * sr + (j % sr)
                pts.extend([projected[idx][0], projected[idx][1]])
            self.canvas.create_line(pts, fill=UI_GREEN, width=1)

        for j in range(0, sr, max(6, sr // 18)):
            pts = []
            for i in range(sh + 1):
                idx = i * sr + j
                pts.extend([projected[idx][0], projected[idx][1]])
            self.canvas.create_line(pts, fill="#b8b8b8", width=1)

        self.canvas.create_text(
            14, 14, anchor="nw",
            text=f"shape={params['forma']}  filter={params['filtro']}  width={params['ancho_base']}mm  depth={params['largo_base']}mm  height={params['altura']}mm",
            fill=UI_GREEN, font=FONT_SMALL
        )

        if params["filtro"] == "Perlin Flux" and not HAS_NOISE:
            self.canvas.create_text(14, 34, anchor="nw", text="warning: install noise with pip3 install noise to use real Perlin Flux", fill=UI_GREEN_LIGHT, font=FONT_SMALL)

        self.draw_mini_views(vertices)

    def exportar(self):
        params = self.get_params()
        path = filedialog.asksaveasfilename(initialfile=nombre_sugerido(params), defaultextension=".obj", filetypes=[("OBJ", "*.obj")])
        if not path:
            return
        vertices, faces = exportar_obj(params, path)
        messagebox.showinfo("obj exported", f"file saved:\n{path}\n\nvertices: {vertices}\nfaces: {faces}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
