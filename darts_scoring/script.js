let players = [];
let scores = [];
let currentTurn = 1;
let initialScore = 301;
let gameInfo = {   // Declare gameInfo object globally
    startTime: new Date().toISOString(),
    endTime: null,
    winner: null
};
let shotList = {}

function addPlayer() {
    const playerName = document.getElementById('player-name').value;
    if (playerName) {
        players.push(playerName);
        scores.push(initialScore);
        
        // Salva i dati in localStorage
        localStorage.setItem('players', JSON.stringify(players));
        localStorage.setItem('scores', JSON.stringify(scores));

        document.getElementById('players-list').innerHTML += `<p>${playerName}</p>`;
        document.getElementById('player-name').value = '';
    }
    if (players.length === 0) {
        startGame();
    }
    console.log(playerName); // Controllo in console
}

// Reset players function
function resetPlayers() {
    // Clear the players array
    players = [];

    // Remove players from localStorage
    localStorage.removeItem("players");
    localStorage.removeItem("scores");

    // Clear the players list in the UI
    const playerList = document.getElementById("players-list");
    if (playerList) {
        playerList.innerHTML = ""; // Clear the list in the UI
    }

    console.log("Players have been reset");
}


function startGame() {
    // Get the initial score from the input field
    const initialScoreInput = parseInt(document.getElementById('initial-score').value);

    // Validate the initial score
    if (isNaN(initialScoreInput) || initialScoreInput <= 0) {
        alert("Please enter a valid positive number for the initial score!");
        return; // Prevent navigation
    }

    // Update the global initialScore variable
    initialScore = initialScoreInput;

    // Retrieve players from localStorage or validate if they exist
    const storedPlayers = JSON.parse(localStorage.getItem("players"));
    if (!storedPlayers || storedPlayers.length === 0) {
        alert("Please add players before starting the game!");
        return; // Prevent navigation
    }

    // Update scores based on the number of players
    scores = storedPlayers.map(() => initialScore);

    // Save updated scores to localStorage
    localStorage.setItem("scores", JSON.stringify(scores));

    // Navigate to the game page
    window.location.href = "game.html";
}





function loadGame() {
    players = JSON.parse(localStorage.getItem('players')) || [];
    scores = JSON.parse(localStorage.getItem('scores')) || [];

    console.log("Players:", players);
    console.log("Scores:", scores);

    fetch('http://localhost:3000/game-history')
    .then(response => response.json())
    .then(data => console.log("Game history:", data))
    .catch(error => console.error("Error loading history:", error));

    
    const scoreInputs = document.getElementById('score-inputs');
    scoreInputs.innerHTML = ''; // Reset content

    players.forEach((player, index) => {
        scoreInputs.innerHTML += `
            <div class="score-input-container">
                <h3 class="player-name">${player}</h3>
                <input type="number" id="throw-1-${index}" placeholder="Tiro 1" min="0" 
                    oninput="handleInputChange(${index})" onkeydown="handleKeyDown(event, ${index}, 1)">
                <input type="number" id="throw-2-${index}" placeholder="Tiro 2" min="0" 
                    oninput="handleInputChange(${index})" onkeydown="handleKeyDown(event, ${index}, 2)">
                <input type="number" id="throw-3-${index}" placeholder="Tiro 3" min="0" 
                    oninput="handleInputChange(${index})" onkeydown="handleKeyDown(event, ${index}, 3)">
                <p class="score"><span id="score-${index}">${scores[index]}</span></p>
            </div>
        `;
    });

    // Create table headers for players
    const tableHeader = document.getElementById('score-table-header');
    players.forEach(player => {
        const headerCell = document.createElement('th');
        headerCell.innerText = player;
        tableHeader.appendChild(headerCell);
    });
}


let tempScores = [...scores];   // Create a copy of the scores to track temporary scores

function handleInputChange(index) {
    const throw1 = parseInt(document.getElementById(`throw-1-${index}`).value) || 0;
    const throw2 = parseInt(document.getElementById(`throw-2-${index}`).value) || 0;
    const throw3 = parseInt(document.getElementById(`throw-3-${index}`).value) || 0;

    const totalThrow = throw1 + throw2 + throw3;

    // Update the temporary score
    tempScores[index] = scores[index] - totalThrow;

    // Prevent negative scores from being displayed
    if (tempScores[index] < 0) {
        tempScores[index] = 0;
    }

    // Update the score display dynamically
    document.getElementById(`score-${index}`).innerText = tempScores[index];
}


// Function to reset input fields for all players
function resetInputs() {
    players.forEach((_, index) => {
        document.getElementById(`throw-1-${index}`).value = '';
        document.getElementById(`throw-2-${index}`).value = '';
        document.getElementById(`throw-3-${index}`).value = '';
    });
}





function nextTurn() {
    let gameFinished = false;

    players.forEach((_, index) => {
        const throw1 = parseInt(document.getElementById(`throw-1-${index}`).value) || 0;
        const throw2 = parseInt(document.getElementById(`throw-2-${index}`).value) || 0;
        const throw3 = parseInt(document.getElementById(`throw-3-${index}`).value) || 0;
        const totalScore = throw1 + throw2 + throw3;

        const newScore = scores[index] - totalScore;


        console.log('currentTurn', currentTurn)
        if (currentTurn === 1){
            shotList[players[index]] = {}
        }  
        shotList[players[index]][currentTurn] = [throw1, throw2, throw3, totalScore, newScore]
        console.log('shot_list', shotList)


        if (newScore < 0) {
            alert(`${players[index]} ha superato lo zero! Torna al punteggio precedente.`);
        } else if (newScore === 0) {
            gameInfo.endTime = new Date().toISOString();
            gameFinished = true;
            gameInfo.winner = players[index]
            scores[index] = newScore
            console.log("Game info before saving:", gameInfo);
            alert(`${players[index]} ha vinto la partita!`);  

        } else {
            scores[index] = newScore; // Update the score
        }

        // Update the score display
        document.getElementById(`score-${index}`).innerText = scores[index];
        scoreChart.data.datasets[index].data.push(newScore);
    });

    // Increment the turn number
    currentTurn++;
    document.getElementById('turn-number').innerText = currentTurn;

    // Add the new turn to the x-axis labels dynamically
    if (scoreChart.data.labels.length < currentTurn) {
        scoreChart.data.labels.push(currentTurn);
    }

    // Adjust the x-axis range to expand beyond 10 only if currentTurn > 8
    if (currentTurn >= 8) {
        scoreChart.options.scales.x.max = currentTurn + 2; // Add extra room for new turns
    } else {
        scoreChart.options.scales.x.max = 10; // Keep default range
    }
    scoreChart.options.scales.x.min = 1; // Always start from 1

    // Update the chart to reflect changes
    scoreChart.update();

    if (gameFinished) {

        gameData = {
            game_id: Date.now(),
            start_time: gameInfo.startTime,
            end_time: gameInfo.endTime,
            players: players,
            initial_score: initialScore,
            winner: gameInfo.winner,  
            total_turns: currentTurn,
            shot_list: shotList
        };

        showResults();
        saveGameToServer(gameData);
        return;
    }

    resetInputs();

    // Set focus on the first player's Tiro 1 input
    document.getElementById(`throw-1-0`).focus();
}







function resetInputs() {
    players.forEach((_, index) => {
        document.getElementById(`throw-1-${index}`).value = '';
        document.getElementById(`throw-2-${index}`).value = '';
        document.getElementById(`throw-3-${index}`).value = '';
    });

}

function showResults() {
    document.getElementById('turn-section').style.display = 'none';
    const resultsDiv = document.getElementById('results');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<h2>Risultati finali</h2>';
    players.forEach((player, index) => {
        resultsDiv.innerHTML += `<p>${player}: ${scores[index]} punti</p>`;
    });
}

// Carica i giocatori se siamo nella pagina del gioco
if (window.location.pathname.endsWith('game.html')) {
    loadGame();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        addPlayer(); // Chiama la funzione per aggiungere il giocatore
    }
}

// Initialize Chart.js
let scoreChart;

// Store scores for each player over turns
const chartData = {
    labels: Array.from({ length: 10 }, (_, i) => i + 1), // Start with 1-10 turns
    datasets: []
};

function handleKeyDown(event, playerIndex, throwNumber) {
    if (event.key === "Enter") {
        const nextPlayerIndex = playerIndex + 1;

        // Check if it's the last player
        if (nextPlayerIndex < players.length) {
            // Move to the first throw of the next player
            document.getElementById(`throw-1-${nextPlayerIndex}`).focus();
        } else {
            // If it's the last player, go to the next turn
            nextTurn();
        }
    }
}


function initializeChart() {
    const ctx = document.getElementById("score-chart").getContext("2d");

    players.forEach((player, index) => {
        chartData.datasets.push({
            label: player,
            data: [scores[index]], // Starting score
            borderColor: getRandomColor(index), // Unique color
            fill: false,
            tension: 0.3,
            pointBackgroundColor: "#ffffff",
            pointBorderWidth: 2
        });
    });

    scoreChart = new Chart(ctx, {
        type: "line",
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        font: {
                            size: 14 // Increase font size
                        },
                        color: "#ffffff" // Set label color to white
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.dataset.label}: ${context.raw}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Turn",
                        font: {
                            size: 16 // Increase font size
                        },
                        color: "#ffffff" // Set color to white
                    },
                    ticks: {
                        stepSize: 1,
                        color: "#ffffff", // Set tick color to white
                        font: {
                            size: 14 // Increase font size
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Total Score",
                        font: {
                            size: 16 // Increase font size
                        },
                        color: "#ffffff" // Set color to white
                    },
                    ticks: {
                        color: "#ffffff", // Set tick color to white
                        font: {
                            size: 14 // Increase font size
                        }
                    }
                }
            }
        }
    });
}

// Function to update the chart
function updateChart() {
    const currentTurn = chartData.labels.length + 1;
    chartData.labels.push(`Turn ${currentTurn}`);

    players.forEach((player, index) => {
        const updatedScore = scores[index]; // Use current score
        chartData.datasets[index].data.push(updatedScore);
    });

    scoreChart.update(); // Refresh the chart
}

// Helper function to generate colors for lines
function getRandomColor(index) {
    const colors = [
        "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"
    ];
    return colors[index % colors.length]; // Rotate colors for players
}

// Initialize the chart after loading the game
if (window.location.pathname.endsWith('game.html')) {
    initializeChart();
}

function updateChart(turn) {
    players.forEach((player, index) => {
        // Push the updated score for each player
        scoreChart.data.datasets[index].data[turn - 1] = scores[index];
    });

    // Update the chart visuals
    scoreChart.update();
}

function restartGameWithReversedOrder() {
    // Reverse the order of players
    players.reverse();

    // Reset scores
    scores = players.map(() => initialScore);

    // Save new order and scores in localStorage
    localStorage.setItem('players', JSON.stringify(players));
    localStorage.setItem('scores', JSON.stringify(scores));

    // Reload the game page
    window.location.href = "game.html";
}

function saveGameToServer(gameData) {
    fetch('http://localhost:3000/save-game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(gameData)
    })
    .then(response => response.json())
    .then(data => console.log("Game saved:", data))
    .catch(error => console.error("Error saving game:", error));
}



