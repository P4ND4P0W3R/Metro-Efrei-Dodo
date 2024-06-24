import React, { useState, useEffect } from 'react';
import CreatableSelect from 'react-select/creatable';


const AutoComplet = () => {
    const [formData, setformData] = useState({
        stopName: ''
    });


    const [stations, setStations] = useState([]);

    useEffect(() => {
        const fetchStations = async () => {
            try {
                const response = await fetch("http://localhost:8000/stations");
                const data = await response.json();
                setStations(data);
            } catch (error) {
                console.error("Error fetching stations:", error);
            }
        };
        fetchStations();
    }, []);

    const handleSelectChange = (selectedOption) => {
        setformData((prevData) => ({
            ...prevData,
            stopName: selectedOption ? selectedOption.value : '',
        }));

    };

    const options = stations.map(station => ({
        value: station.stop_name,
        label: station.stop_name,
    }));

    return (
        <CreatableSelect
            value={options.find(option => option.value === formData.stopName)}
            onChange={handleSelectChange}
            options={options}
            placeholder="Selectionner une station"
            isClearable
        />
    );
};

export default AutoComplet;
