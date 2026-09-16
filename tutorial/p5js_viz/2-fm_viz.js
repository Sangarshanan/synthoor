let modWave = [];
let carWave = [];
let fmWave = [];
let totalNodes = 300; // More nodes for smoother, slower drawing

// Physics and Time Variables
let time = 0;
let timeStep = 0.2; // Slowed down significantly for visibility

// Frequencies and Modulation Parameters
let carFreq = 2.0;    // The fast, steady carrier wiggle
let modFreq = 0.0;    // The message (starts at 0 / idle)
let targetModFreq = 0.0;
let modIndex = 2;   // NEW: Modulation Index (Beta)

// Phases
let modPhase = 0;
let carPhase = 0;
let fmPhase = 0;

function setup() {
  createCanvas(800, 600);
  
  // Initialize empty waves
  for (let i = 0; i < totalNodes; i++) {
    modWave.push(0);
    carWave.push(0);
    fmWave.push(0);
  }
}

function draw() {
  background(20, 24, 30); // Dark theme for better contrast in videos
  
  // Smoothly transition between message frequencies
  modFreq = lerp(modFreq, targetModFreq, 0.05);
  
  // 1. Calculate the math for this exact frame
  modPhase += modFreq * timeStep;
  carPhase += carFreq * timeStep;
  
  // NEW: Calculate Frequency Deviation based on Modulation Index
  // Formula: Delta_f = Beta * f_m
  let freqDeviation = modIndex * modFreq;
  
  // The magic of FM: Instantaneous frequency = Carrier + Deviation
  let currentModulatorAmplitude = sin(modPhase);
  fmPhase += (carFreq + freqDeviation * currentModulatorAmplitude) * timeStep;
  
  // 2. Push new values to the front of our arrays
  modWave.unshift(currentModulatorAmplitude * 40); // 40 is visual height
  carWave.unshift(sin(carPhase) * 40);
  fmWave.unshift(sin(fmPhase) * 40);
  
  // 3. Remove the oldest values at the end of the string
  modWave.pop();
  carWave.pop();
  fmWave.pop();
  
  // 4. Draw the UI and the waves
  drawUI();
  
  drawWave(modWave, 150, color(46, 204, 113), "1. Modulator (The Message: A, B, or C)");
  drawWave(carWave, 300, color(52, 152, 219), "2. Carrier (The Steady Base Wiggle)");
  drawWave(fmWave, 450, color(231, 76, 60),  "3. Final FM Signal (The Modulated String)");
}

// Helper to draw a single wave
function drawWave(waveArray, yOffset, waveColor, label) {
  // Label
  fill(255);
  noStroke();
  textAlign(LEFT, BOTTOM);
  textSize(16);
  text(label, 50, yOffset - 50);
  
  // Center line
  stroke(255, 255, 255, 30);
  strokeWeight(1);
  line(50, yOffset, width - 50, yOffset);
  
  // The Wave
  noFill();
  stroke(waveColor);
  strokeWeight(3);
  beginShape();
  for (let i = 0; i < totalNodes; i++) {
    let x = map(i, 0, totalNodes - 1, 50, width - 50);
    let y = yOffset + waveArray[i];
    vertex(x, y);
  }
  endShape();
}

function drawUI() {
  fill(255);
  noStroke();
  textAlign(CENTER, TOP);
  textSize(24);
  text("FREQUENCY MODULATION (FM)", width / 2, 20);
  
  textSize(14);
  fill(200);
  text("Message: [ A ] = Slow  |  [ B ] = Medium  |  [ C ] = Fast  |  [ Space ] = Idle", width / 2, 50);
  text("Modulation Index: [ UP ] = Increase  |  [ DOWN ] = Decrease", width / 2, 70);
  
  // Active state display
  let currentLetter = "IDLE (No Message)";
  if (targetModFreq === 0.5) currentLetter = "Message A Transmitting";
  if (targetModFreq === 1.0) currentLetter = "Message B Transmitting";
  if (targetModFreq === 1.5) currentLetter = "Message C Transmitting";
  
  // Bottom Status Bar
  fill(241, 196, 15);
  text(`Status: ${currentLetter}`, width / 3, height - 30);
  fill(155, 89, 182);
  text(`Modulation Index (Beta): ${modIndex.toFixed(1)}`, (width / 3) * 2, height - 30);
}

function keyPressed() {
  // Handle Modulator Frequency (Message)
  if (key === 'a' || key === 'A') {
    targetModFreq = 0.5; // Slow wave
  } else if (key === 'b' || key === 'B') {
    targetModFreq = 1.0; // Medium wave
  } else if (key === 'c' || key === 'C') {
    targetModFreq = 1.5; // Fast wave
  } else if (key === ' ') {
    targetModFreq = 0.0; // Flatline / no message
  }
  
  // Handle Modulation Index
  if (keyCode === UP_ARROW) {
    modIndex += 0.5;
  } else if (keyCode === DOWN_ARROW) {
    modIndex -= 0.5;
    // Prevent negative modulation index for visual clarity
    if (modIndex < 0) modIndex = 0; 
  }
}

// Mouse click fallback for video recording (Optional)
function mousePressed() {
  if (mouseX > 0 && mouseX < width && mouseY > 0 && mouseY < height) {
    if (targetModFreq === 0.0) {
      targetModFreq = 0.5; // A
    } else if (targetModFreq === 0.5) {
      targetModFreq = 1.0; // B
    } else if (targetModFreq === 1.0) {
      targetModFreq = 1.5; // C
    } else {
      targetModFreq = 0.0; // Back to Idle
    }
  }
}