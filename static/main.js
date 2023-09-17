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
	} else if (imageUploaded) {
		console.log("we should display an image");
	}
}

function mousePressed() {
	drawing = true;
}

function mouseReleased() {
	drawing = false;
}

function submit() {
	const canvasElement = document.getElementById("defaultCanvas0");
	const dataURL = canvasElement.toDataURL("image/jpeg");

	// Create a FormData object and append the image data
	const formData = new FormData();
	formData.append("image", dataURL);

	// Send the data to the API endpoint
	fetch("http://127.0.0.1:5000/submit_canvas", {
		method: "POST",
		body: formData,
	});
	// .then((response) => {
	// 	if (response.ok) {
	// 		// Handle a successful response here if needed
	// 	} else {
	// 		// Handle errors here
	// 	}
	// })
	// .catch((error) => {
	// 	// Handle network errors here
	// });

	clear();
	imageUploaded = false;
	background(220);
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
					newHeight = cHeight;
					newWidth = (img.width * cHeight) / img.height;

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
