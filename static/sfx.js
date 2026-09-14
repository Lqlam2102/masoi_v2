'use strict';
// ══════════════════════════════════════════
//  SFX — âm thanh tổng hợp bằng WebAudio.
//  Không dùng file nhạc: chạy offline, không tải asset, không lệ thuộc CDN.
// ══════════════════════════════════════════

const SFX = (() => {
  let ctx = null;
  let master = null;          // gain tổng, dùng để tắt tiếng
  let musicBus = null;        // nhạc nền (ambience) — chỉnh riêng
  let sfxBus = null;          // hiệu ứng rời
  let ambience = null;        // {mode, nodes:[], gain}
  let muted = localStorage.getItem('masoi_muted') === '1';
  let volume = parseFloat(localStorage.getItem('masoi_volume') || '0.7');

  function ensure() {
    if (ctx) return ctx;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
    master = ctx.createGain();
    master.gain.value = muted ? 0 : volume;
    master.connect(ctx.destination);
    musicBus = ctx.createGain(); musicBus.gain.value = 0.45; musicBus.connect(master);
    sfxBus = ctx.createGain();   sfxBus.gain.value = 1.0;    sfxBus.connect(master);
    return ctx;
  }

  /** Trình duyệt chặn audio tới khi có thao tác người dùng. */
  function unlock() {
    const c = ensure();
    if (c && c.state === 'suspended') c.resume();
  }

  function setMuted(on) {
    muted = !!on;
    localStorage.setItem('masoi_muted', muted ? '1' : '0');
    if (master) master.gain.setTargetAtTime(muted ? 0 : volume, ctx.currentTime, 0.05);
    if (muted) stopAmbience();
  }

  function setVolume(v) {
    volume = Math.max(0, Math.min(1, v));
    localStorage.setItem('masoi_volume', String(volume));
    if (master && !muted) master.gain.setTargetAtTime(volume, ctx.currentTime, 0.05);
  }

  // ── Khối dựng âm cơ bản ──

  /** Một nốt: dao động + đường bao ADSR đơn giản, có thể trượt cao độ. */
  function tone(o) {
    const c = ensure(); if (!c || muted) return;
    const t0 = c.currentTime + (o.at || 0);
    const dur = o.dur || 0.3;
    const osc = c.createOscillator();
    const gain = c.createGain();
    osc.type = o.type || 'sine';
    osc.frequency.setValueAtTime(o.freq, t0);
    if (o.slideTo) osc.frequency.exponentialRampToValueAtTime(Math.max(1, o.slideTo), t0 + dur);

    let node = osc;
    if (o.filter) {
      const f = c.createBiquadFilter();
      f.type = o.filter; f.frequency.value = o.cutoff || 1200; f.Q.value = o.q || 1;
      osc.connect(f); node = f;
    }
    const peak = o.gain == null ? 0.25 : o.gain;
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(peak, t0 + (o.attack || 0.01));
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    node.connect(gain);
    gain.connect(o.bus || sfxBus);

    if (o.vibrato) {
      const lfo = c.createOscillator(), lfoGain = c.createGain();
      lfo.frequency.value = o.vibrato.rate || 5;
      lfoGain.gain.value = o.vibrato.depth || 6;
      lfo.connect(lfoGain); lfoGain.connect(osc.frequency);
      lfo.start(t0); lfo.stop(t0 + dur);
    }
    osc.start(t0); osc.stop(t0 + dur + 0.02);
  }

  /** Nhiễu trắng đã lọc — dùng cho gió, tiếng bước chân, tiếng súng. */
  function noise(o = {}) {
    const c = ensure(); if (!c || muted) return;
    const t0 = c.currentTime + (o.at || 0);
    const dur = o.dur || 0.3;
    const buf = c.createBuffer(1, Math.ceil(c.sampleRate * dur), c.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    const src = c.createBufferSource(); src.buffer = buf;
    const f = c.createBiquadFilter();
    f.type = o.filter || 'bandpass';
    f.frequency.setValueAtTime(o.cutoff || 800, t0);
    if (o.cutoffTo) f.frequency.exponentialRampToValueAtTime(Math.max(20, o.cutoffTo), t0 + dur);
    f.Q.value = o.q || 1;
    const gain = c.createGain();
    const peak = o.gain == null ? 0.2 : o.gain;
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(peak, t0 + (o.attack || 0.01));
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    src.connect(f); f.connect(gain); gain.connect(o.bus || sfxBus);
    src.start(t0); src.stop(t0 + dur);
  }

  function chord(freqs, o = {}) {
    freqs.forEach((f, i) => tone({ ...o, freq: f, at: (o.at || 0) + i * (o.spread || 0) }));
  }

  // ── Bảng hiệu ứng ──

  const EFFECTS = {
    // Tiếng sói tru — nền cho pha đêm của bầy Sói.
    howl() {
      tone({ freq: 220, slideTo: 420, dur: 0.5, type: 'sawtooth', gain: 0.16,
             filter: 'lowpass', cutoff: 900, attack: 0.12 });
      tone({ at: 0.45, freq: 430, slideTo: 300, dur: 1.1, type: 'sawtooth', gain: 0.18,
             filter: 'lowpass', cutoff: 1100, attack: 0.06,
             vibrato: { rate: 5.5, depth: 9 } });
      noise({ at: 0.2, dur: 1.2, gain: 0.035, filter: 'bandpass', cutoff: 500, q: 0.7 });
    },
    // Màn đêm buông xuống.
    nightfall() {
      chord([110, 164.81, 220], { type: 'sine', dur: 1.8, gain: 0.12, attack: 0.5, spread: 0.12 });
      tone({ freq: 55, dur: 2.4, type: 'sine', gain: 0.18, attack: 0.6 });
    },
    // Bình minh — chuông làng đánh thức dân làng.
    dawn() {
      tone({ freq: 523.25, dur: 2.4, type: 'sine', gain: 0.2, attack: 0.005 });
      tone({ freq: 784, dur: 1.8, type: 'sine', gain: 0.12, attack: 0.005, at: 0.02 });
      tone({ freq: 261.63, dur: 3.0, type: 'sine', gain: 0.16, attack: 0.01 });
      chord([659.25, 880, 1046.5], { type: 'triangle', dur: 0.9, gain: 0.07,
                                     attack: 0.02, spread: 0.16, at: 0.5 });
    },
    // Có người chết.
    death() {
      tone({ freq: 160, slideTo: 42, dur: 1.4, type: 'sawtooth', gain: 0.2,
             filter: 'lowpass', cutoff: 420, attack: 0.005 });
      noise({ dur: 0.5, gain: 0.12, filter: 'lowpass', cutoff: 900, cutoffTo: 120 });
      tone({ at: 0.25, freq: 98, dur: 1.8, type: 'sine', gain: 0.14, attack: 0.05 });
    },
    // Đêm bình yên, không ai chết.
    peace() {
      chord([523.25, 659.25, 783.99], { type: 'sine', dur: 1.2, gain: 0.09,
                                        attack: 0.06, spread: 0.1 });
    },
    // Tiên Tri nhận lời phán.
    reveal() {
      chord([880, 1174.66, 1396.91], { type: 'triangle', dur: 0.7, gain: 0.08,
                                       attack: 0.01, spread: 0.07 });
      tone({ at: 0.18, freq: 1760, dur: 0.5, type: 'sine', gain: 0.05, attack: 0.01 });
    },
    heal() {
      tone({ freq: 392, slideTo: 784, dur: 0.6, type: 'sine', gain: 0.16, attack: 0.03 });
      tone({ at: 0.12, freq: 587.33, dur: 0.6, type: 'triangle', gain: 0.08, attack: 0.03 });
    },
    poison() {
      tone({ freq: 330, slideTo: 90, dur: 0.9, type: 'square', gain: 0.1,
             filter: 'lowpass', cutoff: 700, attack: 0.02 });
      noise({ at: 0.1, dur: 0.7, gain: 0.06, filter: 'bandpass', cutoff: 1600, cutoffTo: 200 });
    },
    shot() {
      noise({ dur: 0.35, gain: 0.3, filter: 'lowpass', cutoff: 4000, cutoffTo: 200, attack: 0.001 });
      tone({ freq: 120, slideTo: 35, dur: 0.4, type: 'square', gain: 0.16, attack: 0.001 });
    },
    // Gõ búa phiên toà — mở pha bỏ phiếu.
    gavel() {
      noise({ dur: 0.12, gain: 0.22, filter: 'lowpass', cutoff: 2200, cutoffTo: 300, attack: 0.001 });
      tone({ freq: 180, slideTo: 70, dur: 0.22, type: 'square', gain: 0.12, attack: 0.001 });
    },
    select()  { tone({ freq: 660, dur: 0.09, type: 'triangle', gain: 0.1, attack: 0.004 }); },
    confirm() {
      tone({ freq: 523.25, dur: 0.12, type: 'triangle', gain: 0.12, attack: 0.005 });
      tone({ at: 0.1, freq: 783.99, dur: 0.18, type: 'triangle', gain: 0.12, attack: 0.005 });
    },
    tick()  { tone({ freq: 1000, dur: 0.05, type: 'square', gain: 0.06, attack: 0.002 }); },
    alarm() { tone({ freq: 1320, dur: 0.09, type: 'square', gain: 0.1, attack: 0.002 }); },
    error() { tone({ freq: 200, slideTo: 130, dur: 0.25, type: 'sawtooth', gain: 0.12,
                     filter: 'lowpass', cutoff: 800, attack: 0.005 }); },
    winVillage() {
      [523.25, 659.25, 783.99, 1046.5].forEach((f, i) =>
        tone({ at: i * 0.16, freq: f, dur: 0.9, type: 'triangle', gain: 0.14, attack: 0.01 }));
      chord([523.25, 659.25, 783.99, 1046.5],
            { at: 0.72, type: 'sine', dur: 2.2, gain: 0.1, attack: 0.04 });
    },
    winWolf() {
      [440, 523.25, 622.25, 830.61].forEach((f, i) =>
        tone({ at: i * 0.18, freq: f, dur: 1.0, type: 'sawtooth', gain: 0.1,
               filter: 'lowpass', cutoff: 1400, attack: 0.02 }));
      tone({ at: 0.8, freq: 55, dur: 2.6, type: 'sine', gain: 0.2, attack: 0.05 });
      EFFECTS.howl();
    },
  };

  function play(name) {
    unlock();
    const fn = EFFECTS[name];
    if (fn) { try { fn(); } catch {} }
  }

  // ── Nhạc nền theo pha ──

  function stopAmbience() {
    if (!ambience) return;
    const { nodes, gain } = ambience;
    try {
      gain.gain.setTargetAtTime(0.0001, ctx.currentTime, 0.4);
      const stopAt = ctx.currentTime + 1.6;
      nodes.forEach(n => { try { n.stop(stopAt); } catch {} });
    } catch {}
    ambience = null;
  }

  /** mode: 'night' | 'day' | null. Gọi lại cùng mode thì không làm gì. */
  function setAmbience(mode) {
    if (ambience && ambience.mode === mode) return;
    stopAmbience();
    if (!mode || muted) return;
    const c = ensure(); if (!c) return;
    unlock();

    const gain = c.createGain();
    gain.gain.setValueAtTime(0.0001, c.currentTime);
    gain.connect(musicBus);
    const nodes = [];

    const drone = (freq, type, level, detune = 0) => {
      const osc = c.createOscillator();
      osc.type = type; osc.frequency.value = freq; osc.detune.value = detune;
      const g = c.createGain(); g.gain.value = level;
      osc.connect(g); g.connect(gain); osc.start();
      nodes.push(osc);
      return osc;
    };

    if (mode === 'night') {
      // Nền trầm, tối, hơi rung — không giai điệu để khỏi át giọng nói.
      drone(55, 'sine', 0.5);
      drone(82.41, 'sine', 0.22, -6);
      drone(110, 'triangle', 0.08, 5);
      const lfo = c.createOscillator(), lfoGain = c.createGain();
      lfo.frequency.value = 0.08; lfoGain.gain.value = 0.35;
      lfo.connect(lfoGain); lfoGain.connect(gain.gain);
      lfo.start(); nodes.push(lfo);
      gain.gain.setTargetAtTime(0.5, c.currentTime, 2.0);
    } else {
      // Ban ngày: quãng năm sáng, nhẹ.
      drone(196, 'sine', 0.16);
      drone(293.66, 'sine', 0.1, 4);
      drone(98, 'sine', 0.3);
      gain.gain.setTargetAtTime(0.32, c.currentTime, 2.0);
    }

    ambience = { mode, nodes, gain };
  }

  return {
    unlock, play, setAmbience, stopAmbience, setMuted, setVolume,
    get muted() { return muted; },
    get volume() { return volume; },
  };
})();

window.SFX = SFX;
