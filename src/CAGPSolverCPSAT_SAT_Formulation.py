from ortools.sat.python import cp_model
import rustworkx as rx
from pyvispoly import PolygonWithHoles
from sympy import assuming

class CAGPSolverCPSAT:

    def __init__(self, K: int, guard_to_witnesses: dict[int, set[int]], witness_to_guards: dict[int, set[int]], initial_witnesses: list[int], all_witnesses: set[int], GC: rx.PyGraph, solution: list[list[int]]=None) -> list[tuple[int, int]]:
        self.GC = GC
        self.K = K
        self.guard_to_witnesses = guard_to_witnesses
        self.witness_to_guards = witness_to_guards
        self.witnesses = initial_witnesses
        self.all_witnesses = all_witnesses
        self.model = cp_model.CpModel()

        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_conflicting_guards_constraints()
        self.__add_guard_coloring_constraints()
        # self.__add_edge_clique_cover_constraints()
        # if solution:
        #     self.__provide_init_solution(solution)

    def __make_vars(self):
        self.guard_vars = {(guard, k): self.model.NewBoolVar(f'{guard}k{k}') for guard in self.guard_to_witnesses.keys() for k in range(self.K)}

    def __add_witness_covering_constraints(self):
        for witness in self.witnesses:
            subset = []
            for guard in self.witness_to_guards[witness]:
                for k in range(self.K):
                    subset.append((guard, k))
            self.model.AddBoolOr([self.guard_vars[guard] for guard in subset])

    def __add_conflicting_guards_constraints(self):
        for e in self.GC.edge_index_map().values():
            for k in range(self.K):
                self.model.AddBoolOr([self.guard_vars[(e[0], k)].Not(), self.guard_vars[(e[1], k)].Not()])

    def __deactivate_guards(self, color_lim: int):
        self.model.ClearAssumptions()
        self.model.AddAssumptions([self.guard_vars[guard, k].Not() for guard in self.guard_to_witnesses.keys() for k in range(color_lim, self.K)])

    def __add_guard_coloring_constraints(self):
        for guard in self.guard_to_witnesses.keys():
            self.model.AddAtMostOne([self.guard_vars[(guard, i)] for i in range(self.K)])

    # These constraints are being replaced by the conflicting guards constraints
    # def __add_edge_clique_cover_constraints(self):
    #     color = 0
    #     for cover in self.edge_clique_covers:
    #         for clique in cover:
    #             self.model.Add(self.color_vars[color] >= sum(self.guard_vars[(guard, color)] for guard in clique))
    #         color += 1
    
    def __check_coverage(self, solution: list[tuple[int, int]]):
        solution = [guard[0] for guard in solution]
        solution = list(set(solution))

        covered_witnesses = set()
        for guard in solution:
            covered_witnesses = covered_witnesses.union(self.guard_to_witnesses[guard])

        missing_witnesses = self.all_witnesses.difference(covered_witnesses)
        
        return missing_witnesses
    
    def __solve(self):
        solver = cp_model.CpSolver()
        # solver.parameters.log_search_progress = True
        status = solver.Solve(self.model)
        if status != cp_model.OPTIMAL:
            print('No solution found')
            return None
        print('Solution found')
        return [(guard, color) for guard, color in self.guard_vars.keys() if solver.Value(self.guard_vars[(guard, color)]) == 1]

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
                        subset.append(self.guard_vars[(guard, k)])
                self.model.AddBoolOr([self.guard_vars[guard] for guard in subset])

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
            self.__deactivate_guards(mid)
            solution = self.__solve()
            if solution:
                optimal_solution = solution
                upper = mid
            else:
                lower = mid + 1
        if not optimal_solution:
            print(f'Checking for {upper} colors')
            self.__deactivate_guards(upper)
            optimal_solution = self.__solve()
        return lower, optimal_solution
    
    def linear_ascent(self, color_lim: int):
        self.__deactivate_guards(color_lim)
        solution = self.__solve()
        while(not solution and color_lim <= self.K):
            color_lim += 1
            print(f'Checking for {color_lim} colors')
            self.__deactivate_guards(color_lim)
            solution = self.__solve()
        return color_lim, solution

    def linear_search(self, color_lim: int):
        print(f'Checking for {color_lim} colors')
        self.__deactivate_guards(color_lim)
        solution = self.__solve()
        if solution:
            while(solution and color_lim > 0):
                color_lim -= 1
                print(f'Checking for {color_lim} colors')
                self.__deactivate_guards(color_lim)
                solution = self.__solve()
        else:
            while(not solution and color_lim <= self.K):
                color_lim += 1
                print(f'Checking for {color_lim} colors')
                self.__deactivate_guards(color_lim)
                solution = self.__solve()
        return solution