import pathlib
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Import Data
if "__file__" in locals():
    current_folder = pathlib.Path(__file__).parent
else:
    current_folder = pathlib.Path(".")
output_data_path = (
    current_folder / "../../../examples/integrator_delay/output/timeseries_export.csv"
)
results = np.genfromtxt(
    output_data_path, delimiter=",", encoding=None, dtype=None, names=True, case_sensitive="lower"
)
input_data_path = current_folder / "../../../examples/integrator_delay/input/timeseries_import.csv"
input_data = np.genfromtxt(
    input_data_path, delimiter=",", encoding=None, dtype=None, names=True, case_sensitive="lower"
)

# Get times as datetime objects
times = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in results["time"]]

# Generate Plot
n_subplots = 2
fig, axarr = plt.subplots(n_subplots, sharex=True, figsize=(8, 3 * n_subplots))

# Subplots
axarr[0].set_title("Fixed inflow")
axarr[1].set_title("Control inflow")
axarr[0].set_ylabel("Flow Rate [m³/s]")
axarr[1].set_ylabel("Flow Rate [m³/s]")
# add dots to clarify where the decision variables are defined:
axarr[0].scatter(times, input_data["q_in"], linewidth=1, color="g")
axarr[1].scatter(times, results["q_control"], linewidth=1, color="r")
# add horizontal lines to the left of these dots, to indicate that the value is attained over an
# entire timestep:
axarr[0].step(times, input_data["q_in"], linewidth=1, where="pre", label="Inflow", color="g")
axarr[1].step(
    times, results["q_control"], linewidth=1, where="pre", label="Control inflow", color="r"
)

# Use a subset of xticks
for i in range(n_subplots):
    axarr[i].xaxis.set_ticks(times[0::2])

# Format bottom axis label
axarr[-1].xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))

# Shrink margins
fig.tight_layout()

# Scale the plot
plt.autoscale(enable=True, axis="x", tight=True)

# Output Plot
plt.show()
