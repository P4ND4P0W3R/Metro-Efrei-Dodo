import { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMapEvents,
  Polyline,
  CircleMarker,
  Tooltip,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";
import {
  FeatureGroup,
  LayersControl,
  LayerGroup,
  Circle,
  Rectangle,
} from "react-leaflet";

// Fix for default icon issues in Leaflet
import L from "leaflet";
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
});


const MapComponent = () => {
  const [stations, setStations] = useState([]);
  // const [formData, setFormData] = useState({
  //   stopName: '',
  // });

  /* Call of the backend by API */
  useEffect(() => {
    const fetchStations = async () => {
      try {
        const response = await fetch("http://localhost:8000/stations");
        const data = await response.json();
        setStations(data);
      } catch (error) {
        console.error("Error fetching stations:", error);
      }
    };
    fetchStations();
  }, []);

  const [routes, setRoutes] = useState([]);
  // const [formData, setFormData] = useState({
  //   stopName: '',
  // });

  useEffect(() => {
    const fetchRoutes = async () => {
      try {
        const response = await fetch("http://localhost:8000/routes");
        const data = await response.json();
        setRoutes(data);
        
      } catch (error) {
        console.error("Error fetching stations:", error);
      }
    };
    fetchRoutes();
  }, []);

  /* permet d'envoyer les infos de la station dans le form en cliquant dessus */
  
  const handleMarkerClick = (stop) => {
    const newFormData = {
      stopName: stop.stop_name,
    };
    // setFormData(newFormData);
    sessionStorage.setItem('formDataStation', JSON.stringify(newFormData));
    console.log("Storing formData in localStorage from Map:", newFormData);
  };

  // /* --------------------------------------------------------------------- */

  // /* permet de gérer le hover des poppup*/

  // const RenderIcons = () => {
  //   const markerRef = useRef();
  
  //   const eventHandlers = useMemo(
  //     () => ({
  //       mouseover() {
  //         if (markerRef) markerRef.current.openPopup();
  //       },
  //       mouseout() {
  //         if (markerRef) markerRef.current.closePopup();
  //       }
  //     }),
  //     []
  //   );
  // }
  // /* --------------------------------------------------------------------- */

  /* Creation of the path by Dijsktra for the layer */

  function fastestPath(objectPath) {
    var pathTable = [];
    pathTable = objectPath.map((stop) => [
      stop.barycenter_lat,
      stop.barycenter_lon,
    ]);
    return pathTable;
  }

  var path = fastestPath(stations);

  var pathes = [[2.37698689849219,48.8908500522752],[2.24352563133847,48.8337005447186],[2.34779496818712,48.8938152613519],[2.32267315791628,48.8664072192036],[2.34346786469835,48.8311430914311]]



  /* Creation of the list with every lignes for the layer */
  function pathLignes(stations, routes) {
    const lignes = {};
  
    // Initialize each route with an empty array
    routes.forEach(route => {
      lignes[route.route_id] = [];
    });
  
    // Populate the lignes object with the coordinates of the stops
    stations.forEach(stop => {
      const routeIds = stop.route_ids;
  
      if (routeIds && routeIds.length > 0) {
        routeIds.forEach(routeId => {
          if (lignes[routeId]) {
            lignes[routeId].push([stop.barycenter_lat, stop.barycenter_lon]);
          } else {
            console.log(`Route ID ${routeId} is not defined in routes`);
          }
        });
      } else {
        console.log("Stop without route_ids:", stop);
      }
    });
  
    // Function to calculate the distance between two points
    function distance(point1, point2) {
      const [lat1, lon1] = point1;
      const [lat2, lon2] = point2;
      return Math.sqrt(Math.pow(lat1 - lat2, 2) + Math.pow(lon1 - lon2, 2));
    }
  
    // Sort the coordinates in each route using the Nearest Neighbor algorithm
    Object.keys(lignes).forEach(routeId => {
      const points = lignes[routeId];
      const sortedPoints = [];
      const visited = new Set();
  
      // Start with the first point
      let currentPoint = points[0];
      sortedPoints.push(currentPoint);
      visited.add(currentPoint);
  
      while (sortedPoints.length < points.length) {
        let nearestPoint = null;
        let nearestDistance = Infinity;
  
        // Find the nearest unvisited point
        points.forEach(point => {
          if (!visited.has(point)) {
            const dist = distance(currentPoint, point);
            if (dist < nearestDistance) {
              nearestDistance = dist;
              nearestPoint = point;
            }
          }
        });
  
        // Add the nearest point to the sorted list and mark it as visited
        if (nearestPoint) {
          sortedPoints.push(nearestPoint);
          visited.add(nearestPoint);
          currentPoint = nearestPoint;
        }
      }
  
      // Update the line with the sorted points
      lignes[routeId] = sortedPoints;
    });
  
    return lignes;
  }
  const subway_lines = pathLignes(stations, routes);
  console.log("Subway Lines:", subway_lines);

  /* Var for testing the Map */

  const center = [48.866667, 2.333333];

  /* Map creation */

  return (
    <MapContainer
      center={center}
      zoom={13}
      style={{ height: "100vh", width: "99%" }}
    >
      <TileLayer
        attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <LayersControl position="topright">

        <LayersControl.Overlay name="Layer with fastest path and stations">
        <LayerGroup>
            {stations.map((stop) => (
              <CircleMarker
                key={stop.parent_station}
                center={[stop.barycenter_lat, stop.barycenter_lon]}
                pathOptions={{ fillColor: "green" }}
                radius={6}
                eventHandlers={{
                  mouseover: (event) => event.target.openPopup(),
                  click: () => handleMarkerClick(stop),
                }}
              >
                <Popup>
                  <span>{stop.stop_name}</span>
                </Popup>
              </CircleMarker>
              
            ))}
            <Polyline positions={pathes} /> 

          </LayerGroup>
        </LayersControl.Overlay>
        <LayersControl.Overlay name="Layer with all lignes and stations">
          <LayerGroup>
            {stations.map((stop) => (
              <CircleMarker
                key={stop.parent_station}
                center={[stop.barycenter_lat, stop.barycenter_lon]}
                pathOptions={{ fillColor: "green" }}
                radius={6}
                eventHandlers={{
                  mouseover: (event) => event.target.openPopup(),
                  click: () => handleMarkerClick(stop),
                }}
              >
                <Popup>
                  <span>{stop.stop_name}</span>
                </Popup>
              </CircleMarker>
              
            ))}

            {Object.entries(subway_lines).map(([routeId, path]) => {
              const route = routes.find(route => route.route_id === routeId);
              const routeColor = route ? `#${route.route_color}` : '#FFFFFF'; // Ensure the color is prefixed with #
              return path.map((point, index) => {
                if (index < path.length - 1) {
                  return (
                    <Polyline
                      key={`${routeId}-${index}`}
                      positions={[point, path[index + 1]]}
                      pathOptions={{ color: routeColor }}
                    />
                  );
                }
                return null;
              });
            })}            

          </LayerGroup>
        </LayersControl.Overlay>
      </LayersControl>
      {/* <LocationMarker/> */}
    </MapContainer>
  );
};

/* ------------------------------------------------------------------------------ */

/* Call of the Map */

function Map() {
  return <MapComponent />;
}
/* ------------------------------------------------------------------------------ */

export default Map;
