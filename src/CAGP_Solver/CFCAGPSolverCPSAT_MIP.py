from collections import Counter
import gurobipy as grb

# DISCLAIMER: This solver is not fully implemented and is not used in the evaluation.
class CFCAGPSolverCPSAT:

    def __init__(self, K: int, guard_to_witnesses: dict[int, set[int]], witness_to_guards: dict[int, set[int]], initial_witnesses: list[int], all_witnesses: set[int], solution: list[list[int]]=None) -> list[tuple[int, int]]:
        self.K = K
        self.guard_to_witnesses = guard_to_witnesses
        self.witness_to_guards = witness_to_guards
        self.initial_witnesses = initial_witnesses
        self.all_witnesses = all_witnesses
        self.model = grb.Model()

        self.__make_vars()
        self.__add_guard_coloring_constraints()
        self.__add_color_constraints()
        self.__add_unique_color_constraints()
        self.__add_color_symmetry_constraints()
        self.__add_guard_symmetry_constraints()
        self.__set_objective()
        
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
            M = len(self.guard_to_witnesses)	
            self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.guard_to_witnesses.keys()) >= self.color_vars[color])
            self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.guard_to_witnesses.keys()) <= M * self.color_vars[color])

    def __add_unique_color_constraints(self):
        for witness in self.initial_witnesses:
            for color in range(self.K):
                # If a witness_color_var is true, there is exactly one guard of that color
                M = len(self.witness_to_guards[witness])
                self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.witness_to_guards[witness]) >= self.witness_color_vars[witness, color])
                self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.witness_to_guards[witness]) <= 1 + M * (1 - self.witness_color_vars[witness, color]))
                
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
        # Create a dictionary mapping guards to their colors
        guard_to_color = {guard: color for (guard, color), variable in self.guard_vars.items() if variable.x >= 0.5}

        # Check each witness
        witnesses_without_unique_guard = []
        for witness, guards in self.witness_to_guards.items():
            # Check if there's a guard with a unique color among the guards of this witness
            colors = [guard_to_color[guard] for guard in guards if guard in guard_to_color]
            color_counts = Counter(colors)
            has_unique_guard = any(count == 1 for count in color_counts.values())
            if not has_unique_guard:
                witnesses_without_unique_guard.append(witness)

        return witnesses_without_unique_guard

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
                    self.witness_color_vars[witness, color] = self.model.addVar(lb=0, ub=1, vtype=grb.GRB.BINARY)
                    # If a witness_color_var is true, there is exactly one guard of that color
                    self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.witness_to_guards[witness]) >= self.witness_color_vars[witness, color])
                    self.model.addConstr(sum(self.guard_vars[guard, color] for guard in self.witness_to_guards[witness]) <= 1 + self.M * (1 - self.witness_color_vars[witness, color]))
                    
                # Ensure that each witness is covered by at least one guard with a unique color
                self.model.addConstr(sum(self.witness_color_vars[witness, color] for color in range(self.K)) >= 1)
                
                self.lazy_witnesses += 1

            self.model.optimize()
            
            self.model.params.BestObjStop = self.model.objVal
            missing_witnesses = self.__check_coverage()

        obj_val = self.model.objVal
        print(f"[CAGP SOLVER]: Found the minimum amount of colors required: {obj_val}")
        print(f"[CAGP SOLVER]: Iterations: {self.iteration}")
        print(f"[CAGP SOLVER]: Lazy witnesses: {self.lazy_witnesses}")
        return [(guard, color) for (guard, color), variable in self.guard_vars.items() if variable.x >= 0.5]