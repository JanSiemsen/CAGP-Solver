from calendar import c
import glob
import multiprocessing
import os
import time
from CAGP_Solver import Point, PolygonWithHoles
from algbench import Benchmark
from CAGP_Solver import CFCAGPSolverSAT
from CAGP_Solver import get_greedy_solution, generate_solver_input_cf, verify_solver_solution_cf

benchmark = Benchmark("/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/benchmarks/mini_benchmark_SAT_with_holes_cf")

alg_params_to_evaluate = [
    # based on pre-selection commented out slow solvers
    {"solver": "Cadical103"},
    {"solver": "Cadical153"},
    {"solver": "Glucose3"},
    {"solver": "Glucose4"},
    {"solver": "Glucose42"},
    # {"solver": "Lingeling", "guard_color_constraints": False}, # Lingeling does not support solve_limited
    # {"solver": "Lingeling", "guard_color_constraints": True},
    {"solver": "MapleChrono"},
    {"solver": "MapleCM"},
    {"solver": "Maplesat"},
    {"solver": "MergeSat3"},
    {"solver": "Minisat22"},

    # only card solvers support atMost constraints
    {"solver": "Gluecard3"},
    {"solver": "Gluecard4"},
    {"solver": "Minicard"},
]

if __name__ == "__main__":

    def load_instance_and_run(instance, metadata, alg_params):
        solver = CFCAGPSolverSAT(instance[0], instance[1], instance[2], instance[3], instance[4], solver_name=alg_params["solver"])

        def eval_SAT(metadata, alg_params, _instance, _solver: CFCAGPSolverSAT):
            # arguments starting with `_` are not saved.

            start = time.time() 
            try:
                # Define a Manager object to share data between processes
                manager = multiprocessing.Manager()
                results = manager.dict({
                    'colors': 0,
                    'solution': [],
                    'iteration': 0,
                    'number_of_witnesses': 0,
                    'status': "timeout",
                })

                # Define the target function for the process
                def target():
                    results['colors'], results['solution'], results['iteration'], results['number_of_witnesses'], results['status'] = _solver.solve()

                # Start the process
                process = multiprocessing.Process(target=target)
                process.start()

                # Wait for the process to finish, with a timeout of 10 minutes
                process.join(timeout=601)

                # If the process is still alive, it didn't finish in time
                if process.is_alive():
                    process.terminate()
                    process.join()
                    raise TimeoutError
            except Exception as e:
                print(f"Timeout with {alg_params['solver']} for {metadata['instance_name']}: {e}")

            end = time.time()
            _solver.__del__()

            if not results['status'] == "timeout" and not verify_solver_solution_cf(results['solution'], _instance[2]):
                results['status'] = "invalid"
            
            return {  # the returned values are saved to the database
                "colors": results['colors'],
                "number_of_guards": len(results['solution']),
                "solution": results['solution'],
                "iterations": results['iteration'],
                "number_of_witnesses": results['number_of_witnesses'],
                "status": results['status'],
                "time_exact": end - start,
            }

        benchmark.add(
            eval_SAT,
            metadata=metadata,
            alg_params=alg_params,
            _instance=instance, 
            _solver=solver)

    start = time.time()
    root_path = os.path.dirname(os.getcwd())

    relative_path = 'cagp_solver/benchmark_instances/mini_benchmark_instances_cf/simple-polygons-with-holes/*.pol'

    files = glob.glob(os.path.join(root_path, relative_path))
    i = 0
    for filename in sorted(files):
        if i < 43:
            i += 1
            continue
        
        instance_name = os.path.splitext(os.path.basename(filename))[0]

        total_vertices = 0
        with open(filename, "r") as file:
            vertices = file.readline().split()
            linear_rings = []
            num_points = int(vertices.pop(0))
            total_vertices += num_points
            linear_ring = []
            for _ in range(num_points):
                x_str = vertices.pop(0).split('/')
                x = int(x_str[0])/int(x_str[1])
                y_str = vertices.pop(0).split('/')
                y = int(y_str[0])/int(y_str[1])
                linear_ring.append(Point(x, y))
            linear_rings.append(linear_ring)  # Add outer boundary to linear_rings
            num_holes = int(vertices.pop(0))  # Get the number of holes
            for _ in range(num_holes):  # Repeat the process for each hole
                num_points = int(vertices.pop(0))
                total_vertices += num_points
                linear_ring = []
                for _ in range(num_points):
                    x_str = vertices.pop(0).split('/')
                    x = int(x_str[0])/int(x_str[1])
                    y_str = vertices.pop(0).split('/')
                    y = int(y_str[0])/int(y_str[1])
                    linear_ring.append(Point(x, y))
                linear_rings.append(linear_ring)  # Add hole to linear_rings
            poly = PolygonWithHoles(linear_rings[0], linear_rings[1:])

        guards, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf_desc, initial_witnesses_cf_asc, all_witnesses_cf, guard_to_witnesses, all_witnesses, GC = generate_solver_input_cf(poly)

        greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)

        for alg_params in alg_params_to_evaluate:
            try:
                print(f"Running {alg_params['solver']} for {instance_name}")
                instance = (greedyColors, guard_to_witnesses_cf, witness_to_guards_cf, all_witnesses_cf, all_witnesses_cf)
                metadata = {"instance_name": instance_name, "vertices": total_vertices, "holes": num_holes, "greedy_colors": greedyColors, "greedy_size": len(greedySolution), "number_total_witnesses": len(all_witnesses_cf)}
                load_instance_and_run(instance, metadata, alg_params)
            except Exception as e:
                print(f"Error with {alg_params['solver']} for {instance_name}: {e}")

    benchmark.compress()

    print(f"Total time: {time.time() - start}")