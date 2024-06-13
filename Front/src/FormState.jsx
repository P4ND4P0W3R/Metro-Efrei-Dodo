import React, { useState } from 'react';
import Form from './Form';
import Path from './Path';

const FormState = () => {
    const [dispResearch, setDispResearch] = useState(true);

    const toggleDisplay = () => {
        setDispResearch(!dispResearch);
    };

    return (
        <div>
            <button onClick={toggleDisplay}>
                Toggle Form/Path
            </button>
            {dispResearch ? <Form /> : <Path />}
        </div>
    );
};

export default FormState;
