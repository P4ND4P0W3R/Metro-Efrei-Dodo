# Metro, Efrei, Dodo (MED)

This project leverages real-time data from Ile-de-France Mobilités (IDFM) to provide an efficient metro navigation system for Paris and Bordeaux (using a simplified dataset). It utilizes graph algorithms to calculate shortest paths, visualize the minimum spanning tree of the metro network, and check network connectivity.

## 📃 Table of Contents

- [Metro, Efrei, Dodo (MED)](#metro-efrei-dodo-med)
  - [📃 Table of Contents](#-table-of-contents)
  - [About the project](#about-the-project)
    - [ℹ️ Project Description](#ℹ️-project-description)
    - [👥 Team Members](#-team-members)
  - [Getting Started](#getting-started)
    - [⚙️ Prerequisites](#️-prerequisites)
    - [🚦 Run the Project](#-run-the-project)
  - [🗂️ File Structure](#️-file-structure)
  - [📝 Additional Notes](#-additional-notes)

## About the project

> [!NOTE]
> This project falls within the scope of the **Solution Factory** for the 2024 IT Mastercamp during our third year curriculum at [EFREI](https://www.efrei.fr/), which is a French CS engineering school. The subject is defined in the following repository: [ossef/Solution_Factory_IT](https://github.com/ossef/Solution_Factory_IT).

### ℹ️ Project Description

This application allows users to:

- **Find the shortest path:** Determine the fastest route between two metro stations, considering real-time schedules and transfer times.
- **Visualize the minimum spanning tree (MST):** Explore the underlying structure of the metro network using Kruskal's algorithm, understanding the most efficient connections.
- **Check network connectivity:** Verify if the entire metro network is reachable from any given station on a specific date.

The project uses:

- **Backend:** Python with [FastAPI](https://fastapi.tiangolo.com/) for building a robust RESTful API, [TortoiseORM](https://tortoise.github.io/toc.html) for interacting with the PostgreSQL database, and advanced graph algorithms for calculations.
- **Frontend:** [React](https://react.dev/) with JavaScript and [Leaflet](https://react-leaflet.js.org/) for a dynamic and interactive user interface, allowing users to visualize the metro map and routes.

### 👥 Team Members

- [P4ND4P0W3R](https://github.com/P4ND4P0W3R) - Paul HU
- [RomainBilly0](https://github.com/RomainBilly0) - Romain BILLY
- [LouisGodfrin](https://github.com/LouisGodfrin) - Louis GODFRIN
- [CTauziede](https://github.com/CTauziede) - Clément TAUZIEDE
- [alexandre-bussiere](https://github.com/alexandre-bussiere) - Alexandre BUSSIERE

## Getting Started

### ⚙️ Prerequisites

- **Backend:**
  - [Python 3.12 or higher](https://www.python.org/downloads/)
  - [PostgreSQL](https://www.postgresql.org/)
- **Frontend:**
  - [Node.js 20 (LTS) or higher](https://nodejs.org/en)
  - [npm](https://www.npmjs.com/) or [Yarn](https://yarnpkg.com/)

### 🚦 Run the Project

1. **Clone the repository:**

    ```bash
    git clone https://github.com/P4ND4P0W3R/Metro-Efrei-Dodo.git
    ```

2. **Navigate to the project directory:**

    ```bash
    cd Metro-Efrei-Dodo
    ```

> [!IMPORTANT]
> Before running the backend, create a `.env` file in the `backend/` directory and add your database connection string as `DATABASE_URL=postgres://username:password@host:port/db_name`.

3. **Setup and run the Backend:**

    ```bash
    python -m venv .venv  # Create a virtual environment
    .venv/Scripts/activate  # Activate the virtual environment
    pip install -r ./backend/requirements.txt  # Install dependencies from requirements.txt

    python populate_database.py  # (OPTIONAL) Populate database with GTFS data (adjust paths if necessary)

    cd backend/app
    uvicorn main:app --reload   # Start the FastAPI server
    ```

    When you are done, you can deactivate your virtual environment:

    ```bash
    deactivate
    ```

4. **Setup and run the Frontend:**

    ```bash
    cd frontend
    npm install  # or yarn install
    npm run dev  # or yarn dev
    ```

Now you should be able to access the frontend application in your browser at `http://localhost:5173` and interact with the FastAPI backend running at `http://localhost:8000`.

## 🗂️ File Structure

- **backend:**
  - `.venv/`: The virtual environment directory containing isolated Python packages.
  - `main.py`: The primary entry point for the FastAPI application.
  - `config.py`: Configuration for the database and other settings.
  - `models.py`: Defines the database models using TortoiseORM.
  - `services/`: Contains logic for specific features (graph, connectivity, MST).
  - `utils/`: Holds general utility functions.
  - `tests/`: Contains unit and integration tests for the backend.
  - `requirements.txt`: Lists the required Python packages for the backend.
- **frontend:**
  - `src/`: The main source code for the React frontend application.
  - `public/`: Holds static files like your `index.html`.
  - `package.json`: Defines frontend dependencies and scripts.

## 📝 Additional Notes

- **GTFS Data:** You will need to download the latest GTFS data from IDFM (<https://data.iledefrance-mobilites.fr/explore/dataset/offre-horaires-tc-gtfs-idfm/information/>) and place it in the appropriate directory (e.g., `backend/data/raw_gtfs/`).
    You process the files to only keep the `RATP` lines by using the command `python backend/app/utils/data_processing.py` in the `root` directory.
- **Database:** Ensure that your PostgreSQL database is set up correctly with the credentials defined in your `.env` file.
- **Leaflet:** Customize the Leaflet map in your frontend component to match the geographic region you're working with.

This project aims to provide a flexible and scalable foundation for a metro navigation application. You can extend it with additional features like:

- **Real-time train information:** Integrate live updates on train delays and disruptions.
- **Multimodal routing:** Incorporate other modes of transportation (bus, tram, etc.) into the pathfinding.
- **User accounts:** Allow users to save favorite routes, set journey preferences, and receive personalized notifications.
- **Accessibility:** Highlight accessible stations and routes.

> [!IMPORTANT]
>
> - The `.venv` folder should be added to your `.gitignore` to avoid unnecessary tracking.
> - This project is for educational purposes and should not be considered a production-ready system.
> - Ensure you have the correct GTFS files and data processing scripts.
