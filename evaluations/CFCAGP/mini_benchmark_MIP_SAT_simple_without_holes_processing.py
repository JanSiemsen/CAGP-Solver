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

data_set_2 = read_as_pandas(
    "benchmarks/mini_benchmark_MIP_without_holes_cf",
    lambda instance: {
        "instance_name": instance["parameters"]["args"]["metadata"]["instance_name"],
        "vertices": int(instance["parameters"]["args"]["metadata"]["vertices"]),
        "holes": instance["parameters"]["args"]["metadata"]["holes"],
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

# Add 'solver' column to data_set and data_set_2
data_set['solver'] = 'SAT'
data_set_2['solver'] = 'MIP'

print(len(data_set))
print(len(data_set_2))

data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time'] < 600) & (data_set['vertices'] <= 300) & (data_set['witness_mode'] == 'all')]

data_set_2 = data_set_2.loc[(data_set_2['status'] == 'success') & (data_set_2['time'] < 600) & (data_set_2['vertices'] <= 300)]

print(len(data_set))
print(len(data_set_2))

combined_data_set = pd.concat([data_set, data_set_2], ignore_index=True)

data_set = combined_data_set

# Create a new column for the label (solver and version)
data_set['label'] = data_set.apply(lambda row: f"{row['solver']}", axis=1)

# Convert inf values to NaN before operating
data_set.replace([np.inf, -np.inf], np.nan, inplace=True)

# Group the data by label
grouped_data = data_set.groupby('label')

sns.set_theme(context="paper", style="whitegrid")

fig, ax = plt.subplots(figsize=(8, 4))

updated_data_set = pd.DataFrame()

# Find the overall maximum time
xmax = data_set['time'].max()

# Find the maximum number of instances solved
ymax = data_set.groupby('label').size().max()

ax.set_xlim([-5, 600])
ax.set_ylim([0, 220])

# For each group (i.e., each solver), plot a separate line
for name, group in grouped_data:
    group_sorted = group.sort_values(by="time")
    group_sorted["cumulative_count"] = range(1, len(group_sorted) + 1)
    max_count = group_sorted["cumulative_count"].max()
    # extra_row = pd.DataFrame({"time_exact": [xmax], "cumulative_count": [max_count], "label": [name]})
    extra_row = pd.DataFrame({"time": [600], "cumulative_count": [max_count], "label": [name]})
    group_sorted = pd.concat([group_sorted, extra_row])
    updated_data_set = pd.concat([updated_data_set, group_sorted])
    
# Plot the data with Seaborn
plot = sns.lineplot(x='time', y='cumulative_count', hue='label', data=updated_data_set, style='label', markers=True, dashes=False, drawstyle='steps-post', ax=ax, linewidth=2)

# Set the marker edge width for all lines
for line in plot.get_lines():
    line.set_markeredgewidth(0.1)  # Set the marker edge width to 0.2
    line.set_markersize(3)  # Set the marker size to 2

# Set the font size of the legend and its location
plot.legend(fontsize='small', loc='lower right')

ax.set(#title="Cactus Plot Comparing Algorithm Performance",
       xlabel="CPU time (seconds)", ylabel="# of instances solved")

fig.tight_layout()
# plt.show()
plt.draw()
plt.savefig("plots/benchmark_cactus_plot_runtime_MIP_SAT_without_holes_increase_ylim_cf.pdf", format="pdf", dpi=600)