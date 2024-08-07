// Form.jsx
import React, { useEffect, useState } from 'react';
import '../App.css';
import AutoComplet from './AutoComplet';
import TimePicker from 'react-time-picker';
import 'react-time-picker/dist/TimePicker.css';
import 'react-clock/dist/Clock.css';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import CircularProgress from '@mui/material/CircularProgress';

const Formulaire = ({
    stations,
    FormDataForAutocomplet,
    shortestPath,
    setShortestPath,
    forward,
    setForward,
}) => {
    const [formData, setFormData] = useState({
        stopName: '',
        lat: '',
        lon: '',
        lieuDepart: '',
        lieuDepartId: '',
        lieuArrivee: '',
        lieuArriveeId: '',
    });

    const [options, setOptions] = useState(false);
    const [departureTime, setDepartureTime] = useState(null);
    const [arrivalTime, setArrivalTime] = useState(null);
    const [selectedDate, setSelectedDate] = useState(null);

    const [isLoadingDijkstra, setIsLoadingDijkstra] = useState(false); // State for loading

    const Dikstra = () => {
        let StringHeure = '';
        let Date = selectedDate;
        if (departureTime !== null) {
            StringHeure = departureTime;
        } else if (arrivalTime !== null) {
            StringHeure = arrivalTime;
            setForward('False'); // Set to arrival time if arrivalTime is selected
        }
        let StringDate = '';
        StringDate = StringDate.concat(Date.getFullYear() + '-');
        StringDate = StringDate.concat('0' + (Date.getMonth() + 1) + '-');
        StringDate = StringDate.concat(Date.getDate());

        StringHeure = StringHeure.concat(':00');

        let DateFinal = '';
        DateFinal = DateFinal.concat(StringDate + ' ');
        DateFinal = DateFinal.concat(StringHeure);

        const StationDepartId = formData.lieuDepartId;
        const StationArriverId = formData.lieuArriveeId;

        let URL = 'http://127.0.0.1:8000/shortest_path/';
        URL = URL.concat(forward + '/'); // Add forward parameter
        URL = URL.concat(StationDepartId + '/');
        URL = URL.concat(StationArriverId + '/');
        URL = URL.concat(StringDate + '%20');
        URL = URL.concat(StringHeure);

        setIsLoadingDijkstra(true); // Set loading to true

        const fetchPath = async () => {
            try {
                const response = await fetch(URL);
                const data = await response.json();
                setShortestPath(data); // Update shortestPath in parent component
                sessionStorage.setItem(
                    'StationsForTheRide',
                    JSON.stringify(data.stations),
                );
            } catch (error) {
                console.error('Error fetching stations:', error);
            } finally {
                setIsLoadingDijkstra(false); // Set loading to false after the request completes
            }
        };
        fetchPath();
    };

    const Options = () => {
        if (!options) {
            clearSelection();
        }
        setOptions(!options);
    };

    const handleDateChange = date => {
        setSelectedDate(date);
    };

    const handleDepartureTimeChange = time => {
        setDepartureTime(time);
        setArrivalTime(null); // Assure qu'une seule option est sélectionnée à la fois
    };

    const handleArrivalTimeChange = time => {
        setArrivalTime(time);
        setDepartureTime(null); // Assure qu'une seule option est sélectionnée à la fois
    };

    const clearSelection = () => {
        setSelectedDate(null);
        setDepartureTime(null);
        setArrivalTime(null);
    };

    const handleLieuDepartChange = (stopName, stopId) => {
        setFormData(prevFormData => ({
            ...prevFormData,
            lieuDepart: stopName,
            lieuDepartId: stopId,
        }));
    };

    const handleLieuArriveeChange = (stopName, stopId) => {
        setFormData(prevFormData => ({
            ...prevFormData,
            lieuArrivee: stopName,
            lieuArriveeId: stopId,
        }));
    };

    const handleSubmit = e => {
        e.preventDefault();

        // Check for missing data and display an alert
        let missingData = [];
        if (!formData.lieuDepartId) {
            missingData.push('Lieu de départ');
        }
        if (!formData.lieuArriveeId) {
            missingData.push("Lieu d'arrivée");
        }
        if (selectedDate === null) {
            missingData.push('Date du trajet');
        }
        if (departureTime === null && arrivalTime === null) {
            missingData.push("Heure de départ ou d'arrivée");
        }

        if (missingData.length > 0) {
            alert(
                `Veuillez saisir les informations suivantes : ${missingData.join(
                    ', ',
                )}`,
            );
            return;
        }

        // Check if the departure and arrival stations are the same
        if (formData.lieuDepartId === formData.lieuArriveeId) {
            missingData.push(
                "Le lieu de départ et d'arrivée ne peuvent être les mêmes.",
            );
        }

        if (missingData.length > 0) {
            alert(`${missingData.join(', ')}`);
            return;
        }

        // If all data is available, call Dikstra
        Dikstra();
    };

    return (
        <div className="form-container">
            <form className="form-content">
                <h1 className="TitleForm">Votre parcours</h1>
                <label className="lieu_de_depart">Lieu de départ :</label>
                <AutoComplet
                    stations={stations}
                    FormDataForAutocomplet={FormDataForAutocomplet}
                    id="AutoComplet1"
                    onChange={handleLieuDepartChange}
                />
                <br />
                <label className="lieu_Arrivee">Lieu d'arrivée :</label>
                <AutoComplet
                    stations={stations}
                    FormDataForAutocomplet={FormDataForAutocomplet}
                    id="AutoComplet2"
                    onChange={handleLieuArriveeChange}
                />
                <br />
                <div className="options-container">
                    <button type="button" id="Options" onClick={Options}>
                        {options ? '-' : '+'}
                    </button>
                    {options && (
                        <div>
                            <label>Date du trajet :</label>
                            <DatePicker
                                selected={selectedDate}
                                onChange={date => handleDateChange(date)}
                                dateFormat="dd/MM/yyyy"
                                minDate={new Date(2024, 2, 1)}
                                maxDate={new Date(2024, 2, 31)}
                                placeholderText="Sélectionner une date"
                            />
                            <br />
                            <br />
                            <div className="time-picker-container">
                                <label>Heure de départ :</label>
                                <TimePicker
                                    onChange={handleDepartureTimeChange}
                                    value={departureTime}
                                    clearIcon={null}
                                    disableClock={true}
                                />
                            </div>
                            <br />
                            <div className="time-picker-container">
                                <label>Heure d'arrivée :</label>
                                <TimePicker
                                    onChange={handleArrivalTimeChange} // -3h si choix d'heure d'arrivée pour appel algo
                                    value={arrivalTime}
                                    clearIcon={null}
                                    disableClock={true}
                                />
                            </div>
                        </div>
                    )}
                </div>
                <br />
                <div className="submit-button">
                    {isLoadingDijkstra ? ( // Loading state
                        <button
                            type="button"
                            disabled
                            style={{ width: '150px', height: '70px' }}
                        >
                            <CircularProgress />
                        </button>
                    ) : (
                        <input
                            type="submit"
                            id="submit-button"
                            value="Rechercher"
                            style={{ width: '150px', height: '70px' }}
                            onClick={handleSubmit}
                        />
                    )}
                </div>
                <br />
            </form>
        </div>
    );
};

const Form = ({
    stations,
    FormDataForAutocomplet,
    setShortestPath,
    forward,
    setForward,
}) => {
    return (
        <Formulaire
            stations={stations}
            FormDataForAutocomplet={FormDataForAutocomplet}
            setShortestPath={setShortestPath}
            forward={forward}
            setForward={setForward}
        />
    );
};

export default Form;
