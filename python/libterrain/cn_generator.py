from psycopg2.pool import ThreadedConnectionPool
from building import Building
from link import Link
from libterrain import terrain
import random
import argparse
import networkx as nx
from collections import defaultdict


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', help="number of nodes in the network", 
                        required=True, type=int)
    parser.add_argument('-H', help="use the highest building as a gateway", 
                        action="store_true")
    return parser.parse_args()

def choose_neighbor(new_node, loss_array, g, mode="pathloss"):
    
    neighbors = []
    if mode == "pathloss":
        neighbors.append(sorted(loss_array.items(), key = lambda x: x[1])[0])
        return neighbors
    
def stop_condition(g, args, mode="nodes"):
    if mode == "nodes":
        if len(g) >= args.n:
            return True
    return False

if __name__ == '__main__':
    max_attempts = 1000
    DSN = 'postgresql://user:pass@IP/postgres'
    working_area_1x1 = (4.8411, 45.7613, 4.8528, 45.7681)
    #working_area_large = (4.841100,4.852800,45.761300,45.768100)
    working_area=working_area_1x1
    g = nx.Graph()
    dataset = 'lyon'
    args = parse_arguments()
    t = terrain(DSN, working_area, dataset)
    building_dict = {}
    building_list = []
    for b in t.buildings:
        building_dict[b.gid] = b
        building_list.append(b.gid)
    if args.H:
        gateway = sorted([b for b in t.buildings], key=lambda x: x.z)[-1]
        random.shuffle(building_list)
    else:
        random.shuffle(building_list)
        gateway = building_dict[building_list.pop()]
    building_list.remove(gateway.gid)
    print("Gateway chosen: {}".format(gateway))
    if args.n > len(building_list):
        print("You want a network larger than the number of"
                "buildings in the area: {}".format(len(t.buildings)))
    
    noloss_nodes = defaultdict(list)
    g.add_node(gateway.gid)
    for new_node in building_list:
        loss_dict = {}
        for old_node in g.nodes():
            loss = t.get_loss(building_dict[new_node], building_dict[old_node])
            if loss:
                loss_dict[old_node] = loss
            else:
                noloss_nodes[new_node].append(old_node)
                noloss_nodes[old_node].append(new_node)
        if loss_dict:
            neighbor_list = choose_neighbor(new_node, loss_dict, g)
            for n in neighbor_list:
                g.add_edge(new_node, n[0], loss=loss_dict[n[0]])
            print("new node added, with loss " + str(n[1]))
        if stop_condition(g, args):
            break
    nx.write_graphml(g, "/tmp/g.graphml")
