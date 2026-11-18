'''
This file is part of Satyrn.
Satyrn is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.
Satyrn is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with Satyrn.
If not, see <https://www.gnu.org/licenses/>.
'''

import networkx as nx
# from .RingObject import RingObject # Don't think this need to inherit from RingObject

class RingRelationshipGraph(object):

    def __init__(self, graph=None):
        # Set default values
        self.graph = graph if graph else nx.Graph()

    def get_path(self, entity_a, entity_b):
        node_path = nx.dijkstra_path(self.graph, entity_a, entity_b)
        # print("path:", node_path)
        return [self.graph.get_edge_data(node_pair[0], node_pair[1])[0]["relationship"] for node_pair in zip(node_path[:-1], node_path[1:])]
        # return [self.graph[node_pair[0]][node_pair[1]]['relationship'] for node_pair in zip(node_path[:-1], node_path[1:])]
    
    def get_all_direct_paths(self, entity_a, entity_b, cutoff=1):
        node_paths = nx.all_simple_paths(self.graph, entity_a, entity_b, cutoff=cutoff)
        return [[self.graph.get_edge_data(node_pair[0], node_pair[1])[i]["relationship"] for node_pair in zip(node_path[:-1], node_path[1:])] for i, node_path in enumerate(node_paths)]