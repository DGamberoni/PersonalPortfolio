const fs = require('fs');
const express = require('express');
const cors = require('cors'); // Import CORS

const app = express();
app.use(express.json()); // Enable JSON parsing
app.use(cors()); // Enable CORS to allow requests from any origin

const FILE_PATH = 'darts_game_history.json';

// Load existing game history
function loadGameHistory() {
    if (!fs.existsSync(FILE_PATH)) {
        return [];
    }
    return JSON.parse(fs.readFileSync(FILE_PATH));
}

// Save a new game to the file
app.post('/save-game', (req, res) => {
    const gameData = req.body;
    const history = loadGameHistory();
    history.push(gameData);

    fs.writeFileSync(FILE_PATH, JSON.stringify(history, null, 2));
    res.json({ message: "Game saved!", gameData });
});

// Retrieve game history
app.get('/game-history', (req, res) => {
    res.json(loadGameHistory());
});

// Start the server
app.listen(3000, () => console.log('Server running on http://localhost:3000'));
