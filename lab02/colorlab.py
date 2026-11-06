# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox


class ConvertResult:
    def __init__(self, clipped=False, note=""):
        self.clipped = clipped
        self.note = note


def rgb_to_cmyk(r, g, b, res=None):
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    k = min(1 - r_, 1 - g_, 1 - b_)
    if k >= 1.0 - 1e-12:
        c = m = y = 0.0
    else:
        c = (1 - r_ - k) / (1 - k)
        m = (1 - g_ - k) / (1 - k)
        y = (1 - b_ - k) / (1 - k)
    if res is not None:
        res.clipped = False
        res.note = ""
    return c, m, y, k


def cmyk_to_rgb(c, m, y, k, res=None):
    r = 255.0 * (1 - c) * (1 - k)
    g = 255.0 * (1 - m) * (1 - k)
    b = 255.0 * (1 - y) * (1 - k)
    clipped = False
    for v in (r, g, b):
        if v < 0 or v > 255:
            clipped = True
    r = max(0.0, min(255.0, r))
    g = max(0.0, min(255.0, g))
    b = max(0.0, min(255.0, b))
    if res is not None:
        res.clipped = clipped
        res.note = "CMYK → RGB: обрезание в [0, 255]" if clipped else ""
    return r, g, b


def rgb_to_hsv(r, g, b, res=None):
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    mx = max(r_, g_, b_)
    mn = min(r_, g_, b_)
    d = mx - mn
    v = mx
    s = 0.0 if mx <= 1e-12 else d / mx
    if d <= 1e-12:
        h = 0.0
    elif mx == r_:
        h = 60.0 * (((g_ - b_) / d) % 6.0)
    elif mx == g_:
        h = 60.0 * ((b_ - r_) / d + 2.0)
    else:
        h = 60.0 * ((r_ - g_) / d + 4.0)
    if h < 0:
        h += 360.0
    if res is not None:
        res.clipped = False
        res.note = ""
    return h, s, v


def hsv_to_rgb(h, s, v, res=None):
    h = h % 360.0
    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c
    if h < 60:
        r1, g1, b1 = c, x, 0
    elif h < 120:
        r1, g1, b1 = x, c, 0
    elif h < 180:
        r1, g1, b1 = 0, c, x
    elif h < 240:
        r1, g1, b1 = 0, x, c
    elif h < 300:
        r1, g1, b1 = x, 0, c
    else:
        r1, g1, b1 = c, 0, x
    r = (r1 + m) * 255.0
    g = (g1 + m) * 255.0
    b = (b1 + m) * 255.0
    clipped = False
    for val in (r, g, b):
        if val < 0 or val > 255:
            clipped = True
    r = max(0.0, min(255.0, r))
    g = max(0.0, min(255.0, g))
    b = max(0.0, min(255.0, b))
    if res is not None:
        res.clipped = clipped
        res.note = "HSV → RGB: обрезание" if clipped else ""
    return r, g, b


def _F_forward(x):
    if x >= 0.04045:
        return ((x + 0.055) / 1.055) ** 2.4
    return x / 12.92


def _F_inverse(x):
    if x >= 0.0031308:
        return 1.055 * (x ** (1.0 / 2.4)) - 0.055
    return 12.92 * x


def rgb_to_xyz(r, g, b, res=None):
    rn = _F_forward(r / 255.0) * 100.0
    gn = _F_forward(g / 255.0) * 100.0
    bn = _F_forward(b / 255.0) * 100.0
    x = 0.412453 * rn + 0.357580 * gn + 0.180423 * bn
    y = 0.212671 * rn + 0.715160 * gn + 0.072169 * bn
    z = 0.019334 * rn + 0.119193 * gn + 0.950227 * bn
    if res is not None:
        res.clipped = False
        res.note = ""
    return x, y, z


def xyz_to_rgb(x, y, z, res=None):
    rn = 3.2406 * (x / 100.0) + -1.5372 * (y / 100.0) + -0.4986 * (z / 100.0)
    gn = -0.9689 * (x / 100.0) + 1.8758 * (y / 100.0) + 0.0415 * (z / 100.0)
    bn = 0.0557 * (x / 100.0) + -0.2040 * (y / 100.0) + 1.0570 * (z / 100.0)
    clipped = False
    out = []
    for v in (rn, gn, bn):
        s = _F_inverse(v) * 255.0
        if s < 0 or s > 255:
            clipped = True
        s = max(0.0, min(255.0, s))
        out.append(s)
    if res is not None:
        res.clipped = clipped
        res.note = "XYZ → RGB: цвет вне sRGB-гамута, обрезание" if clipped else ""
    return out[0], out[1], out[2]


_Xw, _Yw, _Zw = 95.047, 100.000, 108.883


def _lab_F_forward(x):
    if x >= 0.008856:
        return x ** (1.0 / 3.0)
    return 7.787 * x + 16.0 / 116.0


def _lab_F_inverse(x):
    x3 = x * x * x
    if x3 >= 0.008856:
        return x3
    return (x - 16.0 / 116.0) / 7.787


def xyz_to_lab(x, y, z, res=None):
    fx = _lab_F_forward(x / _Xw)
    fy = _lab_F_forward(y / _Yw)
    fz = _lab_F_forward(z / _Zw)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    if res is not None:
        res.clipped = False
        res.note = ""
    return L, a, b


def lab_to_xyz(L, a, b, res=None):
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + (L + 16.0) / 116.0
    fz = (L + 16.0) / 116.0 - b / 200.0
    x = _lab_F_inverse(fx) * _Xw
    y = _lab_F_inverse(fy) * _Yw
    z = _lab_F_inverse(fz) * _Zw
    if res is not None:
        res.clipped = False
        res.note = ""
    return x, y, z


def cmyk_to_lab(c, m, y, k, res=None):
    r1, r2, r3 = ConvertResult(), ConvertResult(), ConvertResult()
    r, g, b = cmyk_to_rgb(c, m, y, k, r1)
    x, yy, z = rgb_to_xyz(r, g, b, r2)
    L, a, bb = xyz_to_lab(x, yy, z, r3)
    if res is not None:
        res.clipped = r1.clipped or r2.clipped or r3.clipped
        res.note = r1.note or r3.note
    return L, a, bb


def lab_to_cmyk(L, a, b, res=None):
    r1, r2, r3 = ConvertResult(), ConvertResult(), ConvertResult()
    x, yy, z = lab_to_xyz(L, a, b, r1)
    r, g, bb = xyz_to_rgb(x, yy, z, r2)
    c, m, y_, k = rgb_to_cmyk(r, g, bb, r3)
    if res is not None:
        res.clipped = r2.clipped
        res.note = r2.note
    return c, m, y_, k


def cmyk_to_hsv(c, m, y, k, res=None):
    r1, r2 = ConvertResult(), ConvertResult()
    r, g, b = cmyk_to_rgb(c, m, y, k, r1)
    h, s, v = rgb_to_hsv(r, g, b, r2)
    if res is not None:
        res.clipped = r1.clipped
        res.note = r1.note
    return h, s, v


def hsv_to_cmyk(h, s, v, res=None):
    r1, r2 = ConvertResult(), ConvertResult()
    r, g, b = hsv_to_rgb(h, s, v, r1)
    c, m, y_, k = rgb_to_cmyk(r, g, b, r2)
    if res is not None:
        res.clipped = r1.clipped
        res.note = r1.note
    return c, m, y_, k


def lab_to_hsv(L, a, b, res=None):
    r1, r2, r3 = ConvertResult(), ConvertResult(), ConvertResult()
    x, yy, z = lab_to_xyz(L, a, b, r1)
    r, g, bb = xyz_to_rgb(x, yy, z, r2)
    h, s, v = rgb_to_hsv(r, g, bb, r3)
    if res is not None:
        res.clipped = r2.clipped
        res.note = r2.note
    return h, s, v


def hsv_to_lab(h, s, v, res=None):
    r1, r2, r3 = ConvertResult(), ConvertResult(), ConvertResult()
    r, g, b = hsv_to_rgb(h, s, v, r1)
    x, yy, z = rgb_to_xyz(r, g, b, r2)
    L, a, bb = xyz_to_lab(x, yy, z, r3)
    if res is not None:
        res.clipped = r1.clipped
        res.note = r1.note
    return L, a, bb


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class ColorLab(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ColorLab — CMYK / LAB / HSV")

        self.rgb = (128.0, 128.0, 128.0)
        self.updating = False

        self.cmyk_vars = [tk.DoubleVar(value=0) for _ in range(4)]
        self.lab_vars = [tk.DoubleVar(value=0) for _ in range(3)]
        self.hsv_vars = [tk.DoubleVar(value=0) for _ in range(3)]

        self._build_ui()
        self._apply_from_rgb(*self.rgb, source="init")

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TLabelframe", padding=6)
        style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9), padding=3)
        style.configure("TEntry", font=("Segoe UI", 9))

        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        self.cmyk_frame = self._make_group(
            main, "CMYK  (0..100 %)",
            labels=["C", "M", "Y", "K"],
            ranges=[(0, 100)] * 4,
            on_change=self._on_cmyk_changed,
            vars_=self.cmyk_vars,
            gradient_builder=self._gradient_cmyk,
        )
        self.cmyk_frame.pack(fill="x", pady=(0, 4))

        self.lab_frame = self._make_group(
            main, "LAB  (L 0..100, a,b -128..127)",
            labels=["L", "a", "b"],
            ranges=[(0, 100), (-128, 127), (-128, 127)],
            on_change=self._on_lab_changed,
            vars_=self.lab_vars,
            gradient_builder=self._gradient_lab,
        )
        self.lab_frame.pack(fill="x", pady=4)

        self.hsv_frame = self._make_group(
            main, "HSV  (H 0..360, S,V 0..100 %)",
            labels=["H", "S", "V"],
            ranges=[(0, 360), (0, 100), (0, 100)],
            on_change=self._on_hsv_changed,
            vars_=self.hsv_vars,
            gradient_builder=self._gradient_hsv,
        )
        self.hsv_frame.pack(fill="x", pady=(4, 0))

        bottom = ttk.LabelFrame(main, text="Результат", padding=6)
        bottom.pack(fill="x", pady=(8, 0))

        self.swatch = tk.Label(bottom, width=8, height=3, bg="#808080",
                               relief="flat", bd=0)
        self.swatch.pack(side="left", padx=(0, 8))

        right = ttk.Frame(bottom)
        right.pack(side="left", fill="both", expand=True)

        hex_row = ttk.Frame(right)
        hex_row.pack(fill="x", pady=(0, 4))
        ttk.Label(hex_row, text="HEX:", width=5).pack(side="left")
        self.hex_var = tk.StringVar(value="#808080")
        self.hex_entry = ttk.Entry(hex_row, textvariable=self.hex_var, width=9)
        self.hex_entry.pack(side="left", padx=(0, 10))
        self.hex_entry.bind("<Return>", lambda e: self._on_hex_changed())
        self.hex_entry.bind("<FocusOut>", lambda e: self._on_hex_changed())

        ttk.Label(hex_row, text="RGB:").pack(side="left", padx=(0, 4))
        self.rgb_label = ttk.Label(hex_row, text="128, 128, 128",
                                   foreground="#444")
        self.rgb_label.pack(side="left")

        btn_row = ttk.Frame(right)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Палитра",
                   command=self._pick_color,
                   width=11).pack(side="left", padx=(0, 3))
        ttk.Button(btn_row, text="Сохранить",
                   command=self._save_color,
                   width=11).pack(side="left", padx=3)
        ttk.Button(btn_row, text="Загрузить",
                   command=self._load_color,
                   width=11).pack(side="left", padx=3)

        self.warning = ttk.Label(right, text="", foreground="#b45309",
                                 font=("Segoe UI", 8, "italic"),
                                 wraplength=420, justify="left")
        self.warning.pack(fill="x", pady=(4, 0))

        self.update_idletasks()
        w = self.winfo_reqwidth() + 4
        h = self.winfo_reqheight() + 4
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)

    def _make_group(self, parent, title, labels, ranges,
                    on_change, vars_, gradient_builder):
        box = ttk.LabelFrame(parent, text=title, padding=(6, 3))
        rows = []
        for i, lbl in enumerate(labels):
            row = ttk.Frame(box)
            row.pack(fill="x", pady=1)

            ttk.Label(row, text=lbl, width=2,
                      font=("Segoe UI", 9, "bold")).pack(side="left")

            var = vars_[i]
            lo, hi = ranges[i]

            entry_var = tk.StringVar(value="0")
            entry = ttk.Entry(row, textvariable=entry_var, width=6,
                              justify="right")
            entry.pack(side="right", padx=(4, 0))

            slider = ttk.Scale(row, from_=lo, to=hi,
                               orient="horizontal",
                               variable=var,
                               length=180,
                               command=lambda v, idx=i:
                               on_change(idx, float(v)))
            slider.pack(side="right", padx=4)

            entry.bind("<Return>",
                       lambda e, idx=i, v=entry_var:
                       on_change(idx, self._parse_entry(v.get(), ranges[idx])))
            entry.bind("<FocusOut>",
                       lambda e, idx=i, v=entry_var:
                       on_change(idx, self._parse_entry(v.get(), ranges[idx])))

            grad = tk.Canvas(row, height=6, highlightthickness=0, bd=0)
            grad.pack(side="left", fill="x", expand=True, padx=(4, 4))

            rows.append({
                "slider": slider,
                "entry": entry,
                "entry_var": entry_var,
                "gradient": grad,
                "range": (lo, hi),
            })

        box._rows = rows
        box._gradient_builder = gradient_builder
        return box

    @staticmethod
    def _parse_entry(text, rng):
        try:
            v = float(str(text).replace(",", "."))
        except ValueError:
            v = rng[0]
        return clamp(v, rng[0], rng[1])

    def _on_cmyk_changed(self, idx, value):
        if self.updating:
            return
        self.cmyk_vars[idx].set(value)
        c, m, y, k = (v.get() / 100.0 for v in self.cmyk_vars)
        res = ConvertResult()
        r, g, b = cmyk_to_rgb(c, m, y, k, res)
        self._apply_from_rgb(r, g, b, source="cmyk")
        self._show_warning(res.note if res.clipped else "")

    def _on_lab_changed(self, idx, value):
        if self.updating:
            return
        self.lab_vars[idx].set(value)
        L = self.lab_vars[0].get()
        a = self.lab_vars[1].get()
        b_ = self.lab_vars[2].get()
        r1 = ConvertResult()
        x, y, z = lab_to_xyz(L, a, b_, r1)
        r2 = ConvertResult()
        r, g, b = xyz_to_rgb(x, y, z, r2)
        self._apply_from_rgb(r, g, b, source="lab")
        self._show_warning(r2.note if r2.clipped else "")

    def _on_hsv_changed(self, idx, value):
        if self.updating:
            return
        self.hsv_vars[idx].set(value)
        h = self.hsv_vars[0].get()
        s = self.hsv_vars[1].get() / 100.0
        v = self.hsv_vars[2].get() / 100.0
        res = ConvertResult()
        r, g, b = hsv_to_rgb(h, s, v, res)
        self._apply_from_rgb(r, g, b, source="hsv")
        self._show_warning(res.note if res.clipped else "")

    def _on_hex_changed(self):
        if self.updating:
            return
        s = self.hex_var.get().strip()
        if not s.startswith("#"):
            s = "#" + s
        if len(s) != 7:
            self._show_warning("Некорректный HEX-код")
            return
        try:
            r = int(s[1:3], 16)
            g = int(s[3:5], 16)
            b = int(s[5:7], 16)
        except ValueError:
            self._show_warning("Некорректный HEX-код")
            return
        self._apply_from_rgb(r, g, b, source="hex")
        self._show_warning("")

    def _pick_color(self):
        r, g, b = (int(round(v)) for v in self.rgb)
        color = colorchooser.askcolor(color=(r, g, b), title="Выбор цвета")
        if color is None or color[0] is None:
            return
        rr, gg, bb = color[0]
        self._apply_from_rgb(rr, gg, bb, source="picker")
        self._show_warning("")

    def _save_color(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt")],
            title="Сохранить цвет")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("CMYK: {} {} {} {}\n".format(
                    *(round(v.get()) for v in self.cmyk_vars)))
                f.write("LAB:  {} {} {}\n".format(
                    *(round(v.get()) for v in self.lab_vars)))
                f.write("HSV:  {} {} {}\n".format(
                    *(round(v.get()) for v in self.hsv_vars)))
                f.write("HEX:  {}\n".format(self.hex_var.get()))
        except OSError as e:
            messagebox.showerror("Ошибка", str(e))

    def _load_color(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text", "*.txt")],
            title="Загрузить цвет")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("HEX:"):
                        hexv = line[4:].strip()
                        self.hex_var.set(hexv)
                        self._on_hex_changed()
                        return
            messagebox.showinfo("Загрузка", "HEX-код не найден")
        except OSError as e:
            messagebox.showerror("Ошибка", str(e))

    def _apply_from_rgb(self, r, g, b, source="init"):
        self.updating = True
        try:
            r = clamp(r, 0, 255)
            g = clamp(g, 0, 255)
            b = clamp(b, 0, 255)
            self.rgb = (r, g, b)

            if source != "cmyk":
                c, m, y, k = rgb_to_cmyk(r, g, b)
                self.cmyk_vars[0].set(round(c * 100, 1))
                self.cmyk_vars[1].set(round(m * 100, 1))
                self.cmyk_vars[2].set(round(y * 100, 1))
                self.cmyk_vars[3].set(round(k * 100, 1))
            self._sync_entries(self.cmyk_frame, self.cmyk_vars)

            if source != "lab":
                x, y_, z = rgb_to_xyz(r, g, b)
                L, a, bb = xyz_to_lab(x, y_, z)
                self.lab_vars[0].set(round(L, 2))
                self.lab_vars[1].set(round(a, 2))
                self.lab_vars[2].set(round(bb, 2))
            self._sync_entries(self.lab_frame, self.lab_vars)

            if source != "hsv":
                h, s, v = rgb_to_hsv(r, g, b)
                self.hsv_vars[0].set(round(h, 1))
                self.hsv_vars[1].set(round(s * 100, 1))
                self.hsv_vars[2].set(round(v * 100, 1))
            self._sync_entries(self.hsv_frame, self.hsv_vars)

            hex_str = "#{:02X}{:02X}{:02X}".format(
                int(round(r)), int(round(g)), int(round(b)))
            self.hex_var.set(hex_str)
            self.swatch.configure(bg=hex_str)
            self.rgb_label.configure(
                text=f"{int(round(r))}, {int(round(g))}, {int(round(b))}")

            self._refresh_gradients()
        finally:
            self.updating = False

    def _sync_entries(self, frame, vars_):
        for i, row in enumerate(frame._rows):
            row["entry_var"].set(f"{vars_[i].get():.1f}")

    def _show_warning(self, text):
        self.warning.configure(text=("⚠ " + text) if text else "")

    def _refresh_gradients(self):
        self._update_gradient_rows(self.cmyk_frame)
        self._update_gradient_rows(self.lab_frame)
        self._update_gradient_rows(self.hsv_frame)

    def _update_gradient_rows(self, frame):
        colors = frame._gradient_builder()
        for i, row in enumerate(frame._rows):
            canvas = row["gradient"]
            canvas.update_idletasks()
            w = max(canvas.winfo_width(), 60)
            h = max(canvas.winfo_height(), 6)
            canvas.delete("all")
            n = len(colors)
            if n < 2:
                continue
            seg = w / (n - 1)
            for j in range(n - 1):
                c1 = colors[j]
                c2 = colors[j + 1]
                steps = 8
                for s in range(steps):
                    t = s / steps
                    r = int(c1[0] + (c2[0] - c1[0]) * t)
                    g = int(c1[1] + (c2[1] - c1[1]) * t)
                    b = int(c1[2] + (c2[2] - c1[2]) * t)
                    color = "#{:02x}{:02x}{:02x}".format(
                        clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255))
                    x0 = j * seg + s * seg / steps
                    x1 = x0 + seg / steps + 1
                    canvas.create_rectangle(x0, 0, x1, h,
                                            fill=color, outline="")

    def _gradient_cmyk(self):
        base = [v.get() / 100.0 for v in self.cmyk_vars]
        out = []
        for i in range(11):
            t = i / 10.0
            c, m, y, k = base
            r, g, b = cmyk_to_rgb(c, m, y, t)
            out.append((r, g, b))
        return out

    def _gradient_lab(self):
        a = self.lab_vars[1].get()
        b_ = self.lab_vars[2].get()
        out = []
        for i in range(11):
            t = i / 10.0
            L2 = t * 100
            x, y, z = lab_to_xyz(L2, a, b_)
            r, g, b = xyz_to_rgb(x, y, z)
            out.append((r, g, b))
        return out

    def _gradient_hsv(self):
        h = self.hsv_vars[0].get()
        s = self.hsv_vars[1].get() / 100.0
        v = self.hsv_vars[2].get() / 100.0
        out = []
        for i in range(11):
            t = i / 10.0
            h2 = t * 360
            r, g, b = hsv_to_rgb(h2, s, v)
            out.append((r, g, b))
        return out


if __name__ == "__main__":
    app = ColorLab()
    app.mainloop()