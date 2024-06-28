import React, { useState, useEffect } from 'react';
import CreatableSelect from 'react-select/creatable';

const AutoComplet = ({ stations, FormDataForAutocomplet, id, onChange }) => {
    const [formData, setFormData] = useState({
        stopName: '',
        stopId: '',
    });

    useEffect(() => {
        if (FormDataForAutocomplet) {
            if (FormDataForAutocomplet.destination === true && id === "AutoComplet1") {
                setFormData({
                    stopName: FormDataForAutocomplet.stopName,
                    stopId: FormDataForAutocomplet.stopId,
                });
            } else if (FormDataForAutocomplet.destination === false && id === "AutoComplet2") {
                setFormData({
                    stopName: FormDataForAutocomplet.stopName,
                    stopId: FormDataForAutocomplet.stopId,
                });
            }
        }
    }, [FormDataForAutocomplet, id]);

    const handleSelectChange = (selectedOption) => {
        const newFormData = {
            stopName: selectedOption ? selectedOption.label : '',
            stopId: selectedOption ? selectedOption.value : '',
        };
        setFormData(newFormData);
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
                value={options.find(option => option.value === formData.stopId)} // Set the value based on formData.stopId
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
