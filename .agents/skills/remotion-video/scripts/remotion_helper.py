#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remotion_helper.py - Công cụ khởi tạo, kiểm toán tĩnh (Static QA Linter) và cầu nối thuyết minh
offline cho kỹ năng remotion-video (tuân thủ Luật R4 & R7).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

SHARED_DIR = Path(__file__).resolve().parents[2] / "_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

import bootstrap  # noqa: F401,E402
from output_manager import resolve_output_dir  # noqa: E402

ASPECT_DIMENSIONS: Dict[str, Tuple[int, int]] = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}


def scaffold_project(
    project_dir: Path,
    comp_id: str = "MainVideo",
    title: str = "AI Workforce Programmatic Video",
    aspect: str = "16:9",
    fps: int = 30,
    duration_sec: float = 15.0,
) -> Dict[str, Any]:
    """Khởi tạo bộ khung dự án Remotion 4.x + TypeScript + Zod chuẩn sản xuất."""
    project_dir = project_dir.expanduser().resolve()
    src_dir = project_dir / "src"
    utils_dir = src_dir / "utils"
    public_audio_dir = project_dir / "public" / "audio"
    utils_dir.mkdir(parents=True, exist_ok=True)
    public_audio_dir.mkdir(parents=True, exist_ok=True)

    width, height = ASPECT_DIMENSIONS.get(aspect, (1920, 1080))
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", comp_id) or "MainVideo"

    pkg_json = {
        "name": f"aiwf-remotion-{clean_id.lower()}",
        "version": "1.0.0",
        "private": True,
        "scripts": {
            # `remotion add zod` cài đúng bản zod mà phiên bản Remotion đang dùng yêu cầu
            # (đã kiểm chứng: Remotion 4 hiện tại yêu cầu zod 4.x, ghim 3.x sẽ bị `remotion versions` báo lệch).
            "setup": "npm install --no-audit --no-fund && npx remotion add zod && npx remotion versions",
            "studio": "remotion studio src/index.ts",
            "render": f"remotion render src/index.ts {clean_id} out/{clean_id}.mp4 --codec=h264",
            "still": f"remotion still src/index.ts {clean_id} out/preview.png --frame=45",
            "typecheck": "tsc --noEmit",
        },
        "dependencies": {
            "@remotion/captions": "^4.0.0",
            "@remotion/cli": "^4.0.0",
            "@remotion/layout-utils": "^4.0.0",
            "@remotion/motion-blur": "^4.0.0",
            "@remotion/transitions": "^4.0.0",
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "remotion": "^4.0.0",
            "zod": "^4.0.0",
        },
        "devDependencies": {
            "@types/react": "^18.3.3",
            "typescript": "^5.5.4",
        },
    }
    (project_dir / "package.json").write_text(
        json.dumps(pkg_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    tsconfig = {
        "compilerOptions": {
            "target": "ES2022",
            "module": "ESNext",
            "moduleResolution": "bundler",
            "jsx": "react-jsx",
            "strict": True,
            "noEmit": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True,
        },
        "include": ["src"],
    }
    (project_dir / "tsconfig.json").write_text(
        json.dumps(tsconfig, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    (project_dir / "remotion.config.ts").write_text(
        "import {Config} from '@remotion/cli/config';\n\n"
        "Config.setVideoImageFormat('jpeg');\n"
        "Config.setOverwriteOutput(true);\n",
        encoding="utf-8",
    )

    (src_dir / "index.ts").write_text(
        "import {registerRoot} from 'remotion';\n"
        "import {RemotionRoot} from './Root';\n\n"
        "registerRoot(RemotionRoot);\n",
        encoding="utf-8",
    )

    (utils_dir / "motion.ts").write_text(
        "import {Easing, interpolate} from 'remotion';\n\n"
        "/**\n"
        " * Nội suy kẹp biên an toàn mặc định (tránh vọt giá trị ngoài dải keyframe).\n"
        " */\n"
        "export function clampInterpolate(\n"
        "  input: number,\n"
        "  inputRange: readonly number[],\n"
        "  outputRange: readonly number[],\n"
        "  easing: (t: number) => number = Easing.out(Easing.cubic)\n"
        "): number {\n"
        "  return interpolate(input, inputRange, outputRange, {\n"
        "    easing,\n"
        "    extrapolateLeft: 'clamp',\n"
        "    extrapolateRight: 'clamp',\n"
        "  });\n"
        "}\n\n"
        "/**\n"
        " * Nội suy tỷ lệ phóng to/thu nhỏ theo thang logarit đều mắt (Perceptual Scale).\n"
        " */\n"
        "export function perceptualScale(startScale: number, endScale: number, progress: number): number {\n"
        "  const s0 = Math.max(0.0001, startScale);\n"
        "  const s1 = Math.max(0.0001, endScale);\n"
        "  const u = Math.max(0, Math.min(1, progress));\n"
        "  return s0 * Math.pow(s1 / s0, u);\n"
        "}\n\n"
        "/**\n"
        " * Ước lượng cỡ chữ tiêu đề tự động không tràn vùng an toàn 84% chiều rộng khung hình.\n"
        " */\n"
        "export function fitHeadlineFontSize(\n"
        "  text: string,\n"
        "  frameWidth: number,\n"
        "  baseFontSize = 72,\n"
        "  minFontSize = 28\n"
        "): number {\n"
        "  const safeWidth = frameWidth * 0.84;\n"
        "  const estimatedWidth = Math.max(1, text.length * baseFontSize * 0.56);\n"
        "  if (estimatedWidth <= safeWidth) {\n"
        "    return baseFontSize;\n"
        "  }\n"
        "  return Math.max(minFontSize, Math.floor(baseFontSize * (safeWidth / estimatedWidth)));\n"
        "}\n",
        encoding="utf-8",
    )

    per_scene = round(max(3.0, duration_sec / 3.0), 2)
    schema_ts = f"""import {{z}} from 'zod';

export const SceneItemSchema = z.object({{
  id: z.string(),
  tag: z.string(),
  headline: z.string(),
  highlightWord: z.string().optional(),
  subline: z.string(),
  durationSec: z.number().positive(),
  accentColor: z.string(),
  audioFile: z.string().optional(),
}});

export const VideoPropsSchema = z.object({{
  title: z.string(),
  fps: z.number().int().positive(),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  backgroundColor: z.string(),
  textColor: z.string(),
  scenes: z.array(SceneItemSchema).min(1),
}});

export type SceneItem = z.infer<typeof SceneItemSchema>;
export type VideoProps = z.infer<typeof VideoPropsSchema>;

export const defaultVideoProps: VideoProps = {{
  title: {json.dumps(title, ensure_ascii=False)},
  fps: {fps},
  width: {width},
  height: {height},
  backgroundColor: '#0B0F19',
  textColor: '#F8FAFC',
  scenes: [
    {{
      id: 'scene_01',
      tag: 'AI WORKFORCE REMOTION',
      headline: {json.dumps(title, ensure_ascii=False)},
      highlightWord: 'Remotion',
      subline: 'Chuyển động tất định theo từng khung hình với React và TypeScript',
      durationSec: {per_scene},
      accentColor: '#8B5CF6',
    }},
    {{
      id: 'scene_02',
      tag: 'CHUẨN HÓA BỐ CỤC',
      headline: 'Tự Động Co Chữ & Bảo Toàn Vùng An Toàn',
      highlightWord: 'An Toàn',
      subline: 'Tích hợp Perceptual Scale, Rough Highlight và thuyết minh giọng đọc Offline',
      durationSec: {per_scene},
      accentColor: '#06B6D4',
    }},
    {{
      id: 'scene_03',
      tag: 'SẴN SÀNG XUẤT BẢN',
      headline: 'Đồng Bộ 100% Quy Chuẩn Chất Lượng AIWF',
      highlightWord: '100%',
      subline: 'Kiểm định tĩnh tự động trước khi kết xuất MP4 H.264 sắc nét',
      durationSec: {per_scene},
      accentColor: '#10B981',
    }},
  ],
}};
"""
    (src_dir / "schema.ts").write_text(schema_ts, encoding="utf-8")

    main_video_tsx = """import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {SceneItem, VideoProps} from './schema';
import {clampInterpolate, fitHeadlineFontSize, perceptualScale} from './utils/motion';

const HighlightedHeadline: React.FC<{
  headline: string;
  highlightWord?: string;
  accentColor: string;
  textColor: string;
  fontSize: number;
}> = ({headline, highlightWord, accentColor, textColor, fontSize}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const highlightProgress = spring({
    frame,
    fps,
    config: {damping: 200},
    delay: Math.round(0.35 * fps),
    durationInFrames: Math.round(0.55 * fps),
  });

  if (!highlightWord || !headline.includes(highlightWord)) {
    return (
      <h1
        style={{
          fontSize,
          fontWeight: 800,
          color: textColor,
          margin: 0,
          lineHeight: 1.2,
          textAlign: 'center',
        }}
      >
        {headline}
      </h1>
    );
  }

  const idx = headline.indexOf(highlightWord);
  const before = headline.slice(0, idx);
  const after = headline.slice(idx + highlightWord.length);

  return (
    <h1
      style={{
        fontSize,
        fontWeight: 800,
        color: textColor,
        margin: 0,
        lineHeight: 1.2,
        textAlign: 'center',
      }}
    >
      {before}
      {/* margin âm bù đúng padding: vệt highlight rộng hơn chữ nhưng không đẩy dấu câu/khoảng trắng kề bên */}
      <span style={{position: 'relative', display: 'inline-block', padding: '0 0.12em', margin: '0 -0.12em'}}>
        <span
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: '0.06em',
            height: '0.38em',
            backgroundColor: accentColor,
            opacity: 0.38,
            borderRadius: 6,
            scale: `${highlightProgress} 1`,
            transformOrigin: 'left center',
            zIndex: 0,
          }}
        />
        <span style={{position: 'relative', zIndex: 1}}>{highlightWord}</span>
      </span>
      {after}
    </h1>
  );
};

const SceneCard: React.FC<{
  scene: SceneItem;
  backgroundColor: string;
  textColor: string;
}> = ({scene, backgroundColor, textColor}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const totalFrames = Math.max(1, Math.round(scene.durationSec * fps));

  const enter = spring({
    frame,
    fps,
    config: {damping: 200},
    durationInFrames: Math.round(0.65 * fps),
  });

  const exitOpacity = clampInterpolate(
    frame,
    [Math.max(0, totalFrames - Math.round(0.35 * fps)), totalFrames],
    [1, 0],
    Easing.in(Easing.quad)
  );

  const cardScale = perceptualScale(0.92, 1.0, enter);
  const translateY = clampInterpolate(enter, [0, 1], [36, 0], Easing.out(Easing.cubic));
  const subOpacity = clampInterpolate(frame, [0.25 * fps, 0.75 * fps], [0, 1]);
  const fontSize = fitHeadlineFontSize(scene.headline, width, Math.round(Math.min(width, height) * 0.064));

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        justifyContent: 'center',
        alignItems: 'center',
        padding: `${Math.round(height * 0.08)}px ${Math.round(width * 0.08)}px`,
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        opacity: exitOpacity,
      }}
    >
      {scene.audioFile ? <Audio src={staticFile(scene.audioFile)} /> : null}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 24,
          maxWidth: Math.round(width * 0.84),
          scale: String(cardScale),
          translate: `0px ${translateY}px`,
        }}
      >
        <div
          style={{
            padding: '8px 20px',
            borderRadius: 999,
            backgroundColor: `${scene.accentColor}22`,
            border: `1.5px solid ${scene.accentColor}`,
            color: scene.accentColor,
            fontSize: Math.max(16, Math.round(fontSize * 0.28)),
            fontWeight: 700,
            letterSpacing: '0.08em',
          }}
        >
          {scene.tag}
        </div>
        <HighlightedHeadline
          headline={scene.headline}
          highlightWord={scene.highlightWord}
          accentColor={scene.accentColor}
          textColor={textColor}
          fontSize={fontSize}
        />
        <p
          style={{
            fontSize: Math.max(20, Math.round(fontSize * 0.42)),
            color: '#CBD5E1',
            margin: 0,
            textAlign: 'center',
            lineHeight: 1.45,
            opacity: subOpacity,
            maxWidth: Math.round(width * 0.74),
          }}
        >
          {scene.subline}
        </p>
      </div>
    </AbsoluteFill>
  );
};

export const MainVideo: React.FC<VideoProps> = ({scenes, backgroundColor, textColor}) => {
  const {fps} = useVideoConfig();
  let cursorFrames = 0;

  return (
    <AbsoluteFill style={{backgroundColor}}>
      {scenes.map((scene) => {
        const durFrames = Math.max(1, Math.round(scene.durationSec * fps));
        const fromFrame = cursorFrames;
        cursorFrames += durFrames;
        return (
          <Sequence
            key={scene.id}
            from={fromFrame}
            durationInFrames={durFrames}
            premountFor={Math.round(0.5 * fps)}
          >
            <SceneCard
              scene={scene}
              backgroundColor={backgroundColor}
              textColor={textColor}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
"""
    (src_dir / "MainVideo.tsx").write_text(main_video_tsx, encoding="utf-8")

    root_tsx = f"""import React from 'react';
import {{Composition}} from 'remotion';
import {{MainVideo}} from './MainVideo';
import {{defaultVideoProps, SceneItem, VideoPropsSchema}} from './schema';

// Tổng frame = tổng frame ĐÃ LÀM TRÒN của từng cảnh (khớp đúng cách MainVideo xếp Sequence),
// tránh lệch 1-2 frame cuối do làm tròn tổng giây.
const totalFrames = (scenes: SceneItem[], fps: number): number =>
  Math.max(1, scenes.reduce((acc, s) => acc + Math.max(1, Math.round(s.durationSec * fps)), 0));

export const RemotionRoot: React.FC = () => {{
  return (
    <Composition
      id="{clean_id}"
      component={{MainVideo}}
      schema={{VideoPropsSchema}}
      defaultProps={{defaultVideoProps}}
      fps={{defaultVideoProps.fps}}
      width={{defaultVideoProps.width}}
      height={{defaultVideoProps.height}}
      durationInFrames={{totalFrames(defaultVideoProps.scenes, defaultVideoProps.fps)}}
      calculateMetadata={{async ({{props}}) => {{
        return {{
          fps: props.fps,
          width: props.width,
          height: props.height,
          durationInFrames: totalFrames(props.scenes, props.fps),
        }};
      }}}}
    />
  );
}};
"""
    (src_dir / "Root.tsx").write_text(root_tsx, encoding="utf-8")

    return {
        "status": "OK",
        "project_dir": str(project_dir),
        "composition_id": clean_id,
        "width": width,
        "height": height,
        "fps": fps,
        "files_created": [
            "package.json",
            "tsconfig.json",
            "remotion.config.ts",
            "src/index.ts",
            "src/Root.tsx",
            "src/schema.ts",
            "src/MainVideo.tsx",
            "src/utils/motion.ts",
        ],
    }


def lint_remotion_project(project_dir: Path) -> Dict[str, Any]:
    """
    Kiểm toán tĩnh mã nguồn Remotion (.tsx, .ts) phát hiện các vi phạm quy tắc tất định và hiển thị.
    """
    project_dir = project_dir.expanduser().resolve()
    src_dir = project_dir / "src" if (project_dir / "src").is_dir() else project_dir
    files = sorted(list(src_dir.rglob("*.tsx")) + list(src_dir.rglob("*.ts")))

    findings: List[Dict[str, Any]] = []
    if not files:
        findings.append({
            "level": "FAIL",
            "code": "NO_SOURCE_FILES",
            "file": str(project_dir),
            "message": "Không tìm thấy tệp .ts hoặc .tsx nào trong dự án.",
        })
        return {"passed": False, "fail_count": 1, "warn_count": 0, "files_checked": 0, "findings": findings}

    for fpath in files:
        rel = str(fpath.relative_to(project_dir)) if fpath.is_relative_to(project_dir) else str(fpath)
        content = fpath.read_text(encoding="utf-8", errors="replace")

        # 1. Cấm Math.random()
        if re.search(r"\bMath\.random\s*\(", content):
            findings.append({
                "level": "FAIL",
                "code": "NON_DETERMINISTIC_RANDOM",
                "file": rel,
                "message": "Phát hiện Math.random(). Bắt buộc dùng random(seed) từ 'remotion' để đảm bảo tính tất định.",
            })

        # 2. Cấm CSS transition / animation hoặc lớp Tailwind animate-*
        if re.search(r"\b(transition|animation)\s*:\s*['\"`]", content) or re.search(
            r"className\s*=\s*['\"`][^'\"`]*\b(animate-[a-z0-9-]+|transition-(all|transform|opacity))\b",
            content,
        ):
            findings.append({
                "level": "FAIL",
                "code": "FORBIDDEN_CSS_ANIMATION",
                "file": rel,
                "message": "Phát hiện CSS transition/animation hoặc Tailwind animate-*. Mọi chuyển động trong Remotion phải điều khiển qua useCurrentFrame().",
            })

        # 3. Cấm setTimeout / setInterval / requestAnimationFrame
        if re.search(r"\b(setTimeout|setInterval|requestAnimationFrame)\s*\(", content):
            findings.append({
                "level": "FAIL",
                "code": "FORBIDDEN_TIMER_API",
                "file": rel,
                "message": "Phát hiện setTimeout/setInterval/requestAnimationFrame. Dùng Sequence hoặc useCurrentFrame() thay thế.",
            })

        # 4. Cấm thẻ <img>, <video>, <audio> HTML thô
        if re.search(r"<(img|video|audio)\b", content):
            findings.append({
                "level": "FAIL",
                "code": "RAW_MEDIA_TAG",
                "file": rel,
                "message": "Phát hiện thẻ <img>/<video>/<audio> HTML thô. Bắt buộc dùng <Img>, <OffthreadVideo>, <Audio> từ 'remotion'.",
            })

        # 5. Kiểm tra interpolate() phải có extrapolateLeft / extrapolateRight
        for match in re.finditer(r"\binterpolate\s*\(([^;]{10,260})\)", content, flags=re.DOTALL):
            call_body = match.group(1)
            # Bỏ qua nếu đây là định nghĩa hàm bọc bên trong utils/motion.ts đã có extrapolateLeft
            if "extrapolateLeft" not in call_body or "extrapolateRight" not in call_body:
                findings.append({
                    "level": "WARN",
                    "code": "UNCLAMPED_INTERPOLATE",
                    "file": rel,
                    "message": "Lệnh gọi interpolate() thiếu extrapolateLeft/extrapolateRight: 'clamp' (hoặc hãy dùng clampInterpolate từ utils/motion.ts).",
                })

    fails = sum(1 for item in findings if item["level"] == "FAIL")
    warns = sum(1 for item in findings if item["level"] == "WARN")
    return {
        "passed": fails == 0,
        "fail_count": fails,
        "warn_count": warns,
        "files_checked": len(files),
        "findings": findings,
    }


def _wav_duration_seconds(path: Path) -> float:
    """Thời lượng WAV PCM bằng thư viện chuẩn `wave` (không phụ thuộc ffprobe); WAV không phải PCM thì dùng ffprobe."""
    import wave
    try:
        with wave.open(str(path), "rb") as w:
            frames, rate = w.getnframes(), w.getframerate()
        if rate > 0:
            return frames / float(rate)
    except (wave.Error, EOFError) as e:
        print(f"[remotion_helper] {path.name} không đọc được bằng wave ({e}); thử ffprobe", file=sys.stderr)
    from ffmpeg_tools import duration as ffprobe_duration
    return float(ffprobe_duration(str(path)))


def bridge_offline_audio(
    scenes_json_path: Path,
    project_dir: Path,
    lang: str = "vi",
    fps: int = 30,
) -> Dict[str, Any]:
    """
    Sinh file thuyết minh giọng đọc offline qua _shared/media/tts.py vào public/audio/
    và xuất src/audio-manifest.json với thời lượng chính xác từng cảnh.
    TTS chạy trong thư mục tạm (engine ghi file job cạnh WAV), chỉ WAV hoàn chỉnh được chuyển vào public/audio/
    để không lọt file rác vào bundle Remotion.
    """
    import shutil
    import tempfile
    from tts import synthesize_line

    scenes_data = json.loads(scenes_json_path.expanduser().resolve().read_text(encoding="utf-8"))
    if not isinstance(scenes_data, list):
        raise ValueError("File scenes_json phải là một mảng JSON các đối tượng {id, text}")

    project_dir = project_dir.expanduser().resolve()
    audio_dir = project_dir / "public" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    manifest: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="aiwf_remotion_tts_") as work:
        for idx, item in enumerate(scenes_data):
            if not isinstance(item, dict):
                raise ValueError(f"Phần tử thứ {idx} trong scenes_json không phải đối tượng {{id, text}}")
            scene_id = re.sub(r"[^A-Za-z0-9_-]", "_", str(item.get("id") or f"scene_{idx + 1:02d}"))
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            tmp_wav = Path(work) / f"{scene_id}.wav"
            # synthesize_line(text, output_path, lang=...) trả dict {success, error|output_path}, không ném lỗi
            res = synthesize_line(text, str(tmp_wav), lang=lang)
            if not res.get("success") or not tmp_wav.is_file():
                errors.append({"id": scene_id, "error": str(res.get("error") or "TTS không tạo được file WAV")})
                continue
            out_wav = audio_dir / f"{scene_id}.wav"
            shutil.move(str(tmp_wav), str(out_wav))
            dur_sec = round(_wav_duration_seconds(out_wav), 3)
            manifest.append({
                "id": scene_id,
                "text": text,
                "audioFile": f"audio/{scene_id}.wav",
                "durationSec": dur_sec,
                "durationInFrames": max(1, int(round(dur_sec * fps))),
            })

    manifest_path = project_dir / "src" / "audio-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "OK" if not errors else "PARTIAL_FAIL",
        "manifest_path": str(manifest_path),
        "scenes_synthesized": len(manifest),
        "errors": errors,
        "items": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AIWF Remotion Video Helper CLI")
    parser.add_argument("--scaffold", type=str, help="Đường dẫn thư mục khởi tạo dự án Remotion")
    parser.add_argument("--id", type=str, default="MainVideo", help="Composition ID")
    parser.add_argument("--title", type=str, default="AI Workforce Programmatic Video", help="Tiêu đề mặc định")
    parser.add_argument("--aspect", type=str, default="16:9", choices=list(ASPECT_DIMENSIONS.keys()))
    parser.add_argument("--fps", type=int, default=30, help="Số khung hình trên giây")
    parser.add_argument("--duration", type=float, default=15.0, help="Thời lượng mặc định (giây)")
    parser.add_argument("--lint", type=str, help="Đường dẫn thư mục dự án Remotion cần kiểm toán tĩnh")
    parser.add_argument("--bridge-audio", type=str, help="Đường dẫn file JSON lời thoại cần sinh TTS offline")
    parser.add_argument("--project-dir", type=str, help="Thư mục dự án Remotion đích khi dùng --bridge-audio")
    parser.add_argument("--lang", type=str, default="vi", help="Ngôn ngữ TTS (vi, en, ja)")
    parser.add_argument("--json", type=str, help="Đường dẫn lưu báo cáo JSON")

    args = parser.parse_args()

    if args.scaffold:
        target = Path(args.scaffold).expanduser()
        if not target.is_absolute():
            # Tên tương đối -> ~/Downloads/AIWF_Output/remotion-video/<tên> (Anti-Repo Bloat, Luật R1)
            target = resolve_output_dir("remotion-video", project_name=args.scaffold)
        res = scaffold_project(
            project_dir=target,
            comp_id=args.id,
            title=args.title,
            aspect=args.aspect,
            fps=args.fps,
            duration_sec=args.duration,
        )
        if args.json:
            out_json = Path(args.json).expanduser().resolve()
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if args.lint:
        report = lint_remotion_project(Path(args.lint))
        if args.json:
            out_json = Path(args.json).expanduser().resolve()
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(
            f"Remotion Static QA: {'PASS' if report['passed'] else 'FAIL'} "
            f"({report['files_checked']} files, {report['fail_count']} FAIL, {report['warn_count']} WARN)"
        )
        for item in report["findings"]:
            print(f"  [{item['level']}] {item['code']} ({item['file']}): {item['message']}")
        return 0 if report["passed"] else 1

    if args.bridge_audio:
        if not args.project_dir:
            print("Lỗi: Cần truyền --project-dir cùng với --bridge-audio", file=sys.stderr)
            return 2
        res = bridge_offline_audio(
            scenes_json_path=Path(args.bridge_audio),
            project_dir=Path(args.project_dir),
            lang=args.lang,
            fps=args.fps,
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if not res["errors"] else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
