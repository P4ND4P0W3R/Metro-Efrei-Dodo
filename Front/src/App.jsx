import Fuse from 'fuse.js'
import { useState } from 'react'
import {MapContainer,TileLayer,Marker,Popup} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css'

// const data = "Parys"

// const fuse = new Fuse(data, {
//   // The algorithms to use for fuzzy matching.
//   algorithms: ["levenshtein", "jaro-winkler"],
//   // The minimum similarity score required for a match.
//   minScore: 70,
// });

// // Search for the string "bar".
// const results = fuse.search("bar");

const MapComponent = () => {
  return (
    <MapContainer center={[51.505, -0.09]} zoom={9} style={{ height: "600px", width: "99%" }}>
      <TileLayer
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Marker position={[51.505, -0.09]}>
        <Popup>
          A pretty CSS3 popup. <br /> Easily customizable.
        </Popup>
      </Marker>
    </MapContainer>
  );
};

function App() {

  return (
    <>
      <div>
        <h1>Indiquez votre destination</h1>
        <div className="App">
          <form>
              <label>Lieu de départ: <input type = "texte" ></input></label>
              <label>Lieu d'arrivé: <input type = "texte" ></input></label>
              <input type = "submit" value = "Rechercher le plus court chemin"></input> 
          </form>
        </div>
        <MapComponent/>
      </div>
    </>
  )
}

export default App
