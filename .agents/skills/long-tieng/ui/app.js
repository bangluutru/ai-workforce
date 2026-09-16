/**
 * app.js — Client logic điều phối toàn diện Lồng Tiếng Studio (AIWF).
 * Quản trị đồng bộ Video Player, Dual-Track Audio Sync (giọng lồng tiếng phát đè lên giọng gốc thời gian thực),
 * Live Subtitle Overlay, Timeline Scrubber, Bộ chọn Voice Nam/Nữ, Instant Voice Preview, Chia câu và Re-render.
 */

import { SubtitleOverlay } from "./lib/subtitle_overlay.js";

class DubbingStudioApp {
  constructor() {
    this.project = null;
    this.voices = [];
    this.video = document.getElementById("videoPlayer");
    this.activeSegment = null;
    this.currentAudioPreview = null;
    this.sampleAudio = null;
    this.saveTimeout = null;
    this.renderPollingInterval = null;
    this.overlay = null;
    this.isShowingDubbed = false;

    // Dual-Track Realtime Audio Sync Engine
    this.liveDubAudio = new Audio("/audio/speech");
    this.liveDubAudio.preload = "auto";
    this.isLiveDubEnabled = true;

    this.init();
  }

  async init() {
    try {
      await Promise.all([this.loadProject(), this.loadVoices()]);
      this.initOverlay();
      this.initLiveDubbingSync();
      this.bindPlayerEvents();
      this.bindTimelineEvents();
      this.bindTabs();
      this.bindVoiceAudioControls();
      this.bindStyleControls();
      this.bindToolbarActions();
      this.bindRenderModal();
      this.bindSplitButton();
      this.bindVideoSwitcher();
      this.bindLiveDubToggle();
      this.renderAll();
    } catch (err) {
      console.error("Lỗi khởi tạo Lồng Tiếng Studio:", err);
      alert("Không thể tải thông tin dự án lồng tiếng: " + err.message);
    }
  }

  /* ----------------------------------------------------
     LOAD DATA & OVERLAY INITIALIZATION
  ---------------------------------------------------- */
  async loadProject() {
    const res = await fetch("/api/project");
    if (!res.ok) throw new Error("Lỗi nạp dự án từ server");
    this.project = await res.json();
    if (!this.project.style) {
      this.project.style = {
        mode: "monolingual",
        font_family: "Be Vietnam Pro",
        font_size: 24,
        primary_color: "#ffffff",
        secondary_color: "#ffd700",
        outline_color: "#000000",
        outline_width: 2.2,
        background_color: "#000000",
        background_opacity: 35,
        alignment: 2,
        margin_v: 45
      };
    }
  }

  async loadVoices() {
    try {
      const res = await fetch("/api/voices");
      if (res.ok) {
        const data = await res.json();
        this.voices = data.voices || [];
      }
    } catch (e) {
      console.warn("Không tải được danh mục giọng từ server, dùng danh mục fallback", e);
    }
  }

  initOverlay() {
    const overlayEl = document.getElementById("subtitleOverlay");
    const containerEl = document.getElementById("videoContainer");
    if (overlayEl && containerEl && this.video) {
      this.overlay = new SubtitleOverlay(this.video, overlayEl, containerEl);
      this.overlay.setStyle(this.project.style);
    }
  }

  initLiveDubbingSync() {
    this.syncAudioVolumes();
    this.liveDubAudio.load();
  }

  syncAudioVolumes() {
    if (this.isShowingDubbed) {
      // Khi xem video đã lồng tiếng, video đã có sẵn track âm thanh hòa âm
      this.video.volume = 1.0;
      this.liveDubAudio.volume = 0;
      return;
    }

    const s = this.project?.audio_settings || {};
    const bgVol = s.bg_volume !== undefined ? s.bg_volume : 0.05;
    const voiceVol = s.voice_volume !== undefined ? s.voice_volume : 1.4;

    if (this.isLiveDubEnabled) {
      // Khi bật lồng tiếng đè lên gốc:
      // Video gốc hạ âm lượng xuống mức bg_volume (Ducking)
      this.video.volume = Math.max(0, Math.min(1.0, bgVol));
      // Giọng lồng tiếng phát rõ nét
      this.liveDubAudio.volume = Math.max(0, Math.min(1.0, voiceVol / 1.4));
    } else {
      // Khi tắt lồng tiếng: Video gốc phát âm lượng đầy đủ
      this.video.volume = 1.0;
      this.liveDubAudio.volume = 0;
    }
  }

  renderAll() {
    this.updateHeaderMeta();
    this.populateAudioControls();
    this.populateStyleControls();
    this.renderTimelineCues();
    this.renderSegmentsList();
    this.syncAudioVolumes();
  }

  updateHeaderMeta() {
    const v = this.project.video || {};
    const metaEl = document.getElementById("projectMeta");
    const durStr = this.formatTime(v.duration || 0);
    metaEl.textContent = `${v.filename || "Video"} (${durStr} • ${v.width || 1920}x${v.height || 1080})`;
  }

  formatTime(sec) {
    if (isNaN(sec) || sec === null) return "00:00.0";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 10);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}.${ms}`;
  }

  /* ----------------------------------------------------
     AUDIO & VOICE CONTROLS (WITH INSTANT PREVIEW)
  ---------------------------------------------------- */
  populateAudioControls() {
    const s = this.project.audio_settings || {};
    const curLang = s.lang || "vi";
    const curGender = s.gender || "female";
    const curVoice = s.voice || "vi-VN-HoaiMyNeural";
    const curSpeed = s.speed || 1.0;
    const curBgVol = Math.round((s.bg_volume !== undefined ? s.bg_volume : 0.05) * 100);
    const curVoiceVol = Math.round((s.voice_volume !== undefined ? s.voice_volume : 1.4) * 100);
    const curDucking = Math.round((s.ducking_ratio !== undefined ? s.ducking_ratio : 0.15) * 100);
    const curSubtitles = s.include_subtitles !== undefined ? s.include_subtitles : true;

    // 1. Language segmented buttons
    document.querySelectorAll("#langSelector .btn-seg").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.lang === curLang);
    });

    // 2. Gender segmented buttons
    document.querySelectorAll("#genderSelector .btn-seg").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.gender === curGender);
    });

    // 3. Populate Voice Picker
    this.updateVoicePicker(curLang, curGender, curVoice);

    // 4. Sliders
    const sliderSpeed = document.getElementById("sliderSpeed");
    const valSpeed = document.getElementById("valSpeed");
    if (sliderSpeed && valSpeed) {
      sliderSpeed.value = curSpeed;
      valSpeed.textContent = `${parseFloat(curSpeed).toFixed(2)}x`;
    }

    const sliderBgVol = document.getElementById("sliderBgVol");
    const valBgVol = document.getElementById("valBgVol");
    if (sliderBgVol && valBgVol) {
      sliderBgVol.value = curBgVol;
      valBgVol.textContent = `${curBgVol}%`;
    }

    const sliderVoiceVol = document.getElementById("sliderVoiceVol");
    const valVoiceVol = document.getElementById("valVoiceVol");
    if (sliderVoiceVol && valVoiceVol) {
      sliderVoiceVol.value = curVoiceVol;
      valVoiceVol.textContent = `${curVoiceVol}%`;
    }

    const sliderDucking = document.getElementById("sliderDucking");
    const valDucking = document.getElementById("valDucking");
    if (sliderDucking && valDucking) {
      sliderDucking.value = curDucking;
      valDucking.textContent = `${curDucking}%`;
    }

    const chkSubtitles = document.getElementById("chkSubtitles");
    if (chkSubtitles) chkSubtitles.checked = curSubtitles;
  }

  updateVoicePicker(lang, gender, selectedVoiceId = null) {
    const picker = document.getElementById("voicePicker");
    if (!picker) return;
    picker.innerHTML = "";

    let matched = this.voices.filter(v => v.lang === lang && v.gender === gender);
    if (matched.length === 0) {
      matched = this.voices.filter(v => v.lang === lang);
    }
    if (matched.length === 0) {
      matched = this.voices;
    }

    matched.forEach(v => {
      const opt = document.createElement("option");
      opt.value = v.id;
      opt.textContent = `${v.name} — ${v.description}`;
      picker.appendChild(opt);
    });

    if (selectedVoiceId && matched.some(v => v.id === selectedVoiceId)) {
      picker.value = selectedVoiceId;
    } else if (matched.length > 0) {
      picker.value = matched[0].id;
    }

    this.updateVoiceDescription();
  }

  updateVoiceDescription() {
    const picker = document.getElementById("voicePicker");
    const descEl = document.getElementById("voiceDesc");
    if (!picker || !descEl) return;
    const selectedVoice = this.voices.find(v => v.id === picker.value);
    if (selectedVoice) {
      descEl.textContent = `🎯 ${selectedVoice.description}`;
    }
  }

  bindVoiceAudioControls() {
    // Language clicks
    document.querySelectorAll("#langSelector .btn-seg").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#langSelector .btn-seg").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const lang = btn.dataset.lang;
        this.project.audio_settings.lang = lang;

        const currentGender = document.querySelector("#genderSelector .btn-seg.active")?.dataset.gender || "female";
        this.updateVoicePicker(lang, currentGender);
        const newVoice = document.getElementById("voicePicker").value;
        this.project.audio_settings.voice = newVoice;
        this.playVoiceSample(newVoice);
        this.scheduleAutoSave();
      });
    });

    // Gender clicks
    document.querySelectorAll("#genderSelector .btn-seg").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#genderSelector .btn-seg").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const gender = btn.dataset.gender;
        this.project.audio_settings.gender = gender;

        const currentLang = document.querySelector("#langSelector .btn-seg.active")?.dataset.lang || "vi";
        this.updateVoicePicker(currentLang, gender);
        const newVoice = document.getElementById("voicePicker").value;
        this.project.audio_settings.voice = newVoice;
        this.playVoiceSample(newVoice);
        this.scheduleAutoSave();
      });
    });

    // Voice Picker change
    const voicePicker = document.getElementById("voicePicker");
    if (voicePicker) {
      voicePicker.addEventListener("change", (e) => {
        const voiceId = e.target.value;
        this.project.audio_settings.voice = voiceId;
        this.updateVoiceDescription();
        this.playVoiceSample(voiceId);
        this.scheduleAutoSave();
      });
    }

    // Play voice sample button
    const btnPlayVoiceSample = document.getElementById("btnPlayVoiceSample");
    if (btnPlayVoiceSample && voicePicker) {
      btnPlayVoiceSample.addEventListener("click", () => {
        const voiceId = voicePicker.value;
        this.playVoiceSample(voiceId);
      });
    }

    // Speed slider
    const sliderSpeed = document.getElementById("sliderSpeed");
    const valSpeed = document.getElementById("valSpeed");
    if (sliderSpeed && valSpeed) {
      sliderSpeed.addEventListener("input", () => {
        const val = parseFloat(sliderSpeed.value);
        valSpeed.textContent = `${val.toFixed(2)}x`;
        this.project.audio_settings.speed = val;
        this.scheduleAutoSave();
      });
    }

    // Background volume slider (Thay đổi âm lượng video gốc tức thì trên loa)
    const sliderBgVol = document.getElementById("sliderBgVol");
    const valBgVol = document.getElementById("valBgVol");
    if (sliderBgVol && valBgVol) {
      sliderBgVol.addEventListener("input", () => {
        const val = parseInt(sliderBgVol.value, 10);
        valBgVol.textContent = `${val}%`;
        this.project.audio_settings.bg_volume = val / 100.0;
        this.syncAudioVolumes();
        this.scheduleAutoSave();
      });
    }

    // Voice volume slider (Thay đổi âm lượng giọng lồng tiếng tức thì trên loa)
    const sliderVoiceVol = document.getElementById("sliderVoiceVol");
    const valVoiceVol = document.getElementById("valVoiceVol");
    if (sliderVoiceVol && valVoiceVol) {
      sliderVoiceVol.addEventListener("input", () => {
        const val = parseInt(sliderVoiceVol.value, 10);
        valVoiceVol.textContent = `${val}%`;
        this.project.audio_settings.voice_volume = val / 100.0;
        this.syncAudioVolumes();
        this.scheduleAutoSave();
      });
    }

    // Ducking slider
    const sliderDucking = document.getElementById("sliderDucking");
    const valDucking = document.getElementById("valDucking");
    if (sliderDucking && valDucking) {
      sliderDucking.addEventListener("input", () => {
        const val = parseInt(sliderDucking.value, 10);
        valDucking.textContent = `${val}%`;
        this.project.audio_settings.ducking_ratio = val / 100.0;
        this.scheduleAutoSave();
      });
    }

    // Hardsub checkbox
    const chkSubtitles = document.getElementById("chkSubtitles");
    if (chkSubtitles) {
      chkSubtitles.addEventListener("change", () => {
        this.project.audio_settings.include_subtitles = chkSubtitles.checked;
        this.scheduleAutoSave();
      });
    }
  }

  async playVoiceSample(voiceId) {
    if (!voiceId) return;
    const btn = document.getElementById("btnPlayVoiceSample");
    const originalHtml = btn ? btn.innerHTML : "";

    if (btn) {
      btn.innerHTML = "<span>⏳ Đang tải...</span>";
      btn.disabled = true;
    }

    if (this.sampleAudio) {
      this.sampleAudio.pause();
      this.sampleAudio = null;
    }

    try {
      if (btn) {
        btn.innerHTML = "<span>🔊 Đang đọc...</span>";
      }

      this.sampleAudio = new Audio(`/api/voice-sample?voice=${encodeURIComponent(voiceId)}&t=${Date.now()}`);

      this.sampleAudio.onended = () => {
        if (btn) {
          btn.innerHTML = originalHtml;
          btn.disabled = false;
        }
      };

      this.sampleAudio.onerror = () => {
        if (btn) {
          btn.innerHTML = originalHtml;
          btn.disabled = false;
        }
      };

      await this.sampleAudio.play();
    } catch (e) {
      console.warn("Lỗi phát giọng mẫu:", e);
      if (btn) {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
      }
    }
  }

  /* ----------------------------------------------------
     SUBTITLE STYLES (TRỰC QUAN NHƯ PHU-DE)
  ---------------------------------------------------- */
  populateStyleControls() {
    const s = this.project.style || {};
    const mode = s.mode || "monolingual";
    const bilingualOrder = s.bilingual_order || "target_top";
    const fontFamily = s.font_family || "Be Vietnam Pro";
    const fontSize = s.font_size || 24;
    const primaryColor = s.primary_color || "#ffffff";
    const secondaryColor = s.secondary_color || "#ffd700";
    const outlineColor = s.outline_color || "#000000";
    const bgOpacity = s.background_opacity !== undefined ? s.background_opacity : 35;
    const marginV = s.margin_v || 45;

    const selMode = document.getElementById("styleMode");
    if (selMode) selMode.value = mode;

    const orderGroup = document.getElementById("bilingualOrderGroup");
    if (orderGroup) orderGroup.style.display = mode === "bilingual" ? "block" : "none";

    const selOrder = document.getElementById("styleBilingualOrder");
    if (selOrder) selOrder.value = bilingualOrder;

    const selFont = document.getElementById("styleFontFamily");
    if (selFont) selFont.value = fontFamily;

    const sliderSize = document.getElementById("styleFontSize");
    const valSize = document.getElementById("valFontSize");
    if (sliderSize && valSize) {
      sliderSize.value = fontSize;
      valSize.textContent = `${fontSize}px`;
    }

    const colPrimary = document.getElementById("stylePrimaryColor");
    if (colPrimary) colPrimary.value = primaryColor;

    const colSecondary = document.getElementById("styleSecondaryColor");
    if (colSecondary) colSecondary.value = secondaryColor;

    const colOutline = document.getElementById("styleOutlineColor");
    if (colOutline) colOutline.value = outlineColor;

    const sliderBgOp = document.getElementById("styleBgOpacity");
    const valBgOp = document.getElementById("valBgOpacity");
    if (sliderBgOp && valBgOp) {
      sliderBgOp.value = bgOpacity;
      valBgOp.textContent = `${bgOpacity}%`;
    }

    const sliderMarginV = document.getElementById("styleMarginV");
    const valMarginV = document.getElementById("valMarginV");
    if (sliderMarginV && valMarginV) {
      sliderMarginV.value = marginV;
      valMarginV.textContent = `${marginV}px`;
    }
  }

  bindStyleControls() {
    const updateStyle = (key, value) => {
      this.project.style[key] = value;
      if (this.overlay) {
        this.overlay.setStyle(this.project.style);
      }
      this.scheduleAutoSave();
    };

    const selMode = document.getElementById("styleMode");
    const orderGroup = document.getElementById("bilingualOrderGroup");
    if (selMode) {
      selMode.addEventListener("change", (e) => {
        const val = e.target.value;
        if (orderGroup) orderGroup.style.display = val === "bilingual" ? "block" : "none";
        updateStyle("mode", val);
      });
    }

    const selOrder = document.getElementById("styleBilingualOrder");
    if (selOrder) {
      selOrder.addEventListener("change", (e) => updateStyle("bilingual_order", e.target.value));
    }

    const selFont = document.getElementById("styleFontFamily");
    if (selFont) {
      selFont.addEventListener("change", (e) => updateStyle("font_family", e.target.value));
    }

    const sliderSize = document.getElementById("styleFontSize");
    const valSize = document.getElementById("valFontSize");
    if (sliderSize && valSize) {
      sliderSize.addEventListener("input", (e) => {
        const val = parseInt(e.target.value, 10);
        valSize.textContent = `${val}px`;
        updateStyle("font_size", val);
      });
    }

    const colPrimary = document.getElementById("stylePrimaryColor");
    if (colPrimary) {
      colPrimary.addEventListener("input", (e) => updateStyle("primary_color", e.target.value));
    }

    const colSecondary = document.getElementById("styleSecondaryColor");
    if (colSecondary) {
      colSecondary.addEventListener("input", (e) => updateStyle("secondary_color", e.target.value));
    }

    const colOutline = document.getElementById("styleOutlineColor");
    if (colOutline) {
      colOutline.addEventListener("input", (e) => updateStyle("outline_color", e.target.value));
    }

    const sliderBgOp = document.getElementById("styleBgOpacity");
    const valBgOp = document.getElementById("valBgOpacity");
    if (sliderBgOp && valBgOp) {
      sliderBgOp.addEventListener("input", (e) => {
        const val = parseInt(e.target.value, 10);
        valBgOp.textContent = `${val}%`;
        updateStyle("background_opacity", val);
      });
    }

    const sliderMarginV = document.getElementById("styleMarginV");
    const valMarginV = document.getElementById("valMarginV");
    if (sliderMarginV && valMarginV) {
      sliderMarginV.addEventListener("input", (e) => {
        const val = parseInt(e.target.value, 10);
        valMarginV.textContent = `${val}px`;
        updateStyle("margin_v", val);
      });
    }

    document.querySelectorAll(".preset-chips .chip").forEach(chip => {
      chip.addEventListener("click", () => {
        document.querySelectorAll(".preset-chips .chip").forEach(c => c.classList.remove("active"));
        chip.classList.add("active");
        const preset = chip.dataset.preset;
        this.applyPreset(preset);
      });
    });
  }

  applyPreset(presetName) {
    if (presetName === "modern_bottom") {
      Object.assign(this.project.style, {
        font_family: "Be Vietnam Pro",
        font_size: 24,
        primary_color: "#ffffff",
        secondary_color: "#ffd700",
        outline_color: "#000000",
        outline_width: 2.2,
        background_opacity: 35,
        alignment: 2,
        margin_v: 45
      });
    } else if (presetName === "tiktok_box") {
      Object.assign(this.project.style, {
        font_family: "Montserrat",
        font_size: 28,
        primary_color: "#ffd700",
        secondary_color: "#ffffff",
        outline_color: "#000000",
        outline_width: 2.0,
        background_opacity: 75,
        alignment: 2,
        margin_v: 60
      });
    } else if (presetName === "cinema_classic") {
      Object.assign(this.project.style, {
        font_family: "Roboto",
        font_size: 22,
        primary_color: "#ffffff",
        secondary_color: "#ffd700",
        outline_color: "#000000",
        outline_width: 2.5,
        background_opacity: 0,
        alignment: 2,
        margin_v: 35
      });
    } else if (presetName === "top_banner") {
      Object.assign(this.project.style, {
        font_family: "Be Vietnam Pro",
        font_size: 24,
        primary_color: "#ffffff",
        secondary_color: "#ffd700",
        outline_color: "#000000",
        outline_width: 2.0,
        background_opacity: 50,
        alignment: 8,
        margin_v: 25
      });
    }

    this.populateStyleControls();
    if (this.overlay) {
      this.overlay.setStyle(this.project.style);
    }
    this.scheduleAutoSave();
  }

  /* ----------------------------------------------------
     VIDEO PLAYER & DUAL-TRACK AUDIO SYNC
  ---------------------------------------------------- */
  bindPlayerEvents() {
    const btnPlay = document.getElementById("btnPlayPause");
    const timeDisplay = document.getElementById("timeDisplay");

    btnPlay.addEventListener("click", () => {
      if (this.video.paused) {
        this.video.play();
        btnPlay.textContent = "⏸";
      } else {
        this.video.pause();
        btnPlay.textContent = "▶";
      }
    });

    this.video.addEventListener("play", () => {
      btnPlay.textContent = "⏸";
      if (this.isLiveDubEnabled && !this.isShowingDubbed) {
        this.syncAudioVolumes();
        this.liveDubAudio.currentTime = this.video.currentTime;
        this.liveDubAudio.play().catch(e => console.warn("Lỗi phát audio lồng tiếng đồng bộ:", e));
      }
    });

    this.video.addEventListener("pause", () => {
      btnPlay.textContent = "▶";
      if (!this.isShowingDubbed) {
        this.liveDubAudio.pause();
      }
    });

    this.video.addEventListener("seeking", () => {
      if (this.isLiveDubEnabled && !this.isShowingDubbed) {
        this.liveDubAudio.currentTime = this.video.currentTime;
      }
    });

    this.video.addEventListener("timeupdate", () => {
      const cur = this.video.currentTime;
      const dur = this.video.duration || (this.project.video ? this.project.video.duration : 1) || 1;
      timeDisplay.textContent = `${this.formatTime(cur)} / ${this.formatTime(dur)}`;

      const pct = (cur / dur) * 100;
      const progEl = document.getElementById("timelineProgress");
      const handleEl = document.getElementById("timelineHandle");
      if (progEl) progEl.style.width = `${pct}%`;
      if (handleEl) handleEl.style.left = `${pct}%`;

      // Giữ đồng bộ nhịp âm thanh lồng tiếng không bị trôi quá 0.25s
      if (this.isLiveDubEnabled && !this.isShowingDubbed && !this.video.paused) {
        const drift = Math.abs(this.liveDubAudio.currentTime - cur);
        if (drift > 0.25) {
          this.liveDubAudio.currentTime = cur;
        }
      }

      this.syncActiveSegment(cur);
    });

    document.getElementById("btnStepBack").addEventListener("click", () => {
      this.video.currentTime = Math.max(0, this.video.currentTime - 1.0);
      if (this.isLiveDubEnabled && !this.isShowingDubbed) {
        this.liveDubAudio.currentTime = this.video.currentTime;
      }
    });

    document.getElementById("btnStepForward").addEventListener("click", () => {
      this.video.currentTime = Math.min(this.video.duration, this.video.currentTime + 1.0);
      if (this.isLiveDubEnabled && !this.isShowingDubbed) {
        this.liveDubAudio.currentTime = this.video.currentTime;
      }
    });

    window.addEventListener("keydown", (e) => {
      if (e.code === "Space" && e.target.tagName !== "TEXTAREA" && e.target.tagName !== "INPUT") {
        e.preventDefault();
        btnPlay.click();
      }
    });
  }

  bindTimelineEvents() {
    const track = document.getElementById("timelineTrack");
    let isDragging = false;

    const seek = (e) => {
      const rect = track.getBoundingClientRect();
      const clickX = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const pct = clickX / rect.width;
      const dur = this.video.duration || (this.project.video ? this.project.video.duration : 1) || 1;
      const targetTime = pct * dur;
      this.video.currentTime = targetTime;
      if (this.isLiveDubEnabled && !this.isShowingDubbed) {
        this.liveDubAudio.currentTime = targetTime;
      }
    };

    track.parentElement.addEventListener("mousedown", (e) => {
      isDragging = true;
      seek(e);
    });

    window.addEventListener("mousemove", (e) => {
      if (isDragging) seek(e);
    });

    window.addEventListener("mouseup", () => {
      if (isDragging) isDragging = false;
    });
  }

  renderTimelineCues() {
    const cuesContainer = document.getElementById("timelineCues");
    cuesContainer.innerHTML = "";
    const dur = this.project.video?.duration || this.video.duration || 1;
    const segments = this.project.segments || [];

    segments.forEach(seg => {
      const cue = document.createElement("div");
      cue.className = "cue-point";
      const startPct = (seg.start / dur) * 100;
      const endPct = (seg.end / dur) * 100;
      const widthPct = Math.max(0.4, endPct - startPct);
      cue.style.left = `${startPct}%`;
      cue.style.width = `${widthPct}%`;
      cue.title = `[#${seg.id}] ${seg.target_text || seg.text}`;
      cuesContainer.appendChild(cue);
    });
  }

  syncActiveSegment(time) {
    const segments = this.project.segments || [];
    const matched = segments.find(s => time >= s.start && time <= s.end);

    const bannerText = document.getElementById("nowPlayingText");
    const indicator = document.getElementById("segmentIndicator");

    if (matched) {
      this.activeSegment = matched;
      bannerText.textContent = matched.target_text || matched.text || "";
      indicator.textContent = `Câu ${matched.id} / ${segments.length}`;

      if (this.overlay) {
        this.overlay.renderSegment(matched);
      }

      document.querySelectorAll(".segment-item").forEach(item => {
        const isCur = parseInt(item.dataset.id, 10) === matched.id;
        item.classList.toggle("active", isCur);
        if (isCur && !this.isUserScrolling) {
          item.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      });
    } else {
      bannerText.textContent = "—";
      if (this.overlay) {
        this.overlay.renderSegment(null);
      }
      document.querySelectorAll(".segment-item.active").forEach(el => el.classList.remove("active"));
    }
  }

  /* ----------------------------------------------------
     SPLIT SEGMENT, VIDEO SWITCHER & LIVE DUB TOGGLE
  ---------------------------------------------------- */
  bindLiveDubToggle() {
    const btn = document.getElementById("btnToggleLiveDub");
    if (!btn) return;

    btn.addEventListener("click", () => {
      this.isLiveDubEnabled = !this.isLiveDubEnabled;
      btn.classList.toggle("active", this.isLiveDubEnabled);
      btn.textContent = this.isLiveDubEnabled ? "🎙️ Lồng Tiếng: BẬT" : "🔇 Lồng Tiếng: TẮT";
      this.syncAudioVolumes();

      if (this.isLiveDubEnabled) {
        if (!this.video.paused && !this.isShowingDubbed) {
          this.liveDubAudio.currentTime = this.video.currentTime;
          this.liveDubAudio.play().catch(() => {});
        }
      } else {
        this.liveDubAudio.pause();
      }
    });
  }

  bindSplitButton() {
    const btnSplit = document.getElementById("btnSplitPlayhead");
    if (!btnSplit) return;

    btnSplit.addEventListener("click", async () => {
      const curTime = this.video.currentTime;
      const segments = this.project.segments || [];
      const matched = segments.find(s => curTime > s.start + 0.3 && curTime < s.end - 0.3);

      if (!matched) {
        alert("⚠️ Vị trí phát hiện tại không nằm trong một câu thoại dài hoặc quá gần mép đầu/cuối (cần cách tối thiểu 0.3s). Hãy tua tới giữa câu bạn muốn cắt!");
        return;
      }

      const confirmSplit = confirm(`Bạn có muốn chia câu #${matched.id} tại thời điểm ${this.formatTime(curTime)}?`);
      if (!confirmSplit) return;

      try {
        const res = await fetch("/api/split", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            segment_id: matched.id,
            split_time: curTime
          })
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.error || "Không thể chia câu");
        }

        this.project.segments = data.segments;
        this.renderTimelineCues();
        this.renderSegmentsList();
        this.syncActiveSegment(curTime);
        alert(`✂ Đã chia câu #${matched.id} thành công! Bây giờ bạn có thể chỉnh riêng nội dung và thời gian của từng phần.`);
      } catch (err) {
        alert("Lỗi khi chia câu: " + err.message);
      }
    });
  }

  bindVideoSwitcher() {
    const btnSwitch = document.getElementById("btnSwitchVideo");
    if (!btnSwitch) return;

    btnSwitch.addEventListener("click", () => {
      this.toggleDubbedVideo();
    });

    const btnWatchDubbed = document.getElementById("btnWatchDubbed");
    if (btnWatchDubbed) {
      btnWatchDubbed.addEventListener("click", () => {
        const modal = document.getElementById("renderModal");
        if (modal) modal.style.display = "none";
        if (!this.isShowingDubbed) {
          this.toggleDubbedVideo();
        }
      });
    }
  }

  toggleDubbedVideo() {
    const btnSwitch = document.getElementById("btnSwitchVideo");
    const btnDubToggle = document.getElementById("btnToggleLiveDub");
    const curTime = this.video.currentTime;
    const wasPlaying = !this.video.paused;

    if (!this.isShowingDubbed) {
      // Chuyển sang xem video đã lồng tiếng
      this.isShowingDubbed = true;
      this.liveDubAudio.pause();
      if (btnDubToggle) btnDubToggle.style.display = "none";

      this.video.src = `/video?type=dubbed&t=${Date.now()}`;
      btnSwitch.textContent = "🎬 Đang xem Video Đã Lồng Tiếng (Bấm để về Bản Gốc)";
      btnSwitch.classList.add("btn-active-dubbed");
    } else {
      // Quay về bản gốc
      this.isShowingDubbed = false;
      if (btnDubToggle) btnDubToggle.style.display = "inline-flex";

      this.video.src = `/video?type=orig&t=${Date.now()}`;
      btnSwitch.textContent = "🎬 Xem Video Đã Lồng Tiếng";
      btnSwitch.classList.remove("btn-active-dubbed");
    }

    this.syncAudioVolumes();

    this.video.onloadedmetadata = () => {
      this.video.currentTime = curTime;
      if (wasPlaying) {
        this.video.play();
      }
    };
  }

  /* ----------------------------------------------------
     TAB 3: SEGMENTS LIST & PREVIEW VOICE
  ---------------------------------------------------- */
  renderSegmentsList() {
    const container = document.getElementById("segmentsList");
    container.innerHTML = "";
    const segments = this.project.segments || [];
    const countEl = document.getElementById("scriptCount");
    countEl.textContent = `${segments.length} câu`;

    segments.forEach(seg => {
      const durSec = (seg.end - seg.start).toFixed(1);
      const item = document.createElement("div");
      item.className = "segment-item";
      item.dataset.id = seg.id;

      item.innerHTML = `
        <div class="seg-header">
          <div class="seg-meta">
            <span class="seg-id">#${seg.id}</span>
            <span class="seg-time">${this.formatTime(seg.start)} ➔ ${this.formatTime(seg.end)}</span>
            <span class="seg-dur">(${durSec}s)</span>
          </div>
          <div class="seg-actions">
            <button class="btn-seg-action btn-preview-voice" data-id="${seg.id}" title="Nghe thử giọng đọc cho câu này">
              <span>🔊 Nghe thử</span>
            </button>
            <button class="btn-seg-action btn-seek-video" data-time="${seg.start}" title="Tua video tới mốc thời gian câu này">
              <span>⏩ Tua tới</span>
            </button>
          </div>
        </div>
        ${seg.orig_text ? `<div class="seg-orig-text" style="font-size:12px;color:#94a3b8;margin-bottom:4px;">🇯🇵 Gốc: ${seg.orig_text}</div>` : ""}
        <textarea class="seg-text-input" rows="2" placeholder="Nội dung câu lồng tiếng...">${seg.target_text || seg.text || ""}</textarea>
      `;

      const textarea = item.querySelector(".seg-text-input");
      textarea.addEventListener("input", (e) => {
        seg.target_text = e.target.value;
        seg.text = e.target.value;
        if (this.activeSegment && this.activeSegment.id === seg.id && this.overlay) {
          this.overlay.renderSegment(seg);
        }
        this.scheduleAutoSave();
      });

      const btnSeek = item.querySelector(".btn-seek-video");
      btnSeek.addEventListener("click", () => {
        this.video.currentTime = parseFloat(btnSeek.dataset.time);
        if (this.isLiveDubEnabled && !this.isShowingDubbed) {
          this.liveDubAudio.currentTime = this.video.currentTime;
        }
        this.video.play();
      });

      const btnPreview = item.querySelector(".btn-preview-voice");
      btnPreview.addEventListener("click", () => {
        this.previewVoiceLine(seg, btnPreview);
      });

      container.appendChild(item);
    });

    const searchInput = document.getElementById("searchScript");
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      document.querySelectorAll(".segment-item").forEach(item => {
        const text = item.querySelector(".seg-text-input").value.toLowerCase();
        item.style.display = text.includes(q) ? "flex" : "none";
      });
    });
  }

  async previewVoiceLine(seg, buttonEl) {
    const text = seg.target_text || seg.text;
    if (!text || !text.trim()) {
      alert("Câu thoại chưa có nội dung!");
      return;
    }

    const settings = this.project.audio_settings || {};
    const origBtnHtml = buttonEl.innerHTML;
    buttonEl.innerHTML = "<span>⏳ Đang tạo...</span>";
    buttonEl.disabled = true;

    try {
      const res = await fetch("/api/preview-line", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          lang: settings.lang || "vi",
          gender: settings.gender || "female",
          voice: settings.voice,
          speed: settings.speed || 1.0
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || "Không thể tạo âm thanh thử nghiệm");
      }

      if (this.currentAudioPreview) {
        this.currentAudioPreview.pause();
      }

      buttonEl.innerHTML = "<span>🔊 Đang phát...</span>";
      buttonEl.classList.add("playing");

      this.currentAudioPreview = new Audio(data.audio_url);
      this.currentAudioPreview.play();

      this.currentAudioPreview.onended = () => {
        buttonEl.innerHTML = origBtnHtml;
        buttonEl.classList.remove("playing");
        buttonEl.disabled = false;
      };

      this.currentAudioPreview.onerror = () => {
        buttonEl.innerHTML = origBtnHtml;
        buttonEl.classList.remove("playing");
        buttonEl.disabled = false;
      };
    } catch (err) {
      alert("Lỗi nghe thử câu thoại: " + err.message);
      buttonEl.innerHTML = origBtnHtml;
      buttonEl.disabled = false;
    }
  }

  /* ----------------------------------------------------
     TABS, TOOLBAR & RENDER MODAL
  ---------------------------------------------------- */
  bindTabs() {
    const tabButtons = document.querySelectorAll(".tabs-header .tab-btn");
    tabButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        tabButtons.forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tabs-body .tab-content").forEach(tc => tc.classList.remove("active"));

        btn.classList.add("active");
        const targetId = btn.dataset.tab;
        const targetContent = document.getElementById(targetId);
        if (targetContent) targetContent.classList.add("active");
      });
    });
  }

  scheduleAutoSave() {
    clearTimeout(this.saveTimeout);
    const statusText = document.getElementById("statusText");
    if (statusText) statusText.textContent = "Đang lưu...";

    this.saveTimeout = setTimeout(async () => {
      try {
        await fetch("/api/project", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.project)
        });
        if (statusText) statusText.textContent = "Đã lưu thiết lập";
        setTimeout(() => { if (statusText) statusText.textContent = "Sẵn sàng"; }, 2000);
      } catch (err) {
        if (statusText) statusText.textContent = "Lỗi lưu cấu hình";
      }
    }, 600);
  }

  bindToolbarActions() {
    document.getElementById("btnSaveConfig").addEventListener("click", async () => {
      try {
        const res = await fetch("/api/project", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.project)
        });
        if (res.ok) {
          alert("✅ Đã lưu toàn bộ thiết lập âm thanh, kiểu chữ và kịch bản lồng tiếng thành công!");
        } else {
          throw new Error("Lỗi khi lưu");
        }
      } catch (err) {
        alert("❌ Lỗi khi lưu dự án: " + err.message);
      }
    });

    document.getElementById("btnShutdown").addEventListener("click", async () => {
      if (confirm("Bạn có chắc chắn muốn đóng phòng dựng lồng tiếng này?")) {
        try {
          await fetch("/api/shutdown", { method: "POST" });
        } catch (_) {}
        document.body.innerHTML = `
          <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;background:#0e1015;color:#f8fafc;font-family:sans-serif;text-align:center;gap:16px;">
            <div style="font-size:48px;">🛑</div>
            <h2>Phòng dựng Lồng Tiếng Studio đã đóng an toàn</h2>
            <p style="color:#94a3b8;">Cổng kết nối đã được giải phóng. Bạn có thể đóng tab trình duyệt này và quay lại Antigravity Chat.</p>
          </div>
        `;
      }
    });
  }

  bindRenderModal() {
    const modal = document.getElementById("renderModal");
    const btnOpen = document.getElementById("btnRenderModal");
    const btnClose = document.getElementById("btnCloseRenderModal");
    const btnStart = document.getElementById("btnStartRender");
    const btnReRender = document.getElementById("btnReRender");
    const progBox = document.getElementById("renderProgressBox");
    const progBar = document.getElementById("renderProgressBar");
    const progPct = document.getElementById("renderProgressPct");
    const progStage = document.getElementById("renderProgressStage");
    const doneBox = document.getElementById("renderDoneBox");

    const resetModalUI = () => {
      progBox.style.display = "none";
      doneBox.style.display = "none";
      btnStart.disabled = false;
      btnStart.style.display = "inline-flex";
      btnStart.textContent = "Bắt đầu Xuất Video";
    };

    btnOpen.addEventListener("click", () => {
      modal.style.display = "flex";
      resetModalUI();
    });

    btnClose.addEventListener("click", () => {
      modal.style.display = "none";
      clearInterval(this.renderPollingInterval);
    });

    if (btnReRender) {
      btnReRender.addEventListener("click", () => {
        resetModalUI();
        btnStart.textContent = "🚀 Bắt đầu Render Phiên Bản Mới";
        btnStart.click();
      });
    }

    btnStart.addEventListener("click", async () => {
      btnStart.disabled = true;
      progBox.style.display = "flex";
      doneBox.style.display = "none";
      progBar.style.width = "0%";
      progPct.textContent = "0%";
      progStage.textContent = "Đang chuẩn bị...";

      try {
        const res = await fetch("/api/render", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            audio_settings: this.project.audio_settings,
            style: this.project.style,
            segments: this.project.segments
          })
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.error || "Không thể khởi chạy render");
        }

        this.startRenderPolling();
      } catch (err) {
        alert("Lỗi khi bắt đầu xuất video: " + err.message);
        btnStart.disabled = false;
      }
    });
  }

  startRenderPolling() {
    const progBar = document.getElementById("renderProgressBar");
    const progPct = document.getElementById("renderProgressPct");
    const progStage = document.getElementById("renderProgressStage");
    const doneBox = document.getElementById("renderDoneBox");
    const donePath = document.getElementById("renderDoneFilePath");
    const btnStart = document.getElementById("btnStartRender");

    clearInterval(this.renderPollingInterval);
    this.renderPollingInterval = setInterval(async () => {
      try {
        const res = await fetch("/api/render-status");
        if (!res.ok) return;
        const job = await res.json();

        progBar.style.width = `${job.progress}%`;
        progPct.textContent = `${job.progress}%`;
        progStage.textContent = job.stage || "";

        if (job.status === "done") {
          clearInterval(this.renderPollingInterval);
          btnStart.style.display = "none";
          doneBox.style.display = "flex";
          donePath.textContent = `📁 File thành phẩm: ${job.output_path}`;

          // Cập nhật lại audio stream sau khi render xong
          this.liveDubAudio.src = `/audio/speech?t=${Date.now()}`;
          this.liveDubAudio.load();
        } else if (job.status === "error") {
          clearInterval(this.renderPollingInterval);
          alert("❌ Quá trình xuất video gặp lỗi: " + job.error);
          btnStart.disabled = false;
        }
      } catch (e) {
        console.warn("Lỗi polling render:", e);
      }
    }, 800);
  }
}

// Khởi chạy khi DOM sẵn sàng
window.addEventListener("DOMContentLoaded", () => {
  new DubbingStudioApp();
});
