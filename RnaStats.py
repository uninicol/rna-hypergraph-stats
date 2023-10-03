import hypernetx as hnx
import hypernetx.algorithms.hypergraph_modularity as hmod
import matplotlib.pyplot as plt

from IncidenceProducer import IncidenceProducer


class RnaStats:
    """Classe che raccoglie delle statistiche su una sequenza di RNA utilizzando un ipergrafo"""

    def __init__(self, forna_file_path: str) -> None:
        incidence_dict = IncidenceProducer(forna_file_path).get_incidence_dict()
        self.H = hnx.Hypergraph(incidence_dict)
        del incidence_dict
        self.__partitions: list = None
        self.__precomputed_H: list[set] = None

    def plot_hypergraph(self, size: tuple = (40, 40)) -> None:
        """Disegna un grafico che rappresenta l'ipergrafo costruito"""
        plt.subplots(figsize=size)
        hnx.draw(self.H)
        plt.show()

    def partitions(self) -> list:
        """Computa delle partizioni dell'ipergrafo"""
        if self.__precomputed_H is None:
            self.__precomputed_H = hmod.precompute_attributes(self.H)
        if self.__partitions is None:
            self.__partitions = hmod.kumar(self.__precomputed_H)
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
        return hmod.modularity(self.__precomputed_H, self.__partitions)

    def __get_hyperedges(self, node: int | str) -> list[int | str]:
        """
        Restituisce gli iperarchi che contengono il nodo selezionato
        :param node: il nodo contenuto dagli iperarchi
        :return: la lista di iperarchi che contengono il nodo selezionato
        """
        return [edge for edge in self.H.edges if node in self.H.edges[edge]]

    def get_subset_conductance(self, subset: set) -> float:
        """
        Restituisce la conduttanza di una partizione
        :param subset: la partizione
        :return: la conduttanza della partizione
        """
        subset2 = set(self.H.nodes) - subset
        ws = sum([len(self.__get_hyperedges(node)) for node in subset])
        was = 0
        for edge in self.H.edges:
            he_vertices = set(self.H.edges[edge])
            if len(he_vertices & subset) == 0:
                continue
            if len(he_vertices & subset2) == 0:
                continue
            was += len(he_vertices)
        return was / ws

    def get_partitions_conductance(self) -> enumerate[float]:
        """
        Restituisce la conduttanza di tutte le partizioni
        :return: l'enumerazione contenente la conduttanza di tutte le partizioni
        """
        return enumerate(
            [self.get_subset_conductance(subset) for subset in self.partitions()]
        )

    def plot_partitions_conductance(self) -> None:
        """Disegna un grafico che rappresenta la conduttanza delle partizioni"""
        cond = self.get_partitions_conductance()
        seq = []
        values = []
        for i, c in cond:
            seq.append(i)
            values.append(c)
        plt.bar(seq, values)
        plt.title("Conductance")
        plt.xlabel("Partition")
        plt.ylabel("Conductance")
        plt.show()

    def get_n_between_centrality(self, n: int = 1) -> dict:
        """
        Restituisce la n-between-centrality dei nucleotidi
        :param n: connectedness requirement
        :return: la n-between-centrality dei nucleotidi
        """
        return hnx.algorithms.s_betweenness_centrality(self.H, n)

    def plot_n_between_centrality(self, n: int = 1) -> None:
        """
        Disegna un grafico che rappresenta la n-between-centrality dei nucleotidi
        :param n: connectedness requirement
        """
        centrality = self.get_n_between_centrality(n)
        seq = list(centrality.keys())
        centr = list(centrality.values())

        plt.bar(seq, centr)
        plt.title(f"{n}-centrality")
        plt.xlabel("Nucleotides")
        plt.ylabel("Centrality")
        plt.show()
