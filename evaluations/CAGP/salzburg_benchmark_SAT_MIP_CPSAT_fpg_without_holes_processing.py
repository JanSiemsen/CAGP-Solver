from math import pi
from algbench import describe, read_as_pandas, Benchmark
from matplotlib import pyplot as plt
from matplotlib.pylab import f
import pandas as pd
import seaborn as sns
import numpy as np

data_set = read_as_pandas(
    "benchmarks/salzburg_benchmark_MIP_SAT_CPSAT_fpg_without_holes",
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
        # "time": instance["runtime"],
        "time_exact": instance["result"]["time_exact"],
    },
)

# data_set = data_set.loc[(data_set['status'] == 'invalid')]

# data_set = data_set.loc[data_set['solver'] == 'MIP']

# for index, row in data_set.iterrows():
#     print(row)

# exit()

# data_set = data_set.loc[(data_set['status'] == 'timeout')]
# print(data_set)
# exit()

data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time_exact'] < 600)]

# Check if colors are the same for all instance_name
same_colors = data_set.groupby('instance_name')['colors'].nunique().eq(1).all()

if same_colors:
    print("Colors are the same for all instance_name")
else:
    print("Colors are not the same for all instance_name")


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

#-----------------------------------------------------------------------------------------------------------------------

# Sort the data_set DataFrame by 'vertices'
data_set = data_set.sort_values('vertices')

# Pivot the data to get 'label' as columns, 'instance_name' as rows, and 'time_exact' as values
pivot_table = data_set.pivot_table(values='time_exact', index='instance_name', columns='label')

# Round 'time_exact' to two decimal places
pivot_table = pivot_table.round(2)

# Replace NaN values with '-'
pivot_table = pivot_table.fillna('-')

# Convert the numbers to strings and remove trailing zeros
pivot_table = pivot_table.astype(str).applymap(lambda x: x.rstrip('0').rstrip('.') if '.' in x else x)

# Convert the DataFrame to a LaTeX table
latex_table = pivot_table.to_latex()

# Print the LaTeX table
print(latex_table)
