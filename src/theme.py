"""The 'Indigo Ledger' look shared by every chart in the project."""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import config

P = config.PALETTE
HEAT = LinearSegmentedColormap.from_list("indigo_ledger", ["#F4F5FB", "#B9BCE6", "#6C6AC2", "#3D3B8E", "#1B1F3B"])
DIVERGE = LinearSegmentedColormap.from_list("ledger_div", ["#E4572E", "#F7C9B8", "#F4F5FB", "#B9D9F2", "#3D3B8E"])


def apply():
    mpl.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
        "figure.facecolor": "white", "axes.facecolor": "white",
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.edgecolor": P["grid"], "axes.labelcolor": P["ink"], "axes.titlecolor": P["ink"],
        "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": P["grid"], "grid.linewidth": 0.6, "axes.axisbelow": True,
        "xtick.color": P["muted"], "ytick.color": P["muted"], "text.color": P["ink"],
        "legend.frameon": False, "axes.prop_cycle": mpl.cycler(color=config.CATEGORICAL),
    })


def tag(ax, text):
    """Small caption line under the title - gives every chart the same signature."""
    ax.text(0, 1.02, text, transform=ax.transAxes, fontsize=8, color=P["muted"], va="bottom")


def footer(fig, source="Source: EduPro_Online_Platform.xlsx | EduPro Learner Lens"):
    fig.text(0.01, -0.02, source, fontsize=7, color=P["muted"], ha="left")


def save(fig, name):
    config.FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIG_DIR / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    return path
