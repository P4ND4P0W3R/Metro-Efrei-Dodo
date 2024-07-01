// Path.jsx
import './App.css';
import React, { useState, useEffect } from 'react';
import moment from 'moment'; // Import moment for time calculations

const Path = ({ shortestPath, forward }) => {
    const [path, setPath] = useState([]); // Use a local state for path
    const [stops, setStops] = useState([]);
    const [journeyTime, setJourneyTime] = useState(null); // State for journey time
    const [departureTime, setDepartureTime] = useState(null);
    const [arrivalTime, setArrivalTime] = useState(null);
    const [executionTime, setExecutionTime] = useState(null);

    useEffect(() => {
        if (shortestPath) {
            setPath(shortestPath.stations);
            setStops(shortestPath.stops);

            if (forward === 'True') {
                // Calculate journey time using arrival_date for departure time scenario
                const departureDate = moment(
                    shortestPath.stops[0].arrival_time,
                ); // Use arrival_time of the first stop
                const arrivalDate = moment(shortestPath.arrival_date);
                const journeyDuration = arrivalDate.diff(
                    departureDate,
                    'minutes',
                );
                setJourneyTime(journeyDuration);
                setDepartureTime(departureDate.format('HH:mm'));
                setArrivalTime(arrivalDate.format('HH:mm'));
                setExecutionTime(shortestPath.total_execution_time);
            } else {
                // Calculate journey time using arrival_date for arrival time scenario
                const arrivalDate = moment(
                    shortestPath.stops[shortestPath.stops.length - 1]
                        .arrival_time,
                );
                const departureDate = moment(shortestPath.departure_date); // Use arrival_time of the first stop
                const journeyDuration = arrivalDate.diff(
                    departureDate,
                    'minutes',
                );
                setJourneyTime(journeyDuration);
                setDepartureTime(departureDate.format('HH:mm'));
                setArrivalTime(arrivalDate.format('HH:mm'));
                setExecutionTime(shortestPath.total_execution_time);
            }

            // // Calculate journey time using arrival_date for arrival time scenario
            // const arrivalDate = moment(shortestPath.arrival_date);
            // const departureDate = moment(shortestPath.stops[0].arrival_time); // Use arrival_time of the first stop
            // const journeyDuration = arrivalDate.diff(departureDate, 'minutes');
            // setJourneyTime(journeyDuration);
        }
    }, [shortestPath]); // Update when shortestPath changes

    function FirstStation() {
        return <div id="PathList">{path.length > 0 && path[0].name}</div>;
    }

    function MiddleStation() {
        const Middlepath = path.slice(1, -1);
        return (
            <div id="PathList">
                {Middlepath.map((path, index) => (
                    <div id="StationOnPath" key={index}>
                        {path.name}
                    </div>
                ))}
            </div>
        );
    }

    function LastStation() {
        return (
            <div id="PathList">
                {path.length > 0 && path[path.length - 1].name}
            </div>
        );
    }

    // Conditional Rendering
    return (
        <div id="PathContainer">
            {shortestPath && (
                <>
                    <div>Trajet : </div>
                    <div>
                        {departureTime}
                        {' - '}
                        {arrivalTime}
                    </div>
                    <br />
                    <div>Durée du trajet : {journeyTime} minutes</div>
                    <br />
                    <FirstStation />
                    <MiddleStation />
                    <LastStation />
                    <br />
                    <div>Temps d'exécution : {executionTime} secondes</div>
                </>
            )}
        </div>
    );
};

export default Path;
