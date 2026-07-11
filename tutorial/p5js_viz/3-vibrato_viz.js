// Vibrato Visualizer
// Vibrato = FM where the modulator is a very slow LFO (1–10 Hz).
// The LFO bends the carrier's instantaneous frequency up and down.
//
// f_inst(t) = f_c + depth × sin(ω_lfo · t)
// phase(t)  = 2π × Σ f_inst(τ)·Δτ     ← accumulate phase correctly
// output(t) = sin(phase(t))
//
// Colour key:  orange = pitch bent UP (compressed cycles)
//              blue   = pitch bent DOWN (stretched cycles)

let t     = 0;
let phase = 0;   // accumulated carrier phase

let lfoFreq  = 0.08;   // visual LFO speed (slow spin)
let lfoDepth = 0.55;   // how much the carrier frequency wobbles
let baseFreq = 1.5;    // carrier base frequency (visual units)

let waveHistory = [];
let lfoHistory  = [];

function setup() {
  createCanvas(900, 430);
}

function draw() {
  background(20);

  let dt       = 0.022;
  let lfoAngle = TWO_PI * lfoFreq * t;
  let lfoVal   = sin(lfoAngle);

  // Instantaneous carrier frequency: base ± LFO depth
  let instFreq = baseFreq + lfoDepth * lfoVal;

  // Integrate for correct FM (not just add to angle directly)
  phase += TWO_PI * instFreq * dt;
  t     += dt;

  let outputVal = sin(phase);
  let waveY     = outputVal * 90;

  waveHistory.unshift(waveY);
  lfoHistory.unshift(lfoVal);
  if (waveHistory.length > 500) { waveHistory.pop(); lfoHistory.pop(); }

  // ─────────── LFO Circle ───────────
  let lx = 118, ly = 185, lr = 70;
  let lAngle = lfoAngle - HALF_PI;
  let ldx = cos(lAngle) * lr;
  let ldy = sin(lAngle) * lr;

  stroke(255, 80, 180); strokeWeight(2); noFill();
  circle(lx, ly, lr * 2);

  stroke(255, 80, 180, 50); strokeWeight(1);
  line(lx - lr, ly, lx + lr, ly);
  line(lx, ly - lr, lx, ly + lr);

  stroke(255); strokeWeight(2);
  line(lx, ly, lx + ldx, ly + ldy);

  fill(255, 80, 180); noStroke();
  circle(lx + ldx, ly + ldy, 10);

  fill(255, 140, 210); noStroke();
  textSize(13); textAlign(CENTER);
  text("LFO  (pitch bender)", lx, ly - lr - 20);
  fill(255, 80, 180); textSize(11);
  text(nf(lfoVal, 1, 2), lx, ly + lr + 18);

  // ─────────── Pitch Meter (vertical bar) ───────────
  let mx = 275, my = 185, mh = 118, mw = 28;

  let fillH    = map(lfoVal, -1, 1, 0, mh);
  let barColor = lerpColor(color(50, 130, 255), color(255, 100, 50), (lfoVal + 1) / 2);

  stroke(90); strokeWeight(1); noFill();
  rect(mx - mw / 2, my - mh / 2, mw, mh, 4);

  noStroke(); fill(barColor);
  rect(mx - mw / 2 + 2, my + mh / 2 - fillH - 2, mw - 4, max(fillH, 1), 3);

  // Centre-line = base frequency
  stroke(200, 200, 200, 100); strokeWeight(1);
  drawingContext.setLineDash([3, 3]);
  line(mx - mw - 2, my, mx + mw + 2, my);
  drawingContext.setLineDash([]);

  fill(200); noStroke(); textSize(11); textAlign(CENTER);
  text("PITCH", mx, my - mh / 2 - 14);
  fill(255, 100, 50);  textSize(10); text("▲ HIGH", mx, my - mh / 2 + 10);
  fill(50, 130, 255);  textSize(10); text("▼ LOW",  mx, my + mh / 2 - 6);

  // Arrow from LFO circle to meter
  stroke(150); strokeWeight(1.2);
  line(lx + lr + 4, ly, mx - mw / 2 - 6, my);

  // ─────────── LFO mini-wave (lower left panel) ───────────
  let lwY = 352;

  stroke(55); strokeWeight(1);
  line(18, lwY, 390, lwY);

  noFill(); stroke(255, 80, 180, 160); strokeWeight(1.5);
  beginShape();
  for (let i = 0; i < min(lfoHistory.length, 372); i++) {
    vertex(18 + i, lwY - lfoHistory[i] * 50);
  }
  endShape();

  fill(255, 80, 180); noStroke(); textSize(11); textAlign(LEFT);
  text("LFO output  →  bends pitch ↑↓", 20, lwY - 62);

  // ─────────── Output Wave (right) — coloured by pitch bend ───────────
  let wx0 = 415, midY = 215;

  stroke(55); strokeWeight(1);
  line(wx0, midY, width - 15, midY);

  // Each pixel coloured by instantaneous pitch bend (orange = up, blue = down)
  strokeWeight(2.5); noFill();
  for (let i = 0; i < waveHistory.length - 1; i++) {
    let x = wx0 + i;
    if (x >= width - 16) break;
    let lv = (i < lfoHistory.length) ? lfoHistory[i] : 0;
    let c  = lerpColor(color(50, 130, 255), color(255, 100, 50), (lv + 1) / 2);
    stroke(c);
    line(x, midY + waveHistory[i], x + 1, midY + waveHistory[i + 1]);
  }

  // Live dot at the front of the wave
  fill(0, 255, 130); noStroke();
  circle(wx0, midY + waveY, 11);

  // Legend
  fill(255, 100, 50); noStroke(); textSize(12); textAlign(LEFT);
  text("■  pitch UP  — compressed cycles  (higher pitch)", wx0 + 5, midY - 112);
  fill(50, 130, 255);
  text("■  pitch DOWN — stretched cycles  (lower pitch)",  wx0 + 5, midY - 97);

  fill(200); textSize(13); textAlign(CENTER);
  text("Vibrato Output", wx0 + 220, midY - 124);

  // ─────────── Title ───────────
  fill(255); noStroke(); textSize(17); textAlign(CENTER);
  text("Vibrato  ·  LFO Frequency Modulation", width / 2, 22);
  fill(160); textSize(11);
  text("A slow LFO wobbles pitch up and down — denser cycles = higher pitch · sparser = lower", width / 2, 40);
}
