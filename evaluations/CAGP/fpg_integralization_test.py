from CAGP_Solver import generate_solver_input, plot_polygon
from CAGP_Solver import get_fpg_instance
from matplotlib import pyplot as plt

instance_list = [
    "fpg-poly_0000040000",
    "fpg-poly_0000030000",
    "fpg-poly_0000020000",
    "fpg-poly_0000010000",
    "fpg-poly_0000009500",
    "fpg-poly_0000009000",
    "fpg-poly_0000008500",
    "fpg-poly_0000008000",
    "fpg-poly_0000007500",
    "fpg-poly_0000007000",
    "fpg-poly_0000006500",
    "fpg-poly_0000006000",
    "fpg-poly_0000005500",
    "fpg-poly_0000005000",
    "fpg-poly_0000004500",
    "fpg-poly_0000004000",
    "fpg-poly_0000003500",
    "fpg-poly_0000003000",
    "fpg-poly_0000002500",
    "fpg-poly_0000002000",
    "fpg-poly_0000001500",
    "fpg-poly_0000001000",
]

for inst in instance_list:
    instance = get_fpg_instance(inst)

    poly = instance.as_cgal_polygon()

    print('Generating solver input:')
    guards, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC = generate_solver_input(poly)


# fig, ax = plt.subplots()
# plot_polygon(poly, ax=ax, color="lightgrey")

# plt.show()