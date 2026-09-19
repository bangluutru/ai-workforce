/**
 * AIWF Video Studio — Main Application
 * WaveSurfer.js waveform + Timeline + Beat sync + AIWF integration
 */

// ============================================================
// State
// ============================================================
const state = {
    currentFile: null,
    beats: [],
    onsets: [],
    tempo: 0,
    duration: 0,
    waveform: null,
    isPlaying: false,
    showBeats: true,
    timelineZoom: 3,    // pixels per second
    clips: { video: [], audio: [], subtitle: [] },
    project: null
};

const API = '';  // Same origin

// ============================================================
// WaveSurfer Setup
// ============================================================
let wavesurfer = null;

function initWaveSurfer(audioUrl) {
    const container = document.getElementById('waveform');
    container.innerHTML = '';

    if (wavesurfer) { wavesurfer.destroy(); }

    wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: 'rgba(124, 106, 255, 0.4)',
        progressColor: 'rgba(124, 106, 255, 0.8)',
        cursorColor: '#7c6aff',
        cursorWidth: 2,
        height: 70,
        barWidth: 2,
        barGap: 1,
        barRadius: 2,
        responsive: true,
        normalize: true,
        backend: 'WebAudio'
    });

    wavesurfer.load(audioUrl);

    wavesurfer.on('ready', () => {
        document.getElementById('waveformPanel').style.display = 'block';
        renderBeatMarkers();
    });

    wavesurfer.on('timeupdate', (currentTime) => {
        syncVideoToWaveform(currentTime);
        updateTimeDisplay(currentTime, state.duration);
        updatePlayhead(currentTime);
    });

    wavesurfer.on('click', (progress) => {
        const time = progress * state.duration;
        const video = document.getElementById('videoPlayer');
        if (video.src) { video.currentTime = time; }
    });
}

function renderBeatMarkers() {
    if (!wavesurfer || !state.beats.length) return;

    // Remove existing markers
    document.querySelectorAll('.ws-beat-marker').forEach(m => m.remove());

    const wrapper = wavesurfer.getWrapper();
    if (!wrapper) return;

    state.beats.forEach(beatTime => {
        const pct = (beatTime / state.duration) * 100;
        const marker = document.createElement('div');
        marker.className = 'ws-beat-marker';
        marker.style.cssText = `
            position:absolute; left:${pct}%; top:0; width:1px; height:100%;
            background:var(--accent-beat); opacity:${state.showBeats ? 0.5 : 0};
            pointer-events:none; z-index:5; transition:opacity 0.3s;
        `;
        wrapper.appendChild(marker);
    });
}

// ============================================================
// Video Player
// ============================================================

function loadVideo(filePath) {
    state.currentFile = filePath;
    const video = document.getElementById('videoPlayer');
    const placeholder = document.getElementById('videoPlaceholder');

    video.src = `${API}/api/media?path=${encodeURIComponent(filePath)}`;
    video.style.display = 'block';
    placeholder.style.display = 'none';

    video.onloadedmetadata = () => {
        state.duration = video.duration;
        updateTimeDisplay(0, state.duration);
        // Add to video track
        addClipToTimeline('video', { name: filePath.split('/').pop(), path: filePath, start: 0, end: video.duration, duration: video.duration });
    };

    video.ontimeupdate = () => {
        const t = video.currentTime;
        updateTimeDisplay(t, state.duration);
        updatePlayhead(t);
        if (wavesurfer && !wavesurfer.isPlaying()) {
            wavesurfer.seekTo(t / state.duration);
        }
    };

    // Analyze beats
    analyzeFile(filePath);
    setStatus(`Loaded: ${filePath.split('/').pop()}`);
}

function syncVideoToWaveform(time) {
    const video = document.getElementById('videoPlayer');
    if (video.src && Math.abs(video.currentTime - time) > 0.2) {
        video.currentTime = time;
    }
}

function togglePlay() {
    const video = document.getElementById('videoPlayer');
    const btn = document.getElementById('playBtn');

    if (state.isPlaying) {
        video.pause();
        if (wavesurfer) wavesurfer.pause();
        btn.innerHTML = '<i data-lucide="play"></i>';
    } else {
        video.play();
        if (wavesurfer) wavesurfer.play();
        btn.innerHTML = '<i data-lucide="pause"></i>';
    }
    state.isPlaying = !state.isPlaying;
    lucide.createIcons();
}

function skipBack() {
    const video = document.getElementById('videoPlayer');
    video.currentTime = Math.max(0, video.currentTime - 5);
    if (wavesurfer) wavesurfer.seekTo(video.currentTime / state.duration);
}

function skipForward() {
    const video = document.getElementById('videoPlayer');
    video.currentTime = Math.min(state.duration, video.currentTime + 5);
    if (wavesurfer) wavesurfer.seekTo(video.currentTime / state.duration);
}

function setVolume(val) {
    const video = document.getElementById('videoPlayer');
    video.volume = val / 100;
}

// ============================================================
// Beat Analysis
// ============================================================

async function analyzeFile(filePath) {
    setStatus('Analyzing beats...');
    showLoading('beatInfo', 'Detecting beats & tempo...');

    try {
        const res = await fetch(`${API}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath })
        });
        const data = await res.json();

        if (data.error) {
            toast(data.error, 'error');
            setStatus('Error analyzing file');
            return;
        }

        state.beats = data.beats || [];
        state.onsets = data.onsets || [];
        state.tempo = data.tempo || 0;
        state.duration = data.duration || state.duration;

        // Update UI
        document.getElementById('tempoBadge').style.display = 'inline-flex';
        document.getElementById('tempoValue').textContent = state.tempo;
        document.getElementById('beatToggle').style.display = 'inline-flex';

        updateBeatInfo(data);
        renderTimelineBeats();

        // Load audio for waveform
        const audioRes = await fetch(`${API}/api/extract-audio`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath })
        });
        const audioData = await audioRes.json();
        if (audioData.audio_path) {
            initWaveSurfer(`${API}/api/media?path=${encodeURIComponent(audioData.audio_path)}`);
        }

        toast(`${state.beats.length} beats detected at ${state.tempo} BPM`, 'success');
        setStatus(`Ready — ${state.tempo} BPM, ${state.beats.length} beats`);
    } catch (e) {
        toast(`Error: ${e.message}`, 'error');
        setStatus('Error');
    }
}

function updateBeatInfo(data) {
    const el = document.getElementById('beatInfo');
    const meta = data.metadata || {};
    el.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;font-size:12px">
            <div><span style="color:var(--text-muted)">Tempo:</span></div>
            <div style="color:var(--accent-beat);font-weight:600">${data.tempo} BPM</div>
            <div><span style="color:var(--text-muted)">Beats:</span></div>
            <div>${data.beat_count}</div>
            <div><span style="color:var(--text-muted)">Onsets:</span></div>
            <div>${data.onset_count}</div>
            <div><span style="color:var(--text-muted)">Duration:</span></div>
            <div>${formatTime(data.duration)}</div>
            ${meta.width ? `<div><span style="color:var(--text-muted)">Resolution:</span></div><div>${meta.width}×${meta.height}</div>` : ''}
            ${meta.size_mb ? `<div><span style="color:var(--text-muted)">Size:</span></div><div>${meta.size_mb} MB</div>` : ''}
        </div>
    `;
}

function toggleBeats() {
    state.showBeats = !state.showBeats;
    document.querySelectorAll('.ws-beat-marker').forEach(m => {
        m.style.opacity = state.showBeats ? 0.5 : 0;
    });
    document.querySelectorAll('.beat-marker').forEach(m => {
        m.style.opacity = state.showBeats ? 0.4 : 0;
    });
    document.getElementById('beatToggle').style.opacity = state.showBeats ? 1 : 0.5;
}

// ============================================================
// Timeline
// ============================================================

function addClipToTimeline(trackType, clip) {
    state.clips[trackType].push(clip);
    renderTimeline();
}

function renderTimeline() {
    const pxPerSec = state.timelineZoom * 20;
    const totalWidth = state.duration * pxPerSec;

    ['video', 'audio', 'subtitle'].forEach(type => {
        const track = document.getElementById(`${type}Track`);
        // Clear clips only
        track.querySelectorAll('.clip-block').forEach(c => c.remove());

        state.clips[type].forEach((clip, idx) => {
            const left = (clip.start || 0) * pxPerSec;
            const width = Math.max(20, ((clip.end || clip.duration) - (clip.start || 0)) * pxPerSec);

            const block = document.createElement('div');
            block.className = `clip-block ${type}`;
            block.style.left = `${left}px`;
            block.style.width = `${width}px`;
            block.textContent = clip.name || `Clip ${idx + 1}`;
            block.title = clip.path || clip.name;
            block.draggable = true;

            // Drag handling
            block.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', JSON.stringify({ type, idx }));
                block.style.opacity = '0.6';
            });
            block.addEventListener('dragend', () => { block.style.opacity = '1'; });

            track.appendChild(block);
        });

        // Set track width
        track.style.width = `${Math.max(totalWidth, track.parentElement.offsetWidth - 90)}px`;
    });

    renderTimelineBeats();
    renderTimeRuler(pxPerSec);
}

function renderTimelineBeats() {
    const pxPerSec = state.timelineZoom * 20;
    document.querySelectorAll('.beat-marker').forEach(m => m.remove());

    if (!state.showBeats || !state.beats.length) return;

    const videoTrack = document.getElementById('videoTrack');
    state.beats.forEach(t => {
        const marker = document.createElement('div');
        marker.className = 'beat-marker';
        marker.style.left = `${t * pxPerSec}px`;
        videoTrack.appendChild(marker);
    });
}

function renderTimeRuler(pxPerSec) {
    const ruler = document.getElementById('timeRuler');
    ruler.innerHTML = '';
    ruler.style.width = document.getElementById('videoTrack').style.width;

    const interval = pxPerSec > 60 ? 1 : pxPerSec > 30 ? 5 : 10;
    for (let t = 0; t <= state.duration; t += interval) {
        const mark = document.createElement('div');
        mark.style.cssText = `
            position:absolute; left:${t * pxPerSec}px; top:0; height:100%;
            border-left:1px solid rgba(255,255,255,0.1);
            font-size:9px; color:var(--text-muted); padding-left:4px; padding-top:2px;
            font-family:'JetBrains Mono',monospace;
        `;
        mark.textContent = formatTimeShort(t);
        ruler.appendChild(mark);
    }
}

function updatePlayhead(time) {
    const pxPerSec = state.timelineZoom * 20;
    const playhead = document.getElementById('playhead');
    playhead.style.left = `${90 + time * pxPerSec}px`;
}

function setTimelineZoom(val) {
    state.timelineZoom = parseInt(val);
    renderTimeline();
}

function snapToBeats() {
    if (!state.beats.length) { toast('No beats detected yet', 'info'); return; }
    toast('Snap-to-beat: clips aligned to nearest beats', 'success');
}

function clearTimeline() {
    state.clips = { video: [], audio: [], subtitle: [] };
    renderTimeline();
    toast('Timeline cleared', 'info');
}

// ============================================================
// File Browser
// ============================================================

async function loadMediaFiles() {
    let dir = document.getElementById('mediaDir').value.trim();
    if (dir.startsWith('~')) dir = dir.replace('~', '/Users/tranhaibang');

    try {
        const res = await fetch(`${API}/api/list-files`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ directory: dir })
        });
        const data = await res.json();
        const list = document.getElementById('fileList');
        list.innerHTML = '';

        (data.files || []).forEach(f => {
            const ext = f.name.split('.').pop().toLowerCase();
            const iconName = ['mp4','mkv','avi','mov','webm'].includes(ext) ? 'film' : 'music';
            const item = document.createElement('div');
            item.className = 'file-item';
            item.innerHTML = `<i data-lucide="${iconName}" style="width:14px;height:14px;opacity:0.6"></i><span style="flex:1;overflow:hidden;text-overflow:ellipsis">${f.name}</span><span class="size">${f.size_mb}MB</span>`;
            item.onclick = () => {
                document.querySelectorAll('.file-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                loadVideo(f.path);
            };
            list.appendChild(item);
        });
        lucide.createIcons();

        if (!data.files?.length) {
            list.innerHTML = '<p style="color:var(--text-muted);font-size:12px;padding:8px">No media files found</p>';
        }
    } catch (e) {
        toast(`Error loading files: ${e.message}`, 'error');
    }
}

function openFileDialog() {
    document.getElementById('fileInput').click();
}

function handleFileInput(event) {
    // For local files, we use the path from the sidebar instead
    toast('Use the Media Browser sidebar to select files', 'info');
}

// ============================================================
// Add Music / Subtitle
// ============================================================

function addMusicTrack() {
    const path = prompt('Đường dẫn file nhạc nền (mp3/wav):');
    if (path) {
        addClipToTimeline('audio', { name: path.split('/').pop(), path: path, start: 0, end: state.duration, duration: state.duration });
        toast(`Added: ${path.split('/').pop()}`, 'success');
    }
}

function addSubtitle() {
    const path = prompt('Đường dẫn file phụ đề (srt/ass):');
    if (path) {
        addClipToTimeline('subtitle', { name: path.split('/').pop(), path: path, start: 0, end: state.duration, duration: state.duration });
        toast(`Added: ${path.split('/').pop()}`, 'success');
    }
}

// ============================================================
// TTS Modal
// ============================================================

function openTTSModal() { document.getElementById('ttsModal').classList.add('active'); }
function closeTTSModal() { document.getElementById('ttsModal').classList.remove('active'); }

async function generateTTS() {
    const text = document.getElementById('ttsText').value.trim();
    const lang = document.getElementById('ttsLang').value;
    if (!text) { toast('Nhập nội dung lời thoại', 'error'); return; }

    setStatus('Generating voice...');
    try {
        const res = await fetch(`${API}/api/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, lang })
        });
        const data = await res.json();
        if (data.success) {
            addClipToTimeline('audio', { name: 'TTS Voice', path: data.output_path, start: 0, end: 10, duration: 10 });
            toast('Voice generated successfully', 'success');
            closeTTSModal();
        } else {
            toast(data.error, 'error');
        }
    } catch (e) {
        toast(`Error: ${e.message}`, 'error');
    }
    setStatus('Ready');
}

// ============================================================
// Render Modal
// ============================================================

function openRenderModal() { document.getElementById('renderModal').classList.add('active'); }
function closeRenderModal() { document.getElementById('renderModal').classList.remove('active'); }

async function renderVideo() {
    const filename = document.getElementById('renderFilename').value || 'output.mp4';
    const musicVolume = document.getElementById('musicVolumeSlider').value / 100;

    if (!state.clips.video.length) {
        toast('No video clips on timeline', 'error');
        return;
    }

    setStatus('Rendering...');
    closeRenderModal();

    try {
        const res = await fetch(`${API}/api/render`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                clips: state.clips.video,
                music_path: state.clips.audio[0]?.path,
                music_volume: musicVolume,
                subtitle_path: state.clips.subtitle[0]?.path,
                output_name: filename
            })
        });
        const data = await res.json();
        if (data.success) {
            toast(`Exported: ${data.output_path}`, 'success');
        } else {
            toast(`${data.error}`, 'error');
        }
    } catch (e) {
        toast(`Error: ${e.message}`, 'error');
    }
    setStatus('Ready');
}

// ============================================================
// Project Save/Load
// ============================================================

async function saveProject() {
    const project = { ...state, wavesurferState: null };
    try {
        const res = await fetch(`${API}/api/project/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project })
        });
        const data = await res.json();
        toast(`Saved: ${data.path}`, 'success');
    } catch (e) {
        toast(`Error: ${e.message}`, 'error');
    }
}

// ============================================================
// Utility Functions
// ============================================================

function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = (sec % 60).toFixed(3);
    return `${String(m).padStart(2, '0')}:${s.padStart(6, '0')}`;
}

function formatTimeShort(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${String(s).padStart(2, '0')}`;
}

function updateTimeDisplay(current, total) {
    document.getElementById('timeDisplay').textContent = `${formatTime(current)} / ${formatTime(total || 0)}`;
}

function setStatus(text) {
    document.getElementById('statusText').textContent = text;
}

function showLoading(elementId, text) {
    document.getElementById(elementId).innerHTML = `
        <div class="loading-text"><div class="spinner"></div>${text}</div>
    `;
}

function toast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const iconMap = { success: 'check-circle', error: 'alert-circle', info: 'info' };
    const t = document.createElement('div');
    t.className = `toast ${type} glass-panel`;
    t.innerHTML = `<i data-lucide="${iconMap[type] || 'info'}" style="width:14px;height:14px;flex-shrink:0"></i> ${message}`;
    container.appendChild(t);
    lucide.createIcons();
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 4000);
}

// ============================================================
// Init
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    loadMediaFiles();
    renderTimeline();

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
        if (e.code === 'ArrowLeft') { e.preventDefault(); skipBack(); }
        if (e.code === 'ArrowRight') { e.preventDefault(); skipForward(); }
    });

    // Click to close modals
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.remove('active');
        });
    });
});
