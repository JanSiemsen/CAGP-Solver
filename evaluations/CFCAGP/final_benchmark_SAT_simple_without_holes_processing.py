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

# describe("benchmarks/final_benchmark_SAT_simple_without_holes_cf")
# exit()

# data_set = data_set.loc[data_set['instance_name'] == 'g1_simple-simple_50:200v-20h_21']
# print(data_set)
# exit()

# data_set = data_set.loc[(data_set['status'] == 'timeout')]

# data_set = data_set.loc[(data_set['status'] == 'invalid')]

# for index, row in data_set.iterrows():
#     print(row['instance_name'])
#     break

# exit()

data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time'] < 600)]

# print(data_set)
# exit()

# # Check if colors are the same for all instance_name
# same_colors = data_set.groupby('instance_name')['colors'].nunique().eq(1).all()

# if same_colors:
#     print("Colors are the same for all instance_name")
# else:
#     print("Colors are not the same for all instance_name")

# # Check if each entry has a non-empty solution
# for index, row in data_set.iterrows():
#     solution = row['solution']
#     if solution is None or len(solution) == 0:
#         print(f"Entry {index} does not have a valid solution.")
# exit()

# Convert inf values to NaN before operating
data_set.replace([np.inf, -np.inf], np.nan, inplace=True)

# # Group the data by solver
# grouped_data = data_set.groupby('witness_mode')

# sns.set_theme(context="paper", style="whitegrid")

# fig, ax = plt.subplots(figsize=(8, 4))

# updated_data_set = pd.DataFrame()

# # Find the overall maximum time
# xmax = data_set['time'].max()

# # Find the maximum number of instances solved
# ymax = data_set.groupby('witness_mode').size().max()

# ax.set_xlim([-1, xmax])
# ax.set_ylim([0, ymax])

# # For each group (i.e., each solver), plot a separate line
# for name, group in grouped_data:
#     group_sorted = group.sort_values(by="time")
#     group_sorted["cumulative_count"] = range(1, len(group_sorted) + 1)
#     max_count = group_sorted["cumulative_count"].max()
#     extra_row = pd.DataFrame({"time": [600], "cumulative_count": [max_count], "witness_mode": [name]})
#     group_sorted = pd.concat([group_sorted, extra_row])
#     updated_data_set = pd.concat([updated_data_set, group_sorted])
    
# # Plot the data with Seaborn
# plot = sns.lineplot(x='time', y='cumulative_count', hue='witness_mode', data=updated_data_set, style='witness_mode', markers=False, dashes=False, drawstyle='steps-post', ax=ax)

# # Set the marker edge width for all lines
# for line in plot.get_lines():
#     line.set_markeredgewidth(0.1)  # Set the marker edge width to 0.2
#     line.set_markersize(2)  # Set the marker size to 2

# # Set the font size of the legend and its location
# plot.legend(fontsize='x-small', loc='lower right')

# ax.set(#title="Cactus Plot Comparing Algorithm Performance",
#        xlabel="CPU time (seconds)", ylabel="# of instances solved")

# fig.tight_layout()
# # plt.show()
# plt.savefig("plots/final_cactus_plot_runtime_SAT_without_holes_cf.pdf", format="pdf", dpi=600)
# exit()

#-----------------------------------------------------------------------------------------------------------------------

# Group by solver and vertices, calculate mean time and count
grouped = data_set.groupby(['witness_mode', 'vertices']).agg({'time': ['mean', 'min', 'max']})

# Reset the index
grouped.reset_index(inplace=True)

# Flatten the multi-level column index
grouped.columns = ['_'.join(col) for col in grouped.columns.ravel()]

# Rename the columns
grouped.rename(columns={'witness_mode_': 'witness_mode', 'vertices_': 'vertices'}, inplace=True)

# Round time to 2 decimal places
grouped[['time_mean', 'time_min', 'time_max']] = grouped[['time_mean', 'time_min', 'time_max']].round(2)

# Format the mean, min, and max values into a single string
grouped['time'] = grouped.apply(lambda row: f'{row["time_mean"]:.2f} ({row["time_min"]:.2f}, {row["time_max"]:.2f})', axis=1)

# Drop the mean, min, and max columns
grouped.drop(['time_mean', 'time_min', 'time_max'], axis=1, inplace=True)

# Pivot the data
pivot = grouped.pivot(index='vertices', columns='witness_mode', values='time')

# Sort the multi-index
pivot.sort_index(axis=1, level=[0, 1], inplace=True)

# Flatten the multi-index back to a single index
pivot.columns = pivot.columns.get_level_values(0)

# Convert the DataFrame to a LaTeX table
latex_table = pivot.to_latex()

# Print the LaTeX table to the console
print(latex_table)

# # Group by solver and vertices, calculate mean time, min, max, and number of solved instances
# grouped_time = data_set.groupby(['solver', 'vertices']).agg({'time': ['mean', 'min', 'max']}).reset_index()

# # Flatten the multi-level column index
# grouped_time.columns = ['_'.join(col) for col in grouped_time.columns.ravel()]

# # Rename the columns
# grouped_time.rename(columns={'solver_': 'solver', 'vertices_': 'vertices'}, inplace=True)

# # Round time to 2 decimal places
# grouped_time[['time_mean', 'time_min', 'time_max']] = grouped_time[['time_mean', 'time_min', 'time_max']].round(2)

# # Get the number of solved instances for each solver at a specific vertices size
# grouped_solved = data_set.groupby(['solver', 'vertices']).size().reset_index(name='instances_solved')

# # Merge the two DataFrames on 'solver' and 'vertices'
# merged = pd.merge(grouped_time, grouped_solved, on=['solver', 'vertices'])

# # Replace the mean time with '600*' and the max value with '600' whenever not all instances were solved
# merged.loc[merged['instances_solved'] < 30, ['time_mean', 'time_max']] = '600*'

# # Format the mean, min, and max values into a single string
# merged['time'] = merged.apply(lambda row: f'{row["time_mean"]} ({row["time_min"]:.2f}, {row["time_max"]})', axis=1)

# # Drop the mean, min, max, and solved instances columns
# merged.drop(['time_mean', 'time_min', 'time_max', 'instances_solved'], axis=1, inplace=True)

# # Pivot the data
# pivot = merged.pivot(index='vertices', columns='solver', values='time')

# # Sort the multi-index
# pivot.sort_index(axis=1, level=[0, 1], inplace=True)

# # Flatten the multi-index back to a single index
# pivot.columns = pivot.columns.get_level_values(0)

# # Convert the DataFrame to a LaTeX table
# latex_table = pivot.to_latex()

# # Print the LaTeX table to the console
# print(latex_table)

#-----------------------------------------------------------------------------------------------------------------------

# Group by solver and vertices, calculate min time and count
grouped = data_set.groupby(['witness_mode', 'vertices', 'instance_name']).agg({'time': 'min'}).reset_index()

# Find the solver with the smallest time for each instance
min_times = grouped.groupby(['vertices', 'instance_name'])['time'].min()
grouped['min_witness_mode'] = grouped.apply(lambda row: row['witness_mode'] if row['time'] == min_times[(row['vertices'], row['instance_name'])] else np.nan, axis=1)

# Count the number of instances where each solver had the smallest time
pivot = grouped.groupby(['vertices', 'min_witness_mode']).size().unstack(fill_value=0)

# Convert the DataFrame to a LaTeX table
latex_table = pivot.to_latex()

# Print the LaTeX table to the console
print(latex_table)

#-----------------------------------------------------------------------------------------------------------------------

# Group by solver and vertices, count the number of instances
grouped = data_set.groupby(['witness_mode', 'vertices']).size().reset_index(name='instances_solved')

# Pivot the data
pivot = grouped.pivot(index='vertices', columns='witness_mode', values='instances_solved')

# Fill NaN values with 0
pivot.fillna(0, inplace=True)

# Convert the DataFrame to a LaTeX table
latex_table = pivot.to_latex()

# Print the LaTeX table to the console
print(latex_table)