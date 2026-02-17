// Lightweight animated starfield (GPU-friendly)
// Attach to <canvas id="bg-stars" class="bg-canvas"></canvas>
(function() {
  const canvas = document.getElementById("bg-stars");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let w, h, stars;
  const STAR_COUNT = 180;
  const DRIFT_SPEED = 0.06;
  let DPR = window.devicePixelRatio || 1;

  function resize() {
    DPR = window.devicePixelRatio || 1;
    w = canvas.width = window.innerWidth * DPR;
    h = canvas.height = window.innerHeight * DPR;
    canvas.style.width = window.innerWidth + "px";
    canvas.style.height = window.innerHeight + "px";
    stars = Array.from({ length: STAR_COUNT }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      z: Math.random() * 0.9 + 0.1,
      r: Math.random() * 1.6 + 0.4
    }));
  }

  function tick() {
    ctx.clearRect(0,0,w,h);
    for (const s of stars) {
      s.y += DRIFT_SPEED * s.z * DPR;
      if (s.y > h) s.y = 0;
      const grad = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, s.r * 4);
      grad.addColorStop(0, "rgba(33,212,253,0.95)");
      grad.addColorStop(1, "rgba(183,33,255,0.0)");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI*2);
      ctx.fill();
    }
    requestAnimationFrame(tick);
  }

  window.addEventListener("resize", resize);
  resize();
  requestAnimationFrame(tick);
})();
