let frequency = 0.5; // Slowed down slightly so you can read the angles
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
  
  // Find the pure angle of the current rotation (0 to TWO_PI)
  let sweepAngle = currentAngle % TWO_PI;
  
  // Map the angle (0 to TWO_PI) directly to our amplitude (+100 to -100)
  // 0 degrees = top of the wave (+amplitude)
  // 360 degrees = bottom of the wave (-amplitude)
  let currentY = map(sweepAngle, 0, TWO_PI, amplitude, -amplitude);
  
  // Calculate clock hand position for the visual
  let clockX = cos(sweepAngle - HALF_PI) * amplitude;
  let clockY = sin(sweepAngle - HALF_PI) * amplitude;
  
  // Save frame's Y value to draw a continuous line
  waveHistory.unshift(currentY);
  
  if (waveHistory.length > 400) {
    waveHistory.pop();
  }

  // --- LEFT SIDE: TRACKING THE ANGLE (The Pie Sweep) ---
  let centerX = 150;
  let centerY = height / 2;
  
  // Draw the empty clock outline
  stroke(100);
  strokeWeight(2);
  noFill();
  circle(centerX, centerY, amplitude * 2);
  
  // 1. THE VISUAL FIX: Draw a shaded arc to represent the growing ANGLE
  fill(100, 150, 255, 150); // Semi-transparent blue
  noStroke();
  // We start at -HALF_PI (12 o'clock) and sweep to the current angle
  if (sweepAngle > 0) {
    arc(centerX, centerY, amplitude * 2, amplitude * 2, -HALF_PI, sweepAngle - HALF_PI, PIE);
  }
  
  // Draw the rotating hand
  stroke(255);
  strokeWeight(3);
  line(centerX, centerY, centerX + clockX, centerY + clockY);
  
  // Calculate degrees for the text readout
  let currentDegrees = floor(degrees(sweepAngle));
  
  // Draw the dynamic text showing the angle growing
  fill(255);
  noStroke();
  textSize(20);
  textAlign(CENTER, CENTER);
  text(currentDegrees + "°", centerX, centerY + amplitude + 30);
  
  textSize(14);
  fill(100, 150, 255);
  text("Growing Angle (Phase)", centerX, centerY - amplitude - 30);
  
  // --- CENTER: THE MAPPING EXPLANATION ---
  // Show exactly how the angle translates to the wave height
  let mapX = 300;
  textSize(14);
  fill(200);
  textAlign(LEFT, CENTER);
  text("Mapping:", mapX, centerY - 20);
  text("0°   ->  Top", mapX, centerY);
  text("360° ->  Bottom", mapX, centerY + 20);
  
  // --- RIGHT SIDE: CONTINUOUS SAWTOOTH WAVE ---
  let startWaveX = 400;
  
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
  
  // Replace the dot-tracking dashed line with one that tracks the OUTPUT
  stroke(255, 255, 255, 100);
  strokeWeight(1);
  drawingContext.setLineDash([5, 5]); 
  // It now draws from the mapping text to the wave, breaking the sine-wave illusion
  line(mapX + 100, centerY + currentY, startWaveX, centerY + currentY);
  drawingContext.setLineDash([]); 

  fill(255);
  noStroke();
  textAlign(CENTER, CENTER);
  text("Sawtooth Wave (Mapped Angle)", startWaveX + 150, centerY - amplitude - 30);
}