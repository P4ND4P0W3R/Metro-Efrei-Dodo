import React, { useState, useEffect } from 'react';
import Map from './Map';
import FormState from './FormState';
import 'leaflet/dist/leaflet.css';
import './App.css';

const App = () => {
  const [stations, setStations] = useState([]);
  const [routes, setRoutes] = useState([]);

  // Fetch stations data
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

  // Fetch routes data
  useEffect(() => {
    const fetchRoutes = async () => {
      try {
        const response = await fetch('http://localhost:8000/routes');
        const data = await response.json();
        setRoutes(data);
      } catch (error) {
        console.error('Error fetching stations:', error);
      }
    };
    fetchRoutes();
  }, []);

  return (
    <>
      <FormState stations={stations} routes={routes} />
      <Map stations={stations} routes={routes} />
    </>
  );
};

export default App;
