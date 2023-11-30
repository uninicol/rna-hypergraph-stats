from collections import defaultdict

import hypernetx as hnx
import hypernetx.algorithms.hypergraph_modularity as hmod
import matplotlib.pyplot as plt
import networkx as nx

from hypergraph_folding.temperature_hypergraph import TemperatureFoldingHypergraph
from rna_stats.rna_stats import RnaHypergraphStats, TemporalRnaStats


class RnaStats(RnaHypergraphStats):
    """Classe che raccoglie delle statistiche su una sequenza di RNA utilizzando un ipergrafo"""

    def __init__(self, HG: hnx.Hypergraph) -> None:
        self.HG = HG
        self.__partitions: list = []

    def secondary_structures(self) -> dict:
        structures = {}
        for key, value in self.HG.incidence_dict.items():
            if not key.startswith("l") and not key.startswith("db"):
                structures[key] = value
        return structures

    def partitions(self) -> list:
        """Computa delle partizioni dell'ipergrafo"""
        if len(self.__partitions) == 0:
            self.__partitions = hmod.kumar(self.HG)
        return self.__partitions

    def partition(self, n: int) -> set:
        """
        Restituisce la partizione scelta
        :param n: numero della partizione
        :return: la partizione scelta
        """
        self.partitions()
        return self.__partitions[n]

    def modularity(self) -> float:
        """
        Restituisce la modularità dell'ipergrafo
        :return: la modularità dell'ipergrafo
        """
        self.partitions()
        return hmod.modularity(self.HG, self.__partitions)

    def subset_conductance(self, subset: set) -> float:
        """
        Restituisce la conduttanza di una partizione
        :param subset: la partizione
        :return: la conduttanza della partizione
        """
        return hmod.conductance(self.HG, subset)

    def partitions_conductance(self) -> list[float]:
        """
        Restituisce la conduttanza di tutte le partizioni
        :return: la lista contenente la conduttanza di tutte le partizioni
        """
        return [self.subset_conductance(subset) for subset in self.partitions()]

    def s_between_centrality(self, s=1) -> dict:
        """
        Restituisce la n-between-centrality dei nucleotidi
        :param s: connectedness requirement
        :return: la n-between-centrality dei nucleotidi
        """
        return hnx.algorithms.s_betweenness_centrality(self.HG, s)

    def plot_hypergraph(self, size: tuple = (40, 40)) -> None:
        """Disegna un grafico che rappresenta l'ipergrafo costruito"""
        if len(self.HG.nodes) > 250:
            plt.subplots(figsize=size)
            G = hmod.two_section(self.HG).to_networkx()
            nx.draw(G, node_size=50)
            plt.show()
        else:
            plt.subplots(figsize=size)
            hnx.draw(self.HG, **{'layout_kwargs': {'seed': 39}})
            plt.show()

    def plot_partitions_conductance(self, size=(20, 10)) -> None:
        """Disegna un grafico che rappresenta la conduttanza delle partizioni"""
        plt.subplots(figsize=size)
        cond = self.partitions_conductance()
        seq = []
        values = []
        for i, c in enumerate(cond):
            seq.append(i)
            values.append(c)
        plt.bar(seq, values)
        plt.title("Conductance")
        plt.xlabel("Partition")
        plt.ylabel("Conductance")
        plt.show()

    def plot_n_between_centrality(self, n: int = 1, size=(20, 10)) -> None:
        """
        Disegna un grafico che rappresenta la n-between-centrality dei nucleotidi
        :param n: connectedness requirement
        """
        plt.subplots(figsize=size)
        centrality = self.s_between_centrality()
        seq = list(centrality.keys())
        centr = list(centrality.values())

        plt.bar(seq, centr)
        plt.title(f"{n}-centrality")
        plt.xlabel("Nucleotides")
        plt.ylabel("Centrality")
        plt.show()

    def structure_differences(self, hypergraph: hnx.Hypergraph) -> dict:
        """
        Restituisce un dizionario che indica le strutture aggiunte o rimosse dall'ipergrafo preso in input
        :param hypergraph : ipergrafo da mettere a confronto
        """
        if len(self.HG.nodes) != len(hypergraph.nodes):
            raise Exception("Ipergrafi hanno un numero diverso di nodi")
        this_structures = self.secondary_structures()
        other_structures = RnaStats(hypergraph).secondary_structures()

        this_count = defaultdict(int)
        for name in this_structures.keys():
            this_count[name[0]] = this_count[name[0]] + 1
        other_count = defaultdict(int)
        for name in other_structures.keys():
            other_count[name[0]] = other_count[name[0]] + 1

        result = {key: this_count[key] - other_count[key] for key in this_count if
                  key in other_count and this_count[key] != other_count[key]}
        return result

    def get_nucleotides_change_structure(self, hypergraph: hnx.Hypergraph) -> list:
        """
        Restituisce i nucleotidi che hanno subito un cambiamento di struttura
        :param hypergraph : ipergrafo da mettere a confronto
        """
        if len(self.HG.nodes) != len(hypergraph.nodes):
            raise Exception("Ipergrafi non hanno lo stesso numero di nucleotidi")
        this_structures = self.secondary_structures()
        other_structures = RnaStats(hypergraph).secondary_structures()
        differences = []
        # Scorro le strutture dei due ipergrafi e individuo i nucleotidi che cambiano struttura
        for this_name, this_structure in this_structures.items():
            for other_name, other_structure in other_structures.items():
                if this_name == other_name:
                    differences.append([item for item in this_structure if item not in other_structure])
                    break

        return [element for row in differences for element in row]


class TemperatureFoldingStats(TemporalRnaStats):

    def __init__(self, THG: TemperatureFoldingHypergraph) -> None:
        self.THG = THG

    def get_nucleotide_sensibility_to_changes(self, start_temp, end_temp):
        """Misura la sensibilità al cambiamento di struttura dei nucleotidi in un range di temperatura"""
        self.THG.insert_temperature_range(start_temp, end_temp)
        counts = defaultdict(int)
        for temp in range(start_temp, end_temp):
            h1 = self.THG.get_hypergraph(temp)
            h2 = self.THG.get_hypergraph(temp + 1)
            if h1 is h2:
                continue
            st = RnaStats(h1)
            elements = st.get_nucleotides_change_structure(h2)
            for elem in elements:
                counts[elem] += 1
        return counts

    def plot_nucleotide_sensibility_to_changes(self, start_temp, end_temp, size=(20, 10)):
        sens = self.get_nucleotide_sensibility_to_changes(start_temp, end_temp)
        ordered_keys = sorted(sens.keys())
        ordered_values = [sens[key] for key in ordered_keys]
        seq = list(ordered_keys)
        centr = list(ordered_values)
        plt.subplots(figsize=size)
        plt.bar(seq, centr)
        plt.show()
