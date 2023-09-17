function createAlphabetGrid() {
    const alphabetGrid = document.getElementById('alphabet-grid');
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

    // Define progress values for each letter (0% to 100%)
    const progressValues = {
        A: 25,
        B: 50,
        C: 75,
        // Add progress values for other letters as needed
    };

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
        const progressValue = progressValues[letter] || 0; // Default to 0 if not defined

        // Set the width of the progress bar based on the progress value
        progressBar.style.width = `${progressValue}%`;

        // Append the progress bar to its container
        progressBarContainer.appendChild(progressBar);

        // Append the grid item and progress bar container to the alphabet grid
        gridItem.appendChild(progressBarContainer);
        alphabetGrid.appendChild(gridItem);
    }
}

// Call the function to create and insert grid items with progress bars
createAlphabetGrid();







