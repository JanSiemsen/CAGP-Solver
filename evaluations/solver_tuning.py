import gurobipy as grb

model = grb.read('/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/evaluations/CAGP_MIP_model.mps')

model.Params.LazyConstraints = 1
model.Params.Cuts = 0
model.Params.Presolve = 2
model.Params.Method = 0
model.Params.Heuristics = 0
model.Params.NumericFocus = 2
model.Params.TuneTimeLimit = 10000
model.tune()
