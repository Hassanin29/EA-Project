import random
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from gen_graph import make_graph, rand_route

class ACO:
    def __init__(self, cities: nx.DiGraph, n_ants=20, alpha=1, beta=2, evaporation=0.5, update_callback=lambda i,r,d,t:None, conc=False):
        self.cities = cities
        self.n_ants = n_ants
        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation
        self.update_callback = update_callback if not conc else None
        self.node_list = list(cities.nodes())
        self.node_to_idx = {node: idx for idx, node in enumerate(self.node_list)}
        self.n_cities = len(self.node_list)
        self.pheromone = nx.to_numpy_array(cities,weight=None)

    def construct_solution(self, iterations:int=1, routes=None):
        best_routes = routes
        best_distances=[float('inf')]*self.n_ants
        best_acos=[]
        avg_acos=[]
        if routes:
            best_distances=[]
            for prev_route in routes:
                self.update_pheromones(prev_route, self.route_distance(prev_route),pherm_rate=10)
                best_distances.append(self.route_distance(prev_route))
            best_distances=best_distances[:self.n_ants]
            best_routes=best_routes[:self.n_ants]
        else:
            best_routes=[[]]*self.n_ants
        for it in range(iterations):
            print(f'iter: {it}')
            for _ in range(self.n_ants):
                route = self.ant_tour()
                if not route:
                    continue  # Skip if no valid route found
                # print(route)
                distance = self.route_distance(route)
                for i, best_distance in enumerate(best_distances):
                    if distance < best_distance:
                        if i < len(best_distances)-1:
                            best_distances[i+1:]=best_distances[i:-1]
                            best_routes[i+1:]=best_routes[i:-1]
                        best_routes[i] = route
                        best_distances[i] = distance
                self.update_pheromones(route, distance)
            if self.update_callback:
                self.update_callback(it,best_routes[0],best_distances[0],iterations)
            best_acos.append(min(best_distances))
            avg_acos.append(sum(best_distances)/len(best_distances))
        return best_routes, best_distances, (best_acos,avg_acos)

    def ant_tour(self):
        unvisited = set(self.cities.nodes())
        if not unvisited:
            return []
        current = random.choice(list(unvisited))
        route = [current]
        unvisited.remove(current)
        while unvisited:
            neighbors = list(self.cities.neighbors(current))
            possible_next = [n for n in neighbors if n in unvisited]
            if not possible_next:
                possible_next = list(unvisited)
            probabilities = self.calculate_probabilities(current, possible_next)
            if not probabilities:
                next_city = random.choice(list(neighbors))
            else:
                next_city = random.choices(possible_next, weights=probabilities, k=1)[0]
            if next_city in neighbors:
                route.append(next_city)
            else:
                route+=nx.shortest_path(self.cities,current,next_city,weight="weight")[1:]
            if next_city in unvisited:
                unvisited.remove(next_city)
            current = next_city
        return route

    def calculate_probabilities(self, current, possible_next):
        if not possible_next:
            return []
        current_idx = self.node_to_idx[current]
        total = 0.0
        pheromones = []
        for city in possible_next:
            city_idx = self.node_to_idx[city]
            pheromone = self.pheromone[current_idx][city_idx] ** self.alpha
            distance = self.route_distance([current,city])
            heuristic = (1.0 / distance) ** self.beta
            attraction = pheromone * heuristic
            pheromones.append(attraction)
            total += attraction
        if total == 0:
            return [1.0 / len(possible_next)] * len(possible_next)
        return [p / total for p in pheromones]

    def update_pheromones(self, route, distance,pherm_rate=1.0):
        if not route:
            return
        self.pheromone *= self.evaporation
        for i in range(len(route)):
            u = route[i]
            v = route[(i + 1) % len(route)]
            u_idx = self.node_to_idx[u]
            v_idx = self.node_to_idx[v]
            if self.cities.has_edge(u, v):
                self.pheromone[u_idx][v_idx] += pherm_rate / distance
    def route_distance(self, route):
        distance = 0.0
        for i in range(len(route)-1):
            u = route[i]
            v = route[(i + 1) % len(route)]
            if self.cities.has_edge(u, v):
                distance += self.cities[u][v].get('weight', 0.0)
            else:
                return float('inf')  # Path is invalid
        return distance

    def run_aco(self, iterations=10):
        best_route = None
        best_distance = float('inf')
        routes, distances, history = self.construct_solution(iterations)
        print(f'distance: {distances[0]}')
        if distances[0] < best_distance:
            best_route = routes[0]
            best_distance = distances[0]
        if best_route == None:
            raise Exception("route not found")
        return best_route, best_distance, history

if __name__ == "__main__":
    # Example usage
    # cities = make_graph(25, 0.7,3,5 )
    cities = make_graph(num_nodes=25,seed=656565)
    aco = ACO(cities, n_ants=25, alpha=1, beta=2, evaporation=0.5)
    best_route, best_distance, history = aco.run_aco(iterations=500)
    print("Best route:", best_route)
    print("Best distance:", best_distance)
    # Draw the graph
    positions = nx.get_node_attributes(cities, "pos")
    nx.draw(cities, pos=positions, with_labels=True, node_size=500, node_color='lightblue', font_size=8, font_weight='bold')
    edge_labels = nx.get_edge_attributes(cities, 'weight')
    # Draw the best route
    route_edges = [(best_route[i], best_route[(i + 1) % len(best_route)]) for i in range(len(best_route)-1)]
    nx.draw_networkx_edges(cities, edgelist=route_edges, pos=positions, arrows=True, width=4, edge_color='red')
    plt.show()


