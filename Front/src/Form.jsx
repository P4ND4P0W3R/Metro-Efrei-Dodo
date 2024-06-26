// Form.js
import React, { useEffect, useState } from 'react';
import './App.css';
import AutoComplet from './AutoComplet';
import TimePicker from 'react-time-picker';
import 'react-time-picker/dist/TimePicker.css';
import 'react-clock/dist/Clock.css';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const Formulaire = () => {
    const [formData, setFormData] = useState({
        stopName: '',
        lat: '',
        lon: '',
        lieuDepart: '',
        lieuArrivee: '',
    });

    const [options, setOptions] = useState(false);
    const [departureTime, setDepartureTime] = useState(null);
    const [arrivalTime, setArrivalTime] = useState(null);
    const [selectedDate, setSelectedDate] = useState(null);

    const Dikstra = () => {
        let Heure = '';
        const Date = selectedDate;
        if (departureTime !== null) {
            Heure = departureTime;
        } else {
            Heure = arrivalTime;
        }

        const StationDepart = formData.lieuDepart;
        const StationArriver = formData.lieuArrivee;
        console.log(`Dikstra = \n${Date}\n${Heure}\n${StationDepart}\n${StationArriver}`);
    };

    useEffect(() => {
        const storedFormData = localStorage.getItem('formData');
        if (storedFormData) {
            setFormData(JSON.parse(storedFormData));
        } else {
            console.error("Rien dans le storedFormData qui prend les info de formData");
        }
    }, []);

    const Options = () => {
        if (!options) {
            clearSelection();
        }
        setOptions(!options);
    };

    const handleDateChange = (date) => {
        setSelectedDate(date);
    };

    const handleDepartureTimeChange = (time) => {
        setDepartureTime(time);
        setArrivalTime(null); // Assure qu'une seule option est sélectionnée à la fois
    };

    const handleArrivalTimeChange = (time) => {
        setArrivalTime(time);
        setDepartureTime(null); // Assure qu'une seule option est sélectionnée à la fois
    };

    const clearSelection = () => {
        setSelectedDate(null);
        setDepartureTime(null);
        setArrivalTime(null);
    };

    const handleLieuDepartChange = (value) => {
        setFormData((prevFormData) => ({
            ...prevFormData,
            lieuDepart: value,
        }));
    };

    const handleLieuArriveeChange = (value) => {
        setFormData((prevFormData) => ({
            ...prevFormData,
            lieuArrivee: value,
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        Dikstra();
    };

    return (
        <div id="Form">
            <form id="Main_Form">
                <h1 className="TitleForm">Votre parcours</h1>
                <label className="lieu_de_depart">
                    Lieu de départ :
                </label>
                <AutoComplet id="AutoComplet1" onChange={handleLieuDepartChange} />
                <br />
                <label className="lieu_Arrivee">
                    Lieu d'arrivée :
                </label>
                <AutoComplet id="AutoComplet2" onChange={handleLieuArriveeChange} />
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
                <br/>
                <div className = "SubmitButton">
                    <input type="submit" id="submitButton" value="Rechercher" onClick={handleSubmit}/>
                </div>
            </form>
        </div>
    );
};

function Form() {
    return <Formulaire />;
}

export default Form;
