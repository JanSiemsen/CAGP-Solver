from colorama import init
import gurobipy as grb
import rustworkx as rx
from pyvispoly import Point, PolygonWithHoles, Arrangement, Arr_PointLocation, plot_polygon
import matplotlib.pyplot as plt

# This version of the solver takes in a precomputed visibility and covering graph to create its constraints
# New witnesses are added whenever an optimal solution is found
class CFCAGPSolverMIP:

    def __init__(self, K: int, poly: PolygonWithHoles, guard_to_witnesses: dict[int, set[int]], initial_witnesses: list[int], all_witnesses: set[int], G: rx.PyGraph, solution: list[list[int]]=None) -> list[tuple[int, int]]:
        self.G = G
        self.K = K
        self.poly = poly
        self.guard_to_witnesses = guard_to_witnesses
        self.initial_witnesses = initial_witnesses
        self.all_witnesses = all_witnesses
        self.M = len(self.guard_to_witnesses)
        self.model = grb.Model()
        # self.model.Params.MemLimit = 16

        self.__make_vars()
        self.__add_guard_coloring_constraints()
        self.__add_color_constraints()
        self.__add_unique_color_constraints()
        self.__add_color_symmetry_constraints()
        self.__add_guard_symmetry_constraints()
        self.__set_objective()

        # if solution:
        #     self.__provide_init_solution(solution)
        
    def __make_vars(self):
        self.color_vars = dict()
        self.guard_vars = dict()
        self.witness_color_vars = dict()

        for color in range(self.K):
            self.color_vars[color] = self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY)

        for guard in self.guard_to_witnesses.keys():
            for color in range(self.K):
                self.guard_vars[guard, color] = self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY)

        for witness in self.initial_witnesses:        
            for color in range(self.K):
                self.witness_color_vars[witness, color] = self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY)

    def __add_guard_coloring_constraints(self):
        for guard in self.guard_to_witnesses.keys():
            # Ensure that each guard is only assigned one color
            self.model.addConstr(sum(self.guard_vars[guard, color] for color in range(self.K)) <= 1)

    def __add_color_constraints(self):
        for color in range(self.K):
            # Ensure that a color is only used if there is a guard of that color
            self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.guard_to_witnesses.keys()) >= self.color_vars[color])
            self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.guard_to_witnesses.keys()) <= self.M * self.color_vars[color])

    def __add_unique_color_constraints(self):
        for witness in self.initial_witnesses:
            for color in range(self.K):
                # If a witness_color_var is true, there is exactly one guard of that color
                self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.G.neighbors(witness)) >= self.witness_color_vars[witness, color])
                self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.G.neighbors(witness)) <= 1 + self.M * (1 - self.witness_color_vars[witness, color]))
                
            # Ensure that each witness is covered by at least one guard with a unique color
            self.model.addConstr(sum(self.witness_color_vars[witness, color] for color in range(self.K)) >= 1)

    def __add_color_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.addConstr(0 <= self.color_vars[k] - self.color_vars[k + 1])

    def __add_guard_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.addConstr(0 <= sum(self.guard_vars[x] if x[1] == k else 0 for x in self.guard_vars.keys())
                                            - sum(self.guard_vars[x] if x[1] == k + 1 else 0 for x in self.guard_vars.keys()))

    def __set_objective(self):
        self.model.setObjective(sum(self.color_vars[color] for color in range(self.K)), grb.GRB.MINIMIZE)

    def __check_coverage(self):
        solution = [guard for (guard, color), variable in self.guard_vars.items() if variable.x >= 0.5]
        solution = list(set(solution))

        covered_witnesses = set()
        for guard in solution:
            covered_witnesses = covered_witnesses.union(self.guard_to_witnesses[guard])

        missing_witnesses = self.all_witnesses.difference(covered_witnesses)
        
        return missing_witnesses

    # not used
    def __callback_integral(self, model, guard_vars):
        print('Checking coverage...')
        missing_witnesses = self.__check_coverage(model, guard_vars)

        if(missing_witnesses):
            print('Adding new witnesses...')
            for witness in missing_witnesses:
                subset = []
                for guard, witness_set in self.guard_to_witnesses.items():
                    if witness_set.contains(witness):
                        for k in range(self.K):
                            subset.append((guard, k))
                # TODO: add constraints for new witness and new variables which is not possible during solving time for gurobi
                self.lazy_witnesses += 1
            self.iteration += 1

    # not used
    def __callback_fractional(self, model, varmap):
        # Nothing is being done here yet.
        pass
    
    # not used
    def callback(self, where, model, varmap):
        if where == grb.GRB.Callback.MIPSOL:
            # we have an integral solution (potentially valid solution)
            self.__callback_integral(model, varmap)
        elif where == grb.GRB.Callback.MIPNODE and \
                model.cbGet(grb.GRB.Callback.MIPNODE_STATUS) == grb.GRB.OPTIMAL:
            # we have a fractional solution
            # (intermediate solution with fractional values for all booleans)
            self.__callback_fractional(model, varmap)

    def solve(self):
        self.iteration = 0
        self.lazy_witnesses = 0
        self.model.optimize()
        if self.model.status != grb.GRB.OPTIMAL:
            raise RuntimeError("Unexpected status after optimization!")
        
        missing_witnesses = self.__check_coverage()

        while(missing_witnesses):
            self.iteration += 1

            print('Adding new witnesses...')
            for witness in missing_witnesses:
                for color in range(self.K):
                    # If a witness_color_var is true, there is exactly one guard of that color
                    self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.G.neighbors(witness)) >= self.witness_color_vars[witness, color])
                    self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.G.neighbors(witness)) <= 1 + self.M * (1 - self.witness_color_vars[witness, color]))
                    
                # Ensure that each witness is covered by at least one guard with a unique color
                self.model.addConstr(sum(self.witness_color_vars[witness, color] for color in range(self.K)) >= 1)
                
                self.lazy_witnesses += 1

            self.model.optimize()
            if self.model.status != grb.GRB.OPTIMAL:
                raise RuntimeError("Unexpected status after optimization!")
            missing_witnesses = self.__check_coverage()

        obj_val = self.model.objVal
        print(f"[CAGP SOLVER]: Found the minimum amount of colors required: {obj_val}")
        print(f"[CAGP SOLVER]: Iterations: {self.iteration}")
        print(f"[CAGP SOLVER]: Lazy witnesses: {self.lazy_witnesses}")
        return [(guard, color) for (guard, color), variable in self.guard_vars.items() if variable.x >= 0.5]