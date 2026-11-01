#!/usr/bin/env python3
"""
AI Workforce — ChatGPT Browser Image Generator (scripts/chatgpt_image_generator.py)

Điều khiển trực tiếp tab https://chatgpt.com đang mở trên Google Chrome của macOS
thông qua AppleScript `execute javascript` (không cần mở cổng CDP hay đăng nhập lại).
Hỗ trợ:
  1. Gửi prompt tạo ảnh mới và tự động tải file ảnh gốc (1254x1254+) về máy.
  2. Hoặc `--extract-latest` để tải ngay ảnh vừa tạo gần nhất trên tab ChatGPT hiện tại.

Cách gọi:
  python3 scripts/chatgpt_image_generator.py \
      --prompt "Create a warm editorial illustration..." \
      --output ~/Downloads/AIWF_Output/my_image.png
"""
import argparse
import base64
import json
import subprocess
import sys
import time
from pathlib import Path


def run_chrome_js(js_code: str) -> str:
    """Thực thi JavaScript trên tab ChatGPT đang mở trong Google Chrome."""
    apple_script = """
    on run argv
        set jsCode to item 1 of argv
        tell application "Google Chrome"
            repeat with w in windows
                set tabIdx to 0
                repeat with t in tabs of w
                    set tabIdx to tabIdx + 1
                    if URL of t contains "chatgpt.com" then
                        set active tab index of w to tabIdx
                        return execute t javascript jsCode
                    end if
                end repeat
            end repeat
            return "ERR_NO_CHATGPT_TAB"
        end tell
    end run
    """
    r = subprocess.run(["osascript", "-", js_code], input=apple_script, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Lỗi thực thi AppleScript trên Chrome: {r.stderr.strip()}")
    out = r.stdout.strip()
    if out == "ERR_NO_CHATGPT_TAB":
        raise RuntimeError("Không tìm thấy tab https://chatgpt.com nào đang mở trên Google Chrome.")
    return out


SCAN_JS = """
(() => {
    const imgs = Array.from(document.querySelectorAll('img'));
    const seen = new Set();
    const cands = [];
    for (const img of imgs) {
        if (img.closest('[data-message-author-role="user"]') || img.closest('form')) continue;
        if ((img.alt || '') === 'User attachment') continue;
        const src = img.currentSrc || img.src || '';
        const w = img.naturalWidth || img.width || 0;
        const h = img.naturalHeight || img.height || 0;
        if (!src || seen.has(src) || src.includes('avatar') || src.includes('profile') || src.endsWith('.svg')) continue;
        if ((w >= 384 && h >= 384) || src.includes('oaiusercontent.com') || src.includes('estuary') || src.startsWith('blob:')) {
            seen.add(src);
            cands.push({
                src: src,
                alt: img.alt || '',
                w: w,
                h: h
            });
        }
    }
    const resBtns = Array.from(document.querySelectorAll('button[aria-label^="Open preview of "]')).map(b => {
        const label = b.getAttribute('aria-label') || '';
        return label.replace('Open preview of ', '').trim();
    }).filter(name => /\\.(png|jpg|jpeg|webp)$/i.test(name));
    const stopBtn = document.querySelector('[data-testid="stop-button"], button[aria-label*="Stop"], button[aria-label*="Dừng"]');
    return JSON.stringify({
        url: location.href,
        title: document.title,
        streaming: !!stopBtn,
        images: cands,
        resource_files: resBtns
    });
})()
"""


def download_image_from_tab(img_src: str, output_path: Path) -> dict:
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    src_json = json.dumps(img_src)
    start_fetch_js = f"""
    (() => {{
        window.__aiwf_img_status = 'LOADING';
        window.__aiwf_img_b64 = '';
        window.__aiwf_img_err = '';
        const targetSrc = {src_json};
        (async () => {{
            try {{
                const resp = await fetch(targetSrc, {{credentials: 'include'}});
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const blob = await resp.blob();
                const reader = new FileReader();
                reader.onloadend = () => {{
                    window.__aiwf_img_b64 = reader.result.split(',')[1];
                    window.__aiwf_img_status = 'DONE';
                }};
                reader.onerror = (e) => {{
                    window.__aiwf_img_err = String(e);
                    window.__aiwf_img_status = 'ERROR';
                }};
                reader.readAsDataURL(blob);
            }} catch (err) {{
                try {{
                    const domImg = Array.from(document.querySelectorAll('img')).find(i => (i.currentSrc || i.src) === targetSrc);
                    if (!domImg) throw err;
                    const c = document.createElement('canvas');
                    c.width = domImg.naturalWidth || domImg.width;
                    c.height = domImg.naturalHeight || domImg.height;
                    c.getContext('2d').drawImage(domImg, 0, 0);
                    window.__aiwf_img_b64 = c.toDataURL('image/png').split(',')[1];
                    window.__aiwf_img_status = 'DONE';
                }} catch (err2) {{
                    window.__aiwf_img_err = String(err) + ' / ' + String(err2);
                    window.__aiwf_img_status = 'ERROR';
                }}
            }}
        }})();
        return 'STARTED';
    }})()
    """
    run_chrome_js(start_fetch_js)

    for _ in range(40):
        time.sleep(0.5)
        st = run_chrome_js("window.__aiwf_img_status")
        if st == "DONE":
            break
        if st == "ERROR":
            err_msg = run_chrome_js("window.__aiwf_img_err")
            raise RuntimeError(f"Lỗi trích xuất file ảnh từ ChatGPT DOM: {err_msg}")
    else:
        raise RuntimeError("Quá thời gian trích xuất dữ liệu base64 của ảnh từ trình duyệt.")

    total_len = int(run_chrome_js("String(window.__aiwf_img_b64.length)"))
    chunk_size = 250000
    b64_parts = []
    for offset in range(0, total_len, chunk_size):
        part = run_chrome_js(f"window.__aiwf_img_b64.slice({offset}, {offset + chunk_size})")
        b64_parts.append(part)
    run_chrome_js("window.__aiwf_img_b64 = ''; 'CLEANED'")

    raw_bytes = base64.b64decode("".join(b64_parts))
    tmp_raw = output_path.with_name(output_path.stem + "_raw.bin")
    tmp_raw.write_bytes(raw_bytes)

    from PIL import Image

    im = Image.open(tmp_raw)
    if output_path.suffix.lower() in (".jpg", ".jpeg") and im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    im.save(output_path, quality=95)
    tmp_raw.unlink(missing_ok=True)

    return {
        "status": "SUCCESS",
        "output_path": str(output_path),
        "width": im.width,
        "height": im.height,
        "src": img_src,
    }


def extract_latest_images(output_path: Path) -> dict:
    state = json.loads(run_chrome_js(SCAN_JS))
    cands = [c for c in state.get("images", []) if c["w"] >= 512 and c["h"] >= 512]
    if not cands:
        raise RuntimeError("Không tìm thấy ảnh đã tạo nào (≥ 512x512) trên tab ChatGPT hiện tại.")
    saved = []
    for idx, c in enumerate(cands):
        out_i = output_path if idx == len(cands) - 1 else output_path.with_name(f"{output_path.stem}_v{idx+1}{output_path.suffix}")
        res = download_image_from_tab(c["src"], out_i)
        res["alt"] = c.get("alt", "")
        saved.append(res)
    return {
        "status": "SUCCESS",
        "primary_output": str(output_path.expanduser().resolve()),
        "all_extracted": saved,
        "chat_url": state.get("url"),
    }


def upload_ref_image_to_composer(img_path: Path) -> dict:
    """Đính kèm ảnh tham chiếu (reference image) trực tiếp vào ô chat của ChatGPT qua ClipboardEvent/FileInput."""
    img_path = img_path.expanduser().resolve()
    if not img_path.exists():
        raise FileNotFoundError(f"Không tìm thấy ảnh tham chiếu: {img_path}")
    b64_data = base64.b64encode(img_path.read_bytes()).decode("ascii")
    mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"

    # Truyền base64 theo từng mảnh nếu file lớn
    run_chrome_js("window.__aiwf_ref_b64 = ''; 'INIT'")
    chunk_size = 200000
    for offset in range(0, len(b64_data), chunk_size):
        chunk = json.dumps(b64_data[offset : offset + chunk_size])
        run_chrome_js(f"window.__aiwf_ref_b64 += {chunk}; 'OK'")

    fname_json = json.dumps(img_path.name)
    mime_json = json.dumps(mime)
    attach_js = f"""
    (() => {{
        const b64 = window.__aiwf_ref_b64 || '';
        window.__aiwf_ref_b64 = '';
        const bin = atob(b64);
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        const file = new File([arr], {fname_json}, {{type: {mime_json}}});
        const dt = new DataTransfer();
        dt.items.add(file);

        const editor = document.querySelector('div.ProseMirror[contenteditable="true"], #prompt-textarea');
        if (editor) {{
            editor.focus();
            const pasteEv = new ClipboardEvent('paste', {{
                bubbles: true,
                cancelable: true,
                clipboardData: dt
            }});
            editor.dispatchEvent(pasteEv);
            return JSON.stringify({{ok: true, via: 'paste', name: {fname_json}}});
        }}
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) {{
            fileInput.files = dt.files;
            fileInput.dispatchEvent(new Event('change', {{bubbles: true}}));
            return JSON.stringify({{ok: true, via: 'file_input', name: {fname_json}}});
        }}
        return JSON.stringify({{ok: false, error: 'No editor or file input'}});
    }})()
    """
    res = json.loads(run_chrome_js(attach_js))
    time.sleep(3.5)
    return res


def generate_image_via_chatgpt(
    prompt: str,
    output_path: Path,
    ref_images: list[Path] | None = None,
    timeout_sec: int = 210,
) -> dict:
    init_state = json.loads(run_chrome_js(SCAN_JS))
    before_srcs = {img["src"] for img in init_state.get("images", [])}
    print(f"🌐 Đã kết nối tab ChatGPT: {init_state.get('url')} (ảnh hiện có: {len(before_srcs)})", flush=True)

    if ref_images:
        for ref_img in ref_images:
            up_res = upload_ref_image_to_composer(ref_img)
            print(f"📎 Đã đính kèm ảnh mẫu tham chiếu: {ref_img.name} ({up_res})", flush=True)
        time.sleep(2.0)

    prompt_json = json.dumps(prompt)
    inject_js = f"""
    (() => {{
        const promptText = {prompt_json};
        const editor = document.querySelector('div.ProseMirror[contenteditable="true"], #prompt-textarea');
        if (!editor) return JSON.stringify({{ok: false, error: "Không tìm thấy ô nhập lệnh ProseMirror"}});
        editor.focus();
        document.execCommand('selectAll', false, null);
        const inserted = document.execCommand('insertText', false, promptText);
        if (!inserted || (editor.innerText || '').trim().length < 5) {{
            editor.innerHTML = '<p>' + promptText.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</p>';
            editor.dispatchEvent(new InputEvent('input', {{bubbles: true, inputType: 'insertText', data: promptText}}));
        }}
        return JSON.stringify({{ok: true, len: (editor.innerText || '').length}});
    }})()
    """
    inj_res = json.loads(run_chrome_js(inject_js))
    if not inj_res.get("ok"):
        raise RuntimeError(f"Không thể điền prompt vào ChatGPT: {inj_res}")

    time.sleep(1.5)

    # Chờ nút send không còn bị disabled (do đang upload ảnh mẫu)
    for _ in range(15):
        ready = run_chrome_js("""
        (() => {
            const sendBtn = document.querySelector('[data-testid="send-button"], button[aria-label="Send prompt"], button[aria-label*="Send"], button[aria-label*="Gửi"], form button[type="submit"]');
            return (sendBtn && !sendBtn.disabled) ? 'READY' : 'WAIT';
        })()
        """)
        if ready == "READY":
            break
        time.sleep(1.0)

    send_js = """
    (() => {
        const sendBtn = document.querySelector(
            '[data-testid="send-button"], button[aria-label="Send prompt"], button[aria-label*="Send"], button[aria-label*="Gửi"], form button[type="submit"]'
        );
        if (sendBtn && !sendBtn.disabled) {
            sendBtn.click();
            return JSON.stringify({sent: true, via: "button", aria: sendBtn.getAttribute("aria-label")});
        }
        const editor = document.querySelector('div.ProseMirror[contenteditable="true"], #prompt-textarea');
        if (editor) {
            const ev = new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true});
            editor.dispatchEvent(ev);
            return JSON.stringify({sent: true, via: "enter_key"});
        }
        return JSON.stringify({sent: false});
    })()
    """
    send_res = json.loads(run_chrome_js(send_js))
    print(f"🚀 Đã gửi prompt tạo ảnh lên ChatGPT ({send_res}), đang chờ kết xuất hình ảnh...", flush=True)

    start_ts = time.time()
    chosen_img = None
    stable_ticks = 0
    last_src = None

    while time.time() - start_ts < timeout_sec:
        time.sleep(3.5)
        state = json.loads(run_chrome_js(SCAN_JS))
        cands = state.get("images", [])
        new_cands = [c for c in cands if c["src"] not in before_srcs and c["w"] >= 512 and c["h"] >= 512]
        streaming = state.get("streaming", False)
        elapsed = int(time.time() - start_ts)
        print(f"   ⏳ [{elapsed}s] Đang tạo ảnh trên ChatGPT... (ảnh mới: {len(new_cands)}, streaming={streaming})", flush=True)

        if new_cands:
            cur_src = new_cands[-1]["src"]
            if cur_src == last_src:
                stable_ticks += 1
            else:
                last_src = cur_src
                stable_ticks = 1
            # Ready if either streaming finished OR high-res image (≥1024px) has been stable for ≥ 4 polls (~14s)
            if not streaming or (new_cands[-1]["w"] >= 1024 and stable_ticks >= 4):
                time.sleep(2.0)
                state2 = json.loads(run_chrome_js(SCAN_JS))
                new_cands2 = [c for c in state2.get("images", []) if c["src"] not in before_srcs and c["w"] >= 512 and c["h"] >= 512]
                if new_cands2:
                    chosen_img = new_cands2[-1]
                    break

    if not chosen_img:
        raise RuntimeError(f"Quá thời gian chờ ChatGPT tạo ảnh ({timeout_sec}s).")

    print(f"✅ Đã nhận ảnh từ ChatGPT ({chosen_img['w']}x{chosen_img['h']}), đang trích xuất dữ liệu ảnh...", flush=True)
    res = download_image_from_tab(chosen_img["src"], output_path)
    res["chat_url"] = init_state.get("url")
    return res


def main() -> int:
    parser = argparse.ArgumentParser(description="Điều khiển trình duyệt ChatGPT tạo ảnh minh họa cho Fanpage")
    parser.add_argument("--prompt", default="", help="Câu lệnh tạo ảnh gửi vào ChatGPT")
    parser.add_argument("--output", required=True, help="Đường dẫn lưu file ảnh đầu ra (.png/.jpg/.webp)")
    parser.add_argument(
        "--ref-image",
        action="append",
        default=[],
        help="Đường dẫn ảnh mẫu tham chiếu (có thể truyền nhiều lần) để đính kèm vào ChatGPT",
    )
    parser.add_argument("--extract-latest", action="store_true", help="Trích xuất ngay ảnh đã tạo gần nhất trên tab ChatGPT hiện tại")
    parser.add_argument("--timeout", type=int, default=210, help="Thời gian chờ tối đa (giây)")
    args = parser.parse_args()

    if args.extract_latest:
        res = extract_latest_images(Path(args.output))
    else:
        if not args.prompt:
            parser.error("Cần truyền --prompt hoặc --extract-latest")
        res = generate_image_via_chatgpt(
            prompt=args.prompt,
            output_path=Path(args.output),
            ref_images=[Path(p) for p in args.ref_image] if args.ref_image else None,
            timeout_sec=args.timeout,
        )
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
