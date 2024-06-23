import React, { useEffect, useState } from 'react';
import './App.css';

function Form() {

    const [formData, setFormData] = useState({
        stopName: '',
        lat: '',
        lon: '',
      });

    useState(() => {
        const storedFormData = localStorage.getItem('formData');
        if (storedFormData) {
            setFormData(JSON.parse(storedFormData));
            console.log("Tout dans le storedFormData qui prend les info de formData")
            console.log(storedFormData)
        }
        else
        {
            console.log("Rien dans le storedFormData qui prend les info de formData")
        }
    }, []);

    // Fonction pour gérer les changements dans les champs du formulaire
    // const handleChange = (e) => {
    //     const { name, value } = e.target;
    //     setFormData((prevData) => ({
    //         ...prevData,
    //         [name]: value,
    //     }));
    // };
    return (
        <>
            <div id="Form">
                <form id="Main_Form">
                    <h1 class="TitleForm">Votre Destination</h1>
                    <label class="lieu_de_depart">
                        Lieu de départ:  <input type="text"  defaultValue={formData.stopName} />
                    </label>
                    <br />
                    <label class="lieu_Arrivee">
                        Lieu d'arrivée:  <br />
                        <input type="text" value={formData.stopName}/>
                    </label>
                    <br />
                    <input type="submit" id="submitButton" value="Rechercher" />
                </form>
            </div>
        </>
    );
}

export default Form;