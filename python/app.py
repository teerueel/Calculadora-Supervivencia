"""
Calculadora de supervivencia — aplicación de escritorio (PySide6 + matplotlib).

Pestañas: Tablas de mortalidad · Modelos paramétricos · Comparación · Atlas.
Ejecutar:            python app.py
Generar el .exe:     build_exe.bat   (o pyinstaller calculadora.spec)
"""
import math
import os
import sys

os.environ.setdefault("QT_API", "pyside6")  # matplotlib debe usar PySide6 (importante también en el .exe)

import matplotlib  # noqa: E402
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator  # noqa: E402
from PySide6.QtCore import Qt, QTimer, Signal, QUrl  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen, QStandardItem, QStandardItemModel, QTextDocument  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QPushButton, QScrollArea, QSizePolicy, QSlider, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

import atlas  # noqa: E402
import modelos  # noqa: E402
import tablas  # noqa: E402
from datos import TABLES, TABLE_GROUPS  # noqa: E402

OMEGA = tablas.OMEGA
SERIF = "STIX Two Text, Cambria Math, Cambria, Georgia, serif"
C = dict(paper="#EEF2F4", sheet="#FFFFFF", ink="#1B2A38", muted="#5B6B7A", rule="#D9E0E6", field="#F6F8FA",
         surv="#1F7A6D", death="#A8323E", defer="#C98A1B", mu="#3C5A8A", ref="#8A96A3")
SERIES = ["#1B2A38", "#1F7A6D", "#A8323E", "#C98A1B", "#3C5A8A", "#7B4F8E", "#5E7D2A", "#2A9DB5"]


# ============================================================ formato es-ES
def fnum(v, d):
    if v is None or not math.isfinite(v):
        return "—"
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


SUB = str.maketrans("0123456789,.", "₀₁₂₃₄₅₆₇₈₉,.")


def fP(v): return fnum(v, 6)
def fL(v): return fnum(v, 2)
def fPct(v): return "—" if not math.isfinite(v) else fnum(v * 100, 2) + " %"


def fA(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def fD(v, d=6):
    return ("+" if v >= 0 else "−") + fnum(abs(v), d)


SUPS = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def fParam(v):
    if v == 0:
        return "0"
    a = abs(v)
    if 1e-3 <= a < 1e5:
        return f"{v:.5g}".replace(".", ",")
    e = math.floor(math.log10(a))
    return f"{v / 10 ** e:.4g}".replace(".", ",") + "·10" + str(e).translate(SUPS)


def parse(s):
    s = str(s).strip().replace(" ", "").replace(",", ".").replace("·10", "e")
    s = s.translate(str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "-0123456789"))
    try:
        return float(s)
    except ValueError:
        return float("nan")


def is_int(v): return abs(v - round(v)) < 1e-9


def sym(pre, base, post, size=None, color=None):
    st = f"font-family:{SERIF};" + (f"font-size:{size}px;" if size else "") + (f"color:{color};" if color else "")
    p = f"<sub>{pre}</sub>" if pre not in (None, "") else ""
    q = f"<sub>{post}</sub>" if post not in (None, "") else ""
    return f"<span style='{st}'>{p}<i>{base}</i>{q}</span>"


def lsym(a):
    return sym(None, "l", fA(a) if isinstance(a, (int, float)) else a)


# ============================================================ widgets
class Seg(QWidget):
    changed = Signal(str)

    def __init__(self, options, value, small=False):
        super().__init__()
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        self.group = QButtonGroup(self); self.group.setExclusive(True)
        self.btns = {}
        for i, (v, t) in enumerate(options):
            b = QPushButton(t); b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            b.setObjectName("segS" if small else "seg")
            b.setProperty("pos", "first" if i == 0 else "last" if i == len(options) - 1 else "mid")
            b.clicked.connect(lambda _=False, vv=v: self._set(vv))
            self.group.addButton(b); lay.addWidget(b); self.btns[v] = b
        self.value = value; self.btns[value].setChecked(True)

    def _set(self, v):
        if v != self.value:
            self.value = v; self.changed.emit(v)

    def set(self, v):
        self.value = v; self.btns[v].setChecked(True)


class NumField(QWidget):
    changed = Signal()

    def __init__(self, label, value):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(3)
        lb = QLabel(label); lb.setObjectName("flabel")
        self.edit = QLineEdit(value); self.edit.textChanged.connect(lambda _: self.changed.emit())
        lay.addWidget(lb); lay.addWidget(self.edit)

    def val(self): return parse(self.edit.text())


class ParamSlider(QWidget):
    changed = Signal(float)

    def __init__(self, d, value):
        super().__init__()
        self.d, self.log = d, d["scale"] == "log"
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 2, 0, 6); lay.setSpacing(2)
        head = QHBoxLayout()
        lb = QLabel(f"<span style='font-family:{SERIF}; font-size:17px'><i>{d['sym']}</i></span>&nbsp; <span style='color:{C['muted']}; font-size:12px'>{d['desc']}</span>")
        lb.setWordWrap(True)
        self.edit = QLineEdit(fParam(value)); self.edit.setFixedWidth(100); self.edit.setAlignment(Qt.AlignRight)
        self.edit.editingFinished.connect(self._from_edit)
        head.addWidget(lb, 1); head.addWidget(self.edit)
        self.sl = QSlider(Qt.Horizontal); self.sl.setRange(0, 1000); self.sl.valueChanged.connect(self._from_slider)
        rng = QHBoxLayout()
        for t, al in ((fParam(d["min"]), Qt.AlignLeft), ("escala logarítmica" if self.log else "", Qt.AlignCenter), (fParam(d["max"]), Qt.AlignRight)):
            r = QLabel(t); r.setObjectName("tiny"); r.setAlignment(al); rng.addWidget(r, 1)
        lay.addLayout(head); lay.addWidget(self.sl); lay.addLayout(rng)
        self.value = value; self._sync_slider()

    def _u(self, v):
        lo, hi = self.d["min"], self.d["max"]
        if self.log:
            return (math.log(max(v, lo)) - math.log(lo)) / (math.log(hi) - math.log(lo))
        return (v - lo) / (hi - lo)

    def _v(self, u):
        lo, hi = self.d["min"], self.d["max"]
        return math.exp(math.log(lo) + u * (math.log(hi) - math.log(lo))) if self.log else lo + u * (hi - lo)

    def _sync_slider(self):
        self.sl.blockSignals(True); self.sl.setValue(round(min(1, max(0, self._u(self.value))) * 1000)); self.sl.blockSignals(False)

    def _from_slider(self, k):
        v = float(f"{self._v(k / 1000):.5g}")
        self.value = v; self.edit.setText(fParam(v)); self.changed.emit(v)

    def _from_edit(self):
        v = parse(self.edit.text())
        if math.isfinite(v) and self.d["min"] <= v <= self.d["max"]:
            self.value = v; self._sync_slider(); self.changed.emit(v); self.edit.setStyleSheet("")
        else:
            self.edit.setStyleSheet(f"border:1px solid {C['death']};")
            self.edit.setToolTip(f"Introduce un valor entre {fParam(self.d['min'])} y {fParam(self.d['max'])}.")


class Card(QFrame):
    def __init__(self, accent=None):
        super().__init__()
        self.setObjectName("card")
        if accent:
            self.setStyleSheet(f"#card {{ border-left: 4px solid {accent}; }}")
        self.lay = QVBoxLayout(self); self.lay.setContentsMargins(16, 12, 16, 12); self.lay.setSpacing(4)


class ResultRow(QFrame):
    def __init__(self, accent):
        super().__init__()
        self.setObjectName("rrow"); self.setStyleSheet(f"#rrow {{ border-left: 4px solid {accent}; }}")
        self.accent = accent
        g = QGridLayout(self); g.setContentsMargins(16, 10, 16, 10); g.setHorizontalSpacing(16)
        self.sym = QLabel(); self.sym.setFixedWidth(110)
        self.desc = QLabel(); self.desc.setObjectName("rdesc")
        self.val = QLabel(); self.val.setObjectName("rnum"); self.val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.pct = QLabel(); self.pct.setObjectName("tiny"); self.pct.setAlignment(Qt.AlignRight)
        g.addWidget(self.sym, 0, 0, 2, 1); g.addWidget(self.desc, 0, 1, 2, 1)
        g.addWidget(self.val, 0, 2); g.addWidget(self.pct, 1, 2); g.setColumnStretch(1, 1)

    def set(self, pre, base, post, desc, value):
        self.sym.setText(sym(pre, base, post, 30, self.accent))
        self.desc.setText(desc)
        self.val.setText(fP(value)); self.pct.setText(fPct(value))


def results_card():
    card = QFrame(); card.setObjectName("card")
    v = QVBoxLayout(card); v.setContentsMargins(0, 2, 0, 2); v.setSpacing(0)
    rows = [ResultRow(C["surv"]), ResultRow(C["death"]), ResultRow(C["defer"])]
    for i, r in enumerate(rows):
        if i:
            ln = QFrame(); ln.setObjectName("hline"); ln.setFixedHeight(1); v.addWidget(ln)
        v.addWidget(r)
    ln = QFrame(); ln.setObjectName("hline"); ln.setFixedHeight(1); v.addWidget(ln)
    foot = QLabel(); foot.setObjectName("rfoot"); foot.setWordWrap(True); foot.setContentsMargins(18, 8, 18, 8)
    v.addWidget(foot)
    return card, rows, foot


def fill_rows(rows, R, x, n, m):
    rows[0].set(fA(n), "p", fA(x), f"Sobrevivir {fA(n)} años, hasta la edad {fA(x + n)}", R["npx"])
    rows[1].set(fA(n), "q", fA(x), f"Fallecer antes de la edad {fA(x + n)}", R["nqx"])
    rows[2].set(f"{fA(m)}|{fA(n)}", "q", fA(x), f"Fallecer entre las edades {fA(x + m)} y {fA(x + m + n)}", R["mnqx"])


class ChartTrio(FigureCanvasQTAgg):
    """Tres gráficas: _t p_x, _t q_x y μ_{x+t}."""

    def __init__(self):
        self.fig = Figure(figsize=(11, 3.3), dpi=100, facecolor=C["paper"])
        super().__init__(self.fig)
        self.setMinimumHeight(320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.axS, self.axF, self.axM = self.fig.subplots(1, 3)
        self.fig.subplots_adjust(left=0.05, right=0.99, bottom=0.17, top=0.88, wspace=0.25)

    def plot(self, series, x, n, m, t=None, tval=None, logmu=True, single=False):
        es = lambda v, _p: f"{v:g}".replace(".", ",")  # noqa: E731
        maxT = OMEGA - x
        for ax, title in ((self.axS, "Supervivencia  ₜpₓ"), (self.axF, "Distribución  ₜqₓ"), (self.axM, "Tanto instantáneo  μₓ₊ₜ")):
            ax.clear(); ax.set_facecolor(C["sheet"])
            ax.set_title(title, loc="left", fontsize=12, family="serif", color=C["ink"], fontweight="bold")
            ax.grid(True, color=C["rule"], ls=":", lw=0.8)
            for sp in ax.spines.values():
                sp.set_color(C["rule"])
            ax.tick_params(colors=C["muted"], labelsize=9)
            ax.set_xlim(0, maxT); ax.set_xlabel("t (años)", color=C["muted"], fontsize=9)
            ax.xaxis.set_major_formatter(FuncFormatter(es))
            if n <= maxT:
                ax.axvline(n, color=C["surv"], ls="--", lw=1)
            if ax is not self.axM and n + m > 0 and m < maxT:
                ax.axvspan(m, min(m + n, maxT), color=C["defer"], alpha=0.13, lw=0)
        pos = []
        for s in series:
            colS = C["surv"] if single and s.get("primary") else s["color"]
            colF = C["death"] if single and s.get("primary") else s["color"]
            colM = C["mu"] if single and s.get("primary") else s["color"]
            ls = "--" if s.get("dash") else "-"
            lw = 1.3 if s.get("dash") else 1.8
            self.axS.plot(s["ts"], s["S"], color=colS, ls=ls, lw=lw, label=s["label"])
            self.axF.plot(s["ts"], s["F"], color=colF, ls=ls, lw=lw)
            mu = [v if (v is not None and v > 0) else float("nan") for v in s["MU"]]
            self.axM.plot(s["ts"], mu, color=colM, ls=ls, lw=lw)
            pos += [v for tt, v in zip(s["ts"], mu) if math.isfinite(v) and x + tt <= 110]
        for ax in (self.axS, self.axF):
            ax.set_ylim(0, 1.02); ax.yaxis.set_major_formatter(FuncFormatter(es))
        lo, hi = (min(pos), min(max(pos), 10)) if pos else (1e-4, 1)
        if logmu:
            self.axM.set_yscale("log")
            self.axM.set_ylim(10 ** math.floor(math.log10(lo)), 10 ** max(math.floor(math.log10(lo)) + 1, math.ceil(math.log10(hi))))
            self.axM.yaxis.set_major_locator(LogLocator(base=10))
        else:
            self.axM.set_yscale("linear"); self.axM.set_ylim(0, hi * 1.08)
            self.axM.yaxis.set_major_formatter(FuncFormatter(es))
        if t is not None and tval is not None and t <= maxT:
            self.axS.plot([t], [tval], "o", color=C["ink"], ms=5)
        self.draw_idle()


def scroll(widget, hbar=True):
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(widget); sa.setFrameShape(QFrame.NoFrame)
    if not hbar:
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    return sa


def block(title):
    w = QFrame(); w.setObjectName("block")
    v = QVBoxLayout(w); v.setContentsMargins(0, 10, 0, 12); v.setSpacing(6)
    t = QLabel(title); t.setObjectName("ptitle"); v.addWidget(t)
    return w, v


def note(text):
    lb = QLabel(text); lb.setObjectName("pnote"); lb.setWordWrap(True)
    return lb


def grouped_combo(groups, items_fn):
    """QComboBox con cabeceras de grupo no seleccionables (equivalente a <optgroup>)."""
    cb = QComboBox(); model = QStandardItemModel(cb)
    for title, keys in groups:
        h = QStandardItem(title); h.setFlags(Qt.NoItemFlags)
        f = QFont(); f.setBold(True); h.setFont(f); h.setForeground(QColor(C["muted"]))
        model.appendRow(h)
        for k in keys:
            it = QStandardItem("   " + items_fn(k)); it.setData(k, Qt.UserRole); model.appendRow(it)
    cb.setModel(model)
    cb.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon); cb.setMinimumContentsLength(12)
    cb.view().setMinimumWidth(360)
    return cb


def combo_key(cb):
    return cb.currentData(Qt.UserRole)


def combo_select(cb, key):
    for i in range(cb.count()):
        if cb.itemData(i, Qt.UserRole) == key:
            cb.setCurrentIndex(i); return


class Debounced:
    def __init__(self, fn, ms=40):
        self.t = QTimer(); self.t.setSingleShot(True); self.t.setInterval(ms); self.t.timeout.connect(fn)

    def __call__(self, *a): self.t.start()


LX0 = "l<sub>x</sub> = 0: nadie llega a la edad {x} con esta ley de mortalidad, así que las probabilidades no están definidas. Elige una edad menor."


def validate(x, n, m, t=None, year=None, need_year=False):
    if not math.isfinite(x) or x < 0 or x > 120: return "La edad x debe ser un número entre 0 y 120."
    if not math.isfinite(n) or n < 0: return "El plazo n debe ser un número mayor o igual que 0."
    if not math.isfinite(m) or m < 0: return "El diferimiento m debe ser un número mayor o igual que 0."
    if t is not None and (not math.isfinite(t) or t < 0): return "El tiempo t debe ser un número mayor o igual que 0."
    if need_year and (not math.isfinite(year) or not is_int(year) or year < 1900 or year > 2200):
        return "El año de cálculo debe ser un entero entre 1900 y 2200."
    return None


class CalcTab(QWidget):
    def __init__(self):
        super().__init__()
        h = QHBoxLayout(self); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(18)
        self.panel = QFrame(); self.panel.setObjectName("panel")
        self.pv = QVBoxLayout(self.panel); self.pv.setContentsMargins(16, 4, 16, 8); self.pv.setSpacing(0)
        ps = scroll(self.panel, hbar=False); ps.setFixedWidth(340)
        self.panel.setMaximumWidth(326)
        self.main = QWidget(); self.mv = QVBoxLayout(self.main); self.mv.setContentsMargins(0, 0, 6, 0); self.mv.setSpacing(12)
        h.addWidget(ps); h.addWidget(scroll(self.main, hbar=False), 1)
        self.refresh = Debounced(self.recompute)
        self.err = QLabel(); self.err.setObjectName("error"); self.err.setWordWrap(True); self.err.hide()

    def horizon(self):
        w, v = block("Edad y horizonte")
        g = QGridLayout(); g.setHorizontalSpacing(10); g.setVerticalSpacing(8)
        self.fx, self.fn, self.fm = NumField("Edad x", "45"), NumField("Plazo n", "10"), NumField("Diferimiento m", "5")
        for i, f in enumerate([self.fx, self.fn, self.fm]):
            g.addWidget(f, i // 2, i % 2); f.changed.connect(self.refresh)
        v.addLayout(g); v.addWidget(note("x, n y m admiten decimales."))
        return w

    def interp(self, txt):
        w, v = block("Edades no enteras")
        self.smet = Seg([("lin", "Lineal"), ("exp", "Exponencial")], "lin"); self.smet.changed.connect(self.refresh)
        v.addWidget(self.smet); v.addWidget(note(txt))
        return w

    def show_error(self, msg):
        self.err.setText(msg); self.err.setVisible(bool(msg))
        for w in self.result_widgets:
            w.setVisible(not msg)

# ============================================================ Tablas
class TablasTab(CalcTab):
    def __init__(self):
        super().__init__()
        w, v = block("Tabla")
        lb = QLabel("Tabla de mortalidad"); lb.setObjectName("flabel")
        self.cb = grouped_combo(TABLE_GROUPS, lambda k: TABLES[k]["label"]); combo_select(self.cb, "per_ind_2")
        self.cb.currentIndexChanged.connect(self.refresh)
        self.tags = QLabel(); self.tags.setWordWrap(True)
        v.addWidget(lb); v.addWidget(self.cb); v.addWidget(self.tags); self.pv.addWidget(w)

        w, v = block("Asegurado")
        lb = QLabel("Sexo"); lb.setObjectName("flabel")
        self.ssex = Seg([("H", "Hombre"), ("M", "Mujer")], "H"); self.ssex.changed.connect(self.refresh)
        self.fy = NumField("Año de cálculo", "2026"); self.fy.changed.connect(self.refresh)
        self.ynote = note("")
        v.addWidget(lb); v.addWidget(self.ssex); v.addWidget(self.fy); v.addWidget(self.ynote); self.pv.addWidget(w)
        self.pv.addWidget(self.horizon())
        self.pv.addWidget(self.interp("Se usa cuando x, n o m no son enteros, y define cómo se reparte la mortalidad dentro de cada año."))
        self.pv.addStretch(1)

        self.ctx = QLabel(); self.ctx.setObjectName("context"); self.ctx.setWordWrap(True)
        self.rcard, self.rows, self.foot = results_card()
        self.chart = ChartTrio()
        mu_row = QHBoxLayout(); mu_row.addStretch(1); mu_row.addWidget(QLabel("Escala de μ:"))
        self.slog = Seg([("log", "Log"), ("lin", "Lineal")], "log", small=True); self.slog.changed.connect(self.refresh)
        mu_row.addWidget(self.slog)
        self.cap = note("")
        self.btnL = QPushButton("Mostrar la tabla lₓ utilizada"); self.btnL.setObjectName("ghost"); self.btnL.setCheckable(True)
        self.btnL.toggled.connect(self.refresh)
        self.ltab = QTableWidget(); self.ltab.setEditTriggers(QAbstractItemView.NoEditTriggers); self.ltab.setMinimumHeight(320)
        self.ltab.verticalHeader().setVisible(False); self.ltab.hide()
        for wdg in (self.err, self.ctx, self.rcard):
            self.mv.addWidget(wdg)
        self.mv.addLayout(mu_row); self.mv.addWidget(self.chart); self.mv.addWidget(self.cap)
        self.mv.addWidget(self.btnL, 0, Qt.AlignLeft); self.mv.addWidget(self.ltab); self.mv.addStretch(1)
        self.result_widgets = [self.ctx, self.rcard, self.chart, self.cap, self.btnL]
        self.recompute()

    def recompute(self):
        key = combo_key(self.cb) or "per_ind_2"
        t = TABLES[key]; per = t["kind"] == "per"
        chips = [("Generacional", C["surv"]) if per else ("Estática", C["mu"]),
                 ({"supervivencia": "Supervivencia", "riesgo": "Riesgo", "decesos": "Decesos"}[t["uso"]],
                  {"supervivencia": C["surv"], "riesgo": C["death"], "decesos": C["defer"]}[t["uso"]]),
                 ("2º orden" if t["orden"] == 2 else "1er orden", C["muted"]), (f"Base {t['base']}", C["muted"])]
        self.tags.setText(" &nbsp;".join(f"<span style='color:{c}; font-weight:600; font-size:12px'>● {tx}</span>" for tx, c in chips))
        self.fy.setVisible(per)
        x, n, m, year = self.fx.val(), self.fn.val(), self.fm.val(), self.fy.val()
        met, sex = self.smet.value, self.ssex.value
        self.ynote.setText(f"Generación {int(year - math.floor(x))}" if per and math.isfinite(x) and math.isfinite(year)
                           else "Tabla estática: no depende del año (base 2019).")
        e = validate(x, n, m, None, year, per)
        self.show_error(e)
        if e:
            self.ltab.hide(); return
        year = int(year) if per else 2019
        R = tablas.compute(key, sex, x, n, m, year, met)
        if not R["lx"] > 0:
            self.show_error(LX0.format(x=fA(x))); self.ltab.hide(); return
        self.ctx.setText(f"{'Hombre' if sex == 'H' else 'Mujer'} de {fA(x)} años, {t['label']}. "
                         + (f"Generación {R['cohort']}, año de cálculo {year}." if per else "Tabla estática, año base 2019."))
        fill_rows(self.rows, R, x, n, m)
        self.foot.setText(f"Esperanza de vida: abreviada {sym(None, 'e', fA(x))} = {fnum(R['ex'], 2)} años; "
                          f"completa {sym(None, 'e̊', fA(x))} = {fnum(R['ecx'], 2)} años."
                          + (f" <span style='color:{C['death']}'>x + m + n supera ω = 121, donde l<sub>ω</sub> = 0.</span>" if x + m + n > OMEGA else ""))
        ts, S, F, MU = tablas.curves(R, x, met)
        self.chart.plot([dict(label=t["short"], primary=True, color=C["ink"], ts=ts, S=S, F=F, MU=MU)], x, n, m, n, R["npx"],
                        self.slog.value == "log", single=True)
        self.cap.setText(f"Línea discontinua y punto en t = {fA(n)}; franja ocre entre t = {fA(m)} y t = {fA(m + n)}. "
                         "Con interpolación lineal, μ crece dentro de cada año; con la exponencial, es escalonada.")
        self.btnL.setText(("Ocultar" if self.btnL.isChecked() else "Mostrar") + " la tabla lₓ utilizada")
        self.ltab.setVisible(self.btnL.isChecked())
        if self.btnL.isChecked():
            ages = list(range(math.floor(x), min(OMEGA, math.ceil(x + m + n) + 5) + 1))
            heads = ["Edad"] + (["Año"] if per else []) + ["qₓ (‰)", "lₓ", "dₓ"]
            self.ltab.setColumnCount(len(heads)); self.ltab.setHorizontalHeaderLabels(heads); self.ltab.setRowCount(len(ages))
            self.ltab.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            keys = {math.floor(v) for v in (x, x + n, x + m, x + m + n)}
            for i, a in enumerate(ages):
                vals = [str(a)] + ([str(R["cohort"] + a)] if per else []) + [
                    fnum(R["q"][a] * 1000, 4) if a <= 120 else "—", fL(R["l"][a]), fL(R["l"][a] - R["l"][a + 1]) if a <= 120 else "—"]
                for j, s in enumerate(vals):
                    it = QTableWidgetItem(s); it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if a in keys:
                        it.setBackground(QColor("#FBF3E2")); f = it.font(); f.setBold(True); it.setFont(f)
                    self.ltab.setItem(i, j, it)


# ============================================================ Paramétricos
class ParamTab(CalcTab):
    def __init__(self, store):
        super().__init__()
        self.store = store
        w, v = block("Modelo")
        lb = QLabel("Ley de mortalidad"); lb.setObjectName("flabel")
        groups = [(f, [k for k in modelos.MODEL_KEYS if modelos.MODELS[k]["family"] == f]) for f in modelos.MODEL_FAMILIES]
        self.cb = grouped_combo(groups, lambda k: modelos.MODELS[k]["name"]); combo_select(self.cb, "gompertz")
        self.cb.currentIndexChanged.connect(self.rebuild)
        self.formula = QLabel(); self.formula.setObjectName("mformula"); self.formula.setWordWrap(True)
        lb2 = QLabel("Sexo"); lb2.setObjectName("flabel")
        self.ssex = Seg([("H", "Hombre"), ("M", "Mujer")], "H"); self.ssex.changed.connect(self.rebuild)
        for x_ in (lb, self.cb, self.formula, lb2, self.ssex):
            v.addWidget(x_)
        self.pv.addWidget(w)

        self.pblock, self.pbv = block("Parámetros")
        self.reset = QPushButton("Restaurar valores iniciales"); self.reset.setObjectName("ghost"); self.reset.clicked.connect(self.do_reset)
        self.pbv.addWidget(self.reset, 0, Qt.AlignLeft)
        self.sliders_box = QVBoxLayout(); self.pbv.addLayout(self.sliders_box)
        self.pnote = note(""); self.pbv.addWidget(self.pnote)
        self.pv.addWidget(self.pblock)
        self.pv.addWidget(self.horizon())
        self.iblock = self.interp("Heligman–Pollard da qₓ en edades enteras: entre ellas se interpola como en una tabla.")
        self.pv.addWidget(self.iblock)
        w, v = block("Referencia")
        self.chk = QCheckBox("Superponer PASEM2020 General 2º orden"); self.chk.setChecked(True); self.chk.toggled.connect(self.refresh)
        v.addWidget(self.chk); self.pv.addWidget(w); self.pv.addStretch(1)

        self.ctx = QLabel(); self.ctx.setObjectName("context"); self.ctx.setWordWrap(True)
        self.rcard, self.rows, self.foot = results_card()
        self.chart = ChartTrio()
        mu_row = QHBoxLayout(); mu_row.addStretch(1); mu_row.addWidget(QLabel("Escala de μ:"))
        self.slog = Seg([("log", "Log"), ("lin", "Lineal")], "log", small=True); self.slog.changed.connect(self.refresh)
        mu_row.addWidget(self.slog)
        self.cap = note("")
        for wdg in (self.err, self.ctx, self.rcard):
            self.mv.addWidget(wdg)
        self.mv.addLayout(mu_row); self.mv.addWidget(self.chart); self.mv.addWidget(self.cap); self.mv.addStretch(1)
        self.result_widgets = [self.ctx, self.rcard, self.chart, self.cap]
        self.sliders = []
        self.rebuild()

    def key(self): return combo_key(self.cb) or "gompertz"

    def rebuild(self):
        k, sex = self.key(), self.ssex.value
        m = modelos.MODELS[k]
        self.formula.setText(f"<span style='font-family:{SERIF}; font-size:15px'>{atlas.PARAM_ATLAS[k]['mu']}</span>")
        for s in self.sliders:
            s.setParent(None); s.deleteLater()
        self.sliders = []
        for d in m["params"]:
            s = ParamSlider(d, self.store[k][sex][d["k"]])
            s.changed.connect(lambda v, kk=d["k"]: self.set_param(kk, v))
            self.sliders_box.addWidget(s); self.sliders.append(s)
        self.pnote.setText(f"Valores iniciales: ajuste por mínimos cuadrados a PASEM2020 General 2º orden "
                           f"({'hombres' if sex == 'H' else 'mujeres'}). No son parámetros publicados.")
        self.iblock.setVisible(m["kind"] == "disc")
        self.recompute()

    def set_param(self, k, v):
        self.store[self.key()][self.ssex.value][k] = v; self.refresh()

    def do_reset(self):
        k, sex = self.key(), self.ssex.value
        self.store[k][sex] = modelos.default_params(k, sex); self.rebuild()

    def recompute(self):
        k, sex = self.key(), self.ssex.value
        m = modelos.MODELS[k]
        x, n, mm = self.fx.val(), self.fn.val(), self.fm.val()
        met = self.smet.value
        e = validate(x, n, mm)
        self.show_error(e)
        if e:
            return
        ev = modelos.Evaluator(k, self.store[k][sex], met)
        R = ev.compute(x, n, mm)
        if not R["lx"] > 0:
            self.show_error(LX0.format(x=fA(x))); return
        self.ctx.setText(f"{m['name']}, {'hombre' if sex == 'H' else 'mujer'} de {fA(x)} años. "
                         + ("lₓ se construye con las qₓ del modelo." if m["kind"] == "disc" else "lₓ = 100.000 · S(x), con S(x) = e^(−∫μ)."))
        fill_rows(self.rows, R, x, n, mm)
        extra = ""
        if m["kind"] == "disc":
            ex = sum(ev.l_at(x + j) for j in range(1, OMEGA + 1) if x + j < OMEGA) / R["lx"]
            extra = f"; abreviada {sym(None, 'e', fA(x))} = {fnum(ex, 2)} años"
        self.foot.setText(f"Esperanza de vida completa {sym(None, 'e̊', fA(x))} = {fnum(R['ecx'], 2)} años{extra}.")
        ts, S, F, MU = ev.curves(x)
        series = [dict(label=m["name"], primary=True, color=C["ink"], ts=ts, S=S, F=F, MU=MU)]
        if self.chk.isChecked():
            Rr = tablas.compute("pasem_gen_2", sex, x, 0, 0, 2019, met)
            t2, S2, F2, M2 = tablas.curves(Rr, x, met)
            series.append(dict(label="PASEM2020 General 2º", color=C["ref"], dash=True, ts=t2, S=S2, F=F2, MU=M2))
        self.chart.plot(series, x, n, mm, n, R["npx"], self.slog.value == "log", single=True)
        self.cap.setText("Mueve los parámetros y las tres curvas se recalculan al instante."
                         + (" La línea gris discontinua es la PASEM2020 General 2º orden del mismo sexo." if self.chk.isChecked() else ""))


# ============================================================ Comparación
class CompTab(CalcTab):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.scen, self.next_id, self.open_id = [], 1, None
        for src in ("t:per_ind_2", "t:pasem_gen_2", "m:gompertz", "m:heligman_pollard"):
            self._new(src, "H")
        w, v = block("Escenarios")
        self.list_box = QVBoxLayout(); self.list_box.setSpacing(4); v.addLayout(self.list_box)
        addrow = QHBoxLayout()
        groups = [("Tablas · " + g, ["t:" + k for k in keys]) for g, keys in TABLE_GROUPS] + \
                 [("Modelos · " + f, ["m:" + k for k in modelos.MODEL_KEYS if modelos.MODELS[k]["family"] == f]) for f in modelos.MODEL_FAMILIES]
        self.addcb = grouped_combo(groups, self.src_name); combo_select(self.addcb, "m:makeham")
        self.addbtn = QPushButton("Añadir"); self.addbtn.setObjectName("ghost"); self.addbtn.clicked.connect(self.add)
        addrow.addWidget(self.addcb, 1); addrow.addWidget(self.addbtn); v.addLayout(addrow)
        v.addWidget(note("Pulsa el nombre de un modelo para ajustar sus parámetros aquí mismo. Cada escenario tiene los suyos, "
                         "así que puedes comparar, por ejemplo, dos Gompertz distintos."))
        self.pv.addWidget(w)
        self.pv.addWidget(self.horizon())
        w, v = block("Generación y fraccionamiento")
        self.fy = NumField("Año de cálculo (PER2020)", "2026"); self.fy.changed.connect(self.refresh)
        lb = QLabel("Interpolación entre edades"); lb.setObjectName("flabel")
        self.smet = Seg([("lin", "Lineal"), ("exp", "Exponencial")], "lin"); self.smet.changed.connect(self.refresh)
        v.addWidget(self.fy); v.addWidget(lb); v.addWidget(self.smet); self.pv.addWidget(w); self.pv.addStretch(1)

        self.ctx = QLabel(); self.ctx.setObjectName("context"); self.ctx.setWordWrap(True)
        self.table = QTableWidget(); self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False); self.table.setMinimumHeight(200)
        self.tcap = note("Debajo de cada valor, la diferencia con el primer escenario.")
        self.legend = QLabel(); self.legend.setWordWrap(True)
        self.chart = ChartTrio()
        mu_row = QHBoxLayout(); mu_row.addWidget(self.legend, 1); mu_row.addWidget(QLabel("Escala de μ:"))
        self.slog = Seg([("log", "Log"), ("lin", "Lineal")], "log", small=True); self.slog.changed.connect(self.refresh)
        mu_row.addWidget(self.slog)
        for wdg in (self.err, self.ctx, self.table, self.tcap):
            self.mv.addWidget(wdg)
        self.mv.addLayout(mu_row); self.mv.addWidget(self.chart); self.mv.addStretch(1)
        self.result_widgets = [self.ctx, self.table, self.tcap, self.chart, self.legend]
        self.rebuild_list()

    @staticmethod
    def src_name(src):
        k = src[2:]
        return TABLES[k]["short"] if src.startswith("t:") else modelos.MODELS[k]["name"]

    def _new(self, src, sex):
        """Escenario nuevo. Los modelos copian los parámetros vigentes en la pestaña Modelos paramétricos."""
        d = dict(id=self.next_id, src=src, sex=sex)
        if src.startswith("m:"):
            d["p"] = dict(self.store[src[2:]][sex])
        self.scen.append(d); self.next_id += 1
        return d

    def name_of(self, s):
        base = self.src_name(s["src"])
        same = [c for c in self.scen if c["src"] == s["src"]]
        return f"{base} ({same.index(s) + 1})" if len(same) > 1 else base

    def rebuild_list(self):
        while self.list_box.count():
            it = self.list_box.takeAt(0)
            wd = it.widget()
            if wd:
                wd.hide(); wd.setParent(None); wd.deleteLater()
        for i, s in enumerate(self.scen):
            is_m = s["src"].startswith("m:")
            opened = is_m and self.open_id == s["id"]
            box = QWidget(); bv = QVBoxLayout(box); bv.setContentsMargins(0, 2, 0, 2); bv.setSpacing(4)
            row = QHBoxLayout()
            sw = QLabel(); sw.setFixedSize(18, 5); sw.setStyleSheet(f"background:{SERIES[i % len(SERIES)]}; border-radius:2px")
            if is_m:
                nm = QPushButton(("▾  " if opened else "▸  ") + self.name_of(s)); nm.setObjectName("sname")
                nm.setCursor(Qt.PointingHandCursor); nm.setToolTip("Mostrar u ocultar los parámetros")
                nm.clicked.connect(lambda _=False, sid=s["id"], o=opened: self.toggle(None if o else sid))
            else:
                nm = QLabel(self.name_of(s)); nm.setWordWrap(True)
            sg = Seg([("H", "H"), ("M", "M")], s["sex"], small=True)
            sg.changed.connect(lambda v, sid=s["id"]: self.set_sex(sid, v))
            rm = QPushButton("×"); rm.setObjectName("x"); rm.setFixedWidth(26); rm.setEnabled(len(self.scen) > 1)
            rm.clicked.connect(lambda _=False, sid=s["id"]: self.remove(sid))
            row.addWidget(sw); row.addWidget(nm, 1); row.addWidget(sg); row.addWidget(rm)
            bv.addLayout(row)
            if opened:
                k = s["src"][2:]
                pan = QFrame(); pan.setObjectName("sparams"); pv = QVBoxLayout(pan); pv.setContentsMargins(12, 8, 0, 6)
                f = QLabel(f"<span style='font-family:{SERIF}; font-size:14px'>{atlas.PARAM_ATLAS[k]['mu']}</span>")
                f.setObjectName("mformula"); f.setWordWrap(True); pv.addWidget(f)
                for d in modelos.MODELS[k]["params"]:
                    ps = ParamSlider(d, s["p"][d["k"]])
                    ps.changed.connect(lambda v, sc=s, kk=d["k"]: self.set_param(sc, kk, v))
                    pv.addWidget(ps)
                rs = QPushButton("Restaurar valores iniciales"); rs.setObjectName("ghost")
                rs.clicked.connect(lambda _=False, sc=s: self.reset_params(sc))
                pv.addWidget(rs, 0, Qt.AlignLeft)
                bv.addWidget(pan)
            self.list_box.addWidget(box)
        self.addbtn.setEnabled(len(self.scen) < 8)
        self.recompute()

    def _find(self, sid):
        return next(s for s in self.scen if s["id"] == sid)

    def toggle(self, sid):
        self.open_id = sid; self.rebuild_list()

    def set_param(self, s, k, v):
        s["p"][k] = v; self.refresh()

    def reset_params(self, s):
        s["p"] = modelos.default_params(s["src"][2:], s["sex"]); self.rebuild_list()

    def set_sex(self, sid, v):
        s = self._find(sid); s["sex"] = v
        if s["src"].startswith("m:"):
            s["p"] = dict(self.store[s["src"][2:]][v])
            if self.open_id == sid:
                self.rebuild_list(); return
        self.refresh()

    def remove(self, sid):
        if len(self.scen) > 1:
            self.scen = [s for s in self.scen if s["id"] != sid]; self.rebuild_list()

    def add(self):
        if len(self.scen) < 8:
            d = self._new(combo_key(self.addcb), "H")
            if d["src"].startswith("m:"):
                self.open_id = d["id"]
            self.rebuild_list()

    def recompute(self):
        x, n, m, year, met = self.fx.val(), self.fn.val(), self.fm.val(), self.fy.val(), self.smet.value
        need = any(s["src"].startswith("t:") and TABLES[s["src"][2:]]["kind"] == "per" for s in self.scen)
        self.fy.setVisible(need)
        e = validate(x, n, m, None, year, need)
        self.show_error(e)
        if e:
            return
        data = []
        for i, s in enumerate(self.scen):
            src, sex = s["src"], s["sex"]; k = src[2:]
            label = self.name_of(s) + (", hombre" if sex == "H" else ", mujer")
            color = SERIES[i % len(SERIES)]
            if src.startswith("t:"):
                R = tablas.compute(k, sex, x, n, m, int(year) if need else 2019, met)
                ts, S, F, MU = tablas.curves(R, x, met)
            else:
                ev = modelos.Evaluator(k, s["p"], met)
                R = ev.compute(x, n, m); ts, S, F, MU = ev.curves(x)
            data.append(dict(label=label, color=color, R=R, ts=ts, S=S, F=F, MU=MU))
        self.ctx.setText(f"{len(data)} escenarios evaluados en la edad {fA(x)}, con n = {fA(n)} y m = {fA(m)}."
                         + (f" Las PER2020 corresponden a la generación {int(year - math.floor(x))}." if need else ""))
        sb = lambda v: fA(v).translate(SUB)
        heads = ["Escenario", f"{sb(n)}p{sb(x)}", f"{sb(n)}q{sb(x)}", f"{sb(m)}|{sb(n)}q{sb(x)}", f"e̊{sb(x)}"]
        self.table.setColumnCount(5); self.table.setRowCount(len(data))
        self.table.setHorizontalHeaderLabels(heads)
        hh = self.table.horizontalHeader(); hh.setSectionResizeMode(QHeaderView.Stretch); hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        ref = data[0]["R"]
        for i, d in enumerate(data):
            it = QTableWidgetItem(("■  " + d["label"]) + ("   (referencia)" if i == 0 else "")); it.setForeground(QColor(d["color"]))
            self.table.setItem(i, 0, it)
            for j, (kk, dec) in enumerate((("npx", 6), ("nqx", 6), ("mnqx", 6), ("ecx", 2))):
                v = d["R"][kk]
                txt = fnum(v, dec) + ("" if i == 0 else f"\n{fD(v - ref[kk], dec)}")
                c = QTableWidgetItem(txt); c.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, j + 1, c)
        self.table.resizeRowsToContents()
        self.table.setFixedHeight(self.table.horizontalHeader().height() + sum(self.table.rowHeight(r) for r in range(len(data))) + 4)
        self.legend.setText(" &nbsp;&nbsp; ".join(f"<span style='white-space:nowrap'><span style='color:{d['color']}; font-weight:700'>━</span>&nbsp;{d['label'].replace(' ', '&nbsp;')}</span>" for d in data))
        self.chart.plot(data, x, n, m, logmu=self.slog.value == "log")


# ============================================================ Atlas
def spark_image(k):
    W, H = 440, 112
    img = QImage(W, H, QImage.Format_ARGB32); img.fill(QColor(C["field"]))
    ev = modelos.Evaluator(k, modelos.default_params(k, "H"), "exp")
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
    lo, hi = -5, 1
    Y = lambda v: H - (max(lo, v) - lo) / (hi - lo) * H  # noqa: E731
    p.setPen(QPen(QColor(C["rule"]), 1))
    for g in (-4, -2, 0):
        p.drawLine(0, int(Y(g)), W, int(Y(g)))
    path, first = QPainterPath(), True
    for a in range(0, 111):
        v = ev.mu(a + 0.5)
        if v and v > 0:
            X, Yv = a / 110 * W, Y(math.log10(min(v, 10)))
            (path.moveTo if first else path.lineTo)(X, Yv); first = False
    p.setPen(QPen(QColor(C["mu"]), 3)); p.drawPath(path); p.end()
    return img


class AtlasTab(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0)
        sub = QTabWidget(); sub.setObjectName("subtabs")
        b1 = QTextBrowser(); b1.setOpenExternalLinks(True)
        for k in modelos.MODEL_KEYS:
            b1.document().addResource(QTextDocument.ImageResource, QUrl(f"spark_{k}"), spark_image(k))
        b1.setHtml(atlas.param_html())
        b2 = QTextBrowser(); b2.setHtml(atlas.nonparam_html())
        sub.addTab(b1, "Modelos paramétricos"); sub.addTab(b2, "Tablas e interpolación")
        v.addWidget(sub)


# ============================================================ ventana
QSS = f"""
QWidget {{ font-family: 'Public Sans', 'Segoe UI', sans-serif; font-size: 13px; color: {C['ink']}; }}
QMainWindow, #root, QScrollArea, QScrollArea > QWidget > QWidget {{ background: {C['paper']}; }}
#title {{ font-family: {SERIF}; font-size: 28px; font-weight: 600; }}
#subtitle {{ color: {C['muted']}; }}
QTabWidget::pane {{ border: 0; border-top: 1px solid {C['rule']}; padding-top: 14px; }}
QTabBar::tab {{ background: transparent; padding: 8px 14px 10px; color: {C['muted']}; font-weight: 600; font-size: 13.5px;
  border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {C['ink']}; border-bottom: 2px solid {C['ink']}; }}
QTabBar::tab:hover {{ color: {C['ink']}; }}
#panel {{ background: {C['sheet']}; border: 1px solid {C['rule']}; border-radius: 12px; }}
#block {{ border-bottom: 1px solid {C['rule']}; }}
#ptitle {{ font-family: {SERIF}; font-size: 16px; font-weight: 600; }}
#flabel {{ color: {C['muted']}; font-size: 12px; font-weight: 600; }}
#pnote, #tiny {{ color: {C['muted']}; font-size: 11.5px; }}
#context {{ color: {C['muted']}; }}
#mformula {{ background: {C['field']}; border-radius: 7px; padding: 8px; }}
QLineEdit, QComboBox {{ background: {C['field']}; border: 1px solid {C['rule']}; border-radius: 7px; padding: 6px 8px; }}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {C['surv']}; }}
QPushButton#seg, QPushButton#segS {{ background: {C['field']}; border: 1px solid {C['rule']}; color: {C['muted']}; padding: 6px 10px; border-radius: 0; }}
QPushButton#segS {{ padding: 3px 9px; font-size: 12px; }}
QPushButton#seg[pos="first"], QPushButton#segS[pos="first"] {{ border-top-left-radius: 7px; border-bottom-left-radius: 7px; }}
QPushButton#seg[pos="last"], QPushButton#segS[pos="last"] {{ border-top-right-radius: 7px; border-bottom-right-radius: 7px; }}
QPushButton#seg:checked, QPushButton#segS:checked {{ background: {C['ink']}; color: white; border-color: {C['ink']}; }}
QPushButton#ghost {{ background: transparent; border: 1px solid {C['rule']}; border-radius: 7px; padding: 6px 12px; font-weight: 600; }}
QPushButton#ghost:hover {{ background: {C['field']}; }}
QPushButton#x {{ background: transparent; border: 0; color: {C['muted']}; font-size: 17px; }}
#card, #rrow {{ background: {C['sheet']}; border: 1px solid {C['rule']}; border-radius: 12px; }}
#rrow {{ border: 0; border-radius: 0; }}
#hline {{ background: {C['rule']}; }}
#rdesc {{ font-weight: 600; }}
#rform {{ color: {C['muted']}; font-size: 12px; }}
#rnum {{ font-family: {SERIF}; font-size: 24px; }}
#rfoot {{ color: {C['muted']}; }}
#h3 {{ font-family: {SERIF}; font-size: 17px; font-weight: 600; }}
#error {{ background: #FBECEE; border: 1px solid #D9A0A6; color: {C['death']}; border-radius: 10px; padding: 12px; }}
QSlider::groove:horizontal {{ height: 4px; background: {C['rule']}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {C['ink']}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {C['ink']}; width: 14px; height: 14px; margin: -6px 0; border-radius: 7px; }}
QTableWidget {{ background: {C['sheet']}; border: 1px solid {C['rule']}; border-radius: 8px; gridline-color: {C['rule']}; }}
QHeaderView::section {{ background: {C['field']}; border: 0; border-bottom: 1px solid {C['rule']}; padding: 6px; font-weight: 600; color: {C['muted']}; }}
QTextBrowser {{ background: {C['paper']}; border: 0; }}
QPushButton#sname {{ text-align: left; border: 0; background: transparent; font-weight: 600; padding: 2px 0; }}
QPushButton#sname:hover {{ text-decoration: underline; }}
#sparams {{ border-top: 1px dashed {C['rule']}; }}
"""


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora de supervivencia")
        self.resize(1400, 900)
        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(24, 16, 24, 12)
        t = QLabel("Calculadora de supervivencia"); t.setObjectName("title")
        s = QLabel("Probabilidades de supervivencia y fallecimiento con las tablas PER2020 y PASEM2020 (BOE-A-2020-17154) "
                   "y con leyes paramétricas de mortalidad."); s.setObjectName("subtitle")
        v.addWidget(t); v.addWidget(s)
        self.store = {k: {sx: modelos.default_params(k, sx) for sx in ("H", "M")} for k in modelos.MODEL_KEYS}
        self.tabs = QTabWidget()
        self.t1, self.t2 = TablasTab(), ParamTab(self.store)
        self.t3, self.t4 = CompTab(self.store), AtlasTab()
        self.tabs.addTab(self.t1, "Tablas de mortalidad"); self.tabs.addTab(self.t2, "Modelos paramétricos")
        self.tabs.addTab(self.t3, "Comparación"); self.tabs.addTab(self.t4, "Atlas")
        self.tabs.currentChanged.connect(lambda i: i == 2 and self.t3.recompute())
        v.addWidget(self.tabs, 1)
        foot = QLabel("Fuente de las tablas: Resolución de la DGSFP de 17/12/2020 (BOE-A-2020-17154), anexos 1.1, 1.2, 1.3 y 2.1. "
                      "Los parámetros iniciales de los modelos proceden de un ajuste propio a la PASEM2020 General 2º orden, no de una fuente oficial.")
        foot.setObjectName("pnote"); foot.setWordWrap(True); v.addWidget(foot)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    w = Main(); w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
