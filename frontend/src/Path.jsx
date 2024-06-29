// Path.jsx
import './App.css';
import React, { useState, useEffect } from 'react';
import moment from 'moment'; // Import moment for time calculations

const Path = ({ shortestPath }) => {
    const [path, setPath] = useState([]); // Use a local state for path
    const [stops, setStops] = useState([]);
    const [journeyTime, setJourneyTime] = useState(null); // State for journey time

    useEffect(() => {
        if (shortestPath) {
            setPath(shortestPath.stations);
            setStops(shortestPath.stops);

            // Calculate journey time
            const arrivalDate = moment(shortestPath.arrival_date);
            const departureDate = moment(shortestPath.stops[0].arrival_time); // Use arrival_time of the first stop
            const journeyDuration = arrivalDate.diff(departureDate, 'minutes');
            setJourneyTime(journeyDuration);
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
                        {moment(shortestPath.stops[0].arrival_time).format(
                            'HH:mm',
                        )}{' '}
                        {' - '}{' '}
                        {moment(shortestPath.arrival_date).format('HH:mm')}
                    </div>
                    <div>Durée du trajet : {journeyTime} minutes</div>
                    <FirstStation />
                    <MiddleStation />
                    <LastStation />
                </>
            )}
        </div>
    );
};

export default Path;
