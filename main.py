#!/usr/bin/python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
import networkx as nx
import threading
import sys
import random
from mplt import Gtk4MpltNx
from settings import SettingsWidget
from gen_graph import make_graph
from ga import GA
from aco import ACO
from HybridGAACO import HybridGAACO


class MyWindow(Gtk.ApplicationWindow):
    anim=False
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Hello GTK")
        self.set_default_size(300, 100)
        self.set_icon_name("org.artemis.ea")

        self.settings = SettingsWidget()
        self.settings.connect("run", self.on_run_clicked)
        self.set_child(self.settings)

    def on_run_clicked(self, settings, data:dict):
        print("Button clicked!")
        G = make_graph(data["nodes"][0],data["edge_probability"][0],data["min_traffic"][0],data["max_traffic"][0],data["seed"][0] if not data["seed"][0]=="None" else None)
        if self.anim:
            self.show_mpltnx(G,True,False,None,f'Iteration:  (Distance: )')
            self.update_i=0;
        for i in range(5):
            threading.Thread(target=self.run_task,args=(data,G,i),daemon=True).start()


    def run_task(self,data:dict,G:nx.DiGraph,iteration:int):
        random.seed(data["training_seed"][0] if not data["training_seed"][0]=="None" else None)
        print(data["type"][0])
        route=[]
        distance=0
        history=tuple()
        if data["type"][0]=="GA":
            ga=GA(G,pop_size=50,mutation_rate=0.02,update_callback=self.update_cb)
            routes,history=ga.create_solution(50)
            route = routes[0]
            distance=ga.route_distance(route)
        elif data["type"][0]=="ACO":
            aco = ACO(G, n_ants=25, alpha=1, beta=2, evaporation=0.5,update_callback=self.update_cb)
            route, distance, history = aco.run_aco(iterations=5000)
        elif data["type"][0]=="HYBGA":
            HybridGAACO_TEST= HybridGAACO(G,pop_size=50,mutation_rate=0.02, n_ants=25, alpha=1, beta=2, evaporation=0.5,update_callback=self.update_cb)
            route,distance,history=HybridGAACO_TEST.run_ga_plus_aco(ga_generations=50, aco_iterations=5000, cycles=5)
        elif data["type"][0]=="HYBAG":
            HybridGAACO_TEST= HybridGAACO(G,pop_size=50,mutation_rate=0.02, n_ants=25, alpha=1, beta=2, evaporation=0.5,update_callback=self.update_cb)
            route,distance,history=HybridGAACO_TEST.run_aco_plus_ga(ga_generations=50, aco_iterations=500, cycles=5)
        route_edges=[(route[i],route[i+1]) for i in range(len(route)-1)]
        GLib.idle_add(self.show_mpltnx,G,True,False,route_edges,f'Solution (Distance: {distance:.2f})', history, iteration)

    def show_mpltnx(self,graph: nx.DiGraph, pos_available: bool=True, write_weights: bool=True, route: list=None, title: str="", history=tuple(), i:int=0):
        self.set_default_size(900,600)
        self.mpltnx = Gtk4MpltNx(graph,pos_available,write_weights,route,title)
        self.set_child(self.mpltnx)
        return False

    def update_cb(self,i,r,d,t):
        print(i,file=sys.stderr)
        print(t,file=sys.stderr)
        print(i/t,file=sys.stderr)
        if self.anim and (i%100==0):
            self.update_mpltnx(r,f'Iteration: {i} (Distance: {d:.2f})',i)
        self.settings.progress_update(i/t)
        return None
    def update_mpltnx(self,route:list,title,i):
        if i>self.update_i:
            self.update_i=i;
            print(f'{title} Route(start): {route}',file=sys.stderr)
            route_edges=[(route[i],route[i+1]) for i in range(len(route)-1)]
            self.mpltnx.update(route_edges,title)
        return False


class MyApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.artemis.ea")

    def do_activate(self):
        win = MyWindow(self)
        win.present()

app = MyApp()
app.run()
