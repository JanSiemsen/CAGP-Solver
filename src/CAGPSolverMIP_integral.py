from re import A
import gurobipy as grb
import rustworkx as rx
from pyvispoly import Point, PolygonWithHoles, Arrangement, Arr_PointLocation, plot_polygon
import matplotlib.pyplot as plt

# This version of the solver takes in a precomputed visibility and covering graph to create its constraints
# New witnesses are added whenever an optimal solution is found
class CAGPSolverMIP:

    def __init__(self, K: int, poly: PolygonWithHoles, guards: dict[int, tuple[Point, PolygonWithHoles]], initial_witnesses: dict[int, Point], remaining_witnesses: list[Point], G: rx.PyGraph, edge_clique_covers: list[list[list[int]]], solution: list[list[int]]=None) -> list[tuple[int, int]]:
        self.G = G
        self.K = K
        self.poly = poly
        self.guards = guards
        self.witnesses = initial_witnesses
        self.remaining_witnesses = remaining_witnesses
        self.edge_clique_covers = edge_clique_covers
        self.model = grb.Model()
        # self.model.Params.Timelimit = 300
        self.model.Params.MemLimit = 16

        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_edge_clique_cover_constraints()
        self.__add_guard_coloring_constraints()
        self.__add_color_symmetry_constraints()
        self.__add_guard_symmetry_constraints()

        # if solution:
        #     self.__provide_init_solution(solution)

        # Give the solver a heads up that lazy constraints will be utilized
        self.model.Params.lazyConstraints = 1
        self.model.Params.LogFile = 'mip.log'
        # Set the objective
        self.model.setObjective(sum(self.color_vars.values()), grb.GRB.MINIMIZE)

    def __make_vars(self):
        # Create binary variables for every color
        self.color_vars = {i: self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY) for i in range(self.K)}
        # Create binary variables for every guard color assignment
        self.guard_vars = {}
        for guard in self.G.node_indices()[:len(self.guards)]:
            for k in range(self.K):
                self.guard_vars[(guard, k)] = self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY)

    def __add_witness_covering_constraints(self):
        for witness in self.G.node_indices()[len(self.guards):]:
            subset = []
            for guard in self.G.neighbors(witness):
                for k in range(self.K):
                    subset.append((guard, k))
            self.model.addConstr(1 <= sum(self.guard_vars[x] for x in subset))

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
                self.model.addConstr(self.color_vars[color] >= sum(self.guard_vars[(x, color)] for x in clique))
            color += 1

    def __add_guard_coloring_constraints(self):
        for guard in self.G.node_indices()[:len(self.guards)]:
            self.model.addConstr(1 >= sum(self.guard_vars[x] if x[0] == guard else 0 for x in self.guard_vars.keys()))

    def __add_color_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.addConstr(0 <= self.color_vars[k] - self.color_vars[k + 1])

    def __add_guard_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.addConstr(0 <= sum(self.guard_vars[x] if x[1] == k else 0 for x in self.guard_vars.keys())
                                            - sum(self.guard_vars[x] if x[1] == k + 1 else 0 for x in self.guard_vars.keys()))

    def __check_coverage(self, model, guard_vars):
        solution = [gk[0] for gk, x_gk in guard_vars.items() if model.cbGetSolution(x_gk) >= 0.5]
        solution = list(set(solution))

        # print("List of colored guards: {solution}")
        # fig, ax = plt.subplots()

        missing_area = [self.poly]
        for guard in solution:
            coverage = self.guards[guard][1]
            missing_area = sum((poly.difference(coverage) for poly in missing_area), [])

            # guardpos = next((x.position for x in self.guards if x.id == guard), None)
            # plt.scatter(guardpos.x(), guardpos.y(), color='black', s=10)
        
        # plot_polygon(self.poly, ax=ax, color='gray', alpha=0.5)
        # for polygon in missing_area:
        #     plot_polygon(polygon, ax=ax, color='green', alpha=0.5)
        # plt.show()
        
        return missing_area

    def __callback_integral(self, model, guard_vars):
        print('Checking coverage; adding new witnesses for the missing area...')
        missing_area = self.__check_coverage(model, guard_vars)

        # new_witnesses = []
        # for polygon in missing_area:
        #     for point in polygon.interior_sample_points():
        #         new_witnesses.append(point)

        if(missing_area):
            arr = Arrangement(missing_area[0])
            for polygon in missing_area[0:]:
                arr = arr.overlay(Arrangement(polygon))

            point_locator = Arr_PointLocation(arr)

            for witness in self.remaining_witnesses:
                if point_locator.locate(witness) == 1:
                    self.remaining_witnesses.remove(witness)
                    subset = []
                    for g_id, guard in self.guards.items():
                        if guard[1].contains(witness):
                            for k in range(self.K):
                                subset.append((self.__get_node_index_by_data(g_id), k))
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
        return [gk for gk, x_gk in self.guard_vars.items() if x_gk.x >= 0.5]

    def __provide_init_solution(self, solution):
        for e, v in self.bnvars.items():
            if e in solution:
                v.Start = 1
            else:
                v.Start = 0

    def __get_node_index_by_data(self, data: str):
        for node_index in self.G.node_indices():
            if self.G.get_node_data(node_index) == data:
                return node_index
        return None
