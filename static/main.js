let drawing = false;
let imageUploaded = false;
let cWidth = document.getElementById("canvasHolder").clientWidth;
let cHeight = document.getElementById("canvasHolder").clientHeight;
let canvas;
let canvasBackup = null;

let currentScores = {};

let pointerDown = false;

// Initialize scores from alphabet
function initScores(alphabet) {
    const scores = {};
    for (const char of alphabet) {
        scores[char] = 0;
    }
    return scores;
}

// Update RTL direction for sample text
function updateTextDirection(lang) {
    const sampleElement = document.getElementById('sample');
    sampleElement.style.direction = lang === 'ar' ? 'rtl' : 'ltr';
}

// Fetch current language settings from server
async function fetchLanguageSettings() {
    const response = await fetch('/language');
    const data = await response.json();
    currentAlphabet = data.alphabet;
    setCurrentLang(data.language);
    updateTextDirection(data.language);
    return data;
}

// Switch language
async function switchLanguage(lang) {
    // Update active button immediately
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });

    const response = await fetch('/language', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: lang })
    });
    const data = await response.json();

    currentAlphabet = data.alphabet;
    currentScores = data.scores;
    setCurrentLang(data.language);
    updateTextDirection(data.language);

    // Rebuild grid and fetch new sample
    createAlphabetGrid(currentScores, currentAlphabet);
    clear();
    background(220);
    fetchSample();
}

// Set up language button handlers and sync active state
function setupLanguageButtons(activeLang = 'en') {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === activeLang);
        btn.addEventListener('click', () => {
            switchLanguage(btn.dataset.lang);
        });
    });
}

function setup() {
    canvas = createCanvas(cWidth, cHeight);
    canvas.parent("canvasHolder");
    background(220);

    // Initialize with server settings, then set up buttons
    fetchLanguageSettings().then(data => {
        setupLanguageButtons(data.language);
        currentScores = data.scores || initScores(currentAlphabet);
        createAlphabetGrid(currentScores, currentAlphabet);
        fetchSample();
    });

    const canvasElement = document.getElementById("defaultCanvas0");
    const startListener = window.PointerEvent ? 'pointerdown' : 'touchstart';
    const endListener = window.PointerEvent ? 'pointerup' : 'touchend';
    canvasElement.addEventListener(startListener, () => {
        pointerDown = true;
    });
    canvasElement.addEventListener(endListener, () => {
        pointerDown = false;
    });
    window.addEventListener("touchend", mouseReleased);
    window.addEventListener("pointerup", mouseReleased);
}

function windowResized() {
    const holder = document.getElementById("canvasHolder");
    const newWidth = holder.clientWidth;
    const newHeight = holder.clientHeight;

    const current = get();

    if (!canvasBackup || current.width >= canvasBackup.width) {
        canvasBackup = current;
    } else {
        // Canvas shrank previously — merge new strokes onto the larger backup
        canvasBackup.copy(current, 0, 0, current.width, current.height, 0, 0, current.width, current.height);
    }

    resizeCanvas(newWidth, newHeight);
    background(220);
    image(canvasBackup, 0, 0);

    cWidth = newWidth;
    cHeight = newHeight;
}

// The part of the canvas with writing on it, plus a margin, in canvas units; null if blank.
function inkBounds(margin) {
    const element = document.getElementById("defaultCanvas0");
    const density = element.width / width;
    const data = element.getContext("2d").getImageData(0, 0, element.width, element.height).data;
    let left = element.width, top = element.height, right = -1, bottom = -1;
    for (let y = 0; y < element.height; y++) {
        for (let x = 0; x < element.width; x++) {
            // Strokes are black on a light grey (220) background.
            if (data[(y * element.width + x) * 4] < 128) {
                left = Math.min(left, x);
                right = Math.max(right, x);
                top = Math.min(top, y);
                bottom = y;
            }
        }
    }
    if (right < 0) {
        return null;
    }
    const x = Math.max(0, left / density - margin);
    const y = Math.max(0, top / density - margin);
    return {
        x,
        y,
        width: Math.min(width, (right + 1) / density + margin) - x,
        height: Math.min(height, (bottom + 1) / density + margin) - y,
    };
}

// Resizes the canvas to its holder, keeping what's written. Writing too big for the new
// size is cropped to its own extent and shrunk to fit, so leaving full screen never cuts
// letters off or makes them too small to read.
function fitCanvasToHolder(drawingImage) {
    const holder = document.getElementById("canvasHolder");
    const newWidth = holder.clientWidth;
    const newHeight = holder.clientHeight;
    const fits = drawingImage.width <= newWidth && drawingImage.height <= newHeight;
    const source = (!fits && inkBounds(20)) || {x: 0, y: 0, width: drawingImage.width, height: drawingImage.height};
    const scale = Math.min(1, newWidth / source.width, newHeight / source.height);
    const drawnWidth = source.width * scale;
    const drawnHeight = source.height * scale;

    resizeCanvas(newWidth, newHeight);
    background(220);
    if (fits) {
        image(drawingImage, 0, 0);
    } else {
        image(drawingImage, (newWidth - drawnWidth) / 2, (newHeight - drawnHeight) / 2, drawnWidth, drawnHeight,
            source.x, source.y, source.width, source.height);
    }

    cWidth = newWidth;
    cHeight = newHeight;
    canvasBackup = null;
}

// Fills the screen with the sentence, the canvas and the buttons, for writing on a phone.
// A fixed overlay rather than the Fullscreen API, which iPhones don't offer for a page.
function toggleFullscreen() {
    const area = document.getElementById("writingArea");
    const button = document.getElementById("fullscreenButton");
    const entering = !area.classList.contains("fullscreen");
    const drawingImage = get();

    area.classList.toggle("fullscreen", entering);
    document.body.classList.toggle("writing-fullscreen", entering);
    button.setAttribute("aria-label", entering ? "Exit full screen" : "Full screen");
    button.textContent = entering ? "Done" : "Full screen";
    fitCanvasToHolder(drawingImage);
}

function draw() {
    fill(0);
    if (drawing && !imageUploaded) {
        stroke(0);
        strokeWeight(7);
        line(pmouseX, pmouseY, mouseX, mouseY);
    }
}

const keys = {37: 1, 38: 1, 39: 1, 40: 1};

function preventDefault(e) {
    e.preventDefault();
}

function preventDefaultForScrollKeys(e) {
    if (keys[e.keyCode]) {
        preventDefault(e);
        return false;
    }
}

let supportsPassive = false;
try {
    window.addEventListener("test", null, Object.defineProperty({}, 'passive', {
        get: function () {
            supportsPassive = true;
        }
    }));
} catch (e) {
}

const wheelOpt = supportsPassive ? {passive: false} : false;
const wheelEvent = 'onwheel' in document.createElement('div') ? 'wheel' : 'mousewheel';

function disableScroll() {
    window.addEventListener('DOMMouseScroll', preventDefault, false);
    window.addEventListener(wheelEvent, preventDefault, wheelOpt);
    window.addEventListener('touchmove', preventDefault, wheelOpt);
    window.addEventListener('keydown', preventDefaultForScrollKeys, false);
}

function enableScroll() {
    window.removeEventListener('DOMMouseScroll', preventDefault, false);
    window.removeEventListener(wheelEvent, preventDefault, wheelOpt);
    window.removeEventListener('touchmove', preventDefault, wheelOpt);
    window.removeEventListener('keydown', preventDefaultForScrollKeys, false);
}

function mousePressed() {
    drawing = true;
    if (pointerDown) {
        disableScroll();
    }
}

function mouseReleased() {
    drawing = false;
    enableScroll();
}

function submit(firstTime) {
    let canvasElement = document.getElementById("defaultCanvas0");
    let dataURL = canvasElement.toDataURL("image/jpeg");

    imageUploaded = false;

    const formData = new FormData();
    const statusLine = document.getElementById("statusLine");
    const proccesselement = document.getElementById("statusText");
    const feedbackElement = document.getElementById("feedbackText");
    if (!firstTime) {
        statusLine.style.display = "";
        proccesselement.textContent = "Submission Accepted";
    }
    fetch(dataURL)
        .then((response) => response.blob())
        .then((blob) => {
            formData.append("imageFile", blob);
            fetch("/submit_canvas", {
                method: "POST",
                body: formData,
                enctype: "multipart/form-data",
            })
                .then((res) => {
                    if (!firstTime) {
                        proccesselement.textContent = "Analyzing Your Handwriting...";
                    }
                    return res.json();
                })
                .then((data) => {
                    if (!firstTime) {
                        proccesselement.textContent = "Updating Character Scores...";
                    }
                    if (data["sample"] && data["char_results"]) {
                        feedbackElement.innerHTML = "";
                        const label = document.createElement("strong");
                        label.textContent = "Last Attempt: ";
                        feedbackElement.appendChild(label);
                        const sample = data["sample"];
                        const results = data["char_results"];
                        for (let i = 0; i < sample.length; i++) {
                            const span = document.createElement("span");
                            span.textContent = sample[i];
                            if (results[i] === true) {
                                span.style.color = "#2e7d32";
                            } else if (results[i] === false) {
                                span.style.color = "#c62828";
                            }
                            feedbackElement.appendChild(span);
                        }
                    }
                    currentScores = data['scores'];
                    return createAlphabetGrid(currentScores, currentAlphabet);
                })
                .then(() => {
                    if (!firstTime) {
                        proccesselement.textContent = "Generating New Sentence...";
                    }
                    clear();
                    background(220);
                    return fetchSample();
                });
        });
}

function uploadImage() {
    imageUploaded = true;
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadButton");

    uploadButton.addEventListener("click", () => {
        fileInput.click();
    });
    fileInput.addEventListener("change", () => {
        const selectedFile = fileInput.files[0];
        if (selectedFile) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const canvas = document.getElementById("defaultCanvas0");
                const context = canvas.getContext("2d");

                const img = new Image();
                img.onload = () => {
                    const newHeight = cHeight;
                    const newWidth = (img.width * cHeight) / img.height;

                    context.drawImage(
                        img,
                        (cWidth - newWidth) / 2,
                        0,
                        newWidth,
                        newHeight
                    );
                    canvas.style.display = "block";
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(selectedFile);
        }
    });
}

function fetchSample() {
    const sampleText = document.getElementById("sample");
    sampleText.innerHTML = '';

    fetch("/sample")
        .then((res) => {
            const proccesselement = document.getElementById("statusText");
            proccesselement.innerText = "";
            document.getElementById("statusLine").style.display = "none";
            return res.text();
        })
        .then((sample) => (sampleText.innerHTML = sample));
}
