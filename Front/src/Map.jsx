import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

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
    return (
        <MapContainer center={[48.866667, 2.333333]} zoom={13} style={{ height: '100vh', width: '100%' }}>
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Marker position={[48.866667, 2.333333]}>
                <Popup>
                    A pretty CSS3 popup. <br /> Easily customizable.
                </Popup>
            </Marker>
            <LocationMarker />
        </MapContainer>
    );
};


function Map() {
    return (
        <MapComponent />
    );
}

export default Map;
