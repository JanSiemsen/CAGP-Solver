import gurobipy as grb

# This version of the solver takes in a precomputed visibility and covering graph to create its constraints
# New witnesses are added whenever a feasible solution is found
class CAGPSolverMIP:

    def __init__(self, K: int, guard_to_witnesses: dict[int, set[int]], witness_to_guards: dict[int, set[int]], initial_witnesses: list[int], all_witnesses: set[int], edge_clique_covers: list[list[list[int]]], solution: list[list[int]]=None) -> list[tuple[int, int]]:
        self.K = K
        self.guard_to_witnesses = guard_to_witnesses
        self.witness_to_guards = witness_to_guards
        self.initial_witnesses = initial_witnesses
        self.number_of_witnesses = len(initial_witnesses)
        self.all_witnesses = all_witnesses
        self.edge_clique_covers = edge_clique_covers
        self.model = grb.Model()
        self.model.Params.TimeLimit = 600
        self.model.Params.lazyConstraints = 1

        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_edge_clique_cover_constraints()
        self.__add_guard_coloring_constraints()
        self.__add_color_symmetry_constraints()
        self.__add_guard_symmetry_constraints()

        if solution:
            self.__provide_init_solution(solution)

        # Set solver parameters for faster computation
        self.model.Params.Cuts = 0
        self.model.Params.Presolve = 2
        self.model.Params.Method = 0
        self.model.Params.Heuristics = 0
        self.model.Params.NumericFocus = 2
        self.model.Params.VarBranch = 1
        self.model.Params.PreSparsify = 0
        # self.model.Params.LogFile = 'mip.log'

        # Set the objective
        self.model.setObjective(sum(self.color_vars.values()), grb.GRB.MINIMIZE)

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
            for guard in self.witness_to_guards[witness]:
                for k in range(self.K):
                    subset.append((guard, k))
            self.model.addConstr(1 <= sum(self.guard_vars[guard][k] for guard, k in subset))
                
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
            self.iteration += 1
            self.number_of_witnesses += len(missing_witnesses)
            self.added_witnesses = self.added_witnesses.union(missing_witnesses)
            for witness in missing_witnesses:
                subset = []
                for guard in self.witness_to_guards[witness]:
                    for k in range(self.K):
                        subset.append((guard, k))
                self.model.cbLazy(1 <= sum(self.guard_vars[guard][k] for guard, k in subset))

    def __callback_fractional(self, model, varmap):
        # Nothing is being done here yet.
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
        self.iteration = 1
        self.added_witnesses = set()
        callback = lambda model, where: self.callback(where, model, self.guard_vars)
        self.model.optimize(callback)
        if self.model.status != grb.GRB.OPTIMAL:
            return self.model.objVal, [], self.iteration, self.number_of_witnesses, "timeout"

        obj_val = self.model.objVal
        print(f"[CAGP SOLVER]: Found the minimum amount of colors required: {obj_val}")
        print(f"[CAGP SOLVER]: Iterations: {self.iteration}")
        print(f"[CAGP SOLVER]: Witnesses used: {self.number_of_witnesses}")

        # code for saving the model
        # for witness in self.added_witnesses:
        #     subset = []
        #     for guard in self.witness_to_guards[witness]:
        #         for k in range(self.K):
        #             subset.append((guard, k))
        #     self.model.addConstr(1 <= sum(self.guard_vars[guard][k] for guard, k in subset))
        # self.model.write('CAGP_MIP_model.mps')

        return obj_val, [(guard, color) for guard, color_dict in self.guard_vars.items() for color, variable in color_dict.items() if variable.x >= 0.5], self.iteration, self.number_of_witnesses, "success"

    def __provide_init_solution(self, solution):
        for (guard, color) in solution:
            self.guard_vars[guard][color].Start = 1
            self.color_vars[color].Start = 1
