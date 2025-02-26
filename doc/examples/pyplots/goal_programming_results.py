from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Import Data
data_path = "../../../examples/goal_programming/reference_output/timeseries_export.csv"
results = np.genfromtxt(
    data_path, delimiter=",", encoding=None, dtype=None, names=True, case_sensitive="lower"
)

# Get times as datetime objects
times = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in results["time"]]

# Generate Plot
n_subplots = 3
fig, axarr = plt.subplots(n_subplots, sharex=True, figsize=(8, 3 * n_subplots))
axarr[0].set_title("Water Level and Discharge")

# Upper subplot
axarr[0].set_ylabel("Water Level [m]")
axarr[0].plot(times, results["storage_level"], label="Storage", linewidth=2, color="b")
axarr[0].plot(times, results["sea_level"], label="Sea", linewidth=2, color="m")

# Middle subplot
axarr[1].set_ylabel("Water Level [m]")
axarr[1].plot(times, results["storage_level"], label="Storage", linewidth=2, color="b")
axarr[1].plot(
    times,
    0.44 * np.ones_like(times),
    label="Storage Max",
    linewidth=2,
    color="r",
    linestyle="--",
)
axarr[1].plot(
    times,
    0.43 * np.ones_like(times),
    label="Storage Min",
    linewidth=2,
    color="g",
    linestyle="--",
)

# Lower Subplot
axarr[2].set_ylabel("Flow Rate [m³/s]")
axarr[2].scatter(times, results["q_orifice"], linewidth=1, color="g")
axarr[2].scatter(times, results["q_pump"], linewidth=1, color="r")
# add horizontal lines to the left of these dots, to indicate that the value is attained over an
# entire timestep:
axarr[2].step(times, results["q_orifice"], linewidth=2, where="pre", label="Orifice", color="g")
axarr[2].step(times, results["q_pump"], linewidth=1, where="pre", label="Pump", color="r")

# Format bottom axis label
axarr[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

# Shrink margins
fig.tight_layout()

# Shrink each axis and put a legend to the right of the axis
for i in range(n_subplots):
    box = axarr[i].get_position()
    axarr[i].set_position([box.x0, box.y0, box.width * 0.8, box.height])
    axarr[i].legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)

plt.autoscale(enable=True, axis="x", tight=True)

# Output Plot
plt.show()
