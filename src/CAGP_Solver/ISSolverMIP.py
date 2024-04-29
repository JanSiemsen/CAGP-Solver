import gurobipy as grb
import rustworkx as rx

class ISSolverMIP:

    def __init__(self, weights: list[(int, int)], G: rx.PyGraph):
        self.G = G
        self.weights = weights
        self.model = grb.Model()
        self.model.setParam('OutputFlag', False)
        self.__make_vars()
        self.__add_conflicting_guards_constraints()
        self.model.setObjective(sum(self.guard_vars[guard] * weight for guard, weight in weights), grb.GRB.MAXIMIZE)
        self.model.update()

    def __make_vars(self):
        self.guard_vars = {guard: self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY) for guard in self.G.node_indices()}

    def __add_conflicting_guards_constraints(self):
        for e in self.G.edge_index_map().values():
            self.model.addConstr(1 >= self.guard_vars[e[0]] + self.guard_vars[e[1]])

    def solve(self):
        self.model.optimize()
        return [guard for guard, weight in self.weights if self.guard_vars[guard].x >= 0.5]