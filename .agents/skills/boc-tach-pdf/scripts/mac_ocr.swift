import Foundation
import Vision
import Cocoa

let arguments = CommandLine.arguments
if arguments.count < 2 {
    print("Usage: swift mac_ocr.swift <processing_dir>")
    exit(1)
}

let processingDir = arguments[1]
let inputDir = "\(processingDir)/01.input"
let processDir = "\(processingDir)/02.process"

let fileManager = FileManager.default
guard let files = try? fileManager.contentsOfDirectory(atPath: inputDir) else {
    print("Error: Cannot read input directory at \(inputDir)")
    exit(1)
}

let pngFiles = files.filter { $0.hasSuffix(".png") }.sorted()
print("Found \(pngFiles.count) images to process.")

for pngFile in pngFiles {
    let mdFileName = "\(pngFile).md"
    let mdFilePath = "\(processDir)/\(mdFileName)"
    
    // Checkpoint: Skip if already processed
    if fileManager.fileExists(atPath: mdFilePath) {
        print("Skipping \(pngFile) (already processed)")
        continue
    }
    
    let imagePath = "\(inputDir)/\(pngFile)"
    guard let image = NSImage(contentsOfFile: imagePath),
          let tiffData = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiffData),
          let cgImage = bitmap.cgImage else {
        print("Error: Failed to load \(pngFile)")
        continue
    }
    
    var outputText = ""
    let semaphore = DispatchSemaphore(value: 0)
    
    let request = VNRecognizeTextRequest { request, error in
        defer { semaphore.signal() }
        if let error = error {
            print("OCR Error on \(pngFile): \(error.localizedDescription)")
            return
        }
        guard let observations = request.results as? [VNRecognizedTextObservation] else {
            return
        }
        
        let sortedObservations = observations.sorted { (obs1, obs2) -> Bool in
            let box1 = obs1.boundingBox
            let box2 = obs2.boundingBox
            if abs(box1.origin.y - box2.origin.y) < 0.03 {
                return box1.origin.x < box2.origin.x
            }
            return box1.origin.y > box2.origin.y
        }
        
        for observation in sortedObservations {
            guard let candidate = observation.topCandidates(1).first else { continue }
            outputText += candidate.string + "\n"
        }
    }
    
    request.recognitionLanguages = ["vi-VN", "en-US"]
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    
    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    do {
        try handler.perform([request])
        semaphore.wait()
        
        // Write text to md file
        try outputText.write(toFile: mdFilePath, atomically: true, encoding: .utf8)
        print("Processed \(pngFile) -> \(mdFileName)")
    } catch {
        print("Failed to perform OCR on \(pngFile): \(error.localizedDescription)")
    }
}
print("OCR completed successfully!")
