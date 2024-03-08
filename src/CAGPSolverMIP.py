import gurobipy as grb
from numpy import cov
import rustworkx as rx
from pyvispoly import Point, PolygonWithHoles, Arrangement, Arr_PointLocation, plot_polygon
import matplotlib.pyplot as plt

# This version of the solver takes in a precomputed visibility and covering graph to create its constraints
# New witnesses are added whenever an optimal solution is found
class CAGPSolverMIP:

    def __init__(self, K: int, poly: PolygonWithHoles, guard_to_witnesses: dict[int, set[int]], initial_witnesses: list[int], all_witnesses: set[int], G: rx.PyGraph, edge_clique_covers: list[list[list[int]]], solution: list[list[int]]=None) -> list[tuple[int, int]]:
        self.G = G
        self.K = K
        self.poly = poly
        self.guard_to_witnesses = guard_to_witnesses
        self.initial_witnesses = initial_witnesses
        self.all_witnesses = all_witnesses
        self.edge_clique_covers = edge_clique_covers
        self.model = grb.Model()
        # self.model.Params.MemLimit = 16

        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_edge_clique_cover_constraints()
        self.__add_guard_coloring_constraints()
        self.__add_color_symmetry_constraints()
        self.__add_guard_symmetry_constraints()

        if solution:
            self.__provide_init_solution(solution)

        # Set solver parameters for faster computation
        # parameters generated from DCAGP paper benchmark instance
        self.model.Params.lazyConstraints = 1
        self.model.Params.Method = 0
        self.model.Params.Heuristics = 0
        self.model.Params.MIPFocus = 2 # important
        self.model.Params.Cuts = 0
        self.model.Params.AggFill = 0
        self.model.Params.PrePasses = 1 # important

        # parameters generated from salzburg benchmark instance
        # self.model.Params.lazyConstraints = 1
        # self.model.Params.MIPFocus = 2
        # self.model.Params.PrePasses = 1
        # self.model.Params.Method = 0
        # self.model.Params.DegenMoves = 2
        # self.model.Params.Cuts = 1
        self.model.Params.LogFile = 'mip.log'

        # Set the objective
        self.model.setObjective(sum(self.color_vars.values()), grb.GRB.MINIMIZE)

        # Tune the solver
        # self.model.Params.TuneTimeLimit = 30000
        # self.model.tune()

    def __make_vars(self):
        # Create binary variables for every color
        self.color_vars = {i: self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY) for i in range(self.K)}
        # Create binary variables for every guard color assignment
        self.guard_vars = dict()
        for guard in self.guard_to_witnesses.keys():
            guard_dict = dict()
            for k in range(self.K):
                guard_dict[k] = self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY)
            self.guard_vars[guard] = guard_dict

    def __add_witness_covering_constraints(self):
        for witness in self.initial_witnesses:
            subset = []
            for guard in self.G.neighbors(witness):
                for k in range(self.K):
                    subset.append((guard, k))
            self.model.addConstr(1 <= sum(self.guard_vars[guard][k] for guard, k in subset))

    # These constraints are being replaced by the edge clique cover constraints
    def __add_conflicting_guards_constraints(self):
        for e in self.G.edge_index_map().values():
            if self.G[e[0]] < len(self.guards) and self.G[e[1]] < len(self.guards):
                for k in range(self.K):
                    self.model.addConstr(0 >= self.guard_vars[(e[0], k)] + self.guard_vars[(e[1], k)] - self.color_vars[k])
                
    def __add_edge_clique_cover_constraints(self):
        color = 0
        for cover in self.edge_clique_covers:
            for clique in cover:
                self.model.addConstr(self.color_vars[color] >= sum(self.guard_vars[guard][color] for guard in clique))
            color += 1

    def __add_guard_coloring_constraints(self):
        for guard, color_dict in self.guard_vars.items():
            self.model.addConstr(1 >= sum(color_dict.values()))

    def __add_color_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.addConstr(0 <= self.color_vars[k] - self.color_vars[k + 1])

    def __add_guard_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.addConstr(0 <= sum(color_dict[k] for color_dict in self.guard_vars.values())
                                            - sum(color_dict[k + 1] for color_dict in self.guard_vars.values()))

    def __check_coverage(self, model, guard_vars):
        solution = [guard for guard, color_dict in guard_vars.items() for variable in color_dict.values() if model.cbGetSolution(variable) >= 0.5]
        solution = list(set(solution))

        covered_witnesses = set()
        for guard in solution:
            covered_witnesses = covered_witnesses.union(self.guard_to_witnesses[guard])

        missing_witnesses = self.all_witnesses.difference(covered_witnesses)
        
        return missing_witnesses

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
                self.model.cbLazy(1 <= sum(self.guard_vars[x] for x in subset))
                self.lazy_witnesses += 1
            self.iteration += 1

    def __callback_fractional(self, model, varmap):
        # Nothing is being done here yet.
        # Some more advanced techniques can be used to add helpful constraints
        # just from looking at a fractional solution.
        pass

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
        callback = lambda model, where: self.callback(where, model, self.guard_vars)
        self.model.optimize(callback)
        if self.model.status != grb.GRB.OPTIMAL:
            raise RuntimeError("Unexpected status after optimization!")

        obj_val = self.model.objVal
        print(f"[CAGP SOLVER]: Found the minimum amount of colors required: {obj_val}")
        print(f"[CAGP SOLVER]: Iterations: {self.iteration}")
        print(f"[CAGP SOLVER]: Lazy witnesses: {self.lazy_witnesses}")
        return [(guard, color) for guard, color_dict in self.guard_vars.items() for color, variable in color_dict.items() if variable.x >= 0.5]

    def __provide_init_solution(self, solution):
        for (guard, color) in solution:
            self.guard_vars[guard][color].Start = 1
            self.color_vars[color].Start = 1
