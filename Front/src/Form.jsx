import './App.css';

function Form() {
    return (
        <>
            <div className="App">
                <form className="Main_Form">
                    <h1>Indiquez votre destination</h1>
                    <label>
                        Lieu de départ:  <input type="text" />
                    </label>
                    <label>
                        Lieu d'arrivée:  <input type="text" />
                    </label>
                    <input type="submit" value="Rechercher" />
                </form>
            </div>
        </>
    );
}

export default Form;