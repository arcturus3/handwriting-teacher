function createAlphabetGrid(scores) {
    const alphabetGrid = document.getElementById('alphabet-grid');

    while (alphabetGrid.firstChild)
        alphabetGrid.removeChild(alphabetGrid.firstChild);

    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

    for (let i = 0; i < alphabet.length; i++) {
        const letter = alphabet[i];
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
        const progressValue = scores[letter];


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
