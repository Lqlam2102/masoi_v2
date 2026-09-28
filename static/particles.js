'use strict';
// ══════════════════════════════════════════
//  PARTICLES — Hiệu ứng hạt thuần canvas.
//  Không thư viện, không asset, chạy offline.
// ══════════════════════════════════════════

const Particles = (() => {
  // ── Canvas setup ──────────────────────────
  const canvas = document.createElement('canvas');
  canvas.id = 'particle-canvas';
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');

  let W = 0, H = 0;
  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize, { passive: true });
  resize();

  // ── Particle pool ─────────────────────────
  const pool = [];   // active particles
  let raf = null;

  function loop() {
    ctx.clearRect(0, 0, W, H);
    const now = performance.now();
    for (let i = pool.length - 1; i >= 0; i--) {
      const p = pool[i];
      const age = (now - p.born) / p.life;  // 0→1
      if (age >= 1) { pool.splice(i, 1); continue; }
      p.update(age);
      p.draw(ctx, age);
    }
    if (pool.length > 0) {
      raf = requestAnimationFrame(loop);
    } else {
      raf = null;
      ctx.clearRect(0, 0, W, H);
    }
  }

  function kick() {
    if (!raf) raf = requestAnimationFrame(loop);
  }

  function spawn(p) {
    p.born = performance.now();
    pool.push(p);
    kick();
  }

  function spawnMany(arr) { arr.forEach(spawn); }

  // ── Easings ──────────────────────────────
  const easeOut  = t => 1 - (1 - t) ** 3;
  const easeIn   = t => t * t * t;
  const easeInOut= t => t < .5 ? 4*t*t*t : 1 - (-2*t+2)**3/2;

  // ── Helper: screen-center burst origin ───
  function center() { return { x: W / 2, y: H * .38 }; }
  function rand(a, b) { return a + Math.random() * (b - a); }
  function randInt(a, b) { return Math.floor(rand(a, b + 1)); }
  function randColor(colors) { return colors[Math.floor(Math.random() * colors.length)]; }

  // ══════════════════════════════════════════
  //  CONFETTI — chiến thắng dân làng / cặp đôi
  // ══════════════════════════════════════════
  function confetti(opts = {}) {
    const count  = opts.count  || 120;
    const colors = opts.colors || ['#a855f7','#22c55e','#f59e0b','#e9d5ff','#86efac','#fde68a','#f472b6','#60a5fa'];
    const cx     = opts.x != null ? opts.x : W / 2;
    const cy     = opts.y != null ? opts.y : -20;

    for (let i = 0; i < count; i++) {
      const angle  = rand(-Math.PI * .9, Math.PI * .9);  // fan downward
      const speed  = rand(4, 13);
      const color  = randColor(colors);
      const shape  = Math.random() < .6 ? 'rect' : 'circle';
      const w      = rand(6, 14);
      const h      = shape === 'rect' ? rand(4, 8) : w;
      const rot    = rand(0, Math.PI * 2);
      const rotV   = rand(-6, 6);
      const life   = rand(1800, 3200);
      const gravity= rand(.06, .18);
      let vx = Math.cos(angle) * speed;
      let vy = Math.sin(angle) * speed - rand(2, 6);
      let x = cx + rand(-W * .3, W * .3);
      let y = cy;
      let curRot = rot;

      spawn({
        life,
        update(age) {
          vy += gravity;
          x  += vx; vx *= .993;
          y  += vy;
          curRot += rotV * .04;
        },
        draw(ctx, age) {
          const alpha = age < .15 ? age / .15 : 1 - easeIn(Math.max(0, (age - .7) / .3));
          ctx.save();
          ctx.globalAlpha = alpha * .92;
          ctx.translate(x, y);
          ctx.rotate(curRot);
          ctx.fillStyle = color;
          if (shape === 'circle') {
            ctx.beginPath();
            ctx.arc(0, 0, w / 2, 0, Math.PI * 2);
            ctx.fill();
          } else {
            ctx.fillRect(-w / 2, -h / 2, w, h);
          }
          ctx.restore();
        },
      });
    }
  }

  // ══════════════════════════════════════════
  //  WOLF CONFETTI — chiến thắng phe Sói
  // ══════════════════════════════════════════
  function wolfConfetti() {
    confetti({
      count: 100,
      colors: ['#ef4444','#991b1b','#fca5a5','#7f1d1d','#f97316','#fef2f2'],
      y: -20,
    });
    // Thêm "móng vuốt" bay tứ tung
    for (let i = 0; i < 18; i++) {
      const x = rand(0, W);
      const life = rand(900, 1800);
      const size = rand(18, 36);
      const vy   = rand(1.5, 4);
      const vx   = rand(-2, 2);
      let y = rand(-80, -20);
      spawn({
        life,
        update() { y += vy; x += vx; },
        draw(ctx, age) {
          const alpha = age < .2 ? age / .2 : 1 - easeOut(Math.max(0, (age - .6) / .4));
          ctx.save();
          ctx.globalAlpha = alpha * .75;
          ctx.font = `${size}px serif`;
          ctx.textAlign = 'center';
          ctx.fillText('🐺', x, y);
          ctx.restore();
        },
      });
    }
  }

  // ══════════════════════════════════════════
  //  BLOOD — người chết (nhỏ giọt từ vị trí thẻ)
  // ══════════════════════════════════════════
  function blood(originEl) {
    const rect = originEl
      ? originEl.getBoundingClientRect()
      : { left: W / 2, top: H / 2, width: 60, height: 60 };
    const cx = rect.left + rect.width  / 2;
    const cy = rect.top  + rect.height / 2;
    const count = randInt(14, 22);

    for (let i = 0; i < count; i++) {
      const angle = rand(-Math.PI, 0);  // chỉ bay lên/ngang
      const speed = rand(1.5, 5.5);
      const size  = rand(3, 9);
      const life  = rand(700, 1400);
      let x  = cx + rand(-14, 14);
      let y  = cy;
      let vx = Math.cos(angle) * speed * rand(.6, 1.2);
      let vy = Math.sin(angle) * speed - rand(1, 3);
      const gravity = rand(.08, .18);
      let trail = [];

      spawn({
        life,
        update(age) {
          trail.push({ x, y });
          if (trail.length > 5) trail.shift();
          vy += gravity;
          x  += vx; vx *= .97;
          y  += vy;
        },
        draw(ctx, age) {
          const alpha = age < .1 ? age / .1 : 1 - easeIn(Math.max(0, (age - .55) / .45));
          ctx.save();
          ctx.globalAlpha = alpha * .88;
          // vệt trail
          for (let t = 0; t < trail.length - 1; t++) {
            const a = (t + 1) / trail.length * alpha * .4;
            ctx.globalAlpha = a;
            ctx.beginPath();
            ctx.arc(trail[t].x, trail[t].y, size * .4, 0, Math.PI * 2);
            ctx.fillStyle = '#dc2626';
            ctx.fill();
          }
          ctx.globalAlpha = alpha * .88;
          ctx.beginPath();
          ctx.arc(x, y, size / 2, 0, Math.PI * 2);
          ctx.fillStyle = '#ef4444';
          ctx.fill();
          ctx.restore();
        },
      });
    }

    // Skull emoji rơi ra
    for (let i = 0; i < 3; i++) {
      let x = cx + rand(-20, 20);
      let y = cy;
      const vy0  = rand(-4, -1.5);
      const life = rand(900, 1500);
      const size = rand(20, 32);
      spawn({
        life,
        update() { y += vy0 + (performance.now() - this.born) / 1000 * 2.2; x += rand(-.5, .5); },
        draw(ctx, age) {
          const alpha = age < .12 ? age / .12 : 1 - easeIn(Math.max(0, (age - .5) / .5));
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.font = `${size}px serif`;
          ctx.textAlign = 'center';
          ctx.fillText('💀', x, y);
          ctx.restore();
        },
      });
    }
  }

  // ══════════════════════════════════════════
  //  STARS — Tiên Tri nhận kết quả
  // ══════════════════════════════════════════
  function stars(originEl, isWolf) {
    const rect = originEl
      ? originEl.getBoundingClientRect()
      : { left: W / 2 - 40, top: H * .35, width: 80, height: 40 };
    const cx = rect.left + rect.width  / 2;
    const cy = rect.top  + rect.height / 2;
    const color = isWolf ? ['#ef4444','#fca5a5','#f97316'] : ['#a855f7','#e9d5ff','#c4b5fd','#818cf8'];
    const count = 28;

    for (let i = 0; i < count; i++) {
      const angle = rand(0, Math.PI * 2);
      const speed = rand(1.2, 5);
      const size  = rand(10, 24);
      const life  = rand(900, 1800);
      let x  = cx + rand(-10, 10);
      let y  = cy;
      const vx = Math.cos(angle) * speed;
      let vy   = Math.sin(angle) * speed;
      const emoji = isWolf ? (Math.random() < .5 ? '🐺' : '❗') : (Math.random() < .6 ? '✨' : '🔮');

      spawn({
        life,
        update() { vy += .04; x += vx; y += vy; },
        draw(ctx, age) {
          const alpha = age < .12 ? age / .12 : 1 - easeOut(Math.max(0, (age - .5) / .5));
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.font = `${size}px serif`;
          ctx.textAlign = 'center';
          ctx.fillText(emoji, x, y);
          ctx.restore();
        },
      });
    }

    // Glow ring toả ra từ tâm
    const ringLife = 900;
    spawn({
      life: ringLife,
      draw(ctx, age) {
        const r = easeOut(age) * 90;
        const alpha = (1 - age) * .55;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.strokeStyle = isWolf ? '#ef4444' : '#a855f7';
        ctx.lineWidth = 3 - age * 2;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      },
    });
  }

  // ══════════════════════════════════════════
  //  HEARTS — Cupid ghép đôi
  // ══════════════════════════════════════════
  function hearts(originEl) {
    const rect = originEl
      ? originEl.getBoundingClientRect()
      : { left: W / 2 - 30, top: H * .4, width: 60, height: 50 };
    const cx = rect.left + rect.width  / 2;
    const cy = rect.top  + rect.height / 2;

    for (let i = 0; i < 22; i++) {
      const size  = rand(16, 34);
      const life  = rand(1200, 2400);
      let x   = cx + rand(-40, 40);
      let y   = cy + rand(-10, 10);
      let vx  = rand(-2, 2);
      let vy  = rand(-4, -1.5);
      const swayFreq = rand(1.5, 3.5);
      const swayAmp  = rand(8, 20);
      const startX   = x;

      spawn({
        life,
        update(age) {
          vy += .01;
          y  += vy;
          x   = startX + Math.sin(age * Math.PI * 2 * swayFreq) * swayAmp;
        },
        draw(ctx, age) {
          const alpha = age < .12 ? age / .12 : 1 - easeIn(Math.max(0, (age - .55) / .45));
          const sc    = 1 + Math.sin(age * Math.PI * 4) * .1;
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.font = `${size * sc}px serif`;
          ctx.textAlign = 'center';
          ctx.fillText('💗', x, y);
          ctx.restore();
        },
      });
    }

    // Mũi tên Cupid bay qua
    const arrowLife = 1200;
    let ax = -40, ay = cy - 20;
    const avx = (W + 80) / (arrowLife / 16);
    spawn({
      life: arrowLife,
      update() { ax += avx; ay += (cy + 30 - ay) * .04; },
      draw(ctx, age) {
        const alpha = age < .08 ? age / .08 : age > .88 ? 1 - (age - .88) / .12 : 1;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.font = '28px serif';
        ctx.textAlign = 'center';
        ctx.fillText('💘', ax, ay);
        ctx.restore();
      },
    });
  }

  // ══════════════════════════════════════════
  //  LIGHTNING — phiếu treo cổ xác nhận
  // ══════════════════════════════════════════
  function lightning(originEl) {
    const rect = originEl
      ? originEl.getBoundingClientRect()
      : { left: W / 2 - 20, top: H * .45, width: 40, height: 40 };
    const cx = rect.left + rect.width  / 2;
    const cy = rect.top;

    // Tia sét đi thẳng xuống
    function bolt(x0, y0, x1, y1, depth, life, delay) {
      if (depth === 0) return;
      const points = [[x0, y0]];
      const steps = randInt(4, 8);
      for (let i = 1; i < steps; i++) {
        const t = i / steps;
        const mx = x0 + (x1 - x0) * t + rand(-18, 18) / depth;
        const my = y0 + (y1 - y0) * t + rand(-8, 8) / depth;
        points.push([mx, my]);
      }
      points.push([x1, y1]);
      spawn({
        life,
        draw(ctx, age) {
          if (age < delay / life) return;
          const localAge = (age - delay / life) / (1 - delay / life);
          if (localAge > 1) return;
          const alpha = localAge < .15 ? localAge / .15 : 1 - easeIn(Math.max(0, (localAge - .3) / .7));
          ctx.save();
          ctx.globalAlpha = alpha * .9;
          ctx.strokeStyle = '#fef08a';
          ctx.lineWidth = Math.max(.5, (3 - depth * .5) * (1 - localAge * .6));
          ctx.shadowColor = '#facc15';
          ctx.shadowBlur = 8;
          ctx.beginPath();
          points.forEach(([px, py], i) => i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py));
          ctx.stroke();
          ctx.restore();
        },
      });
      // nhánh
      if (depth > 1 && Math.random() < .45) {
        const branchIdx = randInt(1, points.length - 2);
        const [bx, by] = points[branchIdx];
        const endX = bx + rand(-35, 35);
        const endY = by + rand(20, 50);
        bolt(bx, by, endX, endY, depth - 1, life * .7, delay + life * .05);
      }
    }

    // Vài tia
    for (let i = 0; i < 4; i++) {
      const startX = cx + rand(-24, 24);
      bolt(startX, cy - 60, startX + rand(-16, 16), cy + 80, 3, rand(500, 900), i * 80);
    }

    // Flash màn hình
    spawn({
      life: 300,
      draw(ctx, age) {
        const alpha = age < .2 ? age / .2 * .22 : (1 - age) * .22;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = '#fef9c3';
        ctx.fillRect(0, 0, W, H);
        ctx.restore();
      },
    });

    // Emoji ⚡ văng ra
    for (let i = 0; i < 8; i++) {
      const angle = rand(-Math.PI * .7, Math.PI * .7);
      const speed = rand(3, 8);
      let x = cx + rand(-15, 15);
      let y = cy;
      const vx = Math.cos(angle) * speed;
      let vy   = Math.sin(angle) * speed - 2;
      const size = rand(14, 26);
      const life = rand(500, 1100);
      spawn({
        life,
        update() { vy += .12; x += vx; y += vy; },
        draw(ctx, age) {
          const alpha = age < .1 ? age / .1 : 1 - easeIn(Math.max(0, (age - .4) / .6));
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.font = `${size}px serif`;
          ctx.textAlign = 'center';
          ctx.fillText('⚡', x, y);
          ctx.restore();
        },
      });
    }
  }

  // ══════════════════════════════════════════
  //  HEAL — bình cứu Phù Thủy
  // ══════════════════════════════════════════
  function heal(originEl) {
    const rect = originEl
      ? originEl.getBoundingClientRect()
      : { left: W / 2 - 30, top: H * .4, width: 60, height: 60 };
    const cx = rect.left + rect.width / 2;
    const cy = rect.top  + rect.height / 2;

    for (let i = 0; i < 20; i++) {
      const angle = rand(0, Math.PI * 2);
      const speed = rand(.8, 3.5);
      const emoji = ['✨','💚','🌿','💊'][Math.floor(Math.random() * 4)];
      const size  = rand(14, 26);
      const life  = rand(900, 1600);
      let x = cx, y = cy;
      const vx = Math.cos(angle) * speed;
      let vy   = Math.sin(angle) * speed;
      spawn({
        life,
        update() { vy += .02; x += vx; y += vy; },
        draw(ctx, age) {
          const alpha = age < .1 ? age / .1 : 1 - easeOut(Math.max(0, (age - .5) / .5));
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.font = `${size}px serif`;
          ctx.textAlign = 'center';
          ctx.fillText(emoji, x, y);
          ctx.restore();
        },
      });
    }
    // Vòng sáng xanh
    spawn({
      life: 700,
      draw(ctx, age) {
        const r = easeOut(age) * 70;
        ctx.save();
        ctx.globalAlpha = (1 - age) * .5;
        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      },
    });
  }

  // ══════════════════════════════════════════
  //  POISON — bình độc Phù Thủy
  // ══════════════════════════════════════════
  function poison(originEl) {
    const rect = originEl
      ? originEl.getBoundingClientRect()
      : { left: W / 2 - 30, top: H * .4, width: 60, height: 60 };
    const cx = rect.left + rect.width / 2;
    const cy = rect.top  + rect.height / 2;

    for (let i = 0; i < 18; i++) {
      const emoji = ['☠️','🟣','💜','🫧'][Math.floor(Math.random() * 4)];
      const size  = rand(12, 24);
      const life  = rand(800, 1500);
      let x  = cx + rand(-20, 20);
      let y  = cy + rand(-10, 10);
      const vx = rand(-2.5, 2.5);
      let vy   = rand(-3, -.5);
      spawn({
        life,
        update() { vy += .05; x += vx; y += vy; },
        draw(ctx, age) {
          const alpha = age < .1 ? age / .1 : 1 - easeIn(Math.max(0, (age - .4) / .6));
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.font = `${size}px serif`;
          ctx.textAlign = 'center';
          ctx.fillText(emoji, x, y);
          ctx.restore();
        },
      });
    }
    spawn({
      life: 600,
      draw(ctx, age) {
        const r = easeOut(age) * 65;
        ctx.save();
        ctx.globalAlpha = (1 - age) * .45;
        ctx.strokeStyle = '#a855f7';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      },
    });
  }

  // ══════════════════════════════════════════
  //  SHIELD — Bảo Vệ đỡ đòn thành công
  // ══════════════════════════════════════════
  function shield(originEl) {
    const rect = originEl
      ? originEl.getBoundingClientRect()
      : { left: W / 2 - 30, top: H * .4, width: 60, height: 60 };
    const cx = rect.left + rect.width / 2;
    const cy = rect.top  + rect.height / 2;

    // Vòng khiên bung ra
    for (let ring = 0; ring < 3; ring++) {
      const delay = ring * 140;
      spawn({
        life: 700 + delay,
        draw(ctx, age) {
          const localAge = Math.max(0, age - delay / (700 + delay));
          const r = easeOut(localAge) * (50 + ring * 18);
          const alpha = (1 - localAge) * .6;
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.strokeStyle = '#60a5fa';
          ctx.lineWidth = 2.5 - ring * .5;
          ctx.beginPath();
          ctx.arc(cx, cy, r, 0, Math.PI * 2);
          ctx.stroke();
          ctx.restore();
        },
      });
    }
    for (let i = 0; i < 12; i++) {
      const angle = (i / 12) * Math.PI * 2;
      const speed = rand(2, 5);
      let x = cx, y = cy;
      const vx = Math.cos(angle) * speed;
      const vy = Math.sin(angle) * speed;
      const size = rand(14, 22);
      spawn({
        life: rand(600, 1100),
        update() { x += vx * .96; y += vy * .96; },
        draw(ctx, age) {
          const alpha = age < .15 ? age / .15 : 1 - easeOut(Math.max(0, (age - .4) / .6));
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.font = `${size}px serif`;
          ctx.textAlign = 'center';
          ctx.fillText('🛡️', x, y);
          ctx.restore();
        },
      });
    }
  }

  // ══════════════════════════════════════════
  //  FOOL WIN — Thằng Ngố thắng
  // ══════════════════════════════════════════
  function foolWin() {
    confetti({ count: 80, colors: ['#fde68a','#fcd34d','#f59e0b','#fef3c7','#fbbf24'] });
    for (let i = 0; i < 20; i++) {
      let x = rand(0, W), y = rand(-60, -10);
      const vy = rand(1.5, 4);
      const size = rand(22, 42);
      spawn({
        life: rand(1600, 2800),
        update() { y += vy; x += rand(-.3, .3); },
        draw(ctx, age) {
          const alpha = age < .12 ? age / .12 : 1 - easeIn(Math.max(0, (age - .7) / .3));
          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.font = `${size}px serif`;
          ctx.textAlign = 'center';
          ctx.fillText('🃏', x, y);
          ctx.restore();
        },
      });
    }
  }

  // Public API
  return { confetti, wolfConfetti, blood, stars, hearts, lightning, heal, poison, shield, foolWin };
})();

window.Particles = Particles;
