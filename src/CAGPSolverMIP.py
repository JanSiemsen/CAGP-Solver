import gurobipy as grb
import math
import networkx as nx
from guard import Guard
from pyvispoly import PolygonWithHoles

class CAGPSolverMIP:

    def __make_vars(self):
        # Create binary variables for every color
        self.color_vars = {i: self.model_bottleneck.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY) for i in range(self.K)}
        # Create binary variables for every guard color assignment
        self.guard_vars = {}
        for guard in self.G:
            if guard[0] == 'g':
                for k in range(self.K):
                    self.guard_vars[f'{guard}k{k}'] = self.model_bottleneck.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY)
        # Create a integer variable (vtype=grb.GRB.INTEGER) for the amount of colors used
        self.chromatic_number = self.model_bottleneck.addVar(lb=0, ub=self.K, vtype=grb.GRB.INTEGER)

    def __add_witness_covering_constraints(self):
        for witness in self.G:
            if witness[0] == 'w':
                subset = []
                for guard in self.G.neighbors(witness):
                    for k in range(self.K):
                        subset.append(f'{guard}k{k}')
                self.model_bottleneck.addConstr(1 <= sum(self.guard_vars[x] for x in subset))

    def __add_conflicting_guards_constraints(self):
        for e in self.G.edges():
            if e[0][0] == 'g' and e[1][0] == 'g':
                for k in range(self.K):
                    self.model_bottleneck.addConstr(0 >= self.guard_vars[f'{e[0]}k{k}'] + self.guard_vars[f'{e[1]}k{k}'] - self.color_vars[k])

    def __add_guard_coloring_constraints(self):
        for guard in self.G:
            if guard[0] == 'g':
                self.model_bottleneck.addConstr(1 >= sum(self.guard_vars[x] if x.split('k')[0] == guard else 0 for x in self.guard_vars.keys()))

    def __add_color_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model_bottleneck.addConstr(0 <= self.color_vars[k] - self.color_vars[k + 1])

    def __add_guard_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model_bottleneck.addConstr(0 <= sum(self.guard_vars[x] if x.split('k')[1] == f'{k}' else 0 for x in self.guard_vars.keys())
                                            - sum(self.guard_vars[x] if x.split('k')[1] == f'{k + 1}' else 0 for x in self.guard_vars.keys()))

    def __add_bottleneck_constraint(self):
        """
        Enforce the bottleneck constraints.
        """
        self.model_bottleneck.addConstr(self.chromatic_number >= sum(self.color_vars.values()))

    def __check_coverage(self):
        solution = [gk for gk, x_gk in self.guard_vars.items() if x_gk.x >= 0.5]

        

    def __callback_integral(self):
        uncovered_poly = self.__check_coverage()
        for polygon in uncovered_poly:
            for guard in self.G:
                if guard[0] == 'g':
                    for k in range(self.K):
                        if self.guard_vars[f'{guard}k{k}'].x >= 0.5:
                            if guard.visibility.difference(polygon):
                                self.model_bottleneck.cbLazy(self.guard_vars[f'{guard}k{k}'] == 0)
                                return
    

    def __callback_fractional(self):
        # Nothing has to be done in here.
        # Some more advanced techniques can be used to add helpful constraints
        # just from looking at a fractional solution, but this exceeds the scope
        # of this course. It can still be interesting to analyze fractional solutions
        # that the solver comes up with.
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

    def __init__(self, G: nx.graph, K: int, poly: PolygonWithHoles, guards: list[Guard], solution=None):
        self.G = G
        self.K = K
        self.poly = poly
        self.guards = guards
        self.model_bottleneck = grb.Model()  # "First stage" model for finding the bottleneck edge
        self.model_bottleneck.Params.Timelimit = 300
        self.model_bottleneck.Params.MemLimit = 4

        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_conflicting_guards_constraints()
        self.__add_guard_coloring_constraints()
        self.__add_color_symmetry_constraints()
        self.__add_guard_symmetry_constraints()
        self.__add_bottleneck_constraint()

        if solution:
            self.__provide_init_solution(solution)
        # Give the solver a heads up that lazy constraints will be utilized
        # self.model_bottleneck.Params.lazyConstraints = 1
        # Set the objective
        self.model_bottleneck.setObjective(self.chromatic_number, grb.GRB.MINIMIZE)

    def __solve_bottleneck(self):
        # Find the optimal bottleneck
        cb_bn = lambda model, where: self.callback(where, model)
        self.model_bottleneck.optimize()
        if self.model_bottleneck.status != grb.GRB.OPTIMAL:
            raise RuntimeError("Unexpected status after optimization!")
        bottleneck = self.model_bottleneck.objVal
        print(f"[DBST SOLVER]: Found the minimum amount of colors required: {bottleneck}")
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