import glob
import multiprocessing
import os
import time
from CAGP_Solver import Point, PolygonWithHoles
from algbench import Benchmark
from CAGP_Solver import CFCAGPSolverSAT
from CAGP_Solver import generate_solver_input_cf, get_greedy_solution, verify_solver_solution_cf

benchmark = Benchmark("/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/benchmarks/final_benchmark_SAT_simple_without_holes_cf")

alg_params_to_evaluate = [
    {"witness_mode": "all"},
    {"witness_mode": "descending"},
    {"witness_mode": "ascending"},
]

if __name__ == "__main__":

    def solve_and_verify(solver_params, _instance):
        solver = CFCAGPSolverSAT(_instance[0], _instance[1], _instance[2], _instance[3], _instance[4], solver_name=solver_params["solver"])
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

        def eval_SAT(metadata, alg_params, _instance, _solver1, _solver2, _solver3, _solver4, _solver5):
            # arguments starting with `_` are not saved.

            with multiprocessing.Pool() as pool:
                results = [pool.apply_async(solve_and_verify, args=(solver_params, _instance)) for solver_params in [_solver1, _solver2, _solver3, _solver4, _solver5]]

                # Wait for any process to finish
                while True:
                    time.sleep(0.01)
                    for result in results:
                        if result.ready():
                            finished_result = result.get()
                            # Terminate all other processes
                            pool.terminate()
                            return finished_result
        
        solver1 = {"solver": "Minicard"}
        solver2 = {"solver": "Minisat22"}
        solver3 = {"solver": "Glucose3"}
        solver4 = {"solver": "Gluecard3"}
        solver5 = {"solver": "Gluecard4"}      

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

    start = time.time()
    root_path = os.path.dirname(os.getcwd())

    relative_path = 'cagp_solver/benchmark_instances/final_benchmark_instances/agp2009a-simplerand/*.pol'
    print(os.path.join(root_path, relative_path))

    files = glob.glob(os.path.join(root_path, relative_path))

    for filename in sorted(files):

        instance_name = os.path.splitext(os.path.basename(filename))[0]
        
        with open(filename, "r") as file:
            vertices = file.readline().split()
            number_of_vertices = int(vertices.pop(0))
            linear_ring = []
            for i in range(0, len(vertices), 2):
                x = int(vertices[i].split('/')[0])/int(vertices[i].split('/')[1])
                y = int(vertices[i+1].split('/')[0])/int(vertices[i+1].split('/')[1])
                linear_ring.append(Point(x, y))
            poly = PolygonWithHoles(linear_ring)

        guards, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf_desc, initial_witnesses_cf_asc, all_witnesses_cf, guard_to_witnesses, all_witnesses, GC = generate_solver_input_cf(poly, guards_on_holes=True)

        greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)

        for alg_params in alg_params_to_evaluate:
            if alg_params["witness_mode"] == "all":
                initial_witnesses = all_witnesses_cf
            elif alg_params["witness_mode"] == "descending":
                initial_witnesses = initial_witnesses_cf_desc
            elif alg_params["witness_mode"] == "ascending":
                initial_witnesses = initial_witnesses_cf_asc
            try:
                print(f"Running SAT for {instance_name} with {alg_params['witness_mode']}")
                instance = (greedyColors, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses, all_witnesses_cf)
                metadata = {"instance_name": instance_name, "vertices": number_of_vertices, "holes": 0, "greedy_colors": greedyColors, "greedy_size": len(greedySolution), "number_total_witnesses": len(all_witnesses_cf)}
                load_instance_and_run(instance, metadata, alg_params)
            except Exception as e:
                print(f"Error with SAT for {instance_name}: {e}")

    benchmark.compress()

    print(f"Total time: {time.time() - start}")