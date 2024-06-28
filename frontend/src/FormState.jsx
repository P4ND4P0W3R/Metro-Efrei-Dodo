import React, { useState } from 'react';
import Form from './Form';
import Path from './Path';

const FormComponent = ({ stations, routes, FormDataForAutocomplet }) => {

    const [dispResearch, setDispResearch] = useState(true);
    const toggleDisplay = () => {
        setDispResearch(!dispResearch);
    };

    return (
        <div id="Form">
            {dispResearch ? <>
                <Form stations={stations} FormDataForAutocomplet={FormDataForAutocomplet} />
                <button id="TrajetToggle" onClick={toggleDisplay}>
                    Voir le trajet
                </button>
            </> :
                <> <Path stations={stations}
                    routes={routes}
                />
                    <button id="TrajetToggle" onClick={toggleDisplay}>
                        ⬅
                    </button></>}

        </div>
    );
};

const FormState = ({ stations, routes, FormDataForAutocomplet }) => {
    return <FormComponent stations={stations} routes={routes} FormDataForAutocomplet={FormDataForAutocomplet} />;
};


export default FormState;
