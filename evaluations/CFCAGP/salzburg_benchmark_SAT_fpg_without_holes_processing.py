from math import pi
from algbench import describe, read_as_pandas, Benchmark
from matplotlib import pyplot as plt
from matplotlib.pylab import f
import pandas as pd
import seaborn as sns
import numpy as np

data_set = read_as_pandas(
    "benchmarks/salzburg_benchmark_SAT_fpg_without_holes_cf",
    lambda instance: {
        "instance_name": instance["parameters"]["args"]["metadata"]["instance_name"],
        # "solver": instance["parameters"]["args"]["alg_params"]["solver"],
        # "model": instance["parameters"]["args"]["alg_params"]["model"],
        # "guard_color_constraints_CPSAT": instance["parameters"]["args"]["alg_params"]["guard_color_constraints"],
        "solver_name": instance["result"]["solver_name"],
        # "guard_color_constraints_SAT": instance["result"]["guard_color_constraints"],
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

data_set = data_set.loc[(data_set['status'] == 'success') & (data_set['time_exact'] < 600)]

# Sort the data_set DataFrame by 'vertices'
data_set = data_set.sort_values('vertices')

# Pivot the data to get 'label' as columns, 'instance_name' as rows, and 'time_exact' as values
pivot_table = data_set.pivot_table(values='time_exact', index='instance_name')

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