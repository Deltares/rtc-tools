from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Import Data
output_dir = Path("../../../examples/channel_wave_damping/reference_output/").resolve()
record_local_control = np.genfromtxt(
    output_dir / "timeseries_export_local_control.csv",
    delimiter=",",
    encoding=None,
    dtype=None,
    names=True,
    case_sensitive="lower",
)
record_optimization = np.genfromtxt(
    output_dir / "timeseries_export.csv",
    delimiter=",",
    encoding=None,
    dtype=None,
    names=True,
    case_sensitive="lower",
)

# Get times as datetime objects
times = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in record_optimization["time"]]

# Constants
g = 9.81
crest_width = 50


def crest_level_from_level_and_discharge(H, Q):
    """Inverted weir equation"""
    return H - (Q / (crest_width * (2 / 3) * np.sqrt(2 / 3 * g))) ** (2 / 3)


cmaps = ["Blues", "Oranges", "Greys"]
shades = [0.65, 0.8]

# Generate Plot
groups = ["PID Controlled", "Optimized"]
records = [record_local_control, record_optimization]
n_subplots = len(groups) * 2
fig, axarr = plt.subplots(n_subplots, sharex=True, figsize=(8, 2 * n_subplots))

for i, group in enumerate(groups):
    record = records[i]

    axarr[2 * i].set_title(group + " Weir Discharges")
    axarr[2 * i].set_ylabel("Flow Rate [m³/s]")
    axarr[2 * i].plot(
        times,
        record["q_in"],
        label="Boundary Inflow",
        # linewidth=1,
        color=plt.get_cmap(cmaps[2])(shades[0]),
    )
    axarr[2 * i].plot(
        times,
        record["q_dam_upstream"],
        label="Weir Flow (upstream)",
        # linewidth=1,
        color=plt.get_cmap(cmaps[0])(shades[1]),
    )
    axarr[2 * i].plot(
        times,
        record["q_dam_middle"],
        label="Weir Flow (middle)",
        # linewidth=1,
        color=plt.get_cmap(cmaps[1])(shades[1]),
    )

    axarr[2 * i + 1].set_title(group + " Water Levels")
    axarr[2 * i + 1].set_ylabel("Level [m]")

    axarr[2 * i + 1].plot(
        times,
        np.full_like(record["h_upstream"], 20),
        label="Target Level (upstream)",
        # linewidth=1,
        color=plt.get_cmap(cmaps[2])(shades[0]),
        linestyle="--",
    )
    axarr[2 * i + 1].plot(
        times,
        record["h_upstream"],
        label="Water Level (upstream)",
        # linewidth=1,
        color=plt.get_cmap(cmaps[0])(shades[1]),
    )
    axarr[2 * i + 1].plot(
        times,
        crest_level_from_level_and_discharge(record["h_upstream"], record["q_dam_upstream"]),
        label="Crest Level (upstream)",
        # linewidth=1,
        linestyle="--",
        color=plt.get_cmap(cmaps[0])(shades[0]),
    )

    axarr[2 * i + 1].plot(
        times,
        np.full_like(record["h_middle"], 15),
        label="Target Level (middle)",
        # linewidth=1,
        color=plt.get_cmap(cmaps[2])(shades[0]),
        linestyle="--",
    )
    axarr[2 * i + 1].plot(
        times,
        record["h_middle"],
        label="Water Level (middle)",
        # linewidth=1,
        color=plt.get_cmap(cmaps[1])(shades[1]),
    )
    axarr[2 * i + 1].plot(
        times,
        crest_level_from_level_and_discharge(record["h_middle"], record["q_dam_middle"]),
        label="Crest Level (middle)",
        # linewidth=1,
        linestyle="--",
        color=plt.get_cmap(cmaps[1])(shades[0]),
    )

# Scale the y-axis the same for axes 0 and 2
step = 50
axarr[0].autoscale(enable=True, axis="y", tight=True)
axarr[2].autoscale(enable=True, axis="y", tight=True)
start0, stop0 = axarr[0].get_ylim()
start2, stop2 = axarr[2].get_ylim()
start = (min(start0, start2) // step) * step
stop = (max(stop0, stop2) // step + 1) * step
axarr[0].set_ylim(start, stop)
axarr[2].set_ylim(start, stop)

# Scale the y-axis the same for axes 1 and 3
step = 1
axarr[1].autoscale(enable=True, axis="y", tight=True)
axarr[3].autoscale(enable=True, axis="y", tight=True)
start1, stop1 = axarr[1].get_ylim()
start3, stop3 = axarr[3].get_ylim()
start = (min(start1, start3) // step) * step
stop = (max(stop1, stop3) // step + 1) * step
axarr[1].set_ylim(start, stop)
axarr[3].set_ylim(start, stop)

# Format bottom axis label
axarr[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

# Shrink margins
fig.tight_layout()

# Shrink each axis and put a legend to the right of the axis
for i in range(n_subplots):
    box = axarr[i].get_position()
    axarr[i].set_position([box.x0, box.y0, box.width * 0.75, box.height])
    axarr[i].legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False, prop={"size": 8})

plt.autoscale(enable=True, axis="x", tight=True)

# Output Plot
plt.show()
