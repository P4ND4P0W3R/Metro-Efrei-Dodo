import './App.css';
import React from 'react';


function defineList() {
    return [list, setList] = React.useState([
        { id: 1, name: "Object1" },
        { id: 2, name: "Object2" },
        { id: 3, name: "Object3" }
    ])
}
function filterList(id) {
    const newList = list.filter((l) => l.id !== id);
    setList(newList);
}

function Path() {
    const [list, setList] = React.useState([
        { id: 1, name: "Object1" },
        { id: 2, name: "Object2" },
        { id: 3, name: "Object3" }
    ])
    return (
        <>
            <div>
                <ul>
                    {
                        list.map((path) => {
                            return <li key={path.id}>{path.name}
                                <button onClick={() => filterList(path.id)}> X</button></li>
                        })
                    }
                </ul>
            </div >
        </>
    );
}

export default Path;
