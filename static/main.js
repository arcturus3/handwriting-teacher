let drawing = false;
let imageUploaded = false;
let cWidth = document.getElementById("canvasHolder").clientWidth;
let cHeight = document.getElementById("canvasHolder").clientHeight;
let canvas;

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
        currentScores = initScores(currentAlphabet);
        createAlphabetGrid(currentScores, currentAlphabet);
        submit(true);
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
    const proccesselement = document.getElementById("statusText");
    const feedbackElement = document.getElementById("feedbackText");
    if (!firstTime) {
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
                    if (data["successful"] !== undefined) {
                        console.log(data["successful"]);
                        feedbackElement.textContent = "Great job with these letters: " + data["successful"];
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
            return res.text();
        })
        .then((sample) => (sampleText.innerHTML = sample));
}
