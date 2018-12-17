"""Show the deformation for semi implicit inertial wave"""

from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

import numpy as np

# Map root_dir
root_dir = Path(__file__).parents[1].resolve()

# Import Data
thetas = [0.0, 0.5, 1.0]
formulations = [
    "inertial_wave",
    "inertial_wave_semi_implicit",
    "saint_venant",
    "saint_venant_upwind",
]
outputs = {
    f: {
        t: np.recfromcsv(
            root_dir / f"output.{t}/timeseries_export_{f}.csv", encoding=None
        )
        for t in thetas
    }
    for f in formulations
}


# Get times as datetime objects
times = list(
    map(
        lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"),
        outputs["inertial_wave"][1.0]["time"],
    )
)

# Generate Plot
n_subplots = 2
fig, axarr = plt.subplots(n_subplots, sharex=True, figsize=(5, 1.5 * n_subplots))
# axarr[0].set_title("Homotopy Deformation of Semi-Implicit Inertial Wave Equations")

start_idx = 68
end_idx = -50

# Upper subplot
axarr[0].set_ylabel("Flow Rate [m³/s]")
for theta in thetas:
    axarr[0].plot(
        times[start_idx:end_idx],
        outputs["inertial_wave_semi_implicit"][theta]["channel_q_dn"][
            start_idx:end_idx
        ],
        label=f"Downstream\ntheta={theta}",
    )
axarr[0].plot(
    times[start_idx:end_idx],
    outputs["inertial_wave"][1.0]["channel_q_up"][start_idx:end_idx],
    label="Upstream",
    linestyle="--",
    color="grey",
)

# Lower subplot
axarr[1].set_ylabel("Water Level [m]")
for theta in thetas:
    axarr[1].plot(
        times[start_idx:end_idx],
        outputs["inertial_wave_semi_implicit"][theta]["channel_h_up"][
            start_idx:end_idx
        ],
        label=f"Upstream\ntheta={theta}",
    )
axarr[1].plot(
    times[start_idx:end_idx],
    outputs["inertial_wave"][1.0]["channel_h_dn"][start_idx:end_idx],
    label="Downstream",
    linestyle="--",
    color="grey",
)
# Format bottom axis label
axarr[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
axarr[-1].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))

# Shrink margins
fig.tight_layout()

# Shrink each axis and put a legend to the right of the axis
for i in range(n_subplots):
    box = axarr[i].get_position()
    axarr[i].set_position([box.x0, box.y0, box.width * 0.74, box.height])
    axarr[i].legend(
        loc="center left", bbox_to_anchor=(1, 0.5), frameon=False, prop={"size": 8}
    )

plt.autoscale(enable=True, axis="x", tight=True)

# Output Plot
plt.savefig(Path(__file__).with_suffix(".pdf"))
