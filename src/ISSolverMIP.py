import gurobipy as grb
import networkx as nx
from guard import Guard

class ISSolverMIP:

    def __init__(self, weights: list[(Guard, int)], G: nx.Graph):
        self.G = G
        self.weights = weights
        self.model = grb.Model()
        self.__make_vars()
        self.__add_conflicting_guards_constraints()
        self.model.setObjective(sum(self.guard_vars[guard.id] * weight for guard, weight in weights), grb.GRB.MAXIMIZE)
        self.model.update()

    def __make_vars(self):
        self.guard_vars = {guard.id: self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY) for guard, weight in self.weights}

    def __add_conflicting_guards_constraints(self):
        for e in self.G.edges():
            if e[0][0] == 'g' and e[1][0] == 'g':
                self.model.addConstr(1 >= self.guard_vars[e[0]] + self.guard_vars[e[1]])

    def solve(self):
        self.model.optimize()
        return [guard for guard, weight in self.weights if self.guard_vars[guard.id].x >= 0.5]
