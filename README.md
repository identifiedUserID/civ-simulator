# Python Civilization Sim Prototype

A simple 2D civilization resource gathering and defense game prototype built with Python and Pygame. This project focuses on procedural map generation, basic resource management, unit AI, and simple combat mechanics.

## Features

*   **Procedural Map Generation:** Creates unique circular maps for each game using Perlin noise for elevation, temperature, and moisture.
*   **Biomes:** Includes Forest, Desert, Arctic, Water, and Ice biomes, each influencing resource availability and terrain properties.
*   **Draggable Map:** Click and drag the game world to explore.
*   **Resources:** Gather Wood, Food, Stone, and Iron. Resources respawn over time.
*   **Buildings:**
    *   **Town Hall:** Starting building, spawns Workers. Game over if destroyed.
    *   **House:** Increases population capacity. Costs Wood to build.
*   **Units:**
    *   **Workers:** Automatically gather nearby resources and return them to the Town Hall. Consume Food and Water.
    *   **Enemies:** Basic melee units that spawn periodically and attack workers and buildings.
*   **Basic AI:** Workers search for resources/drop-off points. Enemies seek targets.
*   **Resource Management:** Track collected resources. Population consumes Food and Water over time.
*   **UI Panel:**
    *   Displays current resource counts, population, and population cap.
    *   Sliders to control Simulation Speed, Resource Consumption Rate, Resource Respawn Rate, and Enemy Spawn Rate.
    *   Building placement buttons.
*   **Simple Combat:** Enemies attack buildings and (eventually) units. Buildings have HP.

## Getting Started

### Prerequisites

*   **Python 3.7+:** Make sure Python is installed and added to your system's PATH. You can download it from [python.org](https://www.python.org/).
*   **Pip:** Python's package installer (usually included with Python).

### Installation

There are two ways to set up the game:

**Method 1: Automatic Installation (Windows - Recommended)**

1.  Download or clone this repository.
2.  Navigate to the downloaded folder in your File Explorer.
3.  Double-click the `install.bat` file.
4.  This script will automatically:
    *   Install the required Python packages (`pygame` and `noise`).
    *   Create a shortcut named "Civ Sim Prototype" on your Desktop.
5.  Once the installation is complete, you can run the game using the Desktop shortcut or by running `run_game.bat`.

**Method 2: Manual Installation (All Platforms)**

1.  **Clone the repository:**
    ```bash
    https://github.com/identifiedUserID/civ-simulator.git # Replace with your actual repo URL
    cd civ-simulator
    ```
    Alternatively, download the repository ZIP file and extract it.

2.  **Install dependencies:**
    Open a terminal or command prompt in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```
    *(You might need to use `pip3` instead of `pip` depending on your Python installation.)*

### Running the Game

*   **After Automatic Installation:** Double-click the "Civ Sim Prototype" shortcut on your Desktop or double-click `run_game.bat`.
*   **After Manual Installation:** Open a terminal or command prompt in the project directory and run:
    ```bash
    python main.py
    ```
    *(You might need to use `python3` instead of `python`)*

## How to Play

*   **Camera:** Click and drag the left mouse button on the game map (left side of the screen) to move the camera.
*   **Resources:** Workers will automatically spawn from the Town Hall (up to the population cap) and start gathering nearby Wood and Food.
*   **Building:**
    *   Click the House icon in the bottom-right UI panel.
    *   A semi-transparent "ghost" of the building will follow your mouse over the map.
    *   The ghost is green if placement is valid (walkable ground, no resource/building, sufficient funds) and red otherwise.
    *   Left-click on a valid location to place the House (this costs Wood and increases your population cap).
    *   Right-click anywhere to cancel build mode.
*   **Sliders:** Adjust the sliders in the UI panel to change the game's speed and various rates.
*   **Objective:** Survive enemy attacks, manage resources, and (potentially) expand your civilization (further objectives not yet implemented). Survive by keeping your Town Hall intact.

## Current Limitations & Future Work

This is a prototype with many areas for improvement:

*   **Aesthetics:** Uses basic shapes; needs proper sprites and visual polish.
*   **Pathfinding:** Units use simple direct movement; needs A* or similar for obstacle avoidance.
*   **AI:** Worker/Enemy AI is rudimentary.
*   **Combat:** Very basic; needs more depth (unit HP, attack types, defense).
*   **Content:** More buildings, units, resources, research/tech tree.
*   **Balancing:** Resource/spawn/consumption rates need tuning.
*   **Performance:** May slow down with many units/large maps.
*   **Saving/Loading:** No persistence yet.
*   **Sound:** No audio effects or music.

## Dependencies

*   [Pygame](https://www.pygame.org/): Library for making multimedia applications like games.
*   [Noise](https://pypi.org/project/noise/): Generate Perlin noise for procedural content.

## Contributing

Contributions are welcome! If you have suggestions or want to improve the game, feel free to fork the repository and submit pull requests.

## License

*Apache License*
