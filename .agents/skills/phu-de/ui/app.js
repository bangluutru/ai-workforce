/**
 * app.js — Client logic điều phối toàn diện Phụ Đề Studio (AIWF).
 * Quản trị đồng bộ Video Player, Timeline Scrubber, Segments List,
 * Realtime Visual Styling, AI Edit Loop, Undo/Redo và Render.
 */

import { SubtitleOverlay } from "./lib/subtitle_overlay.js";

class SubtitleStudioApp {
  constructor() {
    this.project = null;
    this.video = document.getElementById("videoPlayer");
    this.overlayEl = document.getElementById("subtitleOverlay");
    this.containerEl = document.getElementById("videoContainer");
    this.overlay = new SubtitleOverlay(this.video, this.overlayEl, this.containerEl);

    this.activeSegment = null;
    this.selectedSegmentIds = new Set();
    this.saveTimeout = null;

    this.init();
  }

  async init() {
    try {
      await this.loadProject();
      this.bindPlayerEvents();
      this.bindTimelineEvents();
      this.bindTabs();
      this.bindStyleControls();
      this.bindSegmentActions();
      this.bindAIEvents();
      this.bindToolbarEvents();
      this.bindKeyboardShortcuts();
      this.renderAll();
    } catch (err) {
      console.error("Lỗi khởi tạo:", err);
      alert("Không thể tải thông tin dự án: " + err.message);
    }
  }

  async loadProject() {
    const res = await fetch("/api/project");
    if (!res.ok) throw new Error(await res.text());
    this.project = await res.json();
  }

  renderAll() {
    this.updateHeaderMeta();
    this.overlay.setStyle(this.project.style || {});
    this.populateStyleForm();
    this.renderTimelineCues();
    this.renderSegmentsList();
    this.updateRevisionUI();
  }

  updateHeaderMeta() {
    const v = this.project.video || {};
    const metaEl = document.getElementById("projectMeta");
    const durStr = this.formatTime(v.duration || 0);
    metaEl.textContent = `${v.filename || "Video"} (${durStr} - ${v.width || 1920}x${v.height || 1080})`;
  }

  updateRevisionUI() {
    const rev = this.project.history?.current_revision || 1;
    const badge = document.getElementById("revisionBadge");
    if (badge) badge.textContent = `Rev ${rev}`;

    const btnUndo = document.getElementById("btnUndo");
    const btnRedo = document.getElementById("btnRedo");
    if (btnUndo) btnUndo.disabled = rev <= 1;
    if (btnRedo) {
      const totalSnaps = this.project.history?.snapshots?.length || 1;
      btnRedo.disabled = rev >= totalSnaps;
    }
  }

  /* ----------------------------------------------------
     VIDEO & TIMELINE SYNC
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

    this.video.addEventListener("play", () => { btnPlay.textContent = "⏸"; });
    this.video.addEventListener("pause", () => { btnPlay.textContent = "▶"; });

    this.video.addEventListener("timeupdate", () => {
      const cur = this.video.currentTime;
      const dur = this.video.duration || 1;
      timeDisplay.textContent = `${this.formatTime(cur)} / ${this.formatTime(dur)}`;

      // Cập nhật vị trí con trỏ trên scrubber
      const pct = (cur / dur) * 100;
      const progEl = document.getElementById("timelineProgress");
      const handleEl = document.getElementById("timelineHandle");
      if (progEl) progEl.style.width = `${pct}%`;
      if (handleEl) handleEl.style.left = `${pct}%`;

      // Tìm câu phụ đề khớp với thời điểm hiện tại
      this.syncActiveSegment(cur);
    });

    document.getElementById("btnStepBack").addEventListener("click", () => {
      this.video.currentTime = Math.max(0, this.video.currentTime - 1.0);
    });
    document.getElementById("btnStepForward").addEventListener("click", () => {
      this.video.currentTime = Math.min(this.video.duration, this.video.currentTime + 1.0);
    });

    document.getElementById("btnSplitPlayhead").addEventListener("click", () => {
      if (this.activeSegment) {
        this.splitSegment(this.activeSegment.id, this.video.currentTime);
      } else {
        alert("Vui lòng tua đến một câu phụ đề để thực hiện chia câu.");
      }
    });
  }

  bindTimelineEvents() {
    const track = document.getElementById("timelineTrack");
    let isDragging = false;

    const seek = (e) => {
      const rect = track.getBoundingClientRect();
      const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const dur = this.video.duration || (this.project.video?.duration || 0);
      if (dur > 0) {
        this.video.currentTime = pos * dur;
      }
    };

    track.addEventListener("mousedown", (e) => {
      isDragging = true;
      seek(e);
    });

    window.addEventListener("mousemove", (e) => {
      if (isDragging) seek(e);
    });

    window.addEventListener("mouseup", () => {
      isDragging = false;
    });
  }

  renderTimelineCues() {
    const cuesContainer = document.getElementById("timelineCues");
    if (!cuesContainer) return;
    cuesContainer.innerHTML = "";

    const dur = this.video.duration || (this.project.video?.duration || 1);
    const segments = this.project.segments || [];

    segments.forEach((s) => {
      const left = (s.start / dur) * 100;
      const width = Math.max(0.5, ((s.end - s.start) / dur) * 100);

      const cue = document.createElement("div");
      cue.className = "timeline-cue-block";
      cue.id = `cue_${s.id}`;
      cue.style.left = `${left}%`;
      cue.style.width = `${width}%`;
      cue.title = `[${s.id}] ${s.start}s - ${s.end}s: ${s.translated_text || s.source_text}`;

      cue.addEventListener("click", (e) => {
        e.stopPropagation();
        this.video.currentTime = s.start;
      });

      cuesContainer.appendChild(cue);
    });
  }

  syncActiveSegment(currentTime) {
    const segments = this.project.segments || [];
    let found = null;

    for (let i = 0; i < segments.length; i++) {
      const s = segments[i];
      if (currentTime >= s.start && currentTime <= s.end) {
        found = s;
        break;
      }
    }

    if (found !== this.activeSegment) {
      this.activeSegment = found;
      this.overlay.renderSegment(found);

      // Highlight card trong danh sách
      document.querySelectorAll(".segment-card").forEach((c) => c.classList.remove("active"));
      document.querySelectorAll(".timeline-cue-block").forEach((b) => b.classList.remove("active"));

      if (found) {
        const card = document.getElementById(`card_${found.id}`);
        if (card) {
          card.classList.add("active");
          // Tự động cuộn đến card (smooth)
          card.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        const cue = document.getElementById(`cue_${found.id}`);
        if (cue) cue.classList.add("active");

        const curBadge = document.getElementById("currentSegBadge");
        if (curBadge) curBadge.textContent = found.id;
      }
    }
  }

  /* ----------------------------------------------------
     TAB 1: SEGMENTS LIST
  ---------------------------------------------------- */
  renderSegmentsList() {
    const container = document.getElementById("segmentsList");
    if (!container) return;
    container.innerHTML = "";

    const segments = this.project.segments || [];
    document.getElementById("segmentCount").textContent = `${segments.length} câu`;

    segments.forEach((seg, idx) => {
      const card = document.createElement("div");
      card.className = "segment-card";
      card.id = `card_${seg.id}`;

      card.innerHTML = `
        <div class="seg-header">
          <input type="checkbox" class="seg-select-cb" data-id="${seg.id}" ${this.selectedSegmentIds.has(seg.id) ? "checked" : ""}>
          <span class="seg-badge">${seg.id}</span>
          <div class="seg-times">
            <input type="number" step="0.05" class="time-input input-start" value="${seg.start}">
            <span>→</span>
            <input type="number" step="0.05" class="time-input input-end" value="${seg.end}">
          </div>
          <div class="seg-actions">
            <button class="btn-seg btn-split" title="Chia đôi câu này">✂ Chia</button>
            <button class="btn-seg btn-merge" title="Gộp với câu tiếp theo">⨁ Gộp</button>
            <button class="btn-seg btn-delete" title="Xóa câu này">🗑</button>
          </div>
        </div>
        <textarea class="seg-text-input seg-target-input" rows="2" placeholder="Nội dung dịch...">${escapeHtml(seg.translated_text || "")}</textarea>
        <textarea class="seg-text-input seg-source-input" rows="1" placeholder="Nội dung gốc...">${escapeHtml(seg.source_text || "")}</textarea>
      `;

      // Click vào card -> tua video
      card.addEventListener("click", (e) => {
        if (["INPUT", "TEXTAREA", "BUTTON"].includes(e.target.tagName)) return;
        this.video.currentTime = seg.start;
      });

      // Bắt sự kiện chọn checkbox
      const cb = card.querySelector(".seg-select-cb");
      cb.addEventListener("change", (e) => {
        if (e.target.checked) this.selectedSegmentIds.add(seg.id);
        else this.selectedSegmentIds.delete(seg.id);
      });

      // Sửa start/end
      const inStart = card.querySelector(".input-start");
      const inEnd = card.querySelector(".input-end");
      inStart.addEventListener("change", () => {
        seg.start = parseFloat(inStart.value) || 0;
        this.triggerAutoSave();
        this.renderTimelineCues();
      });
      inEnd.addEventListener("change", () => {
        seg.end = parseFloat(inEnd.value) || seg.start + 1;
        this.triggerAutoSave();
        this.renderTimelineCues();
      });

      // Sửa text
      const txtTarget = card.querySelector(".seg-target-input");
      const txtSrc = card.querySelector(".seg-source-input");
      txtTarget.addEventListener("input", () => {
        seg.translated_text = txtTarget.value;
        if (this.activeSegment && this.activeSegment.id === seg.id) {
          this.overlay.renderSegment(seg);
        }
        this.triggerAutoSave();
      });
      txtSrc.addEventListener("input", () => {
        seg.source_text = txtSrc.value;
        if (this.activeSegment && this.activeSegment.id === seg.id) {
          this.overlay.renderSegment(seg);
        }
        this.triggerAutoSave();
      });

      // Nút Split
      card.querySelector(".btn-split").addEventListener("click", (e) => {
        e.stopPropagation();
        const midTime = (seg.start + seg.end) / 2;
        this.splitSegment(seg.id, midTime);
      });

      // Nút Merge
      card.querySelector(".btn-merge").addEventListener("click", (e) => {
        e.stopPropagation();
        this.mergeSegment(seg.id);
      });

      // Nút Delete
      card.querySelector(".btn-delete").addEventListener("click", (e) => {
        e.stopPropagation();
        if (confirm(`Bạn có chắc muốn xóa câu ${seg.id}?`)) {
          this.deleteSegment(seg.id);
        }
      });

      container.appendChild(card);
    });
  }

  bindSegmentActions() {
    const filterInput = document.getElementById("filterInput");
    filterInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      document.querySelectorAll(".segment-card").forEach((card) => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(q) ? "flex" : "none";
      });
    });
  }

  async splitSegment(segId, splitTime) {
    try {
      const res = await fetch("/api/split", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ segment_id: segId, split_time: splitTime }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      this.project.segments = data.segments;
      this.renderAll();
    } catch (e) {
      alert("Lỗi chia câu: " + e.message);
    }
  }

  async mergeSegment(segId) {
    try {
      const res = await fetch("/api/merge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ segment_id: segId }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      this.project.segments = data.segments;
      this.renderAll();
    } catch (e) {
      alert("Lỗi gộp câu: " + e.message);
    }
  }

  deleteSegment(segId) {
    const segments = this.project.segments || [];
    this.project.segments = segments.filter((s) => s.id !== segId);
    this.project.segments.forEach((s, idx) => {
      s.id = `seg_${String(idx + 1).padStart(3, "0")}`;
    });
    this.triggerAutoSave();
    this.renderAll();
  }

  /* ----------------------------------------------------
     TAB 2: STYLE & REALTIME VISUAL CONTROLS
  ---------------------------------------------------- */
  populateStyleForm() {
    const s = this.project.style || {};
    setVal("styleMode", s.mode || "bilingual");
    setVal("styleBilingualOrder", s.bilingual_order || "target_top");
    setVal("styleFontFamily", s.font_family || "Be Vietnam Pro");
    setVal("styleFontSize", s.font_size || 24);
    setTxt("valFontSize", s.font_size || 24);

    setVal("stylePrimaryColor", s.primary_color || "#ffffff");
    setVal("txtPrimaryColor", (s.primary_color || "#ffffff").toUpperCase());
    setVal("styleSecondaryColor", s.secondary_color || "#ffd700");
    setVal("txtSecondaryColor", (s.secondary_color || "#ffd700").toUpperCase());

    setVal("styleOutlineColor", s.outline_color || "#000000");
    setVal("txtOutlineColor", (s.outline_color || "#000000").toUpperCase());
    setVal("styleOutlineWidth", s.outline_width || 2.2);
    setTxt("valOutlineWidth", s.outline_width || 2.2);

    setVal("styleBgColor", s.background_color || "#000000");
    setVal("txtBgColor", (s.background_color || "#000000").toUpperCase());
    setVal("styleBgOpacity", s.background_opacity ?? 35);
    setTxt("valBgOpacity", s.background_opacity ?? 35);
    setVal("styleBorderRadius", s.border_radius ?? 8);
    setTxt("valBorderRadius", s.border_radius ?? 8);
    setVal("styleBoxPadding", s.box_padding ?? 16);
    setTxt("valBoxPadding", s.box_padding ?? 16);

    setVal("styleMarginV", s.margin_v || 45);
    setTxt("valMarginV", s.margin_v || 45);
    setVal("styleLineSpacing", s.line_spacing || 6);
    setTxt("valLineSpacing", s.line_spacing || 6);

    // Alignment button active
    const curAlign = String(s.alignment || 2);
    document.querySelectorAll(".align-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.align === curAlign);
    });

    this.toggleBilingualOrderVisibility();
  }

  bindStyleControls() {
    const updateStyle = (key, val) => {
      this.project.style = this.project.style || {};
      this.project.style[key] = val;
      this.overlay.setStyle(this.project.style);
      this.triggerAutoSave();
    };

    // Mode
    document.getElementById("styleMode").addEventListener("change", (e) => {
      updateStyle("mode", e.target.value);
      this.toggleBilingualOrderVisibility();
    });

    document.getElementById("styleBilingualOrder").addEventListener("change", (e) => {
      updateStyle("bilingual_order", e.target.value);
    });

    // Font
    document.getElementById("styleFontFamily").addEventListener("change", (e) => {
      updateStyle("font_family", e.target.value);
    });

    // Font Size
    const fs = document.getElementById("styleFontSize");
    fs.addEventListener("input", (e) => {
      setTxt("valFontSize", e.target.value);
      updateStyle("font_size", parseInt(e.target.value, 10));
    });

    // Colors
    const pickPri = document.getElementById("stylePrimaryColor");
    const txtPri = document.getElementById("txtPrimaryColor");
    pickPri.addEventListener("input", (e) => {
      txtPri.value = e.target.value.toUpperCase();
      updateStyle("primary_color", e.target.value);
    });
    txtPri.addEventListener("change", (e) => {
      pickPri.value = e.target.value;
      updateStyle("primary_color", e.target.value);
    });

    const pickSec = document.getElementById("styleSecondaryColor");
    const txtSec = document.getElementById("txtSecondaryColor");
    pickSec.addEventListener("input", (e) => {
      txtSec.value = e.target.value.toUpperCase();
      updateStyle("secondary_color", e.target.value);
    });
    txtSec.addEventListener("change", (e) => {
      pickSec.value = e.target.value;
      updateStyle("secondary_color", e.target.value);
    });

    // Outline
    const pickOut = document.getElementById("styleOutlineColor");
    const txtOut = document.getElementById("txtOutlineColor");
    pickOut.addEventListener("input", (e) => {
      txtOut.value = e.target.value.toUpperCase();
      updateStyle("outline_color", e.target.value);
    });
    txtOut.addEventListener("change", (e) => {
      pickOut.value = e.target.value;
      updateStyle("outline_color", e.target.value);
    });

    const ow = document.getElementById("styleOutlineWidth");
    ow.addEventListener("input", (e) => {
      setTxt("valOutlineWidth", e.target.value);
      updateStyle("outline_width", parseFloat(e.target.value));
    });

    // Background
    const pickBg = document.getElementById("styleBgColor");
    const txtBg = document.getElementById("txtBgColor");
    pickBg.addEventListener("input", (e) => {
      txtBg.value = e.target.value.toUpperCase();
      updateStyle("background_color", e.target.value);
    });
    txtBg.addEventListener("change", (e) => {
      pickBg.value = e.target.value;
      updateStyle("background_color", e.target.value);
    });

    const op = document.getElementById("styleBgOpacity");
    op.addEventListener("input", (e) => {
      setTxt("valBgOpacity", e.target.value);
      updateStyle("background_opacity", parseInt(e.target.value, 10));
    });

    // Border Radius
    const br = document.getElementById("styleBorderRadius");
    if (br) {
      br.addEventListener("input", (e) => {
        setTxt("valBorderRadius", e.target.value);
        updateStyle("border_radius", parseInt(e.target.value, 10));
      });
    }

    // Box Padding
    const bp = document.getElementById("styleBoxPadding");
    if (bp) {
      bp.addEventListener("input", (e) => {
        setTxt("valBoxPadding", e.target.value);
        updateStyle("box_padding", parseInt(e.target.value, 10));
      });
    }

    // Alignment 9-grid
    document.querySelectorAll(".align-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".align-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        updateStyle("alignment", parseInt(btn.dataset.align, 10));
      });
    });

    // Margins
    const mv = document.getElementById("styleMarginV");
    mv.addEventListener("input", (e) => {
      setTxt("valMarginV", e.target.value);
      updateStyle("margin_v", parseInt(e.target.value, 10));
    });

    const ls = document.getElementById("styleLineSpacing");
    ls.addEventListener("input", (e) => {
      setTxt("valLineSpacing", e.target.value);
      updateStyle("line_spacing", parseInt(e.target.value, 10));
    });

    // Presets
    document.querySelectorAll(".preset-chips .chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        document.querySelectorAll(".preset-chips .chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        this.applyPreset(chip.dataset.preset);
      });
    });
  }

  applyPreset(name) {
    const s = this.project.style || {};
    if (name === "modern_bottom") {
      Object.assign(s, {
        font_family: "Be Vietnam Pro", font_size: 24, primary_color: "#FFFFFF",
        secondary_color: "#FFD700", outline_color: "#000000", outline_width: 2.2,
        background_color: "#000000", background_opacity: 35, alignment: 2, margin_v: 45
      });
    } else if (name === "tiktok_box") {
      Object.assign(s, {
        font_family: "Montserrat", font_size: 26, primary_color: "#FFFFFF",
        secondary_color: "#00FFFF", outline_color: "#000000", outline_width: 1.5,
        background_color: "#111827", background_opacity: 75, alignment: 2, margin_v: 60
      });
    } else if (name === "cinema_classic") {
      Object.assign(s, {
        font_family: "Noto Serif", font_size: 22, primary_color: "#FFF275",
        secondary_color: "#FFFFFF", outline_color: "#000000", outline_width: 2.5,
        background_color: "#000000", background_opacity: 0, alignment: 2, margin_v: 35
      });
    } else if (name === "top_banner") {
      Object.assign(s, {
        font_family: "Roboto", font_size: 22, primary_color: "#FFFFFF",
        secondary_color: "#FFD700", outline_color: "#000000", outline_width: 2.0,
        background_color: "#000000", background_opacity: 50, alignment: 8, margin_v: 30
      });
    }
    this.populateStyleForm();
    this.overlay.setStyle(s);
    this.triggerAutoSave();
  }

  toggleBilingualOrderVisibility() {
    const mode = document.getElementById("styleMode").value;
    const group = document.getElementById("bilingualOrderGroup");
    if (group) group.style.display = mode === "bilingual" ? "flex" : "none";
  }

  /* ----------------------------------------------------
     TAB 3: AI EDIT ASSISTANT
  ---------------------------------------------------- */
  bindAIEvents() {
    const txtArea = document.getElementById("aiPromptInput");
    const btnApply = document.getElementById("btnApplyAI");
    const statusMsg = document.getElementById("aiStatusMsg");

    document.querySelectorAll(".ai-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        txtArea.value = chip.dataset.prompt;
      });
    });

    btnApply.addEventListener("click", async () => {
      const instruction = txtArea.value.trim();
      if (!instruction) {
        alert("Vui lòng nhập chỉ thị cho AI.");
        return;
      }

      const scope = document.querySelector('input[name="aiScope"]:checked').value;
      let targetIds = [];
      if (scope === "current") {
        if (!this.activeSegment) {
          alert("Chưa có câu nào đang phát. Hãy tua video tới 1 câu hoặc chọn scope khác.");
          return;
        }
        targetIds = [this.activeSegment.id];
      } else if (scope === "selected") {
        targetIds = Array.from(this.selectedSegmentIds);
        if (targetIds.length === 0) {
          alert("Vui lòng tích chọn ít nhất 1 câu trong danh sách phụ đề.");
          return;
        }
      }

      btnApply.disabled = true;
      btnApply.querySelector(".btn-text").textContent = "Đang xử lý...";
      btnApply.querySelector(".spinner").style.display = "inline-block";
      statusMsg.className = "status-msg";
      statusMsg.textContent = "";

      try {
        const res = await fetch("/api/ai-edit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: jsonBody({
            instruction,
            scope,
            segment_ids: targetIds,
          }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        this.project.segments = data.segments;
        this.renderAll();

        statusMsg.className = "status-msg success";
        statusMsg.textContent = `✅ Đã áp dụng AI Edit thành công cho ${data.updated_count} câu!`;
      } catch (err) {
        statusMsg.className = "status-msg error";
        statusMsg.textContent = `❌ Lỗi: ${err.message}`;
      } finally {
        btnApply.disabled = false;
        btnApply.querySelector(".btn-text").textContent = "✨ Áp dụng AI Edit";
        btnApply.querySelector(".spinner").style.display = "none";
      }
    });
  }

  /* ----------------------------------------------------
     TOOLBAR & HEADER ACTIONS
  ---------------------------------------------------- */
  bindToolbarEvents() {
    // Undo
    document.getElementById("btnUndo").addEventListener("click", async () => {
      const res = await fetch("/api/undo", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        this.project = data.project;
        this.renderAll();
      } else {
        alert(data.message || data.error);
      }
    });

    // Redo
    document.getElementById("btnRedo").addEventListener("click", async () => {
      const res = await fetch("/api/redo", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        this.project = data.project;
        this.renderAll();
      } else {
        alert(data.message || data.error);
      }
    });

    // Save
    document.getElementById("btnSave").addEventListener("click", async () => {
      await this.saveProjectDirect("Lưu thủ công từ thanh công cụ");
      alert("✅ Dự án đã được lưu an toàn vào project.json!");
    });

    // Export SRT & ASS
    document.getElementById("exportSRT").addEventListener("click", (e) => {
      e.preventDefault();
      this.exportSubtitles("srt");
    });
    document.getElementById("exportASS").addEventListener("click", (e) => {
      e.preventDefault();
      this.exportSubtitles("ass");
    });

    // Modal Xuất Video
    const renderModal = document.getElementById("renderModal");
    document.getElementById("btnRenderModal").addEventListener("click", () => {
      document.getElementById("renderProgressBox").style.display = "none";
      const btn = document.getElementById("btnStartRender");
      btn.disabled = false;
      btn.textContent = "Bắt đầu Xuất Video";
      renderModal.style.display = "flex";
    });
    document.getElementById("btnCloseRenderModal").addEventListener("click", () => {
      renderModal.style.display = "none";
    });

    document.getElementById("btnStartRender").addEventListener("click", () => {
      this.startRender();
    });

    // Shutdown
    document.getElementById("btnShutdown").addEventListener("click", async () => {
      if (confirm("Bạn có chắc muốn đóng phòng dựng tạm thời?")) {
        await fetch("/api/shutdown", { method: "POST" });
        document.body.innerHTML = `
          <div style="display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;gap:12px;">
            <h2>🛑 Phòng dựng đã tắt an toàn</h2>
            <p style="color:#94a3b8;">Bạn có thể đóng tab trình duyệt này.</p>
          </div>
        `;
      }
    });
  }

  async exportSubtitles(format) {
    try {
      const res = await fetch("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({}),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      const filePath = format === "srt" ? data.srt_path : data.ass_path;
      alert(`🎉 Đã xuất phụ đề ${format.toUpperCase()} thành công!\n👉 Vị trí: ${filePath}`);
    } catch (e) {
      alert("Lỗi xuất phụ đề: " + e.message);
    }
  }

  async startRender() {
    const btn = document.getElementById("btnStartRender");
    const progressBox = document.getElementById("renderProgressBox");
    const progressBar = document.getElementById("renderProgressBar");
    const progressLabel = document.getElementById("renderProgressLabel");

    btn.disabled = true;
    btn.textContent = "Đang xử lý...";
    progressBox.style.display = "block";
    progressBar.style.width = "0%";
    progressLabel.textContent = "Đang lưu cấu hình và chuẩn bị xuất video...";

    try {
      // 1. Lưu ngay lập tức toàn bộ trạng thái và style của project xuống server (flush)
      await this.saveProjectDirect("Lưu cấu hình trước khi xuất video", false);

      // 2. Gửi trực tiếp toàn bộ style hiện tại từ preview vào API render
      const res = await fetch("/api/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({
          style: Object.assign({}, this.project.style),
          output_dir: ""
        }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      // Bắt đầu poll tiến độ
      const timer = setInterval(async () => {
        try {
          const sRes = await fetch("/api/render-status");
          const sData = await sRes.json();

          if (sData.status === "rendering") {
            progressBar.style.width = `${sData.progress}%`;
            progressLabel.textContent = `Đang xuất video: ${sData.progress}%`;
          } else if (sData.status === "done") {
            clearInterval(timer);
            progressBar.style.width = "100%";
            progressLabel.textContent = `🎉 XUẤT VIDEO HOÀN TẤT 100%!`;
            btn.disabled = false;
            btn.textContent = "Bắt đầu Xuất Video";
            alert(`🎬 Xuất video có phụ đề thành công!\n👉 File MP4 đã lưu tại:\n${sData.output_path}`);
          } else if (sData.status === "error") {
            clearInterval(timer);
            progressLabel.textContent = `❌ Lỗi khi xuất video: ${sData.error}`;
            btn.disabled = false;
            btn.textContent = "Thử lại";
          }
        } catch (pollErr) {
          console.error("Lỗi poll status:", pollErr);
        }
      }, 800);
    } catch (err) {
      alert("Lỗi khi gọi xuất video: " + err.message);
      btn.disabled = false;
      btn.textContent = "Bắt đầu Xuất Video";
    }
  }

  /* ----------------------------------------------------
     AUTO-SAVE (DEBOUNCED)
  ---------------------------------------------------- */
  triggerAutoSave() {
    clearTimeout(this.saveTimeout);
    this.saveTimeout = setTimeout(() => {
      this.saveProjectDirect("Tự động lưu thay đổi", false);
    }, 600);
  }

  async saveProjectDirect(desc = "Cập nhật", makeSnapshot = false) {
    const payload = Object.assign({}, this.project);
    payload._make_snapshot = makeSnapshot;
    payload._description = desc;

    try {
      await fetch("/api/project", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody(payload),
      });
      this.updateRevisionUI();
    } catch (e) {
      console.warn("Lỗi auto-save:", e);
    }
  }

  bindTabs() {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

        btn.classList.add("active");
        const target = document.getElementById(btn.dataset.tab);
        if (target) target.classList.add("active");
      });
    });
  }

  bindKeyboardShortcuts() {
    window.addEventListener("keydown", (e) => {
      const activeTag = document.activeElement ? document.activeElement.tagName : "";
      const isInput = ["INPUT", "TEXTAREA"].includes(activeTag);

      // Space: Play/Pause (khi không ở ô nhập liệu)
      if (e.code === "Space" && !isInput) {
        e.preventDefault();
        const btnPlay = document.getElementById("btnPlayPause");
        btnPlay.click();
      }

      // Ctrl+Z / Cmd+Z: Undo
      if ((e.ctrlKey || e.metaKey) && e.code === "KeyZ" && !e.shiftKey) {
        e.preventDefault();
        document.getElementById("btnUndo").click();
      }

      // Ctrl+Y / Cmd+Shift+Z: Redo
      if ((e.ctrlKey && e.code === "KeyY") || ((e.ctrlKey || e.metaKey) && e.shiftKey && e.code === "KeyZ")) {
        e.preventDefault();
        document.getElementById("btnRedo").click();
      }

      // Ctrl+S / Cmd+S: Save
      if ((e.ctrlKey || e.metaKey) && e.code === "KeyS") {
        e.preventDefault();
        document.getElementById("btnSave").click();
      }
    });
  }

  formatTime(seconds) {
    const s = Math.max(0, seconds);
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    const ms = Math.floor((s - Math.floor(s)) * 10);
    return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}.${ms}`;
  }
}

function jsonBody(obj) {
  return JSON.stringify(obj);
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

function setTxt(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function bindColorSync(pickerId, textId, onChange) {
  const picker = document.getElementById(pickerId);
  const text = document.getElementById(textId);

  picker.addEventListener("input", (e) => {
    text.value = e.target.value.toUpperCase();
    onChange(e.target.value);
  });

  text.addEventListener("change", (e) => {
    let v = e.target.value.trim();
    if (!v.startsWith("#")) v = "#" + v;
    picker.value = v;
    onChange(v);
  });
}

function escapeHtml(str) {
  return (str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

window.addEventListener("DOMContentLoaded", () => {
  new SubtitleStudioApp();
});
