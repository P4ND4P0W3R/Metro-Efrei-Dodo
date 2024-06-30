// Form.jsx
import React, { useEffect, useState } from 'react';
import './App.css';
import AutoComplet from './AutoComplet';
import TimePicker from 'react-time-picker';
import 'react-time-picker/dist/TimePicker.css';
import 'react-clock/dist/Clock.css';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const Formulaire = ({
    stations,
    FormDataForAutocomplet,
    shortestPath,
    setShortestPath,
    mst,
    setMst,
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

    const [mstCost, setMstCost] = useState(null); // State for MST cost
    const [mstConnexe, setMstConnexe] = useState(null); // State for MST connexity

    const fetchMST = async () => {
        try {
            const parentStation = formData.lieuDepartId; // Use the same station for MST as the departure point
            const date = selectedDate;
            let StringDate = '';
            StringDate = StringDate.concat(date.getFullYear() + '-');
            StringDate = StringDate.concat('0' + (date.getMonth() + 1) + '-');
            let StringHeure = departureTime.concat(':00');
            StringDate = StringDate.concat(date.getDate() + ' ' + StringHeure);
            const response = await fetch(
                `http://127.0.0.1:8000/prim_spanning_tree/${parentStation}/${StringDate}`,
            );
            const data = await response.json();
            setMst(data); // Update the MST
            setMstCost(data.cost);
            setMstConnexe(data.connexe);
        } catch (error) {
            console.error('Error fetching MST:', error);
        }
    };

    const handleMSTClick = e => {
        e.preventDefault();
        fetchMST();
    };

    const Dikstra = () => {
        let StringHeure = '';
        let Date = selectedDate;
        let forward = 'True'; // Default to departure time
        if (departureTime !== null) {
            StringHeure = departureTime;
        } else if (arrivalTime !== null) {
            StringHeure = arrivalTime;
            forward = 'False'; // Set to arrival time if arrivalTime is selected
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
        Dikstra(); // Appel de Dikstra après avoir enregistré les données dans localStorage
    };
    return (
        <div id="Form">
            <form id="Main_Form">
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
                <div className="SubmitButton">
                    <input
                        type="submit"
                        id="submitButton"
                        value="Rechercher"
                        onClick={handleSubmit}
                    />
                </div>
                <br />
                <div className="SubmitButton">
                    <input
                        type="button"
                        id="MSTButton"
                        value="Calculer l'arbre couvrant minimal"
                        onClick={handleMSTClick}
                    />
                </div>
                <br />
                {mstCost !== null && (
                    <div>Coût de l'arbre couvrant minimal : {mstCost}</div>
                )}
                {mstConnexe !== null && (
                    <div>
                        Le réseau est {mstConnexe ? 'connexe' : 'non connexe'}.
                    </div>
                )}
            </form>
        </div>
    );
};

const Form = ({
    stations,
    FormDataForAutocomplet,
    setShortestPath,
    mst,
    setMst,
}) => {
    return (
        <Formulaire
            stations={stations}
            FormDataForAutocomplet={FormDataForAutocomplet}
            setShortestPath={setShortestPath}
            mst={mst}
            setMst={setMst}
        />
    );
};

export default Form;
