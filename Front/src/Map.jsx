import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';
import { FeatureGroup } from 'react-leaflet';
import { LayersControl } from 'react-leaflet';
import { LayerGroup } from 'react-leaflet';

// Fix for default icon issues in Leaflet
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

function LocationMarker() {
    const [position, setPosition] = useState(null);
    const map = useMapEvents({
        click() {
            map.locate();
        },
        locationfound(e) {
            setPosition(e.latlng);
            map.flyTo(e.latlng, map.getZoom());
        },
    });

    return position === null ? null : (
        <Marker position={position}>
            <Popup>You are here</Popup>
        </Marker>
    );
}

const MapComponent = () => {

    var station1 = L.marker([45.78042293651376, 4.805052980122775]).bindPopup('Station 1.'),
    station2    = L.marker([45.77459195820043, 4.805615400117453]).bindPopup('Station 2.'),
    station3    = L.marker([45.76648943348018, 4.805197244080732]).bindPopup('Station 3.'),
    station4    = L.marker([45.75999759848578, 4.8263452847804444]).bindPopup('Station 4.');
  
    var ligne1 = L.layerGroup([station1,station2,station3,station4]);
  
  
    var station5 = L.marker([45.785412065920966, 4.8328326633148215]).bindPopup('Station 5.'),
    station6    = L.marker([45.779466924720936, 4.827478240866985]).bindPopup('Station 6.'),
    station7    = L.marker([45.7742904296382, 4.831895655815764]).bindPopup('Station 7.'),
    station8    = L.marker([45.770941013693516, 4.836235816300927]).bindPopup('Station 8.');
  
    var ligne2 = L.layerGroup([station5,station6,station7,station8]);
  
    var calqueDeBase = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '© OpenStreetMap'
    });
  
    var calqueSuivant = L.tileLayer('https://{s}.tile.openstreetmap.org/calqueSuivant/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors, Tiles style by Humanitarian OpenStreetMap Team hosted by OpenStreetMap France'});
  
  
    var calque = {
    "Calque de base" : calqueDeBase,
    "<span style = 'color : red'> Calque des lignes </span>" : calqueSuivant
    }
  
    var calqueAvecLignes = 
    {
    "Lignes": ligne1
    }
  
    var calqueTotal = {
    "Calque" : calque,
    "Calque des lignes" : calqueAvecLignes
    }
  
    var center = [48.6, 2.5]
  
    return (
      <MapContainer center={center} zoom={9} style={{ height: '100vh', width: '99%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LayersControl position="topright">
          <LayersControl.Overlay name="Marker with popup">
            <Marker position={center}>
              <Popup>
                First PopUp. <br /> Easily
              </Popup>
            </Marker>
          </LayersControl.Overlay>
          <LayersControl.Overlay checked name="Layer group with lignes">
            {/* <LayerGroup>
              <ligne1
                center = {station1}
              />
              <ligne2
                center={station2}
              />
            </LayerGroup> */}
  
            <LayerGroup>
              <calque>
              </calque>
  
              <calqueAvecLignes>
  
              </calqueAvecLignes>
  
              <calqueTotal>
  
              </calqueTotal>
  
            </LayerGroup>
  
          </LayersControl.Overlay>
          <LayersControl.Overlay name="Calque">
            <FeatureGroup pathOptions={{ color: 'purple' }}>
              <Popup>Popup in FeatureGroup</Popup>
            </FeatureGroup>
          </LayersControl.Overlay>
        </LayersControl>
        <LocationMarker/>
      </MapContainer>
    );
  };


function Map() {
    return (
        <MapComponent />
    );
}

export default Map;
