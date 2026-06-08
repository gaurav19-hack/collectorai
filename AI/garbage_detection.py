"""
garbage_detection.py
--------------------
AI-powered garbage detection module using YOLOv8 and OpenCV.
Place this file at: CleanTrackAI/ai/garbage_detection.py
How it works:
1. Loads a YOLOv8 model (pretrained on COCO dataset)
2. Runs object detection on the uploaded image
3. Checks if any garbage-related objects are detected
4. Returns a result dictionary with detection status and confidence
"""
import cv2
import numpy as np
from pathlib import Path
# Garbage-related class labels in COCO dataset (used by default YOLOv8)
# We map known COCO object classes that represent waste/garbage
GARBAGE_CLASSES = [
    "bottle", "cup", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
    "backpack", "handbag", "suitcase", "frisbee", "sports ball",
    "chair", "couch", "potted plant", "dining table", "toilet",
    "vase", "scissors", "toothbrush"
]
# Extended garbage keywords for broader detection
GARBAGE_KEYWORDS = [
    "trash", "garbage", "waste", "litter", "rubbish", "debris",
    "junk", "refuse", "bottle", "bag", "paper", "can", "box",
    "pile", "heap", "dump", "dirt", "mess"
]
def load_model():
    """
    Load the YOLOv8 model.
    Falls back to a simple OpenCV-based heuristic if ultralytics is unavailable.
    """
    try:
        from ultralytics import YOLO
        # Use the nano model for fast inference; auto-downloads on first run
        model = YOLO("yolov8n.pt")
        return model, "yolo"
    except ImportError:
        print("[WARNING] ultralytics not installed. Using fallback heuristic detection.")
        return None, "fallback"
    except Exception as e:
        print(f"[WARNING] Could not load YOLO model: {e}. Using fallback heuristic.")
        return None, "fallback"
def fallback_detection(image_path: str) -> dict:
    """
    Fallback garbage detection using OpenCV image analysis heuristics.
    Analyzes color distribution and texture to estimate likelihood of garbage.
    
    This is used when YOLOv8 cannot be loaded.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {
                "detected": False,
                "confidence": 0.0,
                "method": "fallback",
                "label": "No Garbage Detected",
                "message": "Could not read the image file.",
                "objects": []
            }
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Calculate color statistics
        mean_saturation = np.mean(hsv[:, :, 1])
        mean_value = np.mean(hsv[:, :, 2])
        # Convert to grayscale for texture analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Calculate Laplacian variance (texture/edge complexity)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Heuristic scoring:
        # - Low saturation + high edge complexity often indicates mixed debris
        # - Very dark or very bright regions with high variance suggest waste piles
        score = 0.0
        if laplacian_var > 500:
            score += 0.3  # High texture complexity
        if mean_saturation < 80:
            score += 0.2  # Low color saturation (neutral tones common in waste)
        if mean_value < 100:
            score += 0.2  # Dark image regions
        # Check for brownish/grayish dominant colors (common in garbage)
        brown_mask = cv2.inRange(hsv, np.array([10, 20, 20]), np.array([30, 255, 200]))
        gray_mask = cv2.inRange(hsv, np.array([0, 0, 50]), np.array([180, 30, 200]))
        brown_ratio = np.sum(brown_mask > 0) / (img.shape[0] * img.shape[1])
        gray_ratio = np.sum(gray_mask > 0) / (img.shape[0] * img.shape[1])
        if brown_ratio > 0.15:
            score += 0.15
        if gray_ratio > 0.20:
            score += 0.15
        detected = score >= 0.4
        confidence = min(score, 1.0)
        return {
            "detected": detected,
            "confidence": round(confidence, 2),
            "method": "fallback_heuristic",
            "label": "Garbage Detected" if detected else "No Garbage Detected",
            "message": "Analyzed using image heuristics (YOLOv8 unavailable).",
            "objects": []
        }
    except Exception as e:
        return {
            "detected": False,
            "confidence": 0.0,
            "method": "fallback",
            "label": "Detection Error",
            "message": f"Error during fallback detection: {str(e)}",
            "objects": []
        }
def detect_garbage(image_path: str) -> dict:
    """
    Main garbage detection function.
    Args:
        image_path (str): Absolute or relative path to the uploaded image.
    Returns:
        dict: {
            "detected": bool,
            "confidence": float (0.0 - 1.0),
            "method": str,
            "label": str,
            "message": str,
            "objects": list of detected object names
        }
    """
    # Validate file exists
    if not Path(image_path).exists():
        return {
            "detected": False,
            "confidence": 0.0,
            "method": "none",
            "label": "File Not Found",
            "message": f"Image file not found: {image_path}",
            "objects": []
        }
    # Load model
    model, mode = load_model()
    if mode == "fallback" or model is None:
        return fallback_detection(image_path)
    try:
        # Run YOLOv8 inference
        results = model(image_path, verbose=False)
        detected_objects = []
        max_confidence = 0.0
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = model.names[class_id].lower()
                    detected_objects.append({
                        "name": class_name,
                        "confidence": round(confidence, 2)
                    })
                    # Check if detected object is garbage-related
                    is_garbage = any(
                        garbage_kw in class_name
                        for garbage_kw in GARBAGE_KEYWORDS
                    ) or class_name in GARBAGE_CLASSES
                    if is_garbage and confidence > max_confidence:
                        max_confidence = confidence
        # Determine if garbage is detected
        # A class match with confidence > 0.3 counts as garbage
        garbage_objects = [
            obj for obj in detected_objects
            if obj["name"] in GARBAGE_CLASSES or any(
                kw in obj["name"] for kw in GARBAGE_KEYWORDS
            )
        ]
        # If no specific garbage class, use overall detection as proxy
        # (presence of multiple scattered objects often indicates littering)
        all_object_names = [obj["name"] for obj in detected_objects]
        if not garbage_objects and len(detected_objects) >= 3:
            # Multiple objects detected — heuristic: possible garbage pile
            garbage_objects = detected_objects
            max_confidence = max(
                [obj["confidence"] for obj in detected_objects], default=0.0
            )
        detected = len(garbage_objects) > 0 and max_confidence >= 0.25
        return {
            "detected": detected,
            "confidence": round(max_confidence, 2) if detected else 0.0,
            "method": "yolov8",
            "label": "Garbage Detected" if detected else "No Garbage Detected",
            "message": (
                f"Detected {len(garbage_objects)} garbage-related object(s) with "
                f"max confidence {round(max_confidence * 100, 1)}%."
                if detected
                else "No garbage or waste objects detected in the image."
            ),
            "objects": all_object_names
        }
    except Exception as e:
        print(f"[ERROR] YOLO detection failed: {e}")
        # Fallback on YOLO error
        return fallback_detection(image_path)
# ─── Quick test (run this file directly) ────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python garbage_detection.py <image_path>")
        sys.exit(1)
    test_path = sys.argv[1]
    result = detect_garbage(test_path)
    print("\n=== Garbage Detection Result ===")
    for key, value in result.items():
        print(f"  {key}: {value}")
