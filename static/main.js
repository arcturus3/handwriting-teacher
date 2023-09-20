let drawing = false;
let imageUploaded = false;
let cWidth = document.getElementById("canvasHolder").clientWidth;
let cHeight = document.getElementById("canvasHolder").clientHeight;
let canvas;

const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const initialScores = Object.fromEntries([...alphabet].map((c) => [c, 0]));

let pointerDown = false

function setup() {
    canvas = createCanvas(cWidth, cHeight);
    // Set the canvas size as per your requirements
    canvas.parent("canvasHolder"); // Attach the canvas to the HTML element with id "p5Canvas"
    background(220); // Set the initial background color
    submit(true);

    const canvasElement = document.getElementById("defaultCanvas0");
    const startListener = window.PointerEvent ? 'pointerdown' : 'touchstart';
    const endListener = window.PointerEvent ? 'pointerup' : 'touchend';
    canvasElement.addEventListener(startListener, () => {
        pointerDown = true
    });
    canvasElement.addEventListener(endListener, () => {
        pointerDown = false
    });
    window.addEventListener("touchend", mouseReleased);
    window.addEventListener("pointerup", mouseReleased); //weird hack, lol

}

function draw() {
    fill(0);
    if (drawing && !imageUploaded) {
        stroke(0); // Set the stroke color (black)
        strokeWeight(7); // Set the stroke thickness
        line(pmouseX, pmouseY, mouseX, mouseY); // Draw a line from the previous mouse position to the current position
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

// modern Chrome requires { passive: false } when adding event
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

// call this to Disable
function disableScroll() {
    window.addEventListener('DOMMouseScroll', preventDefault, false); // older FF
    window.addEventListener(wheelEvent, preventDefault, wheelOpt); // modern desktop
    window.addEventListener('touchmove', preventDefault, wheelOpt); // mobile
    window.addEventListener('keydown', preventDefaultForScrollKeys, false);
}

// call this to Enable
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
                // Note: No need to set Content-type or Content-Length headers for FormData
            })
                .then((res) => {
                    if (!firstTime) {
                        proccesselement.textContent = "Analyzing Your Handwriting...";
                    }
                    return res.json();
                })
                .then((scores) => {
                    if (!firstTime) {
                        proccesselement.textContent = "Updating Character Scores...";
                    }
                    if (scores["successful"] !== undefined) {
                        console.log(scores["successful"]);
                        feedbackElement.textContent = "Great job with these letters: " + scores["successful"];
                    }

                    return createAlphabetGrid(scores['scores']);
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

    // Create a link element to download the image
    uploadButton.addEventListener("click", () => {
        fileInput.click(); // Trigger the file input when the button is clicked
    });
    fileInput.addEventListener("change", () => {
        const selectedFile = fileInput.files[0];
        if (selectedFile) {
            const reader = new FileReader();
            reader.onload = (e) => {
                // Draw the image on the canvas
                const canvas = document.getElementById("defaultCanvas0");
                const context = canvas.getContext("2d");

                const img = new Image();
                img.onload = () => {
                    //keep the aspect ratio reasonable
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
    fetch("/sample")
        .then((res) => {
            const proccesselement = document.getElementById("statusText");
            proccesselement.innerText = "";
            return res.text();
        })
        .then((sample) => (sampleText.innerHTML = sample));
}

createAlphabetGrid(initialScores);
