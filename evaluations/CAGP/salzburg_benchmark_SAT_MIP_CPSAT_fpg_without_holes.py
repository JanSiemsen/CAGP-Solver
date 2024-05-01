import multiprocessing
import time
from algbench import Benchmark
from CAGP_Solver import CAGPSolverMIP, CAGPSolverSAT, CAGPSolverCPSAT_MIP, CAGPSolverCPSAT_SAT
from CAGP_Solver import generate_solver_input, get_greedy_solution, generate_edge_clique_covers, verify_solver_solution, get_fpg_instance, plot_polygon
import matplotlib.pyplot as plt
import distinctipy as distcolors
from tqdm import tqdm

benchmark = Benchmark("/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/benchmarks/salzburg_benchmark_MIP_SAT_CPSAT_fpg_without_holes")

alg_params_to_evaluate = [
    {"solver": "MIP", "model": "MIP", "guard_color_constraints": None},
    # {"solver": "SAT", "model": "SAT", "guard_color_constraints": None},
    {"solver": "CPSAT", "model": "MIP", "guard_color_constraints": None},
    # {"solver": "CPSAT", "model": "SAT", "guard_color_constraints": False},
    # {"solver": "CPSAT", "model": "SAT", "guard_color_constraints": True},
]

instance_list = [
#     "fpg-poly_0000040000",
#     "fpg-poly_0000030000",
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

# instance_list = [
    # "fpg-poly_0000001000",
    # "fpg-poly_0000001500",
    # "fpg-poly_0000002000",
    # "fpg-poly_0000002500",
    # "fpg-poly_0000003000",
    # "fpg-poly_0000003500",
    # "fpg-poly_0000004000",
    # "fpg-poly_0000004500",
    # "fpg-poly_0000005000",
    # "fpg-poly_0000005500",
    # "fpg-poly_0000006000",
    # "fpg-poly_0000006500",
    # "fpg-poly_0000007000",
    # "fpg-poly_0000007500",
    # "fpg-poly_0000008000",
    # "fpg-poly_0000008500",
    # "fpg-poly_0000009000",
    # "fpg-poly_0000009500",
    # "fpg-poly_0000010000",
    # "fpg-poly_0000020000",
    # "fpg-poly_0000030000",
    # "fpg-poly_0000040000",
# ]

path_to_plots = "/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/plots/instances/"

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
        solver = CAGPSolverSAT(instance[0], instance[1], instance[2], instance[3], instance[4], instance[5], solver_name=solver_params["solver"], guard_color_constraints=solver_params["guard_color_constraints"])
        start = time.time()
        try:
            colors, solution, iteration, number_of_witnesses, status = solver.solve()
        except Exception as e:
            print(f"Timeout with {alg_params['solver']} for {metadata['instance_name']}: {e}")
            colors = 0
            solution = []
            iteration = 0
            number_of_witnesses = 0
            status = "timeout"
        end = time.time()
        solver.__del__()

        if not status == "timeout" and not verify_solver_solution(solution, _instance[5]):
            status = "invalid"
        
        return {  # the returned values are saved to the database
            "solver_name": solver_params["solver"],
            "guard_color_constraints": solver_params["guard_color_constraints"],
            "colors": colors,
            "number_of_guards": len(solution),
            "solution": solution,
            "iterations": iteration,
            "number_of_witnesses": number_of_witnesses,
            "time_exact": end - start,
            "status": status
        }

    def load_instance_and_run(instance, metadata, alg_params):

        def eval_MIP(metadata, alg_params, _instance, _solver):
            # arguments starting with `_` are not saved.

            start = time.time()
            colors, solution, iteration, number_of_witnesses, status = _solver.solve()
            end = time.time()

            if not status == "timeout" and not verify_solver_solution(solution, _instance[5]):
                status = "invalid"

            if status == "success" and (end - start) < 600:
                plot_solution(_instance[7], solution, colors, f"{path_to_plots}{metadata['instance_name']}_MIP.pdf")
            
            return {  # the returned values are saved to the database
                "solver_name": None,
                "guard_color_constraints": None,
                "colors": colors,
                "number_of_guards": len(solution),
                "solution": solution,
                "iterations": iteration,
                "number_of_witnesses": number_of_witnesses,
                "time_exact": end - start,
                "status": status
            }

        def eval_SAT(metadata, alg_params, _instance, _solver1, _solver2, _solver3, _solver4, _solver5):
            # arguments starting with `_` are not saved.

            with multiprocessing.Pool() as pool:
                results = [pool.apply_async(solve_and_verify, args=(solver_params, _instance[:6])) for solver_params in [_solver1, _solver2, _solver3, _solver4, _solver5]]

                # Wait for any process to finish
                while True:
                    time.sleep(0.01)
                    for result in results:
                        if result.ready():
                            finished_result = result.get()
                            # Terminate all other processes
                            pool.terminate()
                            if finished_result['status'] == "success" and finished_result['time_exact'] < 600:
                                plot_solution(_instance[7], finished_result['solution'], finished_result['colors'], f"{path_to_plots}{metadata['instance_name']}_SAT.pdf")
                            return finished_result
                
        def eval_CPSAT(metadata, alg_params, _instance, _solver):
            # arguments starting with `_` are not saved.
            
            start = time.time()
            colors, solution, iteration, number_of_witnesses, status = _solver.solve()
            end = time.time()

            if not status == "timeout" and not verify_solver_solution(solution, _instance[5]):
                status = "invalid"

            if status == "success" and (end - start) < 600:
                plot_solution(_instance[7], solution, colors, f"{path_to_plots}{metadata['instance_name']}_CPSAT_{alg_params['model']}_{alg_params['guard_color_constraints']}.pdf")
            
            return {  # the returned values are saved to the database
                "solver_name": None,
                "guard_color_constraints": None,
                "colors": colors,
                "number_of_guards": len(solution),
                "solution": solution,
                "iterations": iteration,
                "number_of_witnesses": number_of_witnesses,
                "time_exact": end - start,
                "status": status
            }
        
        if alg_params["solver"] == "MIP":
            solver = CAGPSolverMIP(instance[0], instance[1], instance[2], instance[3], instance[4], instance[6])

            benchmark.add(
            eval_MIP,
            metadata=metadata,
            alg_params=alg_params,
            _instance=instance, 
            _solver=solver)

        elif alg_params["solver"] == "SAT":
            solver1 = {"solver": "Cadical103", "guard_color_constraints": False}
            solver2 = {"solver": "Cadical103", "guard_color_constraints": True}
            solver3 = {"solver": "Glucose42", "guard_color_constraints": False}
            solver4 = {"solver": "Glucose42", "guard_color_constraints": True}
            solver5 = {"solver": "Glucose4", "guard_color_constraints": True}      

            benchmark.add(
            eval_SAT,
            metadata=metadata,
            alg_params=alg_params,
            _instance=instance, 
            _solver1=solver1,
            _solver2=solver2,
            _solver3=solver3,
            _solver4=solver4,
            _solver5=solver5)

        elif alg_params["solver"] == "CPSAT":
            if alg_params["model"] == "MIP":
                solver = CAGPSolverCPSAT_MIP(instance[0], instance[1], instance[2], instance[3], instance[4], instance[6])
            elif alg_params["model"] == "SAT":
                if alg_params["guard_color_constraints"]:
                    solver = CAGPSolverCPSAT_SAT(instance[0], instance[1], instance[2], instance[3], instance[4], instance[5], guard_color_constraints=True)
                else:
                    solver = CAGPSolverCPSAT_SAT(instance[0], instance[1], instance[2], instance[3], instance[4], instance[5], guard_color_constraints=False)

            benchmark.add(
            eval_CPSAT,
            metadata=metadata,
            alg_params=alg_params,
            _instance=instance, 
            _solver=solver)

    start = time.time()
    for instance_name in instance_list:

        processing_start = time.time()

        instance = get_fpg_instance(instance_name)
        poly = instance.as_cgal_polygon()

        guards, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC = generate_solver_input(poly)

        greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)

        edge_clique_covers = generate_edge_clique_covers(GC, greedyColors)
        # edge_clique_covers = None

        print(f"Processing {instance_name} took {time.time() - processing_start}")

        for alg_params in alg_params_to_evaluate:
            try:
                print(f"Running {alg_params['solver']} for {instance_name}")
                instance = (greedyColors, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, edge_clique_covers, poly)
                metadata = {"instance_name": instance_name, "vertices": len(GC.node_indices()), "holes": 0, "greedy_colors": greedyColors, "greedy_size": len(greedySolution), "number_total_witnesses": len(all_witnesses)}
                load_instance_and_run(instance, metadata, alg_params)
            except Exception as e:
                print(f"Error with {alg_params['solver']} for {instance_name}: {e}")

    benchmark.compress()

    print(f"Total time: {time.time() - start}")