// FormState.jsx
import React, { useState } from 'react';
import Form from './Form';
import MSTForm from './MSTForm'; // Import MSTForm
import Path from './Path';

const FormComponent = ({
    stations,
    routes,
    FormDataForAutocomplet,
    shortestPath,
    setShortestPath,
    mst,
    setMst,
    forward,
    setForward,
}) => {
    const [activeTab, setActiveTab] = useState('shortestPath'); // State for active tab
    const [mstCost, setMstCost] = useState(null); // State for MST cost
    const [mstConnexe, setMstConnexe] = useState(null); // State for MST connexity

    const handleTabChange = tab => {
        setActiveTab(tab);
    };

    return (
        <div id="Form">
            <div className="tab-container">
                <button
                    className={`tab ${activeTab === 'shortestPath' ? 'active' : ''}`}
                    onClick={() => handleTabChange('shortestPath')}
                >
                    Chercher un trajet
                </button>
                <button
                    className={`tab ${activeTab === 'path' ? 'active' : ''}`}
                    onClick={() => handleTabChange('path')}
                >
                    Le chemin
                </button>
                <button
                    className={`tab ${activeTab === 'mst' ? 'active' : ''}`}
                    onClick={() => handleTabChange('mst')}
                >
                    Arbre Couvrant Minimal
                </button>
            </div>
            <div className="tab-content">
                {activeTab === 'shortestPath' && (
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
                )}
                {activeTab === 'mst' && (
                    <MSTForm // Display MSTForm
                        stations={stations}
                        FormDataForAutocomplet={FormDataForAutocomplet}
                        mst={mst}
                        setMst={setMst}
                        mstCost={mstCost}
                        setMstCost={setMstCost}
                        mstConnexe={mstConnexe}
                        setMstConnexe={setMstConnexe}
                    />
                )}
                {activeTab === 'path' && ( // Add a new tab for displaying the path
                    <Path
                        stations={stations}
                        routes={routes}
                        shortestPath={shortestPath}
                        forward={forward}
                    />
                )}
            </div>
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
