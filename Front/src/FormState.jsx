import React, { useState } from 'react';
import Form from './Form';
import Path from './Path';

const FormState = () => {
    const [dispResearch, setDispResearch] = useState(true);

    const toggleDisplay = () => {
        setDispResearch(!dispResearch);
    };

    return (
        <div id="Form">
            {dispResearch ? <>
                <Form />
                <button onClick={toggleDisplay}>
                    Voir le trajet
                </button>
            </> :
                <> <Path />
                    <button onClick={toggleDisplay}>
                        ⬅
                    </button></>}

        </div>

    );
};

export default FormState;
