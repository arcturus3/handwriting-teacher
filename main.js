let drawing = false;
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
  if (drawing) {
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

function submit(){

    let canvasElement = document.getElementById("defaultCanvas0");
    let dataURL = canvasElement.toDataURL('image/jpeg');

    // Create a link element to download the image
    let a = document.createElement('a');
    a.href = dataURL;
    a.download = 'your_image.jpg'; // Specify the filename

    // Trigger a click event to download the image
    a.click();
    background(220);
}


// function submit() {
//   let img = get(0, 0, cWidth, cHeight);
//   img.loadPixels();

//   // Get the pixel data from the captured image
//   let pixels = img.pixels;

//   //mr.chat code
//   // Create a 2D array to store black and white pixel values
//   let bwPixels = [];

//   // Iterate through the pixel data
//   for (let y = 0; y < cHeight; y++) {
//     let row = [];
//     for (let x = 0; x < cWidth; x++) {
//       // Calculate the pixel index in the pixel data array
//       let pixelIndex = (y * cWidth + x) * 4; // Each pixel has 4 values (R, G, B, and A)

//       // Get the R, G, and B values of the pixel
//       let r = pixels[pixelIndex];
//       let g = pixels[pixelIndex + 1];
//       let b = pixels[pixelIndex + 2];

//       // Convert the pixel to grayscale (average of R, G, and B values)
//       let grayscaleValue = (r + g + b) / 3;

//       // Push the grayscale value to the row array
//       row.push(grayscaleValue);
//     }
//     // Push the row to the 2D array
//     bwPixels.push(row);
//   }
//   let jsonData = {
//     prompt: "Elliot",
//     sample: bwPixels,
//   };

//   console.log(JSON.stringify(jsonData));

//   // Clear the canvas after processing the pixels
//   background(220);
// }
