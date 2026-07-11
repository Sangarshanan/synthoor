// Waveshaper / Saturator Visualizer
//
// Every audio sample is fed through a transfer function f(x):
//   soft_clip(x) = tanh(drive × x) / tanh(drive)   → warm, analog saturation
//
// The animated yellow dot traces the input sine through the transfer curve
// to produce the saturated output. Rounded peaks = new harmonic content.
//
// Colour key on output wave:
//   orange = near saturation (peak flattening happening here)
//   yellow = comfortable linear region

let t = 0;
let drive = 4.0;

let waveHistory = [];

function softClip(x) {
  return Math.tanh(drive * x) / Math.tanh(drive);
}

function setup() {
  createCanvas(900, 430);
}

function draw() {
  background(20);
  t += 0.022;

  let inputVal  = sin(TWO_PI * 0.65 * t);
  let outputVal = softClip(inputVal);

  waveHistory.unshift({ inp: inputVal, out: outputVal });
  if (waveHistory.length > 460) waveHistory.pop();

  // ─────────── Transfer Curve (left panel) ───────────
  let tcx = 195, tcy = 250, tcW = 158, tcH = 158;

  stroke(60); strokeWeight(1); noFill();
  rect(tcx - tcW, tcy - tcH, tcW * 2, tcH * 2);

  // Grid
  stroke(45); strokeWeight(0.5);
  line(tcx - tcW, tcy, tcx + tcW, tcy);
  line(tcx, tcy - tcH, tcx, tcy + tcH);

  // Linear reference (no distortion baseline)
  stroke(75); strokeWeight(1);
  drawingContext.setLineDash([4, 4]);
  line(tcx - tcW, tcy + tcH, tcx + tcW, tcy - tcH);
  drawingContext.setLineDash([]);

  // Tanh soft clip curve
  noFill(); stroke(255, 140, 50); strokeWeight(2.5);
  beginShape();
  for (let xi = -tcW; xi <= tcW; xi++) {
    let xv = xi / tcW;
    let yv = Math.tanh(drive * xv) / Math.tanh(drive);
    vertex(tcx + xi, tcy - yv * tcH);
  }
  endShape();

  // Animated tracer dot following input → output through the curve
  let dotX = tcx + inputVal * tcW;
  let dotY = tcy - outputVal * tcH;

  // Crosshair guides to the dot
  stroke(100, 150, 255, 130); strokeWeight(1);
  drawingContext.setLineDash([3, 5]);
  line(tcx - tcW - 8, dotY, dotX, dotY);   // horizontal guide (output level)
  line(dotX, tcy + tcH + 8, dotX, dotY);   // vertical guide   (input level)
  drawingContext.setLineDash([]);

  fill(255, 220, 50); noStroke();
  circle(dotX, dotY, 13);

  // Axis labels
  fill(200); noStroke(); textSize(11); textAlign(CENTER);
  text("Input →", tcx, tcy + tcH + 20);
  textAlign(RIGHT);
  text("↑ Output", tcx - tcW - 4, tcy - 8);

  fill(255, 175, 70); textSize(13); textAlign(CENTER);
  text("Transfer Curve  (tanh)", tcx, tcy - tcH - 20);

  fill(130); textSize(10);
  text("drive = " + drive.toFixed(1) + "   (steeper → more distortion)", tcx, tcy + tcH + 34);

  // ─────────── Input Wave (centre) ───────────
  let inX = 400, midY = 215, segW = 215;

  stroke(55); strokeWeight(1);
  line(inX, midY, inX + segW, midY);

  noFill(); stroke(100, 150, 255); strokeWeight(2);
  beginShape();
  for (let i = 0; i < min(waveHistory.length, segW); i++) {
    vertex(inX + i, midY - waveHistory[i].inp * 85);
  }
  endShape();

  fill(100, 150, 255); noStroke();
  circle(inX, midY - inputVal * 85, 9);

  fill(160, 190, 255); noStroke(); textSize(12); textAlign(CENTER);
  text("Input  (clean sine)", inX + segW / 2, midY - 108);

  // ─────────── Arrow ───────────
  fill(200); noStroke(); textSize(26); textAlign(CENTER, CENTER);
  text("→", 648, midY);

  // ─────────── Output Wave (right) ───────────
  let outX = 668, outW = width - 15 - outX;

  stroke(55); strokeWeight(1);
  line(outX, midY, outX + outW, midY);

  // Colour by saturation level: orange where peaks are flattened
  strokeWeight(2.5); noFill();
  for (let i = 0; i < min(waveHistory.length - 1, outW); i++) {
    let yA = waveHistory[i].out;
    let yB = waveHistory[i + 1].out;
    stroke(abs(yA) > 0.88 ? color(255, 100, 50) : color(255, 200, 80));
    line(outX + i, midY - yA * 85, outX + i + 1, midY - yB * 85);
  }

  fill(0, 255, 130); noStroke();
  circle(outX, midY - outputVal * 85, 9);

  fill(255, 170, 70); noStroke(); textSize(12); textAlign(CENTER);
  text("Output  (saturated)", outX + outW / 2, midY - 108);

  // Colour legend
  fill(255, 100, 50); textSize(11); textAlign(LEFT);
  text("■  saturating  (harmonic richness added)", outX + 2, midY + 108);
  fill(255, 200, 80);
  text("■  linear  (unchanged)", outX + 2, midY + 122);

  // ─────────── Title ───────────
  fill(255); noStroke(); textSize(17); textAlign(CENTER);
  text("Waveshaping  ·  Nonlinear Saturation  (tanh soft clip)", width / 2, 22);
  fill(160); textSize(11);
  text("The transfer curve remaps input amplitude → output — rounded peaks introduce warm overtones", width / 2, 40);

  fill(180); textSize(12); textAlign(LEFT);
  text("tanh(drive × x) / tanh(drive)", 20, height - 14);
}
