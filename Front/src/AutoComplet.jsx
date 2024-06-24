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
        <CreatableSelect
            value={options.find(option => option.value === formData.stopName)}
            onChange={handleSelectChange}
            options={options}
            placeholder="Selectionner une station"
            isClearable
            styles={customStyles}
        />
    );
};

export default AutoComplet;
