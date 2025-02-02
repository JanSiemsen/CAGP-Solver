from algbench import describe, read_as_pandas, Benchmark
from matplotlib import pyplot as plt
from matplotlib.pylab import f
import pandas as pd
import seaborn as sns
import numpy as np

# describe("benchmarks/final_benchmark_MIP_SAT_CPSAT_simple_without_holes")

data_set = read_as_pandas(
    "benchmarks/final_benchmark_MIP_SAT_CPSAT_simple_with_holes",
    lambda instance: {
        "instance_name": instance["parameters"]["args"]["metadata"]["instance_name"],
        "solver": instance["parameters"]["args"]["alg_params"]["solver"],
        "model": instance["parameters"]["args"]["alg_params"]["model"],
        "guard_color_constraints_CPSAT": instance["parameters"]["args"]["alg_params"]["guard_color_constraints"],
        "solver_name": instance["result"]["solver_name"],
        "guard_color_constraints_SAT": instance["result"]["guard_color_constraints"],
        "vertices": int(instance["parameters"]["args"]["metadata"]["vertices"]),
        "holes": instance["parameters"]["args"]["metadata"]["holes"],
        "greedy_colors": instance["parameters"]["args"]["metadata"]["greedy_colors"],
        "colors": instance["result"]["colors"],
        "number_of_guards": instance["result"]["number_of_guards"],
        "number_of_witnesses": instance["result"]["number_of_witnesses"],
        "number_total_witnesses": instance["parameters"]["args"]["metadata"]["number_total_witnesses"],
        "iterations": instance["result"]["iterations"],
        "status": instance["result"]["status"],
        # "time": instance["runtime"],
        "time": instance["result"]["time_exact"],
    },
)

data_set2 = read_as_pandas(
    "benchmarks/mini_benchmark_SAT_with_holes_cf",
    lambda instance: {
        "instance_name": instance["parameters"]["args"]["metadata"]["instance_name"],
        "solver": instance["parameters"]["args"]["alg_params"]["solver"],
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
 
data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time'] < 600) & (data_set['vertices'] <= 300) & (data_set['instance_name'] != 'g1_simple-simple_75:300v-30h_24') & (data_set['instance_name'] != 'g1_simple-simple_75:300v-30h_9') & (data_set['solver'] == 'SAT')]
data_set2 = data_set2.loc[(data_set2['status'] == 'success') & (data_set2['time'] < 600) & (data_set2['vertices'] <= 300) & (data_set2['instance_name'] != 'g1_simple-simple_75:300v-30h_24') & (data_set2['instance_name'] != 'g1_simple-simple_75:300v-30h_9')]

# Keep only the first occurrence of each 'instance_name'
data_set = data_set.drop_duplicates(subset='instance_name')

data_set2 = data_set2.drop_duplicates(subset='instance_name')

# Merge the two datasets on 'instance_name'
merged_data = pd.merge(data_set, data_set2, on='instance_name', suffixes=('_1', '_2'))

# Find instances where 'greedy_colors' differ between the two datasets
differing_instances = merged_data[merged_data['greedy_colors_1'] != merged_data['greedy_colors_2']]

# Print the 'instance_name' of the instances where 'greedy_colors' differ
print(differing_instances[['instance_name', 'greedy_colors_1', 'greedy_colors_2']])

# Group the data by 'vertices' and calculate the mean of 'colors' and 'greedy_colors'
grouped_data = data_set.groupby('vertices')[['colors', 'greedy_colors']].mean()

# Round the numbers to two decimal places
grouped_data = grouped_data.round(2).astype(str)

# Remove trailing zeros
grouped_data = grouped_data.applymap(lambda x: x.rstrip('0').rstrip('.') if '.' in x else x)

# Convert the DataFrame to a LaTeX table
latex_table = grouped_data.to_latex()

# Print the LaTeX table
print(latex_table)

# Calculate the average gap between 'greedy_colors' and 'colors'
average_gap = (data_set['greedy_colors'] - data_set['colors']).mean()

# Print the average gap
print(f"The average gap between 'greedy_colors' and 'colors' is {average_gap}")


exit()

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

data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time_exact'] < 600) & (data_set['vertices'] >= 100) & (data_set['solver'] == 'SAT')]

# Group the data by 'vertices' and calculate the mean of 'colors' and 'greedy_colors'
grouped_data = data_set.groupby('vertices')[['colors', 'greedy_colors']].mean()

# Round the numbers to two decimal places
grouped_data = grouped_data.round(2).astype(str)

# Remove trailing zeros
grouped_data = grouped_data.applymap(lambda x: x.rstrip('0').rstrip('.') if '.' in x else x)

# Convert the DataFrame to a LaTeX table
latex_table = grouped_data.to_latex()

# Print the LaTeX table
print(latex_table)

# Calculate the average gap between 'greedy_colors' and 'colors'
average_gap = (data_set['greedy_colors'] - data_set['colors']).mean()

# Print the average gap
print(f"The average gap between 'greedy_colors' and 'colors' is {average_gap}")

exit()

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

fig, ax = plt.subplots(figsize=(8, 4))

updated_data_set = pd.DataFrame()

# Find the overall maximum time
xmax = data_set['time_exact'].max()

# Find the maximum number of instances solved
ymax = data_set.groupby('label').size().max()

ax.set_xlim([-1, xmax])
ax.set_ylim([0, 300])

# For each group (i.e., each solver), plot a separate line
for name, group in grouped_data:
    group_sorted = group.sort_values(by="time_exact")
    group_sorted["cumulative_count"] = range(1, len(group_sorted) + 1)
    max_count = group_sorted["cumulative_count"].max()
    # extra_row = pd.DataFrame({"time_exact": [xmax], "cumulative_count": [max_count], "label": [name]})
    # extra_row = pd.DataFrame({"time_exact": [600], "cumulative_count": [max_count], "label": [name]})
    # group_sorted = pd.concat([group_sorted, extra_row])
    updated_data_set = pd.concat([updated_data_set, group_sorted])
    
# Plot the data with Seaborn
plot = sns.lineplot(x='time_exact', y='cumulative_count', hue='label', data=updated_data_set, style='label', markers=True, dashes=False, drawstyle='steps-post', ax=ax)

# Set the marker edge width for all lines
for line in plot.get_lines():
    line.set_markeredgewidth(0.3)  # Set the marker edge width to 0.2
    line.set_markersize(3)  # Set the marker size to 2

# Set the font size of the legend and its location
plot.legend(fontsize='small', loc='lower right')

ax.set(#title="Cactus Plot Comparing Algorithm Performance",
       xlabel="CPU time (seconds)", ylabel="# of instances solved")

fig.tight_layout()
# plt.show()
plt.draw()
plt.savefig("plots/final_benchmark_cactus_plot_runtime_MIP_SAT_CPSAT_without_holes.pdf", format="pdf", dpi=600)
exit()

#-----------------------------------------------------------------------------------------------------------------------

# Group by solver and vertices, calculate mean time and count
grouped = data_set.groupby(['label', 'vertices']).agg({'time_exact': ['mean', 'min', 'max']})

# Reset the index
grouped.reset_index(inplace=True)

# Flatten the multi-level column index
grouped.columns = ['_'.join(col) for col in grouped.columns.ravel()]

# Rename the columns
grouped.rename(columns={'label_': 'label', 'vertices_': 'vertices'}, inplace=True)

# Round time to 2 decimal places
grouped[['time_exact_mean', 'time_exact_min', 'time_exact_max']] = grouped[['time_exact_mean', 'time_exact_min', 'time_exact_max']].round(2)

# Format the mean, min, and max values into a single string
grouped['time_exact'] = grouped.apply(lambda row: f'{row["time_exact_mean"]:.2f} ({row["time_exact_min"]:.2f}, {row["time_exact_max"]:.2f})', axis=1)

# Drop the mean, min, and max columns
grouped.drop(['time_exact_mean', 'time_exact_min', 'time_exact_max'], axis=1, inplace=True)

# Pivot the data
pivot = grouped.pivot(index='vertices', columns='label', values='time_exact')

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
grouped = data_set.groupby(['label', 'vertices', 'holes', 'instance_name']).agg({'time_exact': 'min'}).reset_index()

# Find the solver with the smallest time for each instance
min_times = grouped.groupby(['vertices', 'holes', 'instance_name'])['time_exact'].min()
grouped['min_solver'] = grouped.apply(lambda row: row['label'] if row['time_exact'] == min_times[(row['vertices'], row['holes'], row['instance_name'])] else np.nan, axis=1)

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