import './App.css';

function Form() {
    return (
        <>
            <div id="Form">
                <form id="Main_Form">
                    <h1 class="TitleForm">Votre Destination</h1>
                    <label class="lieu_de_depart">
                        Lieu de départ:  <input type="text" />
                    </label>
                    <br />
                    <label class="lieu_Arrivee">
                        Lieu d'arrivée:  <br />
                        <input type="text" />
                    </label>
                    <br />
                    <input type="submit" id="submitButton" value="Rechercher" />
                </form>
            </div>
        </>
    );
}

export default Form;