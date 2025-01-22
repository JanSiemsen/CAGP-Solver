from math import e
from algbench import describe, read_as_pandas, Benchmark
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

data_set = read_as_pandas(
    "benchmarks/final_benchmark_SAT_simple_without_holes_cf",
    lambda instance: {
        "instance_name": instance["parameters"]["args"]["metadata"]["instance_name"],
        "witness_mode": instance["parameters"]["args"]["alg_params"]["witness_mode"],
        "vertices": int(instance["parameters"]["args"]["metadata"]["vertices"]),
        "holes": instance["parameters"]["args"]["metadata"]["holes"],
        "greedy_colors": instance["parameters"]["args"]["metadata"]["greedy_colors"],
        "colors": instance["result"]["colors"],
        "solution": instance["result"]["solution"],
        "number_of_guards": instance["result"]["number_of_guards"],
        "number_of_witnesses": instance["result"]["number_of_witnesses"],
        "number_total_witnesses": instance["parameters"]["args"]["metadata"]["number_total_witnesses"],
        "iterations": instance["result"]["iterations"],
        "status": instance["result"]["status"],
        "time": instance["result"]["time_exact"],
    },
)

data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time'] < 600) & (data_set['vertices'] >= 100) & (data_set['witness_mode'] == 'all')]

# Convert inf values to NaN before operating
data_set.replace([np.inf, -np.inf], np.nan, inplace=True)

sns.set_theme(context="paper", style="whitegrid")

fig, ax = plt.subplots(figsize=(8, 4))

updated_data_set = pd.DataFrame()

group_sorted = data_set.sort_values(by="time")
group_sorted["cumulative_count"] = range(1, len(group_sorted) + 1)
max_count = group_sorted["cumulative_count"].max()
extra_row = pd.DataFrame({"time": [610], "cumulative_count": [max_count]})
group_sorted = pd.concat([group_sorted, extra_row])
updated_data_set = pd.concat([updated_data_set, group_sorted])

# Find the overall maximum time
xmax = data_set['time'].max()

# Find the maximum number of instances solved
ymax = data_set.groupby('witness_mode').size().max()

ax.set_xlim([-0.1, xmax])
ax.set_ylim([0, ymax])
    
# Plot the data with Seaborn
plot = sns.lineplot(x='time', y='cumulative_count', data=updated_data_set, marker='o', dashes=False, drawstyle='steps-post', ax=ax, label='SAT')

# Set the marker edge width for all lines
for line in plot.get_lines():
    line.set_markeredgewidth(0.2)  # Set the marker edge width to 0.2
    line.set_markersize(3)  # Set the marker size to 2

# Set the font size of the legend and its location
plot.legend(fontsize='x-small', loc='lower right')

ax.set(#title="Cactus Plot Comparing Algorithm Performance",
       xlabel="CPU time (seconds)", ylabel="# of instances solved")

fig.tight_layout()
# plt.show()
plt.savefig("plots/benchmark_cactus_plot_runtime_SAT_without_holes_only_all_cf.pdf", format="pdf", dpi=600)

fig, ax = plt.subplots(figsize=(8, 4))
scatter_plot = sns.scatterplot(x='vertices', y='time', data=data_set, ax=ax)

ax.set(xlabel="# of vertices", ylabel="CPU time (seconds)")
fig.tight_layout()

plt.savefig("plots/benchmark_scatter_plot_runtime_vs_vertices_SAT_without_holes_only_all_cf.pdf", format="pdf", dpi=600)

# Create a line plot for vertices vs. time
fig, ax = plt.subplots(figsize=(8, 4))
line_plot = sns.lineplot(x='vertices', y='time', data=data_set, ax=ax, marker='o')

ax.set(xlabel="# of vertices", ylabel="CPU time (seconds)")
fig.tight_layout()

plt.savefig("plots/benchmark_line_plot_runtime_vs_vertices_SAT_without_holes_only_all_cf.pdf", format="pdf", dpi=600)