import os
import sys
import time
import argparse
import serial
import serial.tools.list_ports
import numpy as np
import cv2
from PIL import Image

# =====================================================
# DEFAULT SETTINGS
# =====================================================
DEFAULT_BAUD = 1000000
WIDTH = 160
HEIGHT = 120
BYTES_PER_PIXEL = 2
FRAME_SIZE = WIDTH * HEIGHT * BYTES_PER_PIXEL
DEFAULT_BACKEND_URL = "http://localhost:8000/api/inspection"


def auto_detect_port(preferred="COM5"):
    """Auto-detect Arduino / CH340 COM port."""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return preferred

    # 1. Look for known Arduino / CH340 signatures
    for p in ports:
        desc = (p.description or "").lower()
        if "ch340" in desc or "arduino" in desc or "usb-serial" in desc:
            return p.device

    # 2. Match preferred port if present
    for p in ports:
        if p.device.upper() == preferred.upper():
            return preferred

    # 3. Fallback to first available port
    return ports[0].device


def wait_for_handshake(ser, target=b"WAITING FOR C", timeout=15):
    """Wait for Arduino startup banner and ready token."""
    start = time.time()
    window = bytearray()
    while time.time() - start < timeout:
        b = ser.read(1)
        if not b:
            continue
        window += b
        if target in window:
            return True
        if len(window) > 500:
            window = window[-500:]
    return False


def request_and_read_frame(ser, timeout=10):
    """Send 'C' trigger, wait for 'FRM0', and receive 38400 bytes."""
    ser.write(b"C")
    ser.flush()

    # Find FRM0 header
    window = bytearray()
    start = time.time()
    found_frm0 = False
    while time.time() - start < timeout:
        b = ser.read(1)
        if not b:
            continue
        window += b
        if window.endswith(b"FRM0"):
            found_frm0 = True
            break
        if len(window) > 4:
            window = window[-4:]

    if not found_frm0:
        raise TimeoutError("Timeout waiting for 'FRM0' frame start marker.")

    # Read binary payload
    data = bytearray()
    start = time.time()
    while len(data) < FRAME_SIZE:
        remaining = FRAME_SIZE - len(data)
        chunk = ser.read(min(remaining, 2048))
        if not chunk:
            if time.time() - start > timeout:
                raise TimeoutError(f"Timeout during frame transfer ({len(data)}/{FRAME_SIZE} bytes).")
            continue
        data.extend(chunk)

    return bytes(data)


def compute_sharpness(gray_img):
    """Calculate focus / sharpness using Laplacian variance."""
    return float(cv2.Laplacian(gray_img, cv2.CV_64F).var())


def enhance_clarity(raw_bgr, rotate_180=True):
    """
    Apply multi-stage image enhancement tailored for corrosion inspection:
    1. Gray-World White Balance correction (removes CMOS green/cyan tint)
    2. LAB CLAHE contrast adjustment on Luminance (reveals rust & pitting texture)
    3. Bilateral Edge-Preserving Denoising (suppresses CMOS sensor noise)
    4. Unsharp Masking (crisp corrosion boundary definition)
    5. High-fidelity Lanczos 4x Upscaling (640x480 standard resolution)
    """
    # 1. White Balance Correction
    wb_float = raw_bgr.astype(np.float32)
    b_mean = np.mean(wb_float[:, :, 0])
    g_mean = np.mean(wb_float[:, :, 1])
    r_mean = np.mean(wb_float[:, :, 2])
    gray_mean = (b_mean + g_mean + r_mean) / 3.0

    if b_mean > 0 and g_mean > 0 and r_mean > 0:
        wb_float[:, :, 0] = np.clip(wb_float[:, :, 0] * (gray_mean / b_mean), 0, 255)
        wb_float[:, :, 1] = np.clip(wb_float[:, :, 1] * (gray_mean / g_mean), 0, 255)
        wb_float[:, :, 2] = np.clip(wb_float[:, :, 2] * (gray_mean / r_mean), 0, 255)
    balanced_bgr = wb_float.astype(np.uint8)

    # 2. CLAHE on Luminance
    lab = cv2.cvtColor(balanced_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    # 3. Bilateral Filter
    denoised = cv2.bilateralFilter(enhanced_bgr, d=5, sigmaColor=35, sigmaSpace=35)

    # 4. Unsharp Masking
    gaussian = cv2.GaussianBlur(denoised, (0, 0), 2.0)
    sharpened = cv2.addWeighted(denoised, 1.5, gaussian, -0.5, 0)

    # 5. Lanczos Upscaling to 640x480
    upscaled = cv2.resize(sharpened, (640, 480), interpolation=cv2.INTER_LANCZOS4)

    if rotate_180:
        upscaled = cv2.rotate(upscaled, cv2.ROTATE_180)

    return upscaled


def draw_focus_hud(display_img, score, best_score, frame_count):
    """Draw a rich heads-up display overlay on the live focus frame."""
    h, w = display_img.shape[:2]
    overlay = display_img.copy()

    # Top dark header bar
    cv2.rectangle(overlay, (0, 0), (w, 65), (20, 20, 20), -1)
    # Bottom dark footer bar
    cv2.rectangle(overlay, (0, h - 45), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, display_img, 0.25, 0, display_img)

    # Status color & text
    if score < 150:
        status_text = "BLURRY - Rotate lens"
        status_color = (60, 60, 240)  # Red
    elif score < 320:
        status_text = "FAIR - Keep adjusting"
        status_color = (0, 215, 255)  # Yellow
    else:
        status_text = "SHARP! IN FOCUS"
        status_color = (50, 220, 50)  # Green

    # Header text
    cv2.putText(display_img, f"OV7670 FOCUS ASSISTANT (MACRO 5-10cm)", (15, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(display_img, f"Frame #{frame_count:03d} | Sharpness: {score:5.1f} | Peak: {best_score:5.1f}", (15, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 220, 200), 1, cv2.LINE_AA)
    cv2.putText(display_img, status_text, (w - 220, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2, cv2.LINE_AA)

    # Bottom gauge bar
    bar_x, bar_y, bar_w, bar_h = 15, h - 35, w - 30, 12
    cv2.rectangle(display_img, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), 1)
    fill_w = int(np.clip((score / 600.0) * bar_w, 0, bar_w))
    cv2.rectangle(display_img, (bar_x + 1, bar_y + 1), (bar_x + fill_w, bar_y + bar_h - 1), status_color, -1)

    # Instructions text
    cv2.putText(display_img, "Unscrew lens counter-clockwise for 5-10cm | Press 'q' or 'ESC' to finish",
                (15, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)


def run_focus_assistant(ser, output_dir=None, rotate_180=True):
    """Live focus assistant mode: displays live video with HUD and tracks peak sharpness."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "captures")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 65)
    print("OV7670 LIVE FOCUS ASSISTANT (MACRO 5-10 CM)")
    print("=" * 65)
    print("OPTICAL FOCUS INSTRUCTIONS:")
    print("1. Place the camera 5-10 cm away from a textured object or metal.")
    print("2. OV7670 has a manual screw-thread lens barrel.")
    print("3. For macro (5-10 cm), gently UNSCREW the lens COUNTER-CLOCKWISE")
    print("   by about 1 to 2.5 full rotations.")
    print("4. Watch the live window and Sharpness Gauge.")
    print("5. When Sharpness turns GREEN ('SHARP!'), press 'q', 'ESC', or Ctrl+C.")
    print("=" * 65)

    window_name = "OV7670 Live Focus Assistant (5-10cm Macro)"
    has_gui = True
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    except Exception:
        has_gui = False
        print("[Notice: GUI window unavailable, running in terminal gauge mode]")

    frame_count = 0
    best_score = 0.0
    best_frame = None

    try:
        while True:
            frame_count += 1
            try:
                raw_bytes = request_and_read_frame(ser)
            except Exception as e:
                print(f"\nFrame {frame_count} read error: {e}. Retrying...")
                time.sleep(0.1)
                continue

            raw_arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((HEIGHT, WIDTH, 2))
            raw_bgr = cv2.cvtColor(raw_arr, cv2.COLOR_YUV2BGR_YUYV)
            gray = raw_arr[:, :, 0]
            score = compute_sharpness(gray)

            # High quality 640x480 preview
            preview = cv2.resize(raw_bgr, (640, 480), interpolation=cv2.INTER_LANCZOS4)
            if rotate_180:
                preview = cv2.rotate(preview, cv2.ROTATE_180)

            if score > best_score:
                best_score = score
                best_frame = preview.copy()

            # Terminal gauge
            bar_len = 20
            filled = min(bar_len, int((score / 500.0) * bar_len))
            bar = "█" * filled + "░" * (bar_len - filled)
            status = "BLURRY" if score < 150 else ("FAIR" if score < 320 else "SHARP!")
            print(f"\rFrame #{frame_count:03d} | Sharpness: {score:5.1f} (Peak: {best_score:5.1f}) [{bar}] {status}   ", end="", flush=True)

            if has_gui:
                draw_focus_hud(preview, score, best_score, frame_count)
                cv2.imshow(window_name, preview)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), 27, 32):  # 'q', ESC, or Space
                    print(f"\nExiting focus mode via user keypress ({key}).")
                    break

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n\nFocus assistant stopped by Ctrl+C.")
    finally:
        if has_gui:
            cv2.destroyAllWindows()

    print()
    print("=" * 65)
    print("FOCUS CALIBRATION RESULTS")
    print("=" * 65)
    print(f"Total Frames Analyzed : {frame_count}")
    print(f"Peak Sharpness Score  : {best_score:5.1f}")

    if best_frame is not None:
        save_path = os.path.join(output_dir, "ov7670_focus_calibrated_best.png")
        cv2.imwrite(save_path, best_frame)
        print(f"Saved Sharpest Frame  : {save_path}")

    if best_score < 150:
        print("\n[!] WARNING: Image is still blurry.")
        print("    Remember to unscrew the lens barrel counter-clockwise 1-2 full turns")
        print("    and ensure sufficient lighting on the object.")
    else:
        print("\n[✓] EXCELLENT: Camera is focused for macro inspection!")
    print("=" * 65)


def submit_to_backend(image_path, backend_url, device_id="arduino-ov7670"):
    """Submit the captured corrosion image to the FastAPI backend."""
    import requests

    print(f"\nSubmitting {image_path} to {backend_url}...")
    try:
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/png")}
            data = {"device_id": device_id}
            resp = requests.post(backend_url, files=files, data=data, timeout=30)

        if resp.status_code == 201:
            res = resp.json()
            print("=" * 60)
            print("INSPECTION PIPELINE RESULT")
            print("=" * 60)
            print(f"Inspection ID      : {res.get('inspection_id', 'N/A')}")
            print(f"Corrosion Detected : {'YES' if res.get('detected') else 'NO'}")
            print(f"Corrosion Severity : {res.get('severity', 'UNKNOWN').upper()}")
            print(f"Affected Area      : {res.get('affected_area', 0.0):.2f}%")
            print(f"Detections Count   : {len(res.get('detections', []))}")
            if res.get('detections'):
                for i, d in enumerate(res['detections'], 1):
                    cls_name = d.get('class', 'corrosion')
                    conf = d.get('confidence', 0.0) * 100
                    box = d.get('bounding_box', [])
                    print(f"  - Region {i}: {cls_name} ({conf:.1f}% confidence) Box: {box}")
            rec = res.get("recommendation", "")
            if rec:
                print(f"Recommendation     : {rec}")
            if res.get("annotated_image_url"):
                print(f"Annotated Image    : http://localhost:8000{res.get('annotated_image_url')}")
            print("=" * 60)
        else:
            print(f"Backend returned error {resp.status_code}: {resp.text}")
    except Exception as exc:
        print(f"Could not connect to backend: {exc}")
        print("Tip: Make sure backend is running (`uvicorn app.main:app --reload --port 8000`).")


def main():
    parser = argparse.ArgumentParser(description="OV7670 Image Capture & Corrosion Inspection CLI")
    parser.add_argument("--port", default=None, help="Serial COM port (default: auto-detected)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help=f"Serial baud rate (default: {DEFAULT_BAUD})")
    parser.add_argument("--focus", action="store_true", help="Launch live focus assistant mode")
    parser.add_argument("--inspect", action="store_true", help="Automatically submit captured image to FastAPI backend")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL, help=f"Backend inspection endpoint (default: {DEFAULT_BACKEND_URL})")
    parser.add_argument("--output-dir", default=os.path.join(os.path.dirname(__file__), "captures"), help="Folder to save images")
    parser.add_argument("--test-image", default=None, help="Bypass serial camera capture and simulate pipeline on an existing image file")
    parser.add_argument("--rotate-180", dest="rotate_180", action="store_true", default=True, help="Rotate image 180 degrees upright (default: True)")
    parser.add_argument("--no-rotate", dest="rotate_180", action="store_false", help="Disable 180 degree rotation")
    parser.add_argument("--no-show", action="store_true", help="Do not open preview popup")

    args = parser.parse_args()

    # ── Simulated Test Image Mode ────────────────────────────
    if args.test_image:
        if not os.path.exists(args.test_image):
            print(f"ERROR: Test image '{args.test_image}' does not exist.")
            sys.exit(1)

        print("=" * 60)
        print("SIMULATION MODE: Testing pipeline on local image")
        print(f"Input Image : {args.test_image}")
        print("=" * 60)

        test_bgr = cv2.imread(args.test_image)
        if test_bgr is None:
            print("ERROR: Could not decode test image.")
            sys.exit(1)

        gray = cv2.cvtColor(test_bgr, cv2.COLOR_BGR2GRAY)
        sharpness = compute_sharpness(gray)
        enhanced_img = enhance_clarity(test_bgr, rotate_180=False)

        os.makedirs(args.output_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        enhanced_path = os.path.join(args.output_dir, f"simulated_{timestamp}_enhanced.png")
        cv2.imwrite(enhanced_path, enhanced_img)

        print()
        print("=" * 60)
        print("SIMULATION SUMMARY")
        print("=" * 60)
        print(f"Sharpness Score : {sharpness:.1f}")
        print(f"Enhanced Image  : {enhanced_path}")
        print("=" * 60)

        if args.inspect:
            submit_to_backend(enhanced_path, args.backend_url)

        if not args.no_show:
            try:
                Image.open(enhanced_path).show()
            except Exception:
                pass
        return

    # Determine Port
    port = args.port or auto_detect_port()

    print("=" * 60)
    print("OV7670 HARDWARE CAMERA INTERFACE")
    print(f"Port       : {port}")
    print(f"Baud Rate  : {args.baud}")
    print(f"Resolution : {WIDTH}x{HEIGHT} YUV422")
    print("=" * 60)

    try:
        ser = serial.Serial(port, args.baud, timeout=12)
    except Exception as e:
        print(f"ERROR: Could not open port {port}: {e}")
        sys.exit(1)

    # Immediately reset buffer upon connect
    ser.reset_input_buffer()

    print(f"Opened {port}. Waiting for Arduino ready signal...")
    if not wait_for_handshake(ser, target=b"WAITING FOR C", timeout=12):
        print("ERROR: Arduino startup timeout. Make sure Arduino is connected and flashed.")
        ser.close()
        sys.exit(1)

    print("Arduino ready.")

    if args.focus:
        run_focus_assistant(ser, args.output_dir, rotate_180=args.rotate_180)
        ser.close()
        return

    # Single capture mode
    print("Triggering frame capture...")
    try:
        raw_bytes = request_and_read_frame(ser)
    except Exception as exc:
        print(f"ERROR: {exc}")
        ser.close()
        sys.exit(1)
    finally:
        ser.close()

    print(f"Successfully received {len(raw_bytes)} bytes.")

    # Output directory
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # 1. Parse YUYV buffer
    raw_arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((HEIGHT, WIDTH, 2))
    raw_bgr = cv2.cvtColor(raw_arr, cv2.COLOR_YUV2BGR_YUYV)
    gray = raw_arr[:, :, 0]

    # Calculate Sharpness
    sharpness = compute_sharpness(gray)

    # 2. Enhanced Image Processing
    enhanced_640x480 = enhance_clarity(raw_bgr, rotate_180=args.rotate_180)

    # 3. File Paths
    raw_gray_path = os.path.join(args.output_dir, f"ov7670_{timestamp}_160x120_raw.png")
    raw_color_path = os.path.join(args.output_dir, f"ov7670_{timestamp}_160x120_color.png")
    enhanced_path = os.path.join(args.output_dir, f"ov7670_{timestamp}_640x480_enhanced.png")

    cv2.imwrite(raw_gray_path, gray)
    cv2.imwrite(raw_color_path, raw_bgr)
    cv2.imwrite(enhanced_path, enhanced_640x480)

    print()
    print("=" * 60)
    print("CAPTURE SUMMARY")
    print("=" * 60)
    print(f"Focus Sharpness Score : {sharpness:.1f} {'(Needs Lens Adjustment)' if sharpness < 150 else '(Good Focus)'}")
    print(f"Raw Grayscale (160x120) : {raw_gray_path}")
    print(f"Raw Color (160x120)     : {raw_color_path}")
    print(f"Enhanced (640x480)      : {enhanced_path}")
    print("=" * 60)

    # 4. Optional backend inspection
    if args.inspect:
        submit_to_backend(enhanced_path, args.backend_url)

    # 5. Display preview
    if not args.no_show:
        try:
            im = Image.open(enhanced_path)
            im.show()
        except Exception:
            pass


if __name__ == "__main__":
    main()