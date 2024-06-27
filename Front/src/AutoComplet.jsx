import React, { useState, useEffect } from 'react';
import CreatableSelect from 'react-select/creatable';

const AutoComplet = ({ id, onChange }) => {
    const [formData, setFormData] = useState({
        stopName: '',
        stopId: '',
    });

    const [stations, setStations] = useState([]);

    const injectValue = (value, id) => {
        setFormData((prevData) => ({
            ...prevData,
            stopName: value,
            stopId: id,
        }));
    };

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
        sessionStorage.setItem(`formDataStation_${id}`, JSON.stringify(''));
        fetchStations();
    }, [id]);

    useEffect(() => {
        const checkStorageChange = () => {
            const storedData = sessionStorage.getItem(`formDataStation_${id}`);
            if (storedData) {
                const parsedData = JSON.parse(storedData);
                setFormData(parsedData);
                injectValue(parsedData.stopId, parsedData.stopName);
                if (onChange) {
                    onChange(parsedData.stopName, parsedData.stopId); // Envoyer à Form quand il y a une modif
                }
            }
        };

        // Check for storage change every second
        const intervalId = setInterval(checkStorageChange, 100);

        // Cleanup interval on component unmount
        return () => clearInterval(intervalId);
    }, []);

    const handleSelectChange = (selectedOption) => {
        const newFormData = {
            stopName: selectedOption ? selectedOption.label : '',
            stopId: selectedOption ? selectedOption.value : '',
        };
        setFormData(newFormData);
        sessionStorage.setItem(`formDataStation_${id}`, JSON.stringify(newFormData));
        if (onChange) {
            onChange(newFormData.stopName, newFormData.stopId);
        }
    };

    const options = stations.map(station => ({
        value: station.parent_station,
        label: station.stop_name,
    }));

    const customStyles = {
        control: (provided) => ({
            ...provided,
            backgroundColor: 'white',
            borderColor: 'black',
            minHeight: '20px',
            fontSize: '12px',
        }),
        option: (provided, state) => ({
            ...provided,
            backgroundColor: state.isSelected ? 'white' : state.isFocused ? 'white' : null,
            color: state.isSelected ? 'black' : 'black',
            fontSize: '10px',
        }),
        placeholder: (provided) => ({
            ...provided,
            color: 'gray',
            fontSize: '12px',
        }),
        menu: (provided) => ({
            ...provided,
            backgroundColor: 'white',
            border: '1px solid black',
        }),
        menuList: (provided) => ({
            ...provided,
            maxHeight: '50px',
        }),
    };

    return (
        <>
            <CreatableSelect
                value={options.find(option => option.value === formData.stopName)}
                onChange={handleSelectChange}
                options={options}
                placeholder="Sélectionner une station"
                isClearable
                styles={customStyles}
            />
        </>
    );
};

export default AutoComplet;
