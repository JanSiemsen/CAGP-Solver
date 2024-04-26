from collections import Counter
from itertools import combinations
from pysat.solvers import Solver

# This version of the solver takes in a precomputed visibility and covering graph to create its constraints
# New witnesses are added whenever an optimal solution is found
class CFCAGPSolverSAT:

    def __init__(self, K: int, guard_to_witnesses: dict[int, set[int]], witness_to_guards: dict[int, set[int]], initial_witnesses: list[int], all_witnesses: set[int]) -> list[tuple[int, int]]:
        self.K = K
        self.guard_to_witnesses = guard_to_witnesses
        self.witness_to_guards = witness_to_guards
        self.initial_witnesses = initial_witnesses
        self.all_witnesses = all_witnesses
        self.M = len(self.guard_to_witnesses)
        self.solver = Solver(name='Gluecard4', with_proof=False)

        self.__make_vars()
        self.__add_guard_coloring_constraints()
        self.__add_unique_color_constraints()
        
    def __make_vars(self):
        self.guard_to_var = dict()
        self.var_to_guard = dict()
        self.witness_color_to_var = dict()
        self.var_to_witness_color = dict()

        self.id = 1
        for guard in self.guard_to_witnesses.keys():
            for color in range(self.K):
                self.var_to_guard[self.id] = (guard, color)
                self.guard_to_var[guard, color] = self.id
                self.id += 1

        for witness in self.initial_witnesses:
            for color in range(self.K):
                self.var_to_witness_color[self.id] = (witness, color)
                self.witness_color_to_var[witness, color] = self.id
                self.id += 1

    def __add_guard_coloring_constraints(self):
        for guard in self.guard_to_witnesses.keys():
            # Ensure that each guard is only assigned one color
            self.solver.add_atmost([self.guard_to_var[guard, color] for color in range(self.K)], 1)

    def __add_unique_color_constraints(self):
        for witness in self.initial_witnesses:
            neighbors = self.witness_to_guards[witness]
            for color in range(self.K):
                # If a witness_color_var is true, at least one guard of that color is true
                unique_color = self.witness_color_to_var[witness, color]
                neighbor_guards_color = [self.guard_to_var[guard, color] for guard in neighbors]
                self.solver.add_clause([-unique_color] + neighbor_guards_color)
                for guard1, guard2 in combinations(neighbors, 2):
                    # If a witness_color_var is true, no two guards of that color are true
                    guard1_color = self.guard_to_var[guard1, color]
                    guard2_color = self.guard_to_var[guard2, color]
                    self.solver.add_clause([-unique_color, -guard1_color, -guard2_color])
            # Ensure that each witness is covered by at least one guard with a unique color
            self.solver.add_clause([self.witness_color_to_var[witness, color] for color in range(self.K)])

    def __deactivate_guards(self, color_lim: int):
        return [-self.guard_to_var[guard, k] for guard in self.guard_to_witnesses.keys() for k in range(color_lim, self.K)]

    def __check_coverage(self, solution: list[tuple[int, int]]):
        # Create a dictionary mapping guards to their colors
        guard_to_color = {guard: color for guard, color in solution}

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

    def __solve(self, assumptions=None):
        self.solver.solve(assumptions=assumptions)
        if not self.solver.solve(assumptions=assumptions):
            print('No solution found')
            return None
        print('Solution found')
        return [self.var_to_guard.get(var) for var in self.solver.get_model() if var > 0 and var in self.var_to_guard]
    
    def solve(self, color_lim: int=0):
        if color_lim == 0:
            print('Starting binary search')
            color_lim, solution = self.binary_search()
        else:
            solution = self.linear_search(color_lim)

        current_witnesses = len(self.initial_witnesses)
        print('current witnesses', current_witnesses)
        print('Checking coverage')
        missing_witnesses = self.__check_coverage(solution)

        iteration = 0
        while(missing_witnesses):
            current_witnesses += len(missing_witnesses)
            print('current witnesses', current_witnesses)
            iteration += 1
            print(f'Adding new witnesses without a unique color ({iteration})')

            for witness in missing_witnesses:
                for color in range(self.K):
                    self.var_to_witness_color[self.id] = (witness, color)
                    self.witness_color_to_var[witness, color] = self.id
                    self.id += 1

            for witness in missing_witnesses:
                for color in range(self.K):
                    # If a witness_color_var is true, at least one guard of that color is true
                    self.solver.add_clause([-self.witness_color_to_var[witness, color]] + [self.guard_to_var[guard, color] for guard in self.witness_to_guards[witness]])
                    for guard1, guard2 in combinations(self.witness_to_guards[witness], 2):
                        # If a witness_color_var is true, no two guards of that color are true
                        self.solver.add_clause([-self.witness_color_to_var[witness, color], -self.guard_to_var[guard1, color], -self.guard_to_var[guard2, color]])
                # Ensure that each witness is covered by at least one guard with a unique color
                self.solver.add_clause([self.witness_color_to_var[witness, color] for color in range(self.K)])

            print('Starting linear ascent')
            color_lim, solution = self.linear_ascent(color_lim)
            print('Checking coverage')
            missing_witnesses = self.__check_coverage(solution)

        print('all witnesses:', len(self.all_witnesses))
        return solution

    def binary_search(self):
        lower = 1
        upper = self.K
        optimal_solution = None
        while lower < upper:
            mid = (lower + upper) // 2
            print(upper, mid, lower)
            print(f'Checking for {mid} colors')
            solution = self.__solve(assumptions=self.__deactivate_guards(mid))
            if solution:
                optimal_solution = solution
                upper = mid
            else:
                lower = mid + 1
        if not optimal_solution:
            print(f'Checking for {upper} colors')
            optimal_solution = self.__solve(assumptions=self.__deactivate_guards(upper))
        return lower, optimal_solution
    
    def linear_ascent(self, color_lim: int):
        solution = self.__solve(assumptions=self.__deactivate_guards(color_lim))
        while(not solution and color_lim <= self.K):
            color_lim += 1
            print(f'Checking for {color_lim} colors')
            solution = self.__solve(assumptions=self.__deactivate_guards(color_lim))
        return color_lim, solution

    def linear_search(self, color_lim: int):
        print(f'Checking for {color_lim} colors')
        solution = self.__solve(assumptions=self.__deactivate_guards(color_lim))
        if solution:
            while(solution and color_lim > 0):
                color_lim -= 1
                print(f'Checking for {color_lim} colors')
                solution = self.__solve(assumptions=self.__deactivate_guards(color_lim))
        else:
            while(not solution and color_lim <= self.K):
                color_lim += 1
                print(f'Checking for {color_lim} colors')
                solution = self.__solve(assumptions=self.__deactivate_guards(color_lim))
        return solution

    def __del__(self):
        """
        The solvers from python-sat need a special cleanup,
        which is not necessary for normal Python code.
        There seem to occur resource leaks when you leave this out,
        so it should be sufficient to let the solvers clean up at the garbage collection.
        """
        self.solver.delete()