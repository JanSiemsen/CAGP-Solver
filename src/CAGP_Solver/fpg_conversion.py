import lzma
import networkx as nx
from .instance import Instance


def _integralize(g: nx.Graph, s: int):
    for n in g.nodes:
        g.nodes[n]["vertex-coordinate-x"] = round(
            s * float(g.nodes[n]["vertex-coordinate-x"])
        )
        g.nodes[n]["vertex-coordinate-y"] = round(
            s * float(g.nodes[n]["vertex-coordinate-y"])
        )


def _vertex_to_position(graph, vertex):
    return (
        round(graph.nodes[vertex]["vertex-coordinate-x"]),
        round(graph.nodes[vertex]["vertex-coordinate-y"]),
    )


def _graph_to_list(graph: nx.Graph):
    components = [
        [
            _vertex_to_position(graph, v)
            for v in nx.dfs_preorder_nodes(graph, source=next(iter(comp)))
        ]
        for comp in nx.connected_components(graph)
    ]
    if len(components) == 1:
        return components[0][::-1], []
    else:
        # move outer face to front
        components.sort(key=min)
        return components[0][::-1], components[1:]

def _list_to_instance(outer_face, holes):
    positions = outer_face + sum(holes, [])
    position_to_index = {p: i for i, p in enumerate(positions)}
    boundary = [position_to_index[p] for p in outer_face]
    holes = [[position_to_index[p] for p in hole] for hole in holes]
    return Instance(positions, boundary, holes)

def _convert(g: nx.Graph):
    # integralize
    _integralize(g, 100000)
    # convert to list representation
    outer_face, holes = _graph_to_list(g)
    # convert to instance
    return _list_to_instance(outer_face, holes)

def get_fpg_instance(instance_name):
    path = f'/home/yanyan/PythonProjects/CAGP-Solver/db/sbgdb-20200507/polygons/random/fpg/{instance_name}.graphml.xz' #replace with actual path
    with lzma.open(path) as xz:
        if xz == None:
            raise FileNotFoundError(f"File {path} not found")
        g = nx.read_graphml(xz)
        return _convert(g)
