// mac_ocr.swift — Apple Vision OCR ENGINE cho bước ĐỐI CHIẾU (cross-check), KHÔNG thay thế bước OCR của Agent.
//
// Ghi JSON thô (text + toạ độ 4 góc + confidence) cho từng ảnh, chạy NHIỀU LƯỢT ngôn ngữ
// (mặc định: "vi-VN,en-US" và "ja-JP,en-US") để script Python chọn lượt phù hợp theo từng vùng chữ:
// Apple Vision KHÔNG đọc được tiếng Việt + tiếng Nhật trong cùng một lượt
// (lượt vi bỏ mất chữ Nhật, lượt ja làm rơi dấu tiếng Việt).
//
// KHÔNG BAO GIỜ ghi vào 02.process/page_*.png.md (đó là checkpoint OCR của Agent).
//
// Usage:
//   swift mac_ocr.swift <out_dir> <image1.png> [image2.png ...] [--passes "vi-VN,en-US;ja-JP,en-US"]
// Output: <out_dir>/<image_name>.vision.json
// Thường được gọi gián tiếp qua: python3 ocr_crosscheck.py <processing_dir>

import Foundation
import Vision
import AppKit

var args = Array(CommandLine.arguments.dropFirst())
var passesSpec = "vi-VN,en-US;ja-JP,en-US"
if let i = args.firstIndex(of: "--passes"), i + 1 < args.count {
    passesSpec = args[i + 1]
    args.removeSubrange(i...(i + 1))
}
if args.count < 2 {
    FileHandle.standardError.write("Usage: swift mac_ocr.swift <out_dir> <image.png>... [--passes \"vi-VN,en-US;ja-JP,en-US\"]\n".data(using: .utf8)!)
    exit(2)
}
let outDir = args[0]
let images = Array(args.dropFirst())
let passes: [[String]] = passesSpec.split(separator: ";").map { $0.split(separator: ",").map { String($0).trimmingCharacters(in: .whitespaces) } }

try? FileManager.default.createDirectory(atPath: outDir, withIntermediateDirectories: true)

// Ngôn ngữ được hỗ trợ trên máy này (macOS cũ có thể thiếu vi-VN)
var supported: [String] = []
do {
    let probe = VNRecognizeTextRequest()
    probe.recognitionLevel = .accurate
    supported = try probe.supportedRecognitionLanguages()
} catch {}

func pt(_ p: CGPoint, _ w: Int, _ h: Int) -> [Double] {
    // Vision: toạ độ chuẩn hoá, gốc DƯỚI-TRÁI. Đổi sang pixel, gốc TRÊN-TRÁI.
    return [Double(p.x) * Double(w), (1.0 - Double(p.y)) * Double(h)]
}

var failures = 0
for imagePath in images {
    guard let nsImage = NSImage(contentsOfFile: imagePath),
          let tiff = nsImage.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let cgImage = bitmap.cgImage else {
        FileHandle.standardError.write("ERROR: cannot load \(imagePath)\n".data(using: .utf8)!)
        failures += 1
        continue
    }
    let w = cgImage.width, h = cgImage.height
    var passResults: [[String: Any]] = []
    for langs in passes {
        // Apple đặt mã tiếng Việt là "vi-VT" (không phải "vi-VN"): khớp theo tiền tố ngôn ngữ.
        var usable: [String] = []
        var missing: [String] = []
        for l in langs {
            if supported.isEmpty || supported.contains(l) { usable.append(l); continue }
            let prefix = l.split(separator: "-").first.map(String.init) ?? l
            if let alt = supported.first(where: { $0.hasPrefix(prefix + "-") }) { usable.append(alt) } else { missing.append(l) }
        }
        var obsOut: [[String: Any]] = []
        var errText: String? = nil
        let request = VNRecognizeTextRequest { req, err in
            if let err = err { errText = err.localizedDescription; return }
            guard let obs = req.results as? [VNRecognizedTextObservation] else { return }
            for o in obs {
                guard let c = o.topCandidates(1).first else { continue }
                obsOut.append([
                    "text": c.string,
                    "confidence": Double(c.confidence),
                    "quad": [pt(o.topLeft, w, h), pt(o.topRight, w, h), pt(o.bottomRight, w, h), pt(o.bottomLeft, w, h)]
                ])
            }
        }
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = true
        if !usable.isEmpty { request.recognitionLanguages = usable }
        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        do { try handler.perform([request]) } catch { errText = error.localizedDescription }
        var entry: [String: Any] = ["languages": usable, "missing_languages": missing, "observations": obsOut]
        if let e = errText { entry["error"] = e }
        passResults.append(entry)
    }
    let result: [String: Any] = [
        "engine": "apple_vision",
        "image": imagePath,
        "width": w, "height": h,
        "supported_languages": supported,
        "passes": passResults
    ]
    let name = (imagePath as NSString).lastPathComponent
    let outPath = (outDir as NSString).appendingPathComponent("\(name).vision.json")
    do {
        let data = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted])
        try data.write(to: URL(fileURLWithPath: outPath))
        print("OK \(name) -> \(outPath)")
    } catch {
        FileHandle.standardError.write("ERROR: cannot write \(outPath): \(error)\n".data(using: .utf8)!)
        failures += 1
    }
}
exit(failures == 0 ? 0 : 1)
