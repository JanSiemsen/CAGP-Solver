import glob
import os
import time
from CAGP_Solver import Point, PolygonWithHoles
from algbench import Benchmark
from CAGP_Solver import CFCAGPSolverMIP
from CAGP_Solver import generate_solver_input_cf, get_greedy_solution, verify_solver_solution_cf

benchmark = Benchmark("/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/benchmarks/mini_benchmark_MIP_without_holes_cf")

if __name__ == "__main__":

    def load_instance_and_run(instance, metadata):

        def eval_MIP(metadata, _instance, _solver):
            # arguments starting with `_` are not saved.

            start = time.time()
            colors, solution, iteration, number_of_witnesses, status = _solver.solve()
            end = time.time()

            if not status == "timeout" and not verify_solver_solution_cf(solution, instance[2]):
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
        
        
        solver = CFCAGPSolverMIP(instance[0], instance[1], instance[2], instance[3], instance[4])

        benchmark.add(
        eval_MIP,
        metadata=metadata,
        _instance=instance, 
        _solver=solver)


    start = time.time()
    root_path = os.path.dirname(os.getcwd())

    relative_path = 'cagp_solver/benchmark_instances/mini_benchmark_instances_cf/agp2009a-simplerand/*.pol'
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

        guards, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf_desc, initial_witnesses_cf_asc, all_witnesses_cf, guard_to_witnesses, all_witnesses, GC = generate_solver_input_cf(poly)

        greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)

        try:
            print(f"Running MIP for {instance_name}")
            instance = (greedyColors, guard_to_witnesses, witness_to_guards_cf, all_witnesses_cf, all_witnesses_cf)
            metadata = {"instance_name": instance_name, "vertices": number_of_vertices, "holes": 0, "greedy_colors": greedyColors, "greedy_size": len(greedySolution), "number_total_witnesses": len(all_witnesses)}
            load_instance_and_run(instance, metadata)
        except Exception as e:
            print(f"Error with MIP for {instance_name}: {e}")

    benchmark.compress()

    print(f"Total time: {time.time() - start}")