import gurobipy as grb
from guard import Guard
from witness import Witness
import solver
from pyvispoly import PolygonWithHoles, plot_polygon
import matplotlib.pyplot as plt

# This version creates its constraints directly from the set of guards and witnesses
class CAGPSolverMIP:

    def __make_vars(self):
        # Create binary variables for every color
        self.color_vars = {i: self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY) for i in range(self.K)}
        # Create binary variables for every guard color assignment
        self.guard_vars = {}
        for guard in self.guards:
            for k in range(self.K):
                self.guard_vars[(guard.id, k)] = self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY)
        # Create an integer variable (vtype=grb.GRB.INTEGER) for the amount of colors used
        self.chromatic_number = self.model.addVar(lb=0, ub=self.K, vtype=grb.GRB.INTEGER)

    def __add_witness_covering_constraints(self):
        for witness in self.witnesses:
            subset = []
            for guard in self.guards:
                if guard.visibility.contains(witness.position):
                    for k in range(self.K):
                        subset.append((guard.id, k))
            self.model.addConstr(1 <= sum(self.guard_vars[x] for x in subset))
                
    def __add_edge_clique_cover_constraints(self):
        edge_clique_covers = solver.generate_edge_clique_covers(solver.generate_visibility_graph(self.guards), self.K)
        color = 0
        for cover in edge_clique_covers:
            for clique in cover:
                self.model.addConstr(self.color_vars[color] >= sum(self.guard_vars[(x, color)] for x in clique))
            color += 1

    def __add_guard_coloring_constraints(self):
        for guard in self.guards:
            self.model.addConstr(1 >= sum(self.guard_vars[x] if x[0] == guard.id else 0 for x in self.guard_vars.keys()))

    def __add_color_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.addConstr(0 <= self.color_vars[k] - self.color_vars[k + 1])

    def __add_guard_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.addConstr(0 <= sum(self.guard_vars[x] if x[1] == k else 0 for x in self.guard_vars.keys())
                                            - sum(self.guard_vars[x] if x[1] == k + 1 else 0 for x in self.guard_vars.keys()))

    def __add_bottleneck_constraint(self):
        """
        Enforce the bottleneck constraint.
        """
        self.model.addConstr(self.chromatic_number >= sum(self.color_vars.values()))

    def __check_coverage(self, model, guard_vars):
        solution = [gk[0] for gk, x_gk in guard_vars.items() if model.cbGetSolution(x_gk) >= 0.5]
        solution = list(set(solution))

        # print("List of colored guards: {solution}")
        # fig, ax = plt.subplots()

        missing_area = [self.poly]
        for guard in solution:
            # get the coverage of the guard
            coverage = next((x.visibility for x in self.guards if x.id == guard), None)
            # remove the coverage from each polygon in the missing area
            missing_area = sum((poly.difference(coverage) for poly in missing_area), [])

            # guardpos = next((x.position for x in self.guards if x.id == guard), None)
            # plt.scatter(guardpos.x(), guardpos.y(), color='black', s=10)
        
        # plot_polygon(self.poly, ax=ax, color='gray', alpha=0.5)
        # for polygon in missing_area:
        #     plot_polygon(polygon, ax=ax, color='green', alpha=0.5)
        # plt.show()
        
        return missing_area

    def __callback_integral(self, model, guard_vars):
        uncovered_poly = self.__check_coverage(model, guard_vars)

        new_witnesses = []
        index = len(self.witnesses)
        for polygon in uncovered_poly:
            for point in polygon.interior_sample_points():
                new_witnesses.append(Witness(f'w{index}', point))
                # self.witnesses.append(Witness(f'w{index}', point))
                index += 1

        for witness in new_witnesses:
            subset = []
            for guard in self.guards:
                if guard.visibility.contains(witness.position):
                    for k in range(self.K):
                        subset.append((guard.id, k))
            model.cbLazy(1 <= sum(guard_vars[x] for x in subset))

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

    def __init__(self, K: int, poly: PolygonWithHoles, guards: list[Guard], witnesses: list[Witness], solution: list[list[Guard]]=None) -> list[str]:
        self.K = K
        self.poly = poly
        self.guards = guards
        self.witnesses = witnesses
        self.model = grb.Model()
        self.model.Params.Timelimit = 300
        self.model.Params.MemLimit = 16

        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_edge_clique_cover_constraints()
        self.__add_guard_coloring_constraints()
        self.__add_color_symmetry_constraints()
        self.__add_guard_symmetry_constraints()
        self.__add_bottleneck_constraint()

        # if solution:
        #     self.__provide_init_solution(solution)
        # Give the solver a heads up that lazy constraints will be utilized
        self.model.Params.lazyConstraints = 1
        # Set the objective
        self.model.setObjective(self.chromatic_number, grb.GRB.MINIMIZE)

    def __solve_bottleneck(self):
        # Find the optimal bottleneck
        callback = lambda model, where: self.callback(where, model, self.guard_vars)
        self.model.optimize(callback)
        if self.model.status != grb.GRB.OPTIMAL:
            raise RuntimeError("Unexpected status after optimization!")
        obj_val = self.model.objVal
        print(f"[CAGP SOLVER]: Found the minimum amount of colors required: {obj_val}")
        return [gk for gk, x_gk in self.guard_vars.items() if x_gk.x >= 0.5]

    def solve(self):
        guard_coloring = self.__solve_bottleneck()
        return guard_coloring

    def __provide_init_solution(self, solution):
        for e, v in self.bnvars.items():
            if e in solution:
                v.Start = 1
            else:
                v.Start = 0
