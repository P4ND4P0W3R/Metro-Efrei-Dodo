import './App.css';
import React, { useState } from 'react';


const Path = () => {
    const [list, setList] = useState([
        { id: 1, name: "Object1" },
        { id: 2, name: "Object2" },
        { id: 3, name: "Object3" }
    ]);

    function filterList(id, props) {
        const updatedList = list.filter((l) => l.id !== id);
        setList(updatedList);
    }

    return (
        <div>
            <ul>
                {list.map((path) => (
                    <li key={path.id}>
                        {path.name}
                        <button onClick={() => filterList(path.id)}>X</button>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default Path;
