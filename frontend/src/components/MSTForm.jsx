// MSTForm.jsx
import React, { useState, useEffect } from 'react';
import '../App.css';
import AutoComplet from './AutoComplet';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import TimePicker from 'react-time-picker';
import 'react-time-picker/dist/TimePicker.css';

const MSTForm = ({
    stations,
    FormDataForAutocomplet,
    mst,
    setMst,
    mstCost,
    setMstCost,
    mstConnexe,
    setMstConnexe,
}) => {
    const [formData, setFormData] = useState({
        lieuDepart: '',
        lieuDepartId: '',
    });

    const [options, setOptions] = useState(false);
    const [departureTime, setDepartureTime] = useState(null);
    const [arrivalTime, setArrivalTime] = useState(null);
    const [selectedDate, setSelectedDate] = useState(null);

    const [isLoadingMST, setIsLoadingMST] = useState(false); // State for loading

    const [executionTime, setExecutionTime] = useState(null);

    const fetchMST = async () => {
        setIsLoadingMST(true); // Set loading to true
        try {
            const parentStation = formData.lieuDepartId;
            const date = selectedDate;
            let StringDate = '';
            StringDate = StringDate.concat(date.getFullYear() + '-');
            StringDate = StringDate.concat('0' + (date.getMonth() + 1) + '-');
            StringDate = StringDate.concat(date.getDate() + ' 00:00:00');
            const response = await fetch(
                `http://127.0.0.1:8000/prim_spanning_tree/${parentStation}/${StringDate}`,
            );
            const data = await response.json();
            setMst(data); // Update the MST
            setMstCost(data.cost);
            setMstConnexe(data.connexe);
            setExecutionTime(data.total_execution_time);
        } catch (error) {
            console.error('Error fetching MST:', error);
        } finally {
            setIsLoadingMST(false); // Set loading to false after the request completes
        }
    };

    const handleMSTClick = e => {
        e.preventDefault();

        // Check for missing data and display an alert
        let missingData = [];
        if (!formData.lieuDepartId) {
            missingData.push('Lieu de départ');
        }
        if (selectedDate === null) {
            missingData.push('Date du trajet');
        }
        if (departureTime === null) {
            missingData.push('Heure de départ');
        }

        if (missingData.length > 0) {
            alert(
                `Veuillez saisir les informations suivantes : ${missingData.join(
                    ', ',
                )}`,
            );
            return;
        }

        fetchMST(); // Call fetchMST only if all data is present
    };

    const handleLieuDepartChange = (stopName, stopId) => {
        setFormData(prevFormData => ({
            ...prevFormData,
            lieuDepart: stopName,
            lieuDepartId: stopId,
        }));
    };

    const handleDateChange = date => {
        setSelectedDate(date);
    };

    const handleDepartureTimeChange = time => {
        setDepartureTime(time);
        setArrivalTime(null); // Assure qu'une seule option est sélectionnée à la fois
    };

    return (
        <div className="form-container">
            <form className="form-content">
                <h1 className="TitleForm">Arbre Couvrant Minimal</h1>
                <label className="lieu_de_depart">Lieu de départ :</label>
                <AutoComplet
                    stations={stations}
                    FormDataForAutocomplet={FormDataForAutocomplet}
                    id="AutoComplet1"
                    onChange={handleLieuDepartChange}
                />
                <br />
                <label>Date du trajet :</label>
                <DatePicker
                    selected={selectedDate}
                    onChange={handleDateChange}
                    dateFormat="dd/MM/yyyy"
                    minDate={new Date(2024, 2, 1)}
                    maxDate={new Date(2024, 2, 31)}
                    placeholderText="Sélectionner une date"
                />
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
                <div className="SubmitButton">
                    {isLoadingMST ? ( // Loading state
                        <button type="button" disabled>
                            Chargement...
                        </button>
                    ) : (
                        <input
                            type="button"
                            id="MSTButton"
                            value="Calculer l'arbre couvrant minimal"
                            onClick={handleMSTClick}
                        />
                    )}
                </div>
                <br />
                {mstCost !== null && (
                    <div>Coût de l'arbre couvrant minimal : {mstCost}</div>
                )}
                <br />
                {mstConnexe !== null && (
                    <div>
                        Le réseau est {mstConnexe ? 'connexe' : 'non connexe'}.
                    </div>
                )}
                <br />
                {executionTime !== null && (
                    <div>Temps d'exécution : {executionTime} secondes</div>
                )}
            </form>
        </div>
    );
};

export default MSTForm;
