import React, { useEffect, useState } from 'react';
import './App.css';
import AutoComplet from './AutoComplet';

function Form() {

    return (
        <div id="Form">
            <form id="Main_Form">
                <h1 className="TitleForm">Votre Destination</h1>
                <label className="lieu_de_depart">
                    Lieu de départ:
                    <AutoComplet />
                </label>
                <br />
                <label className="lieu_Arrivee">
                    Lieu d'arrivée:
                    <AutoComplet />
                </label>
                <br />
                <input type="submit" id="submitButton" value="Rechercher" />
            </form>
        </div>
    );
}

export default Form;
