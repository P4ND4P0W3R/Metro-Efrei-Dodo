// Map.jsx
import { useState, useEffect } from 'react';
import {
    MapContainer,
    TileLayer,
    Popup,
    Polyline,
    CircleMarker,
    LayersControl,
    LayerGroup,
} from 'react-leaflet';

import 'leaflet/dist/leaflet.css';
import './App.css';
import moment from 'moment';

// Fix for default icon issues in Leaflet
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl:
        'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const MapComponent = ({ stations, routes, onhandleMarkerClick, shortestPath }) => {
    const [OnFirst, setOnFirst] = useState(true)

    const handleMarkerClick = stop => {
        const newFormData = {
            stopName: stop.stop_name,
            stopId: stop.parent_station,
            destination: OnFirst,
        };
        //sessionStorage.setItem('formDataStation_AutoComplet1', JSON.stringify(newFormData));
        onhandleMarkerClick(newFormData);
        console.log(newFormData);
        setOnFirst(!OnFirst);


    };

    /* Creation of the path by Dijsktra for the layer */

    // all lignes with pathLignes
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
                            coordinates: [
                                stop.barycenter_lat,
                                stop.barycenter_lon,
                            ],
                            stop_sequence: stop_sequence,
                        });
                    } else {
                        lignes[route_id].decimalStops.push({
                            coordinates: [
                                stop.barycenter_lat,
                                stop.barycenter_lon,
                            ],
                            stop_sequence: stop_sequence,
                        });
                    }
                } else {
                    console.log(
                        `Route ID ${route_id} is not defined in routes`,
                    );
                }
            });
        });

        // Sort main paths and decimal stops by stop_sequence
        Object.values(lignes).forEach(lineData => {
            lineData.mainPath.sort((a, b) => a.stop_sequence - b.stop_sequence);
            lineData.decimalStops.sort(
                (a, b) => a.stop_sequence - b.stop_sequence,
            );
        });

        return lignes;
    };

    const subwayLines = pathLignes(stations, routes);

    const center = [48.866667, 2.333333];

    // Function to get coordinates for a given station ID
    const getStationCoordinates = stationId => {
        const station = stations.find(s => s.parent_station === stationId);
        return station
            ? [station.barycenter_lat, station.barycenter_lon]
            : null;
    };

    const [pathPolyline, setPathPolyline] = useState([]); // State for path polyline
    const [pathMarkers, setPathMarkers] = useState([]); // State for path markers

    useEffect(() => {
        // When shortestPath changes, update pathPolyline and pathMarkers
        if (shortestPath && shortestPath.stops) {
            // Get coordinates for the path polyline
            const coords = shortestPath.stops.map(stop =>
                getStationCoordinates(stop.station),
            );
            setPathPolyline(coords.filter(coord => coord !== null));

            // Create markers for each stop
            const stopMarkers = shortestPath.stops.map((stop, index) => (
                <CircleMarker
                    key={index}
                    center={getStationCoordinates(stop.station)}
                    radius={3}
                    eventHandlers={{
                        mouseover: event => event.target.openPopup(),
                    }}
                >
                    <Popup>
                        <span>{stop.station}</span>
                        <br />
                        <span>
                            {moment(stop.arrival_time).format('HH:mm')} -{' '}
                            {moment(stop.departure_time).format('HH:mm')}
                        </span>
                    </Popup>
                </CircleMarker>
            ));
            setPathMarkers(stopMarkers);
        }
    }, [shortestPath]);

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
                        {/* Polyline for the path */}
                        {shortestPath && pathPolyline.length > 1 && (
                            <Polyline
                                positions={pathPolyline}
                                pathOptions={{ color: 'red' }}
                            />
                        )}

                        {/* Markers for the stops */}
                        {pathMarkers}
                    </LayerGroup>
                </LayersControl.Overlay>

                <LayersControl.Overlay name="Layer with all lignes and stations">
                    <LayerGroup>
                        {Object.entries(subwayLines).map(
                            ([routeId, lineData]) => {
                                const route = routes.find(
                                    route => route.route_id === routeId,
                                );
                                const routeColor = route
                                    ? `#${route.route_color}`
                                    : '#FFFFFF';

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
                                const decimalStopsCoords =
                                    lineData.decimalStops.map(
                                        stop => stop.coordinates,
                                    );
                                if (decimalStopsCoords.length > 1) {
                                    // Link first decimal stop
                                    const firstDecimalStopSequence = Math.floor(
                                        lineData.decimalStops[0].stop_sequence,
                                    );
                                    const prevMainStopIndex =
                                        lineData.mainPath.findIndex(
                                            stop =>
                                                stop.stop_sequence ===
                                                firstDecimalStopSequence - 1,
                                        );
                                    if (prevMainStopIndex !== -1) {
                                        polylines.push(
                                            <Polyline
                                                key={`${routeId}-link-first`}
                                                positions={[
                                                    lineData.mainPath[
                                                        prevMainStopIndex
                                                    ].coordinates,
                                                    decimalStopsCoords[0],
                                                ]}
                                                pathOptions={{
                                                    color: routeColor,
                                                }}
                                            />,
                                        );
                                    }

                                    // Link last decimal stop
                                    const lastDecimalStopSequence = Math.floor(
                                        lineData.decimalStops[
                                            lineData.decimalStops.length - 1
                                        ].stop_sequence,
                                    );
                                    const nextMainStopIndex =
                                        lineData.mainPath.findIndex(
                                            stop =>
                                                stop.stop_sequence ===
                                                lastDecimalStopSequence + 1,
                                        );
                                    if (nextMainStopIndex !== -1) {
                                        polylines.push(
                                            <Polyline
                                                key={`${routeId}-link-last`}
                                                positions={[
                                                    decimalStopsCoords[
                                                    decimalStopsCoords.length -
                                                    1
                                                    ],
                                                    lineData.mainPath[
                                                        nextMainStopIndex
                                                    ].coordinates,
                                                ]}
                                                pathOptions={{
                                                    color: routeColor,
                                                }}
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
                            },
                        )}
                    </LayerGroup>
                </LayersControl.Overlay>
                <LayersControl.Overlay checked name=" All stations">
                    <LayerGroup>
                        {stations.map(stop => (
                            <CircleMarker
                                key={stop.parent_station}
                                center={[
                                    stop.barycenter_lat,
                                    stop.barycenter_lon,
                                ]}
                                radius={3}
                                eventHandlers={{
                                    mouseover: event =>
                                        event.target.openPopup(),
                                    click: () => handleMarkerClick(stop),
                                }}
                            >
                                <Popup>
                                    <span>{stop.stop_name}</span>
                                </Popup>
                            </CircleMarker>
                        ))}
                    </LayerGroup>
                </LayersControl.Overlay>
            </LayersControl>
        </MapContainer>
    );
};

const Map = ({ stations, routes, onhandleMarkerClick, shortestPath }) => {
    return (
        <MapComponent
            stations={stations}
            routes={routes}
            onhandleMarkerClick={onhandleMarkerClick}
            shortestPath={shortestPath}
        />
    );
};

export default Map;
