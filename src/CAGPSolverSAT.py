from pysat.solvers import Solver
import rustworkx as rx
from pyvispoly import PolygonWithHoles

class CAGPSolverSAT:
    
    def __init__(self, K: int, guard_to_witnesses: dict[int, set[int]], witness_to_guards: dict[int, set[int]], initial_witnesses: list[int], all_witnesses: set[int], GC: rx.PyGraph, guard_color_constraints: bool, solution: list[list[int]]=None) -> list[tuple[int, int]]:
        self.GC = GC
        self.K = K
        self.guard_to_witnesses = guard_to_witnesses
        self.witness_to_guards = witness_to_guards
        self.witnesses = initial_witnesses
        self.all_witnesses = all_witnesses
        self.solver = Solver(name='Gluecard4', with_proof=False)
        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_conflicting_guards_constraints()
        if guard_color_constraints:
            self.__add_guard_coloring_constraints()
        # self.__add_edge_clique_cover_constraints()

    def __make_vars(self):
        self.guard_to_var = dict()
        self.var_to_guard = dict()
        id = 1
        for guard in self.guard_to_witnesses.keys():
            guard_dict = dict()
            for k in range(self.K):
                guard_dict[k] = id
                self.var_to_guard[id] = (guard, k)
                id += 1
            self.guard_to_var[guard] = guard_dict

    def __add_witness_covering_constraints(self):
        for witness in self.witnesses:
            subset = []
            for guard in self.witness_to_guards[witness]:
                for k in range(self.K):
                    subset.append((guard, k))
            self.solver.add_clause([self.guard_to_var[guard][color] for (guard, color) in subset])

    def __add_conflicting_guards_constraints(self):
        for e in self.GC.edge_index_map().values():
            for k in range(self.K):
                self.solver.add_clause([-self.guard_to_var[e[0]][k], -self.guard_to_var[e[1]][k]])

    def __add_guard_coloring_constraints(self):
        for color_dict in self.guard_to_var.values():
            self.solver.add_atmost(list(color_dict.values()), 1)

    # These constraints are being replaced by the conflicting guards constraints
    # def __add_edge_clique_cover_constraints(self):
    #     color = 0
    #     for cover in self.edge_clique_covers:
    #         for clique in cover:
    #             self.solver.add_clause([self.guard_to_var[guard][color] for guard in clique])
    #         color += 1

    def __deactivate_guards(self, color_lim: int):
        return [-self.guard_to_var[guard][k] for guard in self.guard_to_witnesses.keys() for k in range(color_lim, self.K)]
    
    def __check_coverage(self, solution: list[tuple[int, int]]):
        solution = [guard[0] for guard in solution]
        solution = list(set(solution))

        covered_witnesses = set()
        for guard in solution:
            covered_witnesses = covered_witnesses.union(self.guard_to_witnesses[guard])

        missing_witnesses = self.all_witnesses.difference(covered_witnesses)
        
        return missing_witnesses

    def __solve(self, assumptions=None):
        self.solver.solve(assumptions=assumptions)
        if not self.solver.solve(assumptions=assumptions):
            print('No solution found')
            return None
        print('Solution found')
        return [self.var_to_guard[var] for var in self.solver.get_model() if var > 0]
    
    def solve(self, color_lim: int=0):
        if color_lim == 0:
            print('Starting binary search')
            color_lim, solution = self.binary_search()
        else:
            solution = self.linear_search(color_lim)

        print('Checking coverage')
        missing_witnesses = self.__check_coverage(solution)

        iteration = 0
        while(missing_witnesses):
            iteration += 1
            print('Adding new witnesses for missing area ({iteration})')

            for witness in missing_witnesses:
                subset = []
                for guard in self.witness_to_guards[witness]:
                    for k in range(self.K):
                        subset.append((guard, k))
                self.solver.add_clause([self.guard_to_var[guard][color] for (guard, color) in subset])

            print('Starting linear ascent')
            color_lim, solution = self.linear_ascent(color_lim)
            print('Checking coverage')
            missing_witnesses = self.__check_coverage(solution)
        return solution

    def binary_search(self):
        lower = 1
        upper = self.K
        optimal_solution = None
        while lower < upper:
            mid = (lower + upper) // 2
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
