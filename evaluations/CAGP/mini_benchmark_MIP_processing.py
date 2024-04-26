from algbench import describe, read_as_pandas, Benchmark
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

data_set = read_as_pandas(
    "benchmarks/mini_benchmark_MIP_with_holes",
    lambda instance: {
        "instance_name": instance["parameters"]["args"]["metadata"]["instance_name"],
        "parameter_set": instance["parameters"]["args"]["alg_params"]["parameter_set"],
        "vertices": int(instance["parameters"]["args"]["metadata"]["vertices"]),
        "holes": instance["parameters"]["args"]["metadata"]["holes"],
        "colors": instance["result"]["colors"],
        "number_of_guards": instance["result"]["number_of_guards"],
        "number_of_witnesses": instance["result"]["number_of_witnesses"],
        "number_total_witnesses": instance["parameters"]["args"]["metadata"]["number_total_witnesses"],
        "iterations": instance["result"]["iterations"],
        "status": instance["result"]["status"],
        "time": instance["runtime"],
    },
)

# data_set = data_set.loc[(data_set['status'] == 'invalid')]

# for index, row in data_set.iterrows():
#     print(row['instance_name'])

# exit()

# data_set = data_set.loc[(data_set['status'] == 'timeout')]

# for index, row in data_set.iterrows():
#     print(row['instance_name'], row['parameter_set'])

# exit()

# data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time'] < 300) & (data_set['parameter_set'] == 2)]

# # Find the instance with the largest time
# max_time_instance = data_set.loc[data_set['time'].idxmax()]
# print("Instance with the largest time:")
# print(max_time_instance['instance_name'])
# print(max_time_instance['time'])
# exit()

# Convert inf values to NaN before operating
data_set.replace([np.inf, -np.inf], np.nan, inplace=True)

# Group the data by label
grouped_data = data_set.groupby('parameter_set')

sns.set_theme(context="paper", style="whitegrid")

fig, ax = plt.subplots(figsize=(15, 6))

updated_data_set = pd.DataFrame()

# For each group (i.e., each solver), plot a separate line
for name, group in grouped_data:
    group_sorted = group.sort_values(by="time")
    group_sorted["cumulative_count"] = range(1, len(group_sorted) + 1)
    max_count = group_sorted["cumulative_count"].max()
    extra_row = pd.DataFrame({"time": [600], "cumulative_count": [max_count], "model": [name]})
    group_sorted = pd.concat([group_sorted, extra_row])
    updated_data_set = pd.concat([updated_data_set, group_sorted])
    
# Plot the data with Seaborn
sns.lineplot(x='time', y='cumulative_count', hue='parameter_set', data=updated_data_set, style='parameter_set', markers=True, dashes=False, drawstyle='steps-post', ax=ax)

ax.set(title="Cactus Plot Comparing Algorithm Performance",
       xlabel="CPU time (seconds)", ylabel="# of instances solved")

fig.tight_layout()
plt.show()

exit()

# Group by solver and vertices, calculate mean time and count
grouped = data_set.groupby(['parameter_set', 'vertices']).agg({'time': 'count'}).reset_index()

# # Round time to 6 decimal places
grouped['time'] = grouped['time'].round(6)

# Pivot the data
pivot = grouped.pivot_table(index='vertices', columns='parameter_set', values='time')

# pivot = pivot.astype(int)

# Sort the multi-index
pivot.sort_index(axis=1, inplace=True)

# Calculate the maximum length of the text in each column
max_col_length = max([len(str(x)) for x in pivot.columns] + [len(str(x)) for sublist in pivot.values for x in sublist] + [len(str(x)) for x in pivot.index])

# Create a new figure
fig, ax = plt.subplots(1, 1)

# Hide axes
ax.axis('off')

cell_colors = np.array([[(1, 0, 0) if val < 30 else (0, 1, 0) for val in row] for row in pivot.values])

# # Create a color matrix for the table
# cell_colors = np.array([[(1, 1, 1) for _ in range(pivot.shape[1])] for _ in range(pivot.shape[0])])

# # Find the smallest 'Average runtime' in each row and color it
# for i, row in enumerate(pivot.values):
#     avg_runtime_cols = [j for j, col in enumerate(pivot.columns)]
#     sorted_avg_runtime_cols = sorted(avg_runtime_cols, key=lambda j: row[j])
#     if len(sorted_avg_runtime_cols) > 0:
#         cell_colors[i, sorted_avg_runtime_cols[0]] = (0, 1, 0)  # smallest, lime
# if len(sorted_avg_runtime_cols) > 1:
#     cell_colors[i, sorted_avg_runtime_cols[1]] = (1, 1, 0)  # second smallest, yellow
# if len(sorted_avg_runtime_cols) > 2:
#     cell_colors[i, sorted_avg_runtime_cols[2]] = (1, 0, 0)  # third smallest, red

# Create a table and add it to the figure
table = plt.table(cellText=pivot.values, colLabels=pivot.columns, rowLabels=pivot.index, cellLoc = 'center', loc='center', cellColours=cell_colors)

# Auto scale the table
table.auto_set_font_size(False)
table.set_fontsize(6)

# Calculate the maximum length of the text in each column
max_col_length = max([len(str(x)) for x in pivot.columns] + [len(str(x)) for sublist in pivot.values for x in sublist])

# Adjust the figure size based on the maximum text length
fig.set_size_inches(len(pivot.columns)*0.9, len(pivot.index)*0.9)

# Adjust the layout to minimize padding
plt.tight_layout()

plt.savefig("plots/instances_solved_MIP_with_holes_2.png", dpi=300)
# plt.savefig("table_average_runtime_solver.png", dpi=300)