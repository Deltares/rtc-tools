from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Map output_dir
output_dir = Path("../../../examples/channel_pulse/reference_output/").resolve()

# Import Data
rtc_tools_record = np.genfromtxt(
    output_dir / "timeseries_export_inertial_wave.csv",
    delimiter=",",
    encoding=None,
    dtype=None,
    names=True,
    case_sensitive="lower",
)
rtc_tools_semi_impl_record = np.genfromtxt(
    output_dir / "timeseries_export_inertial_wave_semi_implicit.csv",
    delimiter=",",
    encoding=None,
    dtype=None,
    names=True,
    case_sensitive="lower",
)
rtc_tools_conv_acc_record = np.genfromtxt(
    output_dir / "timeseries_export_saint_venant.csv",
    delimiter=",",
    encoding=None,
    dtype=None,
    names=True,
    case_sensitive="lower",
)
rtc_tools_conv_acc_upwind_record = np.genfromtxt(
    output_dir / "timeseries_export_saint_venant_upwind.csv",
    delimiter=",",
    encoding=None,
    dtype=None,
    names=True,
    case_sensitive="lower",
)
hec_ras_record = np.genfromtxt(
    output_dir / "HEC-RAS_export.csv",
    delimiter=",",
    encoding=None,
    dtype=None,
    names=True,
    case_sensitive="lower",
)

# Get times as datetime objects
times = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in rtc_tools_record["time"]]

# Generate Plot
n_subplots = 2
fig, axarr = plt.subplots(n_subplots, sharex=True, figsize=(8, 4 * n_subplots))
axarr[0].set_title("Water Levels and Flow Rates")

# Upper subplot
axarr[0].set_ylabel("Flow Rate [m³/s]")
axarr[0].plot(
    times,
    rtc_tools_record["channel_q_up"],
    label="Upstream",
    color="xkcd:dark sky blue",
)
axarr[0].plot(
    times,
    rtc_tools_record["channel_q_dn"],
    label="Downstream\n(RTC-Tools Inertial Wave)",
    linestyle="--",
    color="red",
)
axarr[0].plot(
    times,
    rtc_tools_semi_impl_record["channel_q_dn"],
    label="Downstream\n(RTC-Tools Inertial Wave semi-impl.)",
    linestyle="--",
    color="pink",
)
axarr[0].plot(
    times,
    rtc_tools_conv_acc_record["channel_q_dn"],
    label="Downstream\n(RTC-Tools Saint Venant central diff.)",
    linestyle="--",
    color="darkorange",
)
axarr[0].plot(
    times,
    rtc_tools_conv_acc_upwind_record["channel_q_dn"],
    label="Downstream\n(RTC-Tools Saint Venant upwind)",
    linestyle="--",
    color="purple",
)
axarr[0].plot(
    times,
    hec_ras_record["channel_q_dn"],
    label="Downstream\n(HEC-RAS)",
    linestyle="--",
    color="darkgreen",
)

# Lower subplot
axarr[1].set_ylabel("Water Level [m]")
axarr[1].plot(
    times,
    rtc_tools_record["channel_h_up"],
    label="Upstream\n(RTC-Tools Inertial Wave)",
    linestyle="--",
    color="red",
)
axarr[1].plot(
    times,
    rtc_tools_semi_impl_record["channel_h_up"],
    label="Upstream\n(RTC-Tools Inertial Wave semi-impl.)",
    linestyle="--",
    color="pink",
)
axarr[1].plot(
    times,
    rtc_tools_conv_acc_record["channel_h_up"],
    label="Upstream\n(RTC-Tools Saint Venant central diff.)",
    linestyle="--",
    color="darkorange",
)
axarr[1].plot(
    times,
    rtc_tools_conv_acc_upwind_record["channel_h_up"],
    label="Upstream\n(RTC-Tools Saint Venant upwind)",
    linestyle="--",
    color="purple",
)
axarr[1].plot(
    times,
    hec_ras_record["channel_h_up"],
    label="Upstream\n(HEC-RAS)",
    linestyle="--",
    color="darkgreen",
)
axarr[1].plot(
    times,
    rtc_tools_record["channel_h_dn"],
    label="Downstream",
    color="xkcd:dark sky blue",
)

# Format bottom axis label
axarr[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

# Shrink margins
fig.tight_layout()

# Shrink each axis by 20% and put a legend to the right of the axis
for i in range(n_subplots):
    box = axarr[i].get_position()
    axarr[i].set_position([box.x0, box.y0, box.width * 0.65, box.height])
    axarr[i].legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False, prop={"size": 8})

plt.autoscale(enable=True, axis="x", tight=True)

# Output Plot
plt.show()
