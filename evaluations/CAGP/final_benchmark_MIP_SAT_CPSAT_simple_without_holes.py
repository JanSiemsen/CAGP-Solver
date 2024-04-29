import glob
import os
import time
import concurrent.futures
from CAGP_Solver import Point, PolygonWithHoles
from algbench import Benchmark
from CAGP_Solver import CAGPSolverMIP, CAGPSolverSAT, CAGPSolverCPSAT_MIP, CAGPSolverCPSAT_SAT
from CAGP_Solver import generate_solver_input, get_greedy_solution, generate_edge_clique_covers, verify_solver_solution

benchmark = Benchmark("/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/benchmarks/final_benchmark_MIP_SAT_CPSAT_simple_without_holes")

alg_params_to_evaluate = [
    {"solver": "MIP", "model": "MIP", "guard_color_constraints": None},
    {"solver": "SAT", "model": "SAT", "guard_color_constraints": None},
    {"solver": "CPSAT", "model": "MIP", "guard_color_constraints": None},
    {"solver": "CPSAT", "model": "SAT", "guard_color_constraints": False},
    {"solver": "CPSAT", "model": "SAT", "guard_color_constraints": True},
]

if __name__ == "__main__":

    def solve_and_verify(solver_params, _instance):
        solver = CAGPSolverSAT(instance[0], instance[1], instance[2], instance[3], instance[4], instance[5], solver_name=solver_params["solver"], guard_color_constraints=solver_params["guard_color_constraints"])
        start = time.time()
        colors, solution, iteration, number_of_witnesses, status = solver.solve()
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

            with concurrent.futures.ProcessPoolExecutor() as executor:
                futures = {executor.submit(solve_and_verify, solver_params, _instance): solver_params for solver_params in [_solver1, _solver2, _solver3, _solver4, _solver5]}
                for future in concurrent.futures.as_completed(futures):
                    return future.result()  # return the result of the first solver that finishes
        
        def eval_CPSAT(metadata, alg_params, _instance, _solver):
            # arguments starting with `_` are not saved.
            
            start = time.time()
            colors, solution, iteration, number_of_witnesses, status = _solver.solve()
            end = time.time()

            if not status == "timeout" and not verify_solver_solution(solution, _instance[5]):
                status = "invalid"
            
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

        guards, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC = generate_solver_input(poly, guards_on_holes=True)

        greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)

        edge_clique_covers = generate_edge_clique_covers(GC, greedyColors)

        for alg_params in alg_params_to_evaluate:
            try:
                print(f"Running {alg_params['solver']} for {instance_name}")
                instance = (greedyColors, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, edge_clique_covers)
                metadata = {"instance_name": instance_name, "vertices": number_of_vertices, "holes": 0, "greedy_colors": greedyColors, "greedy_size": len(greedySolution), "number_total_witnesses": len(all_witnesses)}
                load_instance_and_run(instance, metadata, alg_params)
            except Exception as e:
                print(f"Error with {alg_params['solver']} for {instance_name}: {e}")

    benchmark.compress()

    print(f"Total time: {time.time() - start}")