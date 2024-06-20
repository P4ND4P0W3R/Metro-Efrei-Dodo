import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, Polyline, CircleMarker, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';
import { FeatureGroup, LayersControl,LayerGroup,Circle,Rectangle} from 'react-leaflet';

// Fix for default icon issues in Leaflet
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

/* Call of the backend by API */

// function getElementByApi()
// {

// }

const Data = [
  {
      "stop_id": "IDFM:463070",
      "stop_name": "Wagram",
      "barycenter_lon": 2.30467308758443,
      "barycenter_lat": 48.8838463907272,

  },
  {
      "stop_id": "IDFM:463218",
      "stop_name": "Louvre - Rivoli",
      "barycenter_lon": 2.34099642727202,
      "barycenter_lat": 48.8609073342633,
  },
  {
      "stop_id": "IDFM:22104",
      "stop_name": "Château de Vincennes",
      "barycenter_lon": 2.44054009540611,
      "barycenter_lat": 48.8443175143136,

  },
  {
      "stop_id": "IDFM:483313",
      "stop_name": "Barbara",
      "barycenter_lon": 2.31741740964893,
      "barycenter_lat": 48.8097987811254,
  },
  {
      "stop_id": "IDFM:21933",
      "stop_name": "Bonne Nouvelle",
      "barycenter_lon": 2.34849409793754,
      "barycenter_lat": 48.8706433160169,
  },
  {
      "stop_id": "IDFM:463306",
      "stop_name": "Saint-Michel",
      "barycenter_lon": 2.34399179903329,
      "barycenter_lat": 48.8535940775681,
  }
];

const objectPath = [
  {
      "stop_id": "IDFM:463070",
      "stop_name": "Wagram",
      "barycenter_lon": 2.30467308758443,
      "barycenter_lat": 48.8838463907272,

  },
  {
      "stop_id": "IDFM:463218",
      "stop_name": "Louvre - Rivoli",
      "barycenter_lon": 2.34099642727202,
      "barycenter_lat": 48.8609073342633,
  },
  {
      "stop_id": "IDFM:22104",
      "stop_name": "Château de Vincennes",
      "barycenter_lon": 2.44054009540611,
      "barycenter_lat": 48.8443175143136,

  },
  {
      "stop_id": "IDFM:483313",
      "stop_name": "Barbara",
      "barycenter_lon": 2.31741740964893,
      "barycenter_lat": 48.8097987811254,
  },
  {
      "stop_id": "IDFM:21933",
      "stop_name": "Bonne Nouvelle",
      "barycenter_lon": 2.34849409793754,
      "barycenter_lat": 48.8706433160169,
  },
  {
      "stop_id": "IDFM:463306",
      "stop_name": "Saint-Michel",
      "barycenter_lon": 2.34399179903329,
      "barycenter_lat": 48.8535940775681,
  }
];


/* Geolocalisation */

// function LocationMarker() {
//     const [position, setPosition] = useState(null);
//     const map = useMapEvents({
//         click() {
//             map.locate();
//         },
//         locationfound(e) {
//             setPosition(e.latlng);
//             map.flyTo(e.latlng, map.getZoom());
//         },
//     });

//     return position === null ? null : (
//         <Marker position={position}>
//             <Popup>You are here</Popup>
//         </Marker>
//     );
// }

/* ------------------------------------------------------------------------------ */


/* Creation of the path by Dijsktra for the layer */

function fastestPath(objectPath)
{
  var pathTable = []
  pathTable = objectPath.map(stop => [stop.barycenter_lat, stop.barycenter_lon]);
  return pathTable;
}

var path = fastestPath(objectPath);

/* ------------------------------------------------------------------------------ */


/* Creation of the list with every lignes for the layer */
var lignes = []

function pathLignes(Data)
{
  lignes = Data.map(stop => [stop.barycenter_lon, stop.barycenter_lat]);
  return lignes;
}

var subway_lignes = pathLignes(Data)

/* ------------------------------------------------------------------------------ */

/* Regroupe all stations to display them */

function getStation(Data)
{
  var pathTable = []
  pathTable = objectPath.map(stop => [stop.stop_name,stop.barycenter_lat, stop.barycenter_lon]);
  return pathTable;
}

var localisationStation = getStation(Data)

/* ------------------------------------------------------------------------------ */

/* Var for testing the Map */

var station_concorde = [48.8655981, 2.3212448]
var station_montparnasse = [48.842, 2.3203]


const ligne = 
[ [[45.78042293651376, 4.805052980122775], [45.77459195820043, 4.805615400117453],
    [45.76648943348018, 4.805197244080732], [45.75999759848578, 4.8263452847804444]
  ]
]

const polyline = 
[
  [48.8655981, 2.3212448],
  [48.842, 2.3203],
]


const center = [48.866667, 2.333333];


/* Map creation */

const MapComponent = () => {
  
    return (
      <MapContainer center={center} zoom={13} style={{ height: '100vh', width: '99%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LayersControl position="topright">

          <LayersControl.Overlay name="Layer with fastest path">
            <LayerGroup>
              <Polyline pathOptions={{ color: 'purple' }} positions={path}/>
            </LayerGroup>
          </LayersControl.Overlay>

          <LayersControl.Overlay checked name="Layer with fastest path and stations">
            <LayerGroup>
              {objectPath.map((stop) => (
                <CircleMarker
                  key={stop.station_id}
                  center={[stop.barycenter_lat, stop.barycenter_lon]}
                  pathOptions={{ fillColor: 'red' }}
                  radius={10}
                >
                  <Tooltip permanent>
                    <span>{stop.stop_name}</span>
                  </Tooltip>
                </CircleMarker>
              ))}
              
              <Polyline positions={path}/>

            </LayerGroup>
          </LayersControl.Overlay>
          <LayersControl.Overlay checked name="Layer with just stations">
            <LayerGroup>
              {objectPath.map((stop) => (
                <CircleMarker
                  key={stop.station_id}
                  center={[stop.barycenter_lat, stop.barycenter_lon]}
                  pathOptions={{ fillColor: 'green' }}
                  radius={10}
                >
                  <Tooltip permanent>
                    <span>{stop.stop_name}</span>
                  </Tooltip>
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
    return (
        <MapComponent />
    );
}
/* ------------------------------------------------------------------------------ */

export default Map;
