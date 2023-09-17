let drawing = false;
let imageUploaded = false;
let cWidth = document.getElementById("canvasHolder").clientWidth;
let cHeight = document.getElementById("canvasHolder").clientHeight;
let canvas;

function setup() {
    canvas = createCanvas(cWidth, cHeight);
    // Set the canvas size as per your requirements
    canvas.parent("canvasHolder"); // Attach the canvas to the HTML element with id "p5Canvas"
    background(220); // Set the initial background color
}

function draw() {
    fill(0);
    if (drawing && !imageUploaded) {
        stroke(0); // Set the stroke color (black)
        strokeWeight(7); // Set the stroke thickness
        line(pmouseX, pmouseY, mouseX, mouseY); // Draw a line from the previous mouse position to the current position
    } 
}

function mousePressed() {
    drawing = true;
}

function mouseReleased() {
    drawing = false;
}

function submit() {


    let canvasElement = document.getElementById("defaultCanvas0");
    let dataURL = canvasElement.toDataURL("image/jpeg");
    clear();
    imageUploaded = false;
    background(220);

    const formData = new FormData();

    fetch(dataURL)
        .then((response) => response.blob())
        .then((blob) => {
            formData.append("imageFile", blob);
            formData.append("sample", "Elliot");

            return fetch("/submit_canvas", {
                method: "POST",
                body: formData,
                enctype: "multipart/form-data",
                // Note: No need to set Content-type or Content-Length headers for FormData
            });
        })
        .then((response) => {
            // Handle the response here
            if (response.ok) {
                // Success
                return response.json();
            } else {
                // Handle errors
            }
        }).then((json)=>{
            console.log(json)
        })
        .catch((error) => {
            console.log(error)
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

                    context.drawImage(img, (cWidth - newWidth) / 2, 0, newWidth, newHeight);
                    canvas.style.display = "block";
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(selectedFile);
        }
    });
}
