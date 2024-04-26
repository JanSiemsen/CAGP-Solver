from algbench import describe, read_as_pandas, Benchmark
from matplotlib import pyplot as plt
from matplotlib.pylab import f
import pandas as pd
import seaborn as sns
import numpy as np

# describe("benchmarks/final_benchmark_MIP_SAT_CPSAT_simple_without_holes")

data_set = read_as_pandas(
    "benchmarks/final_benchmark_MIP_SAT_CPSAT_simple_without_holes",
    lambda instance: {
        "instance_name": instance["parameters"]["args"]["metadata"]["instance_name"],
        "solver": instance["parameters"]["args"]["alg_params"]["solver"],
        "model": instance["parameters"]["args"]["alg_params"]["model"],
        "guard_color_constraints_CPSAT": instance["parameters"]["args"]["alg_params"]["guard_color_constraints"],
        "solver_name": instance["result"]["solver_name"],
        "guard_color_constraints_SAT": instance["result"]["guard_color_constraints"],
        "vertices": int(instance["parameters"]["args"]["metadata"]["vertices"]),
        "holes": instance["parameters"]["args"]["metadata"]["holes"],
        "colors": instance["result"]["colors"],
        "number_of_guards": instance["result"]["number_of_guards"],
        "number_of_witnesses": instance["result"]["number_of_witnesses"],
        "number_total_witnesses": instance["parameters"]["args"]["metadata"]["number_total_witnesses"],
        "iterations": instance["result"]["iterations"],
        "status": instance["result"]["status"],
        "time": instance["runtime"],
        "time_exact": instance["result"]["time_exact"],
    },
)

# data_set = data_set.loc[(data_set['status'] == 'invalid')]

# for index, row in data_set.iterrows():
#     print(row['instance_name'])
#     break

# exit()

# data_set = data_set.loc[(data_set['status'] == 'timeout')]
# print(data_set)
# exit()

# Check if colors are the same for all instance_name
# same_colors = data_set.groupby('instance_name')['colors'].nunique().eq(1).all()

# if same_colors:
#     print("Colors are the same for all instance_name")
# else:
#     print("Colors are not the same for all instance_name")

data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time_exact'] < 600) & (data_set['vertices'] >= 100)]

# # Check if colors are the same for all instance_name
# same_colors = data_set.groupby('instance_name')['colors'].nunique().eq(1).all()

# if same_colors:
#     print("Colors are the same for all instance_name")
# else:
#     print("Colors are not the same for all instance_name")

# print(data_set)
# exit()

# Create a new column for the label (solver and version)
data_set['label'] = data_set.apply(lambda row: f"{row['solver']}" if row['solver'] == 'MIP' or row['solver'] == 'SAT' else f"{row['solver']} {row['model']}" if row['model'] == 'MIP' else f"{row['solver']} {row['model']} (version 1)" if row['guard_color_constraints_CPSAT'] == False else f"{row['solver']} {row['model']} (version 2)", axis=1)

# Convert inf values to NaN before operating
data_set.replace([np.inf, -np.inf], np.nan, inplace=True)

# Group the data by label
grouped_data = data_set.groupby('label')

sns.set_theme(context="paper", style="whitegrid")

fig, ax = plt.subplots(figsize=(8, 12))

updated_data_set = pd.DataFrame()

# Find the overall maximum time
max_time_overall = data_set['time'].max()

# For each group (i.e., each solver), plot a separate line
for name, group in grouped_data:
    group_sorted = group.sort_values(by="time")
    group_sorted["cumulative_count"] = range(1, len(group_sorted) + 1)
    max_count = group_sorted["cumulative_count"].max()
    # extra_row = pd.DataFrame({"time": [max_time_overall], "cumulative_count": [max_count], "label": [name]})
    extra_row = pd.DataFrame({"time": [600], "cumulative_count": [max_count], "label": [name]})
    group_sorted = pd.concat([group_sorted, extra_row])
    updated_data_set = pd.concat([updated_data_set, group_sorted])
    
# Plot the data with Seaborn
sns.lineplot(x='time', y='cumulative_count', hue='label', data=updated_data_set, style='label', markers=True, dashes=False, drawstyle='steps-post', ax=ax)

ax.set(#title="Cactus Plot Comparing Algorithm Performance",
       xlabel="CPU time (seconds)", ylabel="# of instances solved")

fig.tight_layout()
plt.show()
# plt.savefig("plots/minibenchmark_cactus_plot_runtime_MIP_SAT_CPSAT_without_holes.png", dpi=600)
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

# Convert the DataFrame to a LaTeX table
latex_table = pivot.to_latex()

# Print the LaTeX table to the console
print(latex_table)

#-----------------------------------------------------------------------------------------------------------------------

# Group by solver and vertices, calculate min time and count
grouped = data_set.groupby(['label', 'vertices', 'holes', 'instance_name']).agg({'time': 'min'}).reset_index()

# Find the solver with the smallest time for each instance
min_times = grouped.groupby(['vertices', 'holes', 'instance_name'])['time'].min()
grouped['min_solver'] = grouped.apply(lambda row: row['label'] if row['time'] == min_times[(row['vertices'], row['holes'], row['instance_name'])] else np.nan, axis=1)

# Count the number of instances where each solver had the smallest time
pivot = grouped.groupby(['vertices', 'holes', 'min_solver']).size().unstack(fill_value=0)

# Convert the DataFrame to a LaTeX table
latex_table = pivot.to_latex()

# Print the LaTeX table to the console
print(latex_table)

#-----------------------------------------------------------------------------------------------------------------------

# Group by solver and vertices, calculate count of instances solved
grouped = data_set.groupby(['label', 'vertices']).size().reset_index(name='count')

# Pivot the data
pivot = grouped.pivot(index='vertices', columns='label', values='count')

# Sort the multi-index
pivot.sort_index(axis=1, level=[0, 1], inplace=True)

# Flatten the multi-index back to a single index
pivot.columns = pivot.columns.get_level_values(0)

# Convert the DataFrame to a LaTeX table
latex_table = pivot.to_latex()

# Print the LaTeX table to the console
print(latex_table)