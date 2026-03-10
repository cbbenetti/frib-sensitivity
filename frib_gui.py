"""
FRIB Minimum Measurable Cross Section - Interactive GUI
"""

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.colors as mcolors
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

# ── Load data once ────────────────────────────────────────────────────────────
FRIB_FILE = "/mnt/c/Users/cbben/Desktop/FRIB_Rates.txt"
MAGIC = [2, 8, 20, 28, 50, 82, 126]
ELEMENTS = {
    1:"H",2:"He",3:"Li",4:"Be",5:"B",6:"C",7:"N",8:"O",9:"F",10:"Ne",
    11:"Na",12:"Mg",13:"Al",14:"Si",15:"P",16:"S",17:"Cl",18:"Ar",19:"K",20:"Ca",
    21:"Sc",22:"Ti",23:"V",24:"Cr",25:"Mn",26:"Fe",27:"Co",28:"Ni",29:"Cu",30:"Zn",
    31:"Ga",32:"Ge",33:"As",34:"Se",35:"Br",36:"Kr",37:"Rb",38:"Sr",39:"Y",40:"Zr",
    41:"Nb",42:"Mo",43:"Tc",44:"Ru",45:"Rh",46:"Pd",47:"Ag",48:"Cd",49:"In",50:"Sn",
    51:"Sb",52:"Te",53:"I",54:"Xe",55:"Cs",56:"Ba",57:"La",58:"Ce",59:"Pr",60:"Nd",
    61:"Pm",62:"Sm",63:"Eu",64:"Gd",65:"Tb",66:"Dy",67:"Ho",68:"Er",69:"Tm",70:"Yb",
    71:"Lu",72:"Hf",73:"Ta",74:"W",75:"Re",76:"Os",77:"Ir",78:"Pt",79:"Au",80:"Hg",
    81:"Tl",82:"Pb",83:"Bi",84:"Po",85:"At",86:"Rn",87:"Fr",88:"Ra",89:"Ac",90:"Th",
    91:"Pa",92:"U",93:"Np",94:"Pu",95:"Am",96:"Cm",97:"Bk",98:"Cf",99:"Es",100:"Fm",
    101:"Md",102:"No",103:"Lr",104:"Rf",105:"Db",106:"Sg",107:"Bh",108:"Hs",109:"Mt",
    110:"Ds",111:"Rg",112:"Cn",113:"Nh",114:"Fl",115:"Mc",116:"Lv",117:"Ts",118:"Og",
}

def load_data():
    rows = []
    with open(FRIB_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                N, Z, rate = int(parts[0]), int(parts[1]), float(parts[2])
            except ValueError:
                continue
            rows.append({"N": N, "Z": Z, "A": N + Z, "rate": rate})
    return pd.DataFrame(rows)

df_all = load_data()
print(f"Loaded {len(df_all)} isotopes")

# ── GUI ───────────────────────────────────────────────────────────────────────
class FRIBApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FRIB Cross Section Sensitivity")
        self.configure(bg="#1a1a2e")
        self.resizable(True, True)

        self._build_controls()
        self._build_canvas()
        self.update_plot()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_hover(self, event):
        if event.inaxes != self.ax or self._annot is None:
            if self._annot:
                self._annot.set_visible(False)
                self.canvas.draw_idle()
            return
        N = int(round(event.xdata))
        Z = int(round(event.ydata))
        sigma = self._hover_lookup.get((N, Z))
        if sigma is not None:
            sym = ELEMENTS.get(Z, f"Z{Z}")
            self._annot.xy = (N, Z)
            self._annot.set_text(f"$^{{{N+Z}}}${sym}  (N={N})\n"
                                 f"σ_min = {sigma:.3e} {self._hover_units}")
            self._annot.set_visible(True)
        else:
            self._annot.set_visible(False)
        self.canvas.draw_idle()

    def _on_close(self):
        plt.close("all")
        self.destroy()

    # ── Control panel ─────────────────────────────────────────────────────────
    def _build_controls(self):
        ctrl = tk.Frame(self, bg="#1a1a2e", padx=10, pady=10)
        ctrl.grid(row=0, column=0, sticky="ns")

        style = {"bg": "#1a1a2e", "fg": "#e0e0e0", "font": ("Consolas", 10)}
        entry_style = {"bg": "#2a2a4e", "fg": "#e0e0e0", "insertbackground": "white",
                       "font": ("Consolas", 10), "width": 12, "relief": "flat",
                       "highlightthickness": 1, "highlightcolor": "#7070ff",
                       "highlightbackground": "#4040aa"}

        def label(parent, text, row, col=0, colspan=1):
            tk.Label(parent, text=text, **style).grid(
                row=row, column=col, columnspan=colspan,
                sticky="w", pady=2, padx=4)

        def entry(parent, default, row, col=1):
            v = tk.StringVar(value=default)
            e = tk.Entry(parent, textvariable=v, **entry_style)
            e.grid(row=row, column=col, sticky="ew", pady=2, padx=4)
            return v

        # ── Section: Target ───────────────────────────────────────────────────
        tk.Label(ctrl, text="-- Target ------------------", **style).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(8, 2))

        label(ctrl, "Thickness [atoms/cm²]", 1)
        self.v_target = entry(ctrl, "1e20", 1)

        label(ctrl, "Beam time [s]", 2)
        self.v_time = entry(ctrl, "604800", 2)

        # Beam time presets
        preset_frame = tk.Frame(ctrl, bg="#1a1a2e")
        preset_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        btn_style = {"bg": "#3a3a6e", "fg": "#e0e0e0", "relief": "flat",
                     "font": ("Consolas", 9), "cursor": "hand2",
                     "activebackground": "#5050aa", "activeforeground": "white"}
        for label_text, secs in [("1 hr", 3600), ("1 day", 86400),
                                   ("1 wk", 604800), ("1 mo", 2592000)]:
            tk.Button(preset_frame, text=label_text,
                      command=lambda s=secs: (self.v_time.set(str(s)), self.update_plot()),
                      **btn_style).pack(side="left", padx=2, expand=True, fill="x")

        # ── Section: Rate limits ──────────────────────────────────────────────
        tk.Label(ctrl, text="-- Rate Limits [pps] -------", **style).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 2))

        label(ctrl, "Min rate (lower cutoff)", 5)
        self.v_min_rate = entry(ctrl, "1e4", 5)

        label(ctrl, "Max rate (color clamp)", 6)
        self.v_max_rate = entry(ctrl, "1e8", 6)

        # ── Section: Sensitivity ──────────────────────────────────────────────
        tk.Label(ctrl, text="-- Sensitivity -------------", **style).grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(8, 2))

        label(ctrl, "Min counts (N_min)", 8)
        self.v_nmin = entry(ctrl, "1e5", 8)

        label(ctrl, "Units", 9)
        self.v_units = tk.StringVar(value="mb")
        unit_frame = tk.Frame(ctrl, bg="#1a1a2e")
        unit_frame.grid(row=9, column=1, sticky="ew", pady=2, padx=4)
        for u in ["nb", "µb", "mb", "b"]:
            tk.Radiobutton(unit_frame, text=u, variable=self.v_units, value=u,
                           bg="#1a1a2e", fg="#e0e0e0", selectcolor="#3a3a6e",
                           activebackground="#1a1a2e", activeforeground="white",
                           font=("Consolas", 9),
                           command=self.update_plot).pack(side="left")

        # ── Section: Display ──────────────────────────────────────────────────
        tk.Label(ctrl, text="-- Display -----------------", **style).grid(
            row=10, column=0, columnspan=2, sticky="w", pady=(8, 2))

        self.v_show_magic = tk.BooleanVar(value=True)
        self.v_show_nz    = tk.BooleanVar(value=True)
        tk.Checkbutton(ctrl, text="Magic number lines", variable=self.v_show_magic,
                       command=self.update_plot,
                       bg="#1a1a2e", fg="#e0e0e0", selectcolor="#3a3a6e",
                       activebackground="#1a1a2e", font=("Consolas", 10)).grid(
            row=11, column=0, columnspan=2, sticky="w", padx=4)
        tk.Checkbutton(ctrl, text="N = Z line", variable=self.v_show_nz,
                       command=self.update_plot,
                       bg="#1a1a2e", fg="#e0e0e0", selectcolor="#3a3a6e",
                       activebackground="#1a1a2e", font=("Consolas", 10)).grid(
            row=12, column=0, columnspan=2, sticky="w", padx=4)

        # ── Update button ─────────────────────────────────────────────────────
        tk.Button(ctrl, text="  Update Plot  ", command=self.update_plot,
                  bg="#5050cc", fg="white", relief="flat",
                  font=("Consolas", 11, "bold"), cursor="hand2",
                  activebackground="#7070ee", activeforeground="white",
                  pady=6).grid(row=13, column=0, columnspan=2,
                               sticky="ew", pady=(14, 4), padx=4)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(ctrl, textvariable=self.status_var, bg="#1a1a2e", fg="#888888",
                 font=("Consolas", 9), wraplength=220, justify="left").grid(
            row=14, column=0, columnspan=2, sticky="w", padx=4, pady=(6, 0))

        # Bind Enter key on entries to update
        for v in [self.v_target, self.v_time, self.v_min_rate,
                  self.v_max_rate, self.v_nmin]:
            self.bind("<Return>", lambda e: self.update_plot())

    # ── Matplotlib canvas ──────────────────────────────────────────────────────
    def _build_canvas(self):
        plot_frame = tk.Frame(self, bg="#0f0f1a")
        plot_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0))
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(13, 8))
        self.fig.patch.set_facecolor("#0f0f1a")
        self.ax.set_facecolor("#1a1a2e")
        self.cbar = None

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar_frame = tk.Frame(plot_frame, bg="#1a1a2e")
        toolbar_frame.pack(fill="x")
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.config(bg="#1a1a2e")
        toolbar.update()

        self._annot = None
        self._hover_lookup = {}
        self._hover_units = "mb"
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)

    # ── Parsing helper ────────────────────────────────────────────────────────
    def _get(self, var, name):
        try:
            return float(var.get())
        except ValueError:
            raise ValueError(f"Invalid value for {name}: '{var.get()}'")

    # ── Plot logic ─────────────────────────────────────────────────────────────
    def update_plot(self):
        try:
            target   = self._get(self.v_target,   "target thickness")
            beam_t   = self._get(self.v_time,      "beam time")
            min_rate = self._get(self.v_min_rate,  "min rate")
            max_rate = self._get(self.v_max_rate,  "max rate")
            n_min    = self._get(self.v_nmin,      "N_min")
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return

        units = self.v_units.get()
        unit_factors = {"nb": 1e-33, "µb": 1e-30, "mb": 1e-27, "b": 1e-24}
        unit_to_cm2 = unit_factors[units]

        # Filter and clamp
        df = df_all[df_all["rate"] >= min_rate].copy()
        df["rate_clamped"] = df["rate"].clip(upper=max_rate)
        df["sigma_min"] = (n_min / (df["rate_clamped"] * target * beam_t)) / unit_to_cm2
        df["log10_sigma"] = np.log10(df["sigma_min"])

        n_total  = len(df)
        n_clamped = (df["rate"] > max_rate).sum()

        self.status_var.set(
            f"{n_total} isotopes plotted\n"
            f"{n_clamped} clamped at {max_rate:.0e} pps\n"
            f"σ_min: {df['sigma_min'].min():.2e} – {df['sigma_min'].max():.2e} {units}"
        )

        # ── Redraw ─────────────────────────────────────────────────────────────
        if self.cbar:
            self.cbar.remove()
            self.cbar = None
        self.ax.cla()

        vmin = np.log10(n_min / (max_rate * target * beam_t) / unit_to_cm2)
        vmax = np.log10(n_min / (min_rate * target * beam_t) / unit_to_cm2)

        N_vals = df["N"].values
        Z_vals = df["Z"].values
        N0, N1 = N_vals.min(), N_vals.max()
        Z0, Z1 = Z_vals.min(), Z_vals.max()
        grid = np.full((Z1 - Z0 + 1, N1 - N0 + 1), np.nan)
        grid[Z_vals - Z0, N_vals - N0] = df["log10_sigma"].values
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        sc = self.ax.pcolormesh(
            np.arange(N0, N1 + 2) - 0.5,
            np.arange(Z0, Z1 + 2) - 0.5,
            grid,
            cmap=plt.cm.plasma_r, norm=norm,
            edgecolors="#0f0f1a", linewidth=0.4,
            zorder=2,
        )

        self._hover_units = units
        self._hover_lookup = {
            (int(row.N), int(row.Z)): row.sigma_min
            for row in df[["N", "Z", "sigma_min"]].itertuples(index=False)
        }

        self._annot = self.ax.annotate(
            "", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.4", fc="#2a2a4e", ec="#7070ff", alpha=0.92),
            color="white", fontsize=9, fontfamily="Consolas",
            arrowprops=dict(arrowstyle="->", color="#aaaaff"),
            zorder=10,
        )
        self._annot.set_visible(False)

        if self.v_show_magic.get():
            for m in MAGIC:
                self.ax.axvline(m, color="white", lw=0.5, alpha=0.25, zorder=1)
                self.ax.axhline(m, color="white", lw=0.5, alpha=0.25, zorder=1)

        if self.v_show_nz.get():
            z = np.arange(0, 100)
            self.ax.plot(z, z, "w--", lw=0.8, alpha=0.4, label="N = Z", zorder=1)
            self.ax.legend(loc="upper left", fontsize=9,
                           framealpha=0.3, labelcolor="white")

        # Colorbar
        self.cbar = self.fig.colorbar(sc, ax=self.ax, pad=0.01, fraction=0.025)
        tick_vals = np.arange(np.ceil(vmin), np.floor(vmax) + 1)
        self.cbar.set_ticks(tick_vals)
        self.cbar.set_ticklabels([f"$10^{{{int(v)}}}$ {units}" for v in tick_vals],
                                  fontsize=9)
        self.cbar.set_label(rf"$\log_{{10}}(\sigma_{{\min}}\ [{units}])$",
                             fontsize=12, color="white")
        self.cbar.ax.yaxis.set_tick_params(color="white")
        plt.setp(self.cbar.ax.yaxis.get_ticklabels(), color="white")

        # Magic number labels
        xl, yl = self.ax.get_xlim(), self.ax.get_ylim()
        for m in MAGIC:
            if xl[0] < m < xl[1]:
                self.ax.text(m, yl[0] + 0.5, str(m), color="white",
                             fontsize=7, ha="center", va="bottom", alpha=0.55)
            if yl[0] < m < yl[1]:
                self.ax.text(xl[0] + 0.5, m, str(m), color="white",
                             fontsize=7, ha="left", va="center", alpha=0.55)

        self.ax.set_facecolor("#1a1a2e")
        self.ax.set_xlabel("Neutron Number  N", fontsize=12, color="white")
        self.ax.set_ylabel("Proton Number  Z", fontsize=12, color="white")
        self.ax.set_ylim(top=94.5)
        self.ax.tick_params(colors="white")

        beam_label = f"{beam_t:.2g} s"
        self.ax.set_title(
            f"FRIB Minimum Measurable Cross Section\n"
            rf"Rate $\geq 10^{{{np.log10(min_rate):.1g}}}$ pps, "
            rf"clamped at $10^{{{np.log10(max_rate):.1g}}}$ pps  |  "
            rf"Target = {target:.1e} atoms/cm²  |  "
            rf"$N_{{\min}}$ = {n_min:.0e}  |  t = {beam_label}",
            fontsize=11, color="white", pad=8,
        )

        self.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    app = FRIBApp()
    app.mainloop()
