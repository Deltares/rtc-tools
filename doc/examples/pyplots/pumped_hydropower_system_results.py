from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Import Data
data_path = "../../../examples/pumped_hydropower_system/reference_output/timeseries_export.csv"
import_data_path = "../../../examples/pumped_hydropower_system/input//timeseries_import.csv"
results = np.genfromtxt(
    data_path, delimiter=",", encoding=None, dtype=None, names=True, case_sensitive="lower"
)
inputs = np.genfromtxt(
    import_data_path, delimiter=",", encoding=None, dtype=None, names=True, case_sensitive="lower"
)

# Get times as datetime objects
times = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in results["time"]]

# Generate Plot
fig, axarr = plt.subplots(4, sharex=True)
axarr[0].set_title("Simple Pumped Hydropower System")

# Subplot 1
axarr[0].set_ylabel("Power [W]")
axarr[0].plot(
    times, results["turbinepower"], label="Upper reservoir turbine", linewidth=1, color="b"
)
axarr[0].plot(times, results["pumppower"], label="Upper reservoir pumping", linewidth=1, color="g")
axarr[0].plot(
    times, results["reservoirpower"], label="Lower reservoir turbine", linewidth=1, color="m"
)
axarr[0].plot(times, results["totalsystempower"], label="Total System", linewidth=1, color="r")
axarr[0].plot(
    times,
    inputs["target_power"],
    label="Target",
    linewidth=2,
    color="black",
    linestyle="--",
)

# Subplot 2
axarr[1].set_ylabel(r"Reservoir Volume ($m^3$)")
axarr[1].plot(times, results["v_upperbasin"], label="Upper reservoir", linewidth=1, color="b")
axarr[1].plot(times, results["v_lowerbasin"], label="Lower reservoir", linewidth=1, color="g")

# Subplot 3
axarr[2].set_ylabel(r"Revenue ($)")
axarr[2].plot(times, results["totalsystemrevenue"], label="Total System", linewidth=1, color="b")
axarr[2].plot(
    times, results["systemgeneratingrevenue"], label="System Generating", linewidth=1, color="g"
)

# Subplot 4
axarr[3].set_ylabel(r"Energy price ($/W)")
axarr[3].plot(times, inputs["cost_perp"], label="Price signal", linewidth=1, color="b")

# Format bottom axis label
axarr[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
axarr[-1].set_xlabel(r"Time")

# Shrink margins
fig.tight_layout()

# Shrink each axis and put a legend to the right of the axis
for i in range(len(axarr)):
    box = axarr[i].get_position()
    axarr[i].set_position([box.x0, box.y0, box.width * 0.8, box.height])
    axarr[i].legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)

plt.autoscale(enable=True, axis="x", tight=True)

# Output Plot
plt.show()
