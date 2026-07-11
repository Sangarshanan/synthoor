// Ring Modulation Visualizer
// output(t) = carrier(t) × modulator(t)
//           = sin(ω_c·t) × sin(ω_m·t)
//           = 0.5 × [cos((ω_c − ω_m)·t) − cos((ω_c + ω_m)·t)]
//
// The carrier frequency DISAPPEARS. Only sidebands at fc ± fm survive.

let t = 0;
let waveHistory = [];

// Visual animation speeds (not real Hz — scaled for readability)
let carrierSpeed = 1.6;   // fast carrier
let modSpeed     = 0.55;  // slower modulator

function setup() {
  createCanvas(900, 420);
}

function draw() {
  background(20);
  t += 0.022;

  let cAngle = TWO_PI * carrierSpeed * t;
  let mAngle = TWO_PI * modSpeed     * t;

  let carrierVal = sin(cAngle);
  let modVal     = sin(mAngle);
  let ringVal    = carrierVal * modVal;
  let ringY      = ringVal * 90;

  waveHistory.unshift(ringY);
  if (waveHistory.length > 460) waveHistory.pop();

  // ─────────── Carrier Circle ───────────
  let c1x = 110, c1y = 215, r1 = 80;
  let cdx = cos(cAngle - HALF_PI) * r1;
  let cdy = sin(cAngle - HALF_PI) * r1;

  stroke(100, 150, 255); strokeWeight(2); noFill();
  circle(c1x, c1y, r1 * 2);

  stroke(100, 150, 255, 50); strokeWeight(1);
  line(c1x - r1, c1y, c1x + r1, c1y);
  line(c1x, c1y - r1, c1x, c1y + r1);

  stroke(255); strokeWeight(2);
  line(c1x, c1y, c1x + cdx, c1y + cdy);

  // Y-projection — the instantaneous amplitude
  stroke(100, 150, 255, 190); strokeWeight(3);
  line(c1x + cdx, c1y, c1x + cdx, c1y + cdy);

  fill(100, 150, 255); noStroke();
  circle(c1x + cdx, c1y + cdy, 10);

  fill(160, 190, 255); noStroke();
  textSize(13); textAlign(CENTER);
  text("Carrier", c1x, c1y - r1 - 22);
  fill(100, 150, 255); textSize(11);
  text(nf(carrierVal, 1, 2), c1x, c1y + r1 + 18);

  // ─────────── × operator ───────────
  fill(255); noStroke();
  textSize(40); textAlign(CENTER, CENTER);
  text("×", 240, c1y);

  // ─────────── Modulator Circle ───────────
  let c2x = 370, c2y = 215, r2 = 65;
  let mdx = cos(mAngle - HALF_PI) * r2;
  let mdy = sin(mAngle - HALF_PI) * r2;

  stroke(255, 160, 50); strokeWeight(2); noFill();
  circle(c2x, c2y, r2 * 2);

  stroke(255, 160, 50, 50); strokeWeight(1);
  line(c2x - r2, c2y, c2x + r2, c2y);
  line(c2x, c2y - r2, c2x, c2y + r2);

  stroke(255); strokeWeight(2);
  line(c2x, c2y, c2x + mdx, c2y + mdy);

  stroke(255, 160, 50, 190); strokeWeight(3);
  line(c2x + mdx, c2y, c2x + mdx, c2y + mdy);

  fill(255, 160, 50); noStroke();
  circle(c2x + mdx, c2y + mdy, 10);

  fill(255, 200, 120); noStroke();
  textSize(13); textAlign(CENTER);
  text("Modulator", c2x, c2y - r2 - 22);
  fill(255, 160, 50); textSize(11);
  text(nf(modVal, 1, 2), c2x, c2y + r2 + 18);

  // ─────────── = operator ───────────
  fill(255); noStroke();
  textSize(28); textAlign(CENTER, CENTER);
  text("=", 465, c1y);

  // ─────────── Ring Mod Output Wave ───────────
  let wx0 = 490;

  stroke(55); strokeWeight(1);
  line(wx0, c1y, width - 15, c1y);

  noFill();
  stroke(0, 255, 130); strokeWeight(2.5);
  beginShape();
  for (let i = 0; i < waveHistory.length; i++) {
    let x = wx0 + i;
    if (x >= width - 15) break;
    vertex(x, c1y + waveHistory[i]);
  }
  endShape();

  // Current-sample dot
  fill(0, 255, 130); noStroke();
  circle(wx0, c1y + ringY, 11);

  // Dashed projection from modulator dot to wave start
  stroke(255, 255, 255, 55); strokeWeight(1);
  drawingContext.setLineDash([4, 6]);
  line(c2x + mdx, c2y + mdy, wx0, c1y + ringY);
  drawingContext.setLineDash([]);

  fill(0, 255, 130); noStroke();
  textSize(13); textAlign(CENTER);
  text("Ring Mod Output", wx0 + 188, c1y - 112);

  // ─────────── Sideband annotation ───────────
  fill(180); noStroke(); textSize(11); textAlign(LEFT);
  text("fc + fm  →", wx0 + 5,  c1y - 98);
  text("fc − fm  →", wx0 + 5,  c1y - 83);
  fill(100, 150, 255); textSize(11);
  text("fc  (carrier)  — GONE", wx0 + 90, c1y - 68);
  stroke(100, 150, 255, 100); strokeWeight(1);
  drawingContext.setLineDash([2, 4]);
  line(wx0 + 85, c1y - 73, wx0 + 85, c1y + 90);
  drawingContext.setLineDash([]);

  // ─────────── Title & live readout ───────────
  fill(255); noStroke(); textSize(17); textAlign(CENTER);
  text("Ring Modulation  ·  output = carrier × modulator", width / 2, 22);
  fill(160); textSize(11);
  text("The carrier frequency vanishes — only sidebands at  fc − fm  and  fc + fm  survive", width / 2, 40);

  fill(180); textSize(12); textAlign(LEFT);
  text(
    "carrier: " + nf(carrierVal, 1, 2) +
    "   ×   modulator: " + nf(modVal, 1, 2) +
    "   =   " + nf(ringVal, 1, 2),
    20, height - 14
  );
}
