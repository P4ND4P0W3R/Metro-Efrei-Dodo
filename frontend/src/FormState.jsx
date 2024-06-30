// FormState.jsx
import React, { useState } from 'react';
import Form from './Form';
import Path from './Path';

const FormComponent = ({
    stations,
    routes,
    FormDataForAutocomplet,
    shortestPath,
    setShortestPath,
    mst,
    setMst,
}) => {
    const [dispResearch, setDispResearch] = useState(true);
    const [forward, setForward] = useState('True'); // Default to departure time

    const toggleDisplay = () => {
        setDispResearch(!dispResearch);
    };

    return (
        <div id="Form">
            {dispResearch ? (
                <>
                    <Form
                        stations={stations}
                        FormDataForAutocomplet={FormDataForAutocomplet}
                        shortestPath={shortestPath}
                        setShortestPath={setShortestPath}
                        mst={mst}
                        setMst={setMst}
                        forward={forward}
                        setForward={setForward}
                    />
                    <button id="TrajetToggle" onClick={toggleDisplay}>
                        Voir le trajet
                    </button>
                </>
            ) : (
                <>
                    <Path
                        stations={stations}
                        routes={routes}
                        shortestPath={shortestPath}
                        forward={forward}
                    />
                    <button id="TrajetToggle" onClick={toggleDisplay}>
                        ⬅
                    </button>
                </>
            )}
        </div>
    );
};

const FormState = ({
    stations,
    FormDataForAutocomplet,
    routes,
    shortestPath,
    setShortestPath,
    mst,
    setMst,
    forward,
    setForward,
}) => {
    return (
        <FormComponent
            stations={stations}
            FormDataForAutocomplet={FormDataForAutocomplet}
            routes={routes}
            shortestPath={shortestPath}
            setShortestPath={setShortestPath}
            mst={mst}
            setMst={setMst}
            forward={forward}
            setForward={setForward}
        />
    );
};

export default FormState;
