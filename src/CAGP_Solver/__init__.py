from .CAGPSolverCPSAT_MIP_Formulation import CAGPSolverCPSAT as CAGPSolverCPSAT_MIP
from .CAGPSolverCPSAT_SAT_Formulation import CAGPSolverCPSAT as CAGPSolverCPSAT_SAT
from .CAGPSolverMIP import CAGPSolverMIP
from .CAGPSolverSAT import CAGPSolverSAT
from .CFCAGPSolverMIP import CFCAGPSolverMIP
from .CFCAGPSolverSAT import CFCAGPSolverSAT
from .CFCAGPSolverCPSAT import CFCAGPSolverCPSAT
from .CAGPGreedy import get_greedy_solution
from .solver_utils import generate_solver_input, generate_edge_clique_covers, verify_solver_solution

"""
This package provides the visibility polygons of CGAL as a
python package.

2023, Dominik Krupke, TU Braunschweig
"""
# ._cgal_bindings will only exist after compilation.
from ._cgal_bindings import (
    FieldNumber,
    Point,
    Polygon,
    PolygonWithHoles,
    VisibilityPolygonCalculator,
    repair,
    AVP_Arrangement,
    Arrangement,
    Arr_PointLocation,
)
from .plotting import plot_polygon

__all__ = ["CAGPSolverCPSAT_MIP", 
           "CAGPSolverCPSAT_SAT", 
           "CAGPSolverMIP", 
           "CAGPSolverSAT", 
           "CFCAGPSolverMIP", 
           "CFCAGPSolverSAT", 
           "CFCAGPSolverCPSAT", 
           "get_greedy_solution", 
           "generate_solver_input", 
           "generate_edge_clique_covers", 
           "verify_solver_solution",
           "FieldNumber",
           "Point",
           "Polygon",
           "PolygonWithHoles",
           "VisibilityPolygonCalculator",
           "plot_polygon",
           "repair",
           "AVP_Arrangement",
           "Arrangement",
           "Arr_PointLocation",]