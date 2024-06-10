import heapq
from copy import copy


# Ce code n'est pas testé, il faudra le tester avec les données qu'on aura récupérées


class Station:
    def __init__(self, num, name, lines):
        self.id = num  # id (int)
        self.name = name  # nom (String)
        self.lines = lines  # lignes de métro reliées (list(TrainLine))
        self.links = []  # liste des RailRoad connectées (list(RailRoad))

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

    def prim(self, start_station_id):

        if not self.stations or start_station_id >= len(self.stations):  # vérification de l'objet fourni
            return MetroSystem()

        new_graph = MetroSystem()
        visited_nodes = set()
        pq = []

        start_node = self.stations[start_station_id]
        visited_nodes.add(start_node)
        new_graph.stations.append(start_node)

        for link in start_node.get_links():  # premier remplissage de la liste de priorité
            heapq.heappush(pq, (link.get_time(), link))  # équivalent à append() mais prend en compte le coût pour réordonner la liste

        while len(visited_nodes) < len(self.stations):  # tant que tous les sommets ne sont pas ajoutés ...
            if not pq:  # On vérifie s'il reste des arêtes dans la pile
                break

            # On récupère les données du lien, la file de priorité nous permet de sélectionner le lien le plus optimal en fonction du coût
            weight, min_link = heapq.heappop(pq)
            end1 = min_link.get_start()
            end2 = min_link.get_end()

            if end1 in visited_nodes and end2 in visited_nodes:  # On vérifie si l'arête est utile (Un sommet pouvant être ajouté)
                continue  # On passe au prochain objet de pq si ce n'est pas le cas

            new_node = end2 if end1 in visited_nodes else end1  # On récupère le nouveau sommet
            visited_nodes.add(new_node)
            new_graph.stations.append(new_node)

            for link in new_node.get_links():  # On vérifie les nouveaux liens de ce sommet
                if link.get_start() not in visited_nodes or link.get_end() not in visited_nodes:
                    heapq.heappush(pq, (link.get_time(), link))

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

    pq = [(0, start_station, [])]  # Cette pile va se comporter comme une file de priorité
    min_distances = {start_station: 0}  # Ce dictionnaire va référencer les coûts au niveau de chaque station

    while pq:
        current_cost, current_station, path_taken = heapq.heappop(pq)

        if current_station == end_station:  # On vérifie si on est arrivés
            return [path_taken + [end_station], current_cost]

        for link in current_station.get_links():  # On vérifie pour chacun des liens de la station

            neighbor = link.get_end() if link.get_start() == current_station and (not link.oriented or link.oriented == (link.get_start, link.get_end)) else link.get_start() if (not link.oriented or link.oriented == (link.get_end, link.get_start)) else None
            # On récupère la station voisine en prenant en compte l'orientation

            if neighbor:
                new_cost = current_cost + link.get_time()  # On met à jour le coût

                if neighbor not in min_distances or new_cost < min_distances[neighbor]:
                    # Il y a 2 cas : soit l'algorithme n'est pas encore passé par cette station, ainsi on l'ajoute au dictionnaire,
                    # soit le nouveau coût est plus faible que le précédent, dans ce cas on met à jour le dictionnaire. Sinon on passe au prochain voisin.

                    min_distances[neighbor] = new_cost
                    heapq.heappush(pq, (new_cost, neighbor, path_taken + [current_station]))

    return None


exit(0)
