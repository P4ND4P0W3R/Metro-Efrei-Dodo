import React, { useState } from 'react';
import Form from './Form';
import Path from './Path';

const FormComponent = ({stations, routes}) => {

    const [dispResearch, setDispResearch] = useState(true);

    const toggleDisplay = () => {
        setDispResearch(!dispResearch);
    };

    return (
        <div id="Form">
            {dispResearch ? <>
                <Form stations = {stations}/>
                <button id = "TrajetToggle" onClick={toggleDisplay}>
                    Voir le trajet
                </button>
            </> :
                <> <Path stations = {stations}
                         routes = {routes}
                    />
                    <button id = "TrajetToggle" onClick={toggleDisplay}>
                        ⬅
                    </button></>}

        </div>
    );
};

const FormState = ({ stations, routes }) => {
    return <FormComponent stations={stations} routes={routes} />;
  };
  

export default FormState;
