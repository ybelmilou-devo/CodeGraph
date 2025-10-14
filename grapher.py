import networkx as nx
import matplotlib.pyplot as plt

def draw_graph(calls):
    G = nx.DiGraph()
    for caller, callee in calls:
        G.add_edge(caller, callee)
    plt.figure(figsize=(10, 8))
    nx.draw(G, with_labels=True, node_color='skyblue', node_size=2000, arrowsize=20)
    plt.show()
