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
    });

    useState(() => {
        const storedFormData = localStorage.getItem('formData');
        if (storedFormData) {
            setFormData(JSON.parse(storedFormData));
            console.log("Tout dans le storedFormData qui prend les info de formData")
            console.log(storedFormData)
        }
        else {
            console.log("Rien dans le storedFormData qui prend les info de formData")
        }
    }, []);

    const [options, setOptions] = useState(false);
    const [departureTime, setDepartureTime] = useState(null);
    const [arrivalTime, setArrivalTime] = useState(null);
    const [selectedDate, setSelectedDate] = useState(null);

    const Options = () => {
        if(!options)
        {
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

    // const handleSubmit = (e) => {
    //     e.preventDefault();
    //     localStorage.setItem('formData', JSON.stringify(formData)); ? 
    //      Pour envoyer à Djisktra les infos du form
    // };

    return (
        <div id = "Form">
            <form id = "Main_Form">
                <h1 className = "TitleForm">Votre parcours</h1>
                <label className = "lieu_de_depart">
                    Lieu de départ :
                </label>
                <AutoComplet id = "AutoComplet 1" />
                <br />
                <label className = "lieu_Arrivee">
                    Lieu d'arrivé :
                </label>
                <AutoComplet id = "AutoComplet 2" />
                <br />
            <div className = "options-container">
                <button type = "button" id = "Options" onClick={Options}>
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
                        <br/>
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

            <input type="submit" id="submitButton" value="Rechercher" /> {/*onSubmit={handleSubmit} />*/}

            </form>
        </div>
    );
}

function Form()
{
    return <Formulaire/>;
}

export default Form;