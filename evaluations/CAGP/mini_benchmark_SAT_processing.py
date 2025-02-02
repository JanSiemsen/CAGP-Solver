from algbench import describe, read_as_pandas, Benchmark
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

data_set = read_as_pandas(
    "benchmarks/mini_benchmark_SAT_with_holes",
    lambda instance: {
        "instance_name": instance["parameters"]["args"]["metadata"]["instance_name"],
        "solver": instance["parameters"]["args"]["alg_params"]["solver"],
        "guard_color_constraints": instance["parameters"]["args"]["alg_params"]["guard_color_constraints"],
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
        "time": instance["runtime"],
    },
)

# data_set = data_set.loc[(data_set['status'] == 'timeout') & (data_set['solver'] == 'Lingeling')]

# data_set = data_set.loc[(data_set['status'] == 'invalid')]

# for index, row in data_set.iterrows():
#     print(row['instance_name'])
#     break

# exit()

# # Check if each entry has a non-empty solution
# for index, row in data_set.iterrows():
#     solution = row['solution']
#     if solution is None or len(solution) == 0:
#         print(f"Entry {index} does not have a valid solution.")

# Group by 'instance_name' and 'guard_color_constraints', get the smallest 'time' for each group
# grouped = data_set[(data_set['solver'] == 'Cadical103')].groupby(['instance_name']).time.min().reset_index()

# Merge the grouped data with the original data to get the corresponding 'guard_color_constraints' values
# merged = pd.merge(grouped, data_set, on=['instance_name', 'time'], how='left')

# Sort by 'time' and get the largest 100
# entry = merged.nlargest(20, 'time')

# Print the entry
# print(entry)

# instances = list(dict.fromkeys(entry['instance_name'].values))
# print(len(instances))

# for i in entry['instance_name'].values:
#     fastest = data_set[(data_set['instance_name'] == i)].nsmallest(3, 'time')
#     if fastest['solver'].values[0] == 'Cadical103':
#         continue
#     print(f"Instance: {i}")
#     print(entry[(entry['instance_name'] == i)][['solver', 'guard_color_constraints', 'time']].nsmallest(1, 'time'))
#     print(fastest[['solver', 'guard_color_constraints', 'time']])

# exit()

data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time'] < 600)]

# Create a new column for the label (solver and version)
data_set['label'] = data_set.apply(lambda row: f"{row['solver']} (version 1)" if row['guard_color_constraints'] == False else f"{row['solver']} (version 2)", axis=1)

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

ax.set_xlim([-1, 600])
ax.set_ylim([0, 160])

# For each group (i.e., each solver), plot a separate line
for name, group in grouped_data:
    group_sorted = group.sort_values(by="time")
    group_sorted["cumulative_count"] = range(1, len(group_sorted) + 1)
    max_count = group_sorted["cumulative_count"].max()
    extra_row = pd.DataFrame({"time": [600], "cumulative_count": [max_count], "label": [name]})
    group_sorted = pd.concat([group_sorted, extra_row])
    updated_data_set = pd.concat([updated_data_set, group_sorted])
    
# Plot the data with Seaborn
plot = sns.lineplot(x='time', y='cumulative_count', hue='label', data=updated_data_set, style='label', markers=True, dashes=False, drawstyle='steps-post', ax=ax)

# Set the marker edge width for all lines
for line in plot.get_lines():
    line.set_markeredgewidth(0.1)  # Set the marker edge width to 0.2
    line.set_markersize(2)  # Set the marker size to 2

# Set the font size of the legend and its location
plot.legend(fontsize='x-small', loc='lower right')

ax.set(#title="Cactus Plot Comparing Algorithm Performance",
       xlabel="CPU time (seconds)", ylabel="# of instances solved")

fig.tight_layout()
# plt.show()
plt.savefig("plots/minibenchmark_cactus_plot_runtime_SAT_with_holes.pdf", format="pdf", dpi=600)
exit()

#-----------------------------------------------------------------------------------------------------------------------

# Group by solver and vertices, calculate mean time and count
grouped = data_set.groupby(['label', 'vertices']).agg({'time': ['mean', 'min', 'max']})

# Reset the index
grouped.reset_index(inplace=True)

# Flatten the multi-level column index
grouped.columns = ['_'.join(col) for col in grouped.columns.ravel()]

# Rename the columns
grouped.rename(columns={'label_': 'label', 'vertices_': 'vertices'}, inplace=True)

# Round time to 2 decimal places
grouped[['time_mean', 'time_min', 'time_max']] = grouped[['time_mean', 'time_min', 'time_max']].round(2)

# Format the mean, min, and max values into a single string
grouped['time'] = grouped.apply(lambda row: f'{row["time_mean"]:.2f} ({row["time_min"]:.2f}, {row["time_max"]:.2f})', axis=1)

# Drop the mean, min, and max columns
grouped.drop(['time_mean', 'time_min', 'time_max'], axis=1, inplace=True)

# Pivot the data
pivot = grouped.pivot(index='vertices', columns='label', values='time')

# Sort the multi-index
pivot.sort_index(axis=1, level=[0, 1], inplace=True)

# Flatten the multi-index back to a single index
pivot.columns = pivot.columns.get_level_values(0)

# Filter the DataFrame for version 1 solvers
pivot_v1 = pivot.filter(like='version 1')

# Filter the DataFrame for version 2 solvers
pivot_v2 = pivot.filter(like='version 2')

# Convert the version 1 DataFrame to a LaTeX table
latex_table_v1 = pivot_v1.to_latex()

# Print the version 1 LaTeX table to the console
print(latex_table_v1)

# Convert the version 2 DataFrame to a LaTeX table
latex_table_v2 = pivot_v2.to_latex()

# Print the version 2 LaTeX table to the console
print(latex_table_v2)

#-----------------------------------------------------------------------------------------------------------------------

# Group by solver and vertices, calculate min time and count
grouped = data_set.groupby(['label', 'vertices', 'holes', 'instance_name']).agg({'time': 'min'}).reset_index()

# Find the solver with the smallest time for each instance
min_times = grouped.groupby(['vertices', 'holes', 'instance_name'])['time'].min()
grouped['min_solver'] = grouped.apply(lambda row: row['label'] if row['time'] == min_times[(row['vertices'], row['holes'], row['instance_name'])] else np.nan, axis=1)

# Count the number of instances where each solver had the smallest time
pivot = grouped.groupby(['vertices', 'holes', 'min_solver']).size().unstack(fill_value=0)

# Filter the DataFrame for version 1 solvers
pivot_v1 = pivot.filter(like='version 1')

# Filter the DataFrame for version 2 solvers
pivot_v2 = pivot.filter(like='version 2')

# Convert the version 1 DataFrame to a LaTeX table
latex_table_v1 = pivot_v1.to_latex()

# Print the version 1 LaTeX table to the console
print(latex_table_v1)

# Convert the version 2 DataFrame to a LaTeX table
latex_table_v2 = pivot_v2.to_latex()

# Print the version 2 LaTeX table to the console
print(latex_table_v2)

#-----------------------------------------------------------------------------------------------------------------------

# Group by solver and vertices, calculate count of instances solved
grouped = data_set.groupby(['label', 'vertices']).size().reset_index(name='count')
# Pivot the data
pivot = grouped.pivot(index='vertices', columns='label', values='count')
# Sort the multi-index
pivot.sort_index(axis=1, level=[0, 1], inplace=True)
# Flatten the multi-index back to a single index
pivot.columns = pivot.columns.get_level_values(0)
# Filter the DataFrame for version 1 solvers
pivot_v1 = pivot.filter(like='version 1')
# Filter the DataFrame for version 2 solvers
pivot_v2 = pivot.filter(like='version 2')
# Convert the version 1 DataFrame to a LaTeX table
latex_table_v1 = pivot_v1.to_latex()
# Print the version 1 LaTeX table to the console
print(latex_table_v1)
# Convert the version 2 DataFrame to a LaTeX table
latex_table_v2 = pivot_v2.to_latex()
# Print the version 2 LaTeX table to the console
print(latex_table_v2)

exit()

# Calculate the maximum length of the text in each column
max_col_length = max([len(str(x)) for x in pivot.columns] + [len(str(x)) for sublist in pivot.values for x in sublist] + [len(str(x)) for x in pivot.index])

# Create a new figure
fig, ax = plt.subplots(1, 1)

# Hide axes
ax.axis('off')

# cell_colors = np.array([[(1, 0, 0) if val < 30 else (0, 1, 0) for val in row] for row in pivot.values])

# Create a color matrix for the table
# cell_colors = np.array([[(1, 1, 1) for _ in range(pivot.shape[1])] for _ in range(pivot.shape[0])])

# Find the smallest 'Average runtime' in each row and color it
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
table = plt.table(cellText=pivot.values, colLabels=pivot.columns, rowLabels=pivot.index, cellLoc = 'center', loc='center')#, cellColours=cell_colors)

# Auto scale the table
table.auto_set_font_size(False)
table.set_fontsize(6)

# Calculate the maximum length of the text in each column
max_col_length = max([len(str(x)) for x in pivot.columns] + [len(str(x)) for sublist in pivot.values for x in sublist])

# Adjust the figure size based on the maximum text length
fig.set_size_inches(len(pivot.columns)*0.9, len(pivot.index)*0.9)

# Adjust the layout to minimize padding
plt.tight_layout()

# plt.savefig("plots/table_number_of_solved_instances_SAT_with_holes.png", dpi=600)
# plt.savefig("plots/table_average_runtime_SAT_with_holes.png", dpi=300)