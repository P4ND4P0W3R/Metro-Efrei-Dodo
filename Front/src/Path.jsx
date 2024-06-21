import './App.css';
import React, { useState } from 'react';


const Path = () => {
    const path = [
        {
            "parent_station": "IDFM:71423",
            "stop_name": "Wagram",
            "barycenter_lon": 2.3046491141557,
            "barycenter_lat": 48.8838035331464
        },
        {
            "parent_station": "IDFM:73630",
            "stop_name": "Louvre - Rivoli",
            "barycenter_lon": 2.34094952037651,
            "barycenter_lat": 48.8608441215251
        },
        {
            "parent_station": "IDFM:71634",
            "stop_name": "Château de Vincennes",
            "barycenter_lon": 2.44054009540611,
            "barycenter_lat": 48.8443175143136
        },
        {
            "parent_station": "IDFM:70441",
            "stop_name": "Barbara",
            "barycenter_lon": 2.31745831683867,
            "barycenter_lat": 48.8097945177163
        },
        {
            "parent_station": "IDFM:71320",
            "stop_name": "Bonne Nouvelle",
            "barycenter_lon": 2.34849872278322,
            "barycenter_lat": 48.8705624005626
        },
        {
            "parent_station": "IDFM:73620",
            "stop_name": "Saint-Michel",
            "barycenter_lon": 2.34397822804783,
            "barycenter_lat": 48.8535895063915
        },
        {
            "parent_station": "IDFM:73622",
            "stop_name": "Chemin Vert",
            "barycenter_lon": 2.36815834907551,
            "barycenter_lat": 48.8570966953562
        },
        {
            "parent_station": "IDFM:478883",
            "stop_name": "Porte de Clignancourt",
            "barycenter_lon": 2.34468568614284,
            "barycenter_lat": 48.8975417063484
        },
        {
            "parent_station": "IDFM:71100",
            "stop_name": "Censier - Daubenton",
            "barycenter_lon": 2.35156092510092,
            "barycenter_lat": 48.8402461283576
        },
        {
            "parent_station": "IDFM:71868",
            "stop_name": "Jourdain",
            "barycenter_lon": 2.3893253789101,
            "barycenter_lat": 48.8752473486414
        },
        {
            "parent_station": "IDFM:71311",
            "stop_name": "République",
            "barycenter_lon": 2.36394217282797,
            "barycenter_lat": 48.8675386912002
        },
        {
            "parent_station": "IDFM:71298",
            "stop_name": "Concorde",
            "barycenter_lon": 2.32267315791628,
            "barycenter_lat": 48.8664072192036
        },
        {
            "parent_station": "IDFM:71026",
            "stop_name": "Glacière",
            "barycenter_lon": 2.34346786469835,
            "barycenter_lat": 48.8311430914311
        },
        {
            "parent_station": "IDFM:71614",
            "stop_name": "Daumesnil",
            "barycenter_lon": 2.39586047717139,
            "barycenter_lat": 48.8395798231288
        },
        {
            "parent_station": "IDFM:73621",
            "stop_name": "Bréguet-Sabin",
            "barycenter_lon": 2.37026467678353,
            "barycenter_lat": 48.8562309328685
        },
        {
            "parent_station": "IDFM:71033",
            "stop_name": "Place d'Italie",
            "barycenter_lon": 2.35564751463176,
            "barycenter_lat": 48.8311546176231
        },
        {
            "parent_station": "IDFM:71346",
            "stop_name": "Miromesnil",
            "barycenter_lon": 2.31532031651874,
            "barycenter_lat": 48.8735901100081
        },
        {
            "parent_station": "IDFM:71519",
            "stop_name": "Anatole France",
            "barycenter_lon": 2.28489695784642,
            "barycenter_lat": 48.8922196015053
        },
        {
            "parent_station": "IDFM:71326",
            "stop_name": "Grands Boulevards",
            "barycenter_lon": 2.34302996163768,
            "barycenter_lat": 48.8715105416744
        }
    ];
    function FirstStation() {
        return <div id="PathList">{path[0].stop_name}</div>
    }
    function MiddleStation() {
        const Middlepath = path.slice(1, -1);
        console.log(Middlepath)
        return <div id="PathList">
            {Middlepath.map(path => (
                <div id="StationOnPath" key={"stop_id"}>
                    {path.stop_name}
                </div>
            ))}
        </div>
    }
    function LastStation() {
        const LastStation = path[path.length - 1]
        return <div id="PathList">{LastStation.stop_name}</div>
    }
    function Ligne() {

    }
    return (
        <div id="PathContainer">
            <div>Ligne {path[0].stop_name} </div>
            <FirstStation />
            <MiddleStation />
            <LastStation />
        </div >
    );
}

export default Path;
