let frequency = 0.5; 
let amplitude = 100;
let t = 0; 

let waveHistory = []; 

function setup() {
  createCanvas(800, 400);
}

function draw() {
  background(30);
  
  let angularVelocity = TWO_PI * frequency;
  t += 0.02; 
  
  let currentAngle = angularVelocity * t;
  
  // Calculate X and Y on the circle
  // We use -sin() so the wave visually goes UP first (matching standard math graphs)
  // because in p5.js, the Y-axis goes down as numbers increase.
  let clockX = cos(currentAngle) * amplitude;
  let clockY = -sin(currentAngle) * amplitude; 
  
  // Save frame's Y value to draw a continuous line
  waveHistory.unshift(clockY);
  
  if (waveHistory.length > 360) {
    waveHistory.pop();
  }

  // --- LEFT SIDE: TRACKING THE HEIGHT (The Circle) ---
  let centerX = 150;
  let centerY = height / 2;
  
  // Draw the empty circle
  stroke(100);
  strokeWeight(2);
  noFill();
  circle(centerX, centerY, amplitude * 2);
  
  // Draw the center X-axis of the circle
  stroke(70);
  strokeWeight(1);
  line(centerX - amplitude, centerY, centerX + amplitude, centerY);
  
  // Draw the rotating radius hand
  stroke(255);
  strokeWeight(2);
  line(centerX, centerY, centerX + clockX, centerY + clockY);
  
  // THE VISUAL FIX: Highlight the Y-height (The actual sine value)
  stroke(255, 100, 255); // Magenta for emphasis
  strokeWeight(4);
  line(centerX + clockX, centerY, centerX + clockX, centerY + clockY);
  
  // Draw the dot on the circle
  fill(255, 100, 255);
  noStroke();
  circle(centerX + clockX, centerY + clockY, 10);
  
  // Label for the left side
  fill(255, 100, 255);
  noStroke();
  textSize(14);
  textAlign(CENTER, CENTER);
  text("Tracking Height (Y-Axis)", centerX, centerY - amplitude - 30);
  
  // --- CENTER: THE MAPPING EXPLANATION ---
  let mapX = 300;
  textSize(14);
  fill(200);
  textAlign(LEFT, CENTER);
  text("Height on Circle is", mapX, centerY);
  text("Amplitude on the Wave", mapX, centerY + 20);
  
  // --- RIGHT SIDE: CONTINUOUS SINE WAVE ---
  let startWaveX = 500;
  
  // Draw the center timeline axis
  stroke(100);
  strokeWeight(2);
  line(startWaveX, centerY, width - 20, centerY);
  
  // Draw the fully formed continuous wave
  noFill();
  stroke(0, 255, 100);
  strokeWeight(3);
  
  beginShape();
  for (let i = 0; i < waveHistory.length; i++) {
    let drawX = startWaveX + i; 
    if (drawX < width - 20) {
      vertex(drawX, centerY + waveHistory[i]);
    }
  }
  endShape();
  
  // Draw a dashed line projecting the exact height from the circle to the wave
  stroke(255, 255, 255, 150);
  strokeWeight(1);
  drawingContext.setLineDash([5, 5]); 
  line(centerX + clockX, centerY + clockY, startWaveX, centerY + clockY);
  drawingContext.setLineDash([]); 

  // Label for the right side
  fill(255);
  noStroke();
  textAlign(CENTER, CENTER);
  text("Sine Wave (Mapped Height)", startWaveX + 150, centerY - amplitude - 30);
}