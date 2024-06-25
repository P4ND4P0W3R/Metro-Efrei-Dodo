import { useState, useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMapEvents,
  Polyline,
  CircleMarker,
  Tooltip,
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';
import {
  FeatureGroup,
  LayersControl,
  LayerGroup,
  Circle,
  Rectangle,
} from 'react-leaflet';

// Fix for default icon issues in Leaflet
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
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
        const response = await fetch('http://localhost:8000/stations');
        const data = await response.json();
        setStations(data);
      } catch (error) {
        console.error('Error fetching stations:', error);
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
        const response = await fetch('http://localhost:8000/routes');
        const data = await response.json();
        setRoutes(data);
      } catch (error) {
        console.error('Error fetching routes:', error);
      }
    };
    fetchRoutes();
  }, []);

  const handleMarkerClick = stop => {
    const newFormData = {
      stopName: stop.stop_name,
    };
    sessionStorage.setItem('formDataStation', JSON.stringify(newFormData));
    console.log('Storing formData in localStorage from Map:', newFormData);
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
    pathTable = objectPath.map(stop => [
      stop.barycenter_lat,
      stop.barycenter_lon,
    ]);
    return pathTable;
  }

  var path = fastestPath(stations);

  var pathes = [
    [2.37698689849219, 48.8908500522752],
    [2.24352563133847, 48.8337005447186],
    [2.34779496818712, 48.8938152613519],
    [2.32267315791628, 48.8664072192036],
    [2.34346786469835, 48.8311430914311],
  ];

  const pathLignes = (stations, routes) => {
    const lignes = {};

    routes.forEach(route => {
      lignes[route.route_id] = {
        mainPath: [],
        decimalStops: [],
      };
    });

    stations.forEach(stop => {
      stop.route_ids_with_sequences.forEach(routeData => {
        const { route_id, stop_sequence } = routeData;
        if (lignes[route_id]) {
          if (Number.isInteger(stop_sequence)) {
            lignes[route_id].mainPath.push({
              coordinates: [stop.barycenter_lat, stop.barycenter_lon],
              stop_sequence: stop_sequence,
            });
          } else {
            lignes[route_id].decimalStops.push({
              coordinates: [stop.barycenter_lat, stop.barycenter_lon],
              stop_sequence: stop_sequence,
            });
          }
        } else {
          console.log(`Route ID ${route_id} is not defined in routes`);
        }
      });
    });

    // Sort main paths and decimal stops by stop_sequence
    Object.values(lignes).forEach(lineData => {
      lineData.mainPath.sort((a, b) => a.stop_sequence - b.stop_sequence);
      lineData.decimalStops.sort((a, b) => a.stop_sequence - b.stop_sequence);
    });

    return lignes;
  };

  const subwayLines = pathLignes(stations, routes);

  const center = [48.866667, 2.333333];

  return (
    <MapContainer
      center={center}
      zoom={13}
      style={{ height: '100vh', width: '99%' }}
    >
      <TileLayer
        attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <LayersControl position="topright">
        <LayersControl.Overlay name="Layer with fastest path and stations">
          <LayerGroup>
            {stations.map(stop => (
              <CircleMarker
                key={stop.parent_station}
                center={[stop.barycenter_lat, stop.barycenter_lon]}
                pathOptions={{ fillColor: 'green' }}
                radius={6}
                eventHandlers={{
                  mouseover: event => event.target.openPopup(),
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
            {stations.map(stop => {
              // Find the first route associated with the stop to determine its color
              const firstRouteId = stop.route_ids_with_sequences[0]?.route_id;
              const route = routes.find(
                route => route.route_id === firstRouteId,
              );
              const routeColor = route ? `#${route.route_color}` : 'green';

              return (
                <CircleMarker
                  key={stop.parent_station}
                  center={[stop.barycenter_lat, stop.barycenter_lon]}
                  pathOptions={{ fillColor: routeColor, color: routeColor }}
                  radius={2}
                  eventHandlers={{
                    mouseover: event => event.target.openPopup(),
                    click: () => handleMarkerClick(stop),
                  }}
                >
                  <Popup>
                    <span>{stop.stop_name}</span>
                  </Popup>
                </CircleMarker>
              );
            })}

            {Object.entries(subwayLines).map(([routeId, lineData]) => {
              const route = routes.find(route => route.route_id === routeId);
              const routeColor = route ? `#${route.route_color}` : '#FFFFFF';

              const polylines = [];

              // Draw main path
              const mainPathCoords = lineData.mainPath.map(
                stop => stop.coordinates,
              );
              if (mainPathCoords.length > 1) {
                polylines.push(
                  <Polyline
                    key={`${routeId}-main`}
                    positions={mainPathCoords}
                    pathOptions={{ color: routeColor }}
                  />,
                );
              }

              // Draw decimal stops and link to main path
              const decimalStopsCoords = lineData.decimalStops.map(
                stop => stop.coordinates,
              );
              if (decimalStopsCoords.length > 1) {
                // Link first decimal stop
                const firstDecimalStopSequence = Math.floor(
                  lineData.decimalStops[0].stop_sequence,
                );
                const prevMainStopIndex = lineData.mainPath.findIndex(
                  stop => stop.stop_sequence === firstDecimalStopSequence - 1,
                );
                if (prevMainStopIndex !== -1) {
                  polylines.push(
                    <Polyline
                      key={`${routeId}-link-first`}
                      positions={[
                        lineData.mainPath[prevMainStopIndex].coordinates,
                        decimalStopsCoords[0],
                      ]}
                      pathOptions={{ color: routeColor }}
                    />,
                  );
                }

                // Link last decimal stop
                const lastDecimalStopSequence = Math.floor(
                  lineData.decimalStops[lineData.decimalStops.length - 1]
                    .stop_sequence,
                );
                const nextMainStopIndex = lineData.mainPath.findIndex(
                  stop => stop.stop_sequence === lastDecimalStopSequence + 1,
                );
                if (nextMainStopIndex !== -1) {
                  polylines.push(
                    <Polyline
                      key={`${routeId}-link-last`}
                      positions={[
                        decimalStopsCoords[decimalStopsCoords.length - 1],
                        lineData.mainPath[nextMainStopIndex].coordinates,
                      ]}
                      pathOptions={{ color: routeColor }}
                    />,
                  );
                }

                // Draw the decimal branch itself
                polylines.push(
                  <Polyline
                    key={`${routeId}-decimal`}
                    positions={decimalStopsCoords}
                    pathOptions={{ color: routeColor }}
                  />,
                );
              }

              return polylines;
            })}
          </LayerGroup>
        </LayersControl.Overlay>
      </LayersControl>
    </MapContainer>
  );
};

function Map() {
  return <MapComponent />;
}

export default Map;
