import time
from copy import copy


# Ce code n'est pas testé, il faudra le tester avec les données qu'on aura récupérées


class Station:
    def __init__(self, num, name):
        self.id = num  # id (int)
        self.name = name  # nom (String)
        self.lines = []  # lignes de métro reliées (list(TrainLine))
        self.links = []  # liste des RailRoad connectées (list(RailRoad))
        self.transits = {}  # liste des temps de transit (dict(tuple(link1, link2) = int(transit_time))

    def get_links(self):
        return self.links


class RailRoad:
    def __init__(self, station1, station2, length, line, direction, oriented):
        self.start = station1  # station reliée à une extrémité
        self.end = station2  # station reliée à l'autre extrémité
        self.time = length  # durée
        self.trainLine = line  # Ligne de métro (int)
        self.direction = direction  # direction sur la ligne de métro (int)
        self.orientation = oriented  # Double sens ou non (tuple : (station_début, station_fin), le tuple est vide si c'est en double sens)

    def get_time(self):
        return self.time

    def get_start(self):
        return self.start

    def get_end(self):
        return self.end


class TrainLine:
    def __init__(self, num, end_stations):
        self.id = num  # id (int)
        self.stations = []  # liste des stations (list(Station))
        self.endPoints = end_stations  # spécifie le premier terminus
        self.directions = []  # regroupe les stations en fonction des directions, exemple avec 3 directions : [[Station1, Station2, ...][StationN, stationN+1, ...][StationM, StationM+1, ...]]


class MetroSystem:
    def __init__(self):
        self.stations = []  # toutes les stations (list(Station))
        self.lines = []  # toutes les lignes (list(TrainLine))

    def prim(self, start_station):

        if not self.stations or start_station not in self.stations:  # vérification de l'objet fourni
            return MetroSystem()

        new_graph = MetroSystem()
        visited_nodes = set()
        pq = []

        visited_nodes.add(start_station)
        new_graph.stations.append(start_station)

        for link in start_station.get_links():  # premier remplissage de la pile
            pq.append((link.get_time(), link))

        while len(visited_nodes) < len(self.stations) and pq:  # tant que tous les sommets ne sont pas ajoutés ...

            # On récupère les données du lien
            weight, min_link = pq.pop(0)
            end1 = min_link.get_start()
            end2 = min_link.get_end()

            if end1 in visited_nodes and end2 in visited_nodes:  # On vérifie si l'arête est utile (Un sommet pouvant être ajouté)
                continue  # On passe à la prochaine si ce n'est pas le cas

            new_node = end2 if end1 in visited_nodes else end1  # On récupère le nouveau sommet
            visited_nodes.add(new_node)
            new_graph.stations.append(new_node)

            for link in new_node.get_links():  # On vérifie les nouveaux liens apportés par ce sommet
                if link.get_start() not in visited_nodes or link.get_end() not in visited_nodes:
                    pq.append((link.get_time(), link))

        return new_graph

    def is_strong_connexe(self):
        output = []
        checked = [self.stations[0]]
        stack = [(self.stations[0], [])]

        while len(checked) != len(self.stations) or stack:
            if not stack:
                checked.sort(key=lambda station_id: station.id)
                output.append(copy(checked))
                checked.clear()

                for station in self.stations:
                    if not is_in_nested_list(station, output):
                        stack.append((station, []))
                        break

            current, path = stack.pop(0)

            for link in current.get_links():
                neighbor = link.get_end() if link.get_start() == current and (not link.orientation or link.orientation == (link.get_start(), link.get_end())) else link.get_start() if (not link.orientation or link.orientation == (link.get_end(), link.get_start())) else None
                if not neighbor:
                    continue

                if neighbor not in checked:
                    stack.append((neighbor, path + [current]))
                    checked.append(neighbor)

        return output

    def is_connected(self):
        output = []
        checked = [self.stations[0]]
        stack = [(self.stations[0], [])]

        while len(checked) != len(self.stations) or stack:
            if not stack:
                checked.sort(key=lambda station_id: station.id)
                output.append(copy(checked))
                checked.clear()

                for station in self.stations:
                    if not is_in_nested_list(station, output):
                        stack.append((station, []))
                        break

            current, path = stack.pop(0)

            for link in current.get_links():
                neighbor = link.get_end() if link.get_start() == current else link.get_start()
                if not neighbor:
                    continue

                if neighbor not in checked:
                    stack.append((neighbor, path + [current]))
                    checked.append(neighbor)

        return output


def is_in_nested_list(element, nested_list):
    for item in nested_list:
        if isinstance(item, list):
            if is_in_nested_list(element, item):
                return True
        elif item == element:
            return True
    return False


def dijkstra_station(start_station, end_station):
    if not start_station or not end_station:
        return None

    start_time = time.time()  # début d'enregistrement temps d'exécution

    stack = [(0, start_station, [], None)]  # création de la pile
    min_distances = {start_station: 0}  # Dictionnaire des distances minimales, initialisées avec la station de départ

    while stack:
        current_cost, current_station, path_taken, previous_link = stack.pop(0)

        # Si nous avons atteint la station de destination, renvoyer le chemin et le coût total
        if current_station == end_station:
            end_time = time.time()
            return [path_taken + [end_station], current_cost], end_time - start_time

        # Parcourir chaque lien de la station actuelle
        for link in current_station.get_links():
            if previous_link and link == previous_link:
                continue  # Ignorer le lien précédent

            # Calcul du coût de transit
            if not previous_link:
                transit_cost = 0  # Pas de coût de transit pour la première itération
            else:
                # Rechercher le coût de transit dans les deux sens (link, previous_link) et (previous_link, link)
                transit_cost = current_station.transits.get((link, previous_link), 0)
                transit_cost = current_station.transits.get((previous_link, link), transit_cost)

            # Détermination de la station voisine en fonction de l'orientation du lien
            if (not link.orientation or link.orientation == (link.get_start(), link.get_end())) and link.get_start() == current_station:
                neighbor = link.get_end()
            elif (not link.orientation or link.orientation == (link.get_end(), link.get_start())) and link.get_end() == current_station:
                neighbor = link.get_start()
            else:
                neighbor = None

            if neighbor:
                new_cost = current_cost + int(link.get_time()) + transit_cost  # Calcul du nouveau coût

                if neighbor not in min_distances or new_cost < min_distances[neighbor]:
                    # Mettre à jour la distance minimale et ajout à la pile
                    min_distances[neighbor] = new_cost
                    stack.append((new_cost, neighbor, path_taken + [current_station], link))

    return None


