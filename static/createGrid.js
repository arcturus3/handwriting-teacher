let currentAlphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
let currentLang = 'en';

function createAlphabetGrid(scores, alphabet) {
    if (alphabet) {
        currentAlphabet = alphabet;
    }

    const alphabetGrid = document.getElementById('alphabet-grid');

    while (alphabetGrid.firstChild)
        alphabetGrid.removeChild(alphabetGrid.firstChild);

    // Add RTL class for Arabic
    if (currentLang === 'ar') {
        alphabetGrid.classList.add('rtl');
    } else {
        alphabetGrid.classList.remove('rtl');
    }

    for (let i = 0; i < currentAlphabet.length; i++) {
        const letter = currentAlphabet[i];
        const gridItem = document.createElement('div');
        gridItem.classList.add('alphabet-item');
        gridItem.textContent = letter;

        // Create the progress bar container
        const progressBarContainer = document.createElement('div');
        progressBarContainer.classList.add('progress-bar-container');

        // Create the progress bar
        const progressBar = document.createElement('div');
        progressBar.classList.add('progress-bar');

        // Get the progress value for the current letter
        const progressValue = scores[letter] || 0;

        // Set the width of the progress bar based on the progress value
        progressBar.style.width = `${progressValue * 100}%`;

        if (progressValue >= 1) {
            progressBar.style.backgroundColor = "gold";
        }

        // Append the progress bar to its container
        progressBarContainer.appendChild(progressBar);

        // Append the grid item and progress bar container to the alphabet grid
        gridItem.appendChild(progressBarContainer);
        alphabetGrid.appendChild(gridItem);
    }
}

function setCurrentLang(lang) {
    currentLang = lang;
}
