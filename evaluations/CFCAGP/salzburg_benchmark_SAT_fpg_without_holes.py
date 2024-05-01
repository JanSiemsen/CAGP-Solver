import multiprocessing
import time
from algbench import Benchmark
from CAGP_Solver import CFCAGPSolverSAT
from CAGP_Solver import generate_solver_input_cf, get_greedy_solution, verify_solver_solution_cf, get_fpg_instance, plot_polygon
import matplotlib.pyplot as plt
import distinctipy as distcolors
from tqdm import tqdm

benchmark = Benchmark("/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/benchmarks/salzburg_benchmark_SAT_fpg_without_holes_cf")

instance_list = [
    # "fpg-poly_0000001000",
    # "fpg-poly_0000001500",
    # "fpg-poly_0000002000",
    # "fpg-poly_0000002500",
    "fpg-poly_0000003000",
    "fpg-poly_0000003500",
    "fpg-poly_0000004000",
    "fpg-poly_0000004500",
    "fpg-poly_0000005000",
    "fpg-poly_0000005500",
    "fpg-poly_0000006000",
    "fpg-poly_0000006500",
    "fpg-poly_0000007000",
    "fpg-poly_0000007500",
    "fpg-poly_0000008000",
    "fpg-poly_0000008500",
    "fpg-poly_0000009000",
    "fpg-poly_0000009500",
    "fpg-poly_0000010000",
    "fpg-poly_0000020000",
    "fpg-poly_0000030000",
    "fpg-poly_0000040000",
]

path_to_plots = "/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/plots/instances_cf/"

def plot_solution(poly, solution, colors, path):
    print('Plotting...')
    colors = distcolors.get_colors(int(colors))
    fig, ax = plt.subplots()
    # Add this line to turn off the axes
    plt.axis('off')
    plot_polygon(poly, ax=ax, color=None, facecolor='none', edgecolor='black', zorder=0, linewidth=0.1)
    progress = tqdm(solution)
    for s in solution:
        (point, visibility) = guards[s[0]]
        plot_polygon(visibility, ax=ax, color=colors[s[1]], alpha=0.3, zorder=0, linewidth=0.0)
        plt.scatter(point.x(), point.y(), color=colors[s[1]], s=3, zorder=1, edgecolors='none')
        progress.update()
    progress.close()

    fig.tight_layout()

    plt.savefig(path, format="pdf", dpi=600)


if __name__ == "__main__":

    def solve_and_verify(solver_params, _instance):
        solver = CFCAGPSolverSAT(_instance[0], _instance[1], _instance[2], _instance[3], _instance[4], solver_name=solver_params["solver"])
        start = time.time()
        try:
            colors, solution, iteration, number_of_witnesses, status = solver.solve()
        except Exception as e:
            print(f"Timeout with SAT for {metadata['instance_name']}: {e}")
            colors = 0
            solution = []
            iteration = 0
            number_of_witnesses = 0
            status = "timeout"
        end = time.time()
        solver.__del__()

        if not status == "timeout" and not verify_solver_solution_cf(solution, _instance[2]):
            status = "invalid"
        
        return {  # the returned values are saved to the database
            "solver_name": solver_params["solver"],
            "colors": colors,
            "number_of_guards": len(solution),
            "solution": solution,
            "iterations": iteration,
            "number_of_witnesses": number_of_witnesses,
            "time_exact": end - start,
            "status": status
        }

    def load_instance_and_run(instance, metadata):

        def eval_SAT(metadata, _instance, _solver1, _solver2, _solver3, _solver4, _solver5):
            # arguments starting with `_` are not saved.

            with multiprocessing.Pool() as pool:
                results = [pool.apply_async(solve_and_verify, args=(solver_params, _instance[:5])) for solver_params in [_solver1, _solver2, _solver3, _solver4, _solver5]]

                # Wait for any process to finish
                while True:
                    time.sleep(0.01)
                    for result in results:
                        if result.ready():
                            finished_result = result.get()
                            # Terminate all other processes
                            pool.terminate()
                            if finished_result['status'] == "success" and finished_result['time_exact'] < 600:
                                plot_solution(_instance[5], finished_result['solution'], finished_result['colors'], f"{path_to_plots}{metadata['instance_name']}_SAT_cf.pdf")
                            return finished_result
        
        solver1 = {"solver": "Minicard"}
        solver2 = {"solver": "Minisat22"}
        solver3 = {"solver": "Glucose3"}
        solver4 = {"solver": "Gluecard3"}
        solver5 = {"solver": "Gluecard4"}      

        benchmark.add(
        eval_SAT,
        metadata=metadata,
        _instance=instance, 
        _solver1=solver1,
        _solver2=solver2,
        _solver3=solver3,
        _solver4=solver4,
        _solver5=solver5)

    start = time.time()
    for instance_name in instance_list:

        processing_start = time.time()

        instance = get_fpg_instance(instance_name)
        poly = instance.as_cgal_polygon()

        guards, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf_desc, initial_witnesses_cf_asc, all_witnesses_cf, guard_to_witnesses, all_witnesses, GC = generate_solver_input_cf(poly, guards_on_holes=True)

        greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)

        print(f"Processing {instance_name} took {time.time() - processing_start}")

        try:
            print(f"Running SAT for {instance_name}")
            instance = (greedyColors, guard_to_witnesses_cf, witness_to_guards_cf, all_witnesses_cf, all_witnesses_cf, poly)
            metadata = {"instance_name": instance_name, "vertices": len(GC.node_indices()), "holes": 0, "greedy_colors": greedyColors, "greedy_size": len(greedySolution), "number_total_witnesses": len(all_witnesses_cf)}
            load_instance_and_run(instance, metadata)
        except Exception as e:
            print(f"Error with SAT for {instance_name}: {e}")

    benchmark.compress()

    print(f"Total time: {time.time() - start}")