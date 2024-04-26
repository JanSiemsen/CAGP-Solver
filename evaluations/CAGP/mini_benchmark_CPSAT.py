import glob
from importlib.metadata import files
import os
import time
from CAGP_Solver import Point, PolygonWithHoles
from algbench import Benchmark
from CAGP_Solver import CAGPSolverCPSAT_MIP
from CAGP_Solver import CAGPSolverCPSAT_SAT
from CAGP_Solver import get_greedy_solution, generate_solver_input, generate_edge_clique_covers, verify_solver_solution

benchmark = Benchmark("/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/benchmarks/mini_benchmark_CPSAT_with_holes")

alg_params_to_evaluate = [
    {"model": "CPSAT_MIP", "guard_color_constraints": True},
    {"model": "CPSAT_SAT", "guard_color_constraints": False},
    {"model": "CPSAT_SAT", "guard_color_constraints": True},
]

if __name__ == "__main__":

    def load_instance_and_run(instance, metadata, alg_params):

        if alg_params["model"] == "CPSAT_MIP":
            solver = CAGPSolverCPSAT_MIP(instance[0], instance[1], instance[2], instance[3], instance[4], instance[6])
        elif alg_params["model"] == "CPSAT_SAT":
            if alg_params["guard_color_constraints"]:
                solver = CAGPSolverCPSAT_SAT(instance[0], instance[1], instance[2], instance[3], instance[4], instance[5], guard_color_constraints=True)
            else:
                solver = CAGPSolverCPSAT_SAT(instance[0], instance[1], instance[2], instance[3], instance[4], instance[5], guard_color_constraints=False)

        def eval_SAT(metadata, alg_params, _instance, _solver):
            # arguments starting with `_` are not saved.

            colors, solution, iteration, number_of_witnesses, status = _solver.solve()

            if not status == "timeout" and not verify_solver_solution(solution, _instance[5]):
                status = "invalid"
            
            return {  # the returned values are saved to the database
                "colors": colors,
                "number_of_guards": len(solution),
                "solution": solution,
                "iterations": iteration,
                "number_of_witnesses": number_of_witnesses,
                "status": status
            }

        benchmark.add(
            eval_SAT,
            metadata=metadata,
            alg_params=alg_params,
            _instance=instance, 
            _solver=solver)

    start = time.time()
    root_path = os.path.dirname(os.getcwd())

    # relative_path = 'cagp_solver/mini_benchmark/agp2009a-simplerand/*.pol'
    # print(os.path.join(root_path, relative_path))

    # for filename in glob.glob(os.path.join(root_path, relative_path)):

    #     instance_name = os.path.splitext(os.path.basename(filename))[0]
        
    #     with open(filename, "r") as file:
    #         vertices = file.readline().split()
    #         number_of_vertices = int(vertices.pop(0))
    #         linear_ring = []
    #         for i in range(0, len(vertices), 2):
    #             x = int(vertices[i].split('/')[0])/int(vertices[i].split('/')[1])
    #             y = int(vertices[i+1].split('/')[0])/int(vertices[i+1].split('/')[1])
    #             linear_ring.append(Point(x, y))
    #         poly = PolygonWithHoles(linear_ring)

    #     guards, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf, all_witnesses_cf = solver_utils.generate_solver_input(poly, guards_on_holes=True)

    #     greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)

    #     for alg_params in alg_params_to_evaluate:
    #         try:
    #             print(f"Running {alg_params['solver']} for {instance_name}")
    #             instance = (greedyColors, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC)
    #             metadata = {"instance_name": instance_name, "vertices": number_of_vertices, "holes": 0, "greedy_colors": greedyColors, "greedy_size": len(greedySolution), "number_total_witnesses": len(all_witnesses)}
    #             load_instance_and_run(instance, metadata, alg_params)
    #         except Exception as e:
    #             print(f"Error with {alg_params['solver']} for {instance_name}: {e}")

    relative_path = 'cagp_solver/benchmark_instances/mini_benchmark_instances/simple-polygons-with-holes/*.pol'

    print(os.path.join(root_path, relative_path))
    files = glob.glob(os.path.join(root_path, relative_path))
    for filename in sorted(files):
        
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

        guards, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC = generate_solver_input(poly, guards_on_holes=True)

        greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)

        edge_clique_covers = generate_edge_clique_covers(GC, greedyColors)

        for alg_params in alg_params_to_evaluate:
            try:
                print(f"Running {alg_params['model']} with {alg_params['guard_color_constraints']} for {instance_name}")
                instance = (greedyColors, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, edge_clique_covers)
                metadata = {"instance_name": instance_name, "vertices": total_vertices, "holes": num_holes, "greedy_colors": greedyColors, "greedy_size": len(greedySolution), "number_total_witnesses": len(all_witnesses)}
                load_instance_and_run(instance, metadata, alg_params)
            except Exception as e:
                print(f"Error with {alg_params['model']} and {alg_params['guard_color_constraints']} for {instance_name}: {e}")

    benchmark.compress()

    print(f"Total time: {time.time() - start}")