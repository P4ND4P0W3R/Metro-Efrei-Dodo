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

/* Call of the backend by API */

const MapComponent = () => {
  const [stations, setStations] = useState([]);

  useEffect(() => {
    const fetchStations = async () => {
      try {
        const response = await fetch("http://localhost:8000/barycenters");
        const data = await response.json();
        setStations(data);
      } catch (error) {
        console.error("Error fetching stations:", error);
      }
    };
    fetchStations();
  }, []);



  /* Creation of the path by Dijsktra for the layer */

  function fastestPath(objectPath) {
    var pathTable = [];
    pathTable = objectPath.map((stop) => [
      stop.barycenter_lat,
      stop.barycenter_lon,
    ]);
    return pathTable;
  }

  // var path = fastestPath(ObjectPath);



  /* Creation of the list with every lignes for the layer */
  var lignes = [];

  function pathLignes(stations) {
    lignes = stations.map((stop) => [stop.barycenter_lon, stop.barycenter_lat]);
    return lignes;
  }

  var subway_lignes = pathLignes(stations);

  /* Regroupe all stations to display them */

  // function getStation(Data) {
  //   var pathTable = [];
  //   pathTable = Data.map((stop) => [
  //     stop.stop_name,
  //     stop.barycenter_lat,
  //     stop.barycenter_lon,
  //   ]);
  //   return pathTable;
  // }

  // var localisationStation = getStation(stations);

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
        <LayersControl.Overlay name="Layer with fastest path">
          <LayerGroup>
            {/* <Polyline pathOptions={{ color: "purple" }} positions={path} /> */}
          </LayerGroup>
        </LayersControl.Overlay>

        <LayersControl.Overlay name="Layer with fastest path and stations">
          <LayerGroup>
            {stations.map((stop) => (
              <CircleMarker
                key={stop.parent_station}
                center={[stop.barycenter_lat, stop.barycenter_lon]}
                pathOptions={{ fillColor: "red" }}
                radius={5}
              >
                <Popup permanent>
                  <span>{stop.stop_name}</span>
                </Popup>
              </CircleMarker>
            ))}
            {/* <Polyline positions={path} /> */}

          </LayerGroup>
        </LayersControl.Overlay>
        <LayersControl.Overlay name="Layer with just stations">
          <LayerGroup>
            {stations.map((stop) => (
              <CircleMarker
                key={stop.parent_station}
                center={[stop.barycenter_lat, stop.barycenter_lon]}
                pathOptions={{ fillColor: "green" }}
                radius={5}
                eventHandlers={{
                  mouseover: (event) => event.target.openPopup(),}}
              >
                <Popup>
                  <span>{stop.stop_name}</span>
                </Popup>
              </CircleMarker>
            ))}
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
