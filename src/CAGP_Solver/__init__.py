from .CAGPSolverCPSAT_MIP_Formulation import CAGPSolverCPSAT as CAGPSolverCPSAT_MIP
from .CAGPSolverCPSAT_SAT_Formulation import CAGPSolverCPSAT as CAGPSolverCPSAT_SAT
from .CAGPSolverMIP import CAGPSolverMIP
from .CAGPSolverSAT import CAGPSolverSAT
from .CFCAGPSolverMIP import CFCAGPSolverMIP
from .CFCAGPSolverSAT import CFCAGPSolverSAT
from .CFCAGPSolverCPSAT_MIP import CFCAGPSolverCPSAT as CFCAGPSolverCPSAT_MIP
from .CFCAGPSolverCPSAT_SAT import CFCAGPSolverCPSAT as CFCAGPSolverCPSAT_SAT
from .CAGPGreedy import get_greedy_solution
from .solver_utils import generate_solver_input, generate_solver_input_cf, generate_shadow_and_light_polygons, generate_edge_clique_covers, verify_solver_solution, verify_solver_solution_cf
from .instance import Instance
from .fpg_conversion import get_fpg_instance

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
           "CFCAGPSolverCPSAT_MIP",
           "CFCAGPSolverCPSAT_SAT", 
           "get_greedy_solution", 
           "generate_solver_input", 
           "generate_solver_input_cf",
           "generate_shadow_and_light_polygons",
           "generate_edge_clique_covers", 
           "verify_solver_solution",
           "verify_solver_solution_cf",
           "Instance",
           "get_fpg_instance",
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