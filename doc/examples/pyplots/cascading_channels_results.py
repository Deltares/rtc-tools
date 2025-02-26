from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Import Data
data_path = "../../../examples/cascading_channels/reference_output/timeseries_export.csv"
record = np.genfromtxt(
    data_path, delimiter=",", encoding=None, dtype=None, names=True, case_sensitive="lower"
)

# Get times as datetime objects
times = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in record["time"]]

channels = "UpperChannel", "MiddleChannel", "LowerChannel"

# Generate Plot
n_subplots = 3
fig, axarr = plt.subplots(n_subplots, sharex=True, figsize=(8, 4 * n_subplots))
axarr[0].set_title("Water Levels and Flow Rates")

# Upper subplot
axarr[0].set_ylabel("Water Level [m]")
for c in channels:
    axarr[0].plot(
        times,
        record[c.lower() + "h1"],
        label=c + ".H[1]",
        linewidth=1,
        color="mediumblue",
    )
    axarr[0].plot(
        times,
        record[c.lower() + "h2"],
        label=c + ".H[2]",
        linewidth=1,
        color="mediumorchid",
    )
    axarr[0].plot(
        times,
        record[c.lower() + "h2_max"],
        label=c + ".H_max",
        linewidth=1,
        color="darkorange",
        linestyle="--",
    )
    axarr[0].plot(
        times,
        record[c.lower() + "h2_min"],
        label=c + ".H_min",
        linewidth=1,
        color="darkred",
        linestyle=":",
    )

# Middle Subplot
axarr[1].set_ylabel("Flow Rate [m³/s]")
# add dots to clarify where the decision variables are defined:
axarr[1].scatter(times, record["Inflow_Q".lower()], linewidth=1, color="mediumorchid")
# these dots were too big to be useful

# add horizontal lines to the left of these dots, to indicate that the value is attained over an
# entire timestep:
axarr[1].step(
    times,
    record["Inflow_Q".lower()],
    linewidth=2,
    where="pre",
    label="Inflow_Q",
    color="mediumorchid",
)
axarr[1].step(
    times,
    record["DrinkingWaterExtractionPump_Q_target".lower()],
    linewidth=6,
    where="pre",
    label="ExtractionPump_Q_target",
    color="lightskyblue",
)
axarr[1].step(
    times,
    record["DrinkingWaterExtractionPump_Q".lower()],
    linewidth=1,
    where="pre",
    label="ExtractionPump_Q",
    color="mediumblue",
)


axarr[1].set_ylim(bottom=0)

# Lower Subplot
axarr[2].set_ylabel("Flow Rate [m³/s]")

# the points:
axarr[2].scatter(times, record["UpperControlStructure_Q".lower()], linewidth=1, color="darkred")
axarr[2].scatter(times, record["LowerControlStructure_Q".lower()], linewidth=1, color="darkorange")
# add horizontal lines to the left of these dots, to indicate that the value is attained over an
# entire timestep:
axarr[2].step(
    times,
    record["UpperControlStructure_Q".lower()],
    linewidth=2,
    where="pre",
    label="UpperControlStructure_Q",
    color="darkred",
)
axarr[2].step(
    times,
    record["LowerControlStructure_Q".lower()],
    linewidth=1,
    where="pre",
    label="LowerControlStructure_Q",
    color="darkorange",
)

axarr[2].set_ylim(bottom=0)

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
