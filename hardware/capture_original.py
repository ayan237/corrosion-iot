import serial
import time
from PIL import Image, ImageOps

# =====================================================
# SETTINGS
# =====================================================

PORT = "COM35"
BAUD = 1000000

WIDTH = 160
HEIGHT = 120

BYTES_PER_PIXEL = 2
FRAME_SIZE = WIDTH * HEIGHT * BYTES_PER_PIXEL


# =====================================================
# OPEN COM PORT
# =====================================================

print("==========================================")
print("OV7670 FINAL REAL IMAGE CAPTURE")
print("==========================================")
print()

print("Opening", PORT)

try:
    ser = serial.Serial(
        PORT,
        BAUD,
        timeout=15
    )
except Exception as e:
    print("ERROR:", e)
    raise SystemExit(1)

# Arduino resets after opening the port
time.sleep(3)

ser.reset_input_buffer()

print("Arduino connected.")


# =====================================================
# WAIT FOR READY
# =====================================================

print("Waiting for Arduino...")

window = bytearray()

target = b"WAITING FOR C"

while True:

    b = ser.read(1)

    if not b:
        print("ERROR: Arduino startup timeout.")
        ser.close()
        raise SystemExit(1)

    window += b

    if window.endswith(target):
        break

    if len(window) > 500:
        window = window[-500:]


print("Arduino ready.")


# =====================================================
# REQUEST FRAME
# =====================================================

print("Requesting image...")

ser.write(b"C")
ser.flush()


# =====================================================
# FIND FRM0
# =====================================================

print("Waiting for FRM0...")

window = bytearray()

while True:

    b = ser.read(1)

    if not b:
        print("ERROR: FRM0 timeout.")
        ser.close()
        raise SystemExit(1)

    window += b

    if window.endswith(b"FRM0"):
        break

    if len(window) > 4:
        window = window[-4:]


print("FRM0 received.")
print("Receiving 160 x 120 image...")
print()


# =====================================================
# RECEIVE EXACTLY 38400 BYTES
# =====================================================

data = bytearray()

last_report = -1

while len(data) < FRAME_SIZE:

    remaining = FRAME_SIZE - len(data)

    chunk = ser.read(
        min(remaining, 2048)
    )

    if not chunk:
        print("ERROR: Image reception timeout.")
        break

    data.extend(chunk)

    line = len(data) // (WIDTH * 2)

    if line != last_report:

        if line <= HEIGHT:
            print(
                "Received line",
                line,
                "/",
                HEIGHT
            )

        last_report = line


ser.close()


# =====================================================
# CHECK
# =====================================================

print()
print("------------------------------------------")
print("Received:", len(data))
print("Expected:", FRAME_SIZE)
print("------------------------------------------")

if len(data) != FRAME_SIZE:

    print("IMAGE CAPTURE FAILED")
    raise SystemExit(1)


# =====================================================
# EXTRACT Y
#
# YUYV:
#
# Y0 U Y1 V
#
# Y = actual luminance information.
# =====================================================

gray_pixels = []

for i in range(0, FRAME_SIZE, 2):

    gray_pixels.append(
        data[i]
    )


gray = Image.new(
    "L",
    (WIDTH, HEIGHT)
)

gray.putdata(gray_pixels)


# =====================================================
# SAVE RAW GRAYSCALE
# =====================================================

gray_name = "ov7670_REAL_160x120_GRAY.png"

gray.save(gray_name)


# =====================================================
# CONTRAST-ENHANCED GRAYSCALE
# =====================================================

enhanced = ImageOps.autocontrast(gray)

enhanced_name = "ov7670_REAL_160x120_ENHANCED.png"

enhanced.save(enhanced_name)


# =====================================================
# YUV422 -> RGB
# =====================================================

def clamp(v):

    v = int(v)

    if v < 0:
        return 0

    if v > 255:
        return 255

    return v


rgb_pixels = []

for i in range(0, FRAME_SIZE, 4):

    y0 = data[i]
    u  = data[i + 1]
    y1 = data[i + 2]
    v  = data[i + 3]

    uoff = u - 128
    voff = v - 128

    # Pixel 0
    r = clamp(y0 + 1.402 * voff)
    g = clamp(y0 - 0.344136 * uoff - 0.714136 * voff)
    b = clamp(y0 + 1.772 * uoff)

    rgb_pixels.append(
        (r, g, b)
    )

    # Pixel 1
    r = clamp(y1 + 1.402 * voff)
    g = clamp(y1 - 0.344136 * uoff - 0.714136 * voff)
    b = clamp(y1 + 1.772 * uoff)

    rgb_pixels.append(
        (r, g, b)
    )


color = Image.new(
    "RGB",
    (WIDTH, HEIGHT)
)

color.putdata(rgb_pixels)


# =====================================================
# SAVE COLOR
# =====================================================

color_name = "ov7670_REAL_160x120_COLOR.png"

color.save(color_name)


# =====================================================
# ENLARGE
# =====================================================

gray_large = enhanced.resize(
    (800, 600),
    Image.Resampling.NEAREST
)

gray_large_name = "ov7670_REAL_GRAY_LARGE.png"

gray_large.save(gray_large_name)


color_large = color.resize(
    (800, 600),
    Image.Resampling.NEAREST
)

color_large_name = "ov7670_REAL_COLOR_LARGE.png"

color_large.save(color_large_name)


# =====================================================
# DONE
# =====================================================

print()
print("==========================================")
print("IMAGE CAPTURE SUCCESSFUL")
print("==========================================")
print()
print("Camera      : OV7670")
print("Resolution  : 160 x 120")
print("Format      : YUV422")
print("Frame bytes :", len(data))
print()
print("Files:")
print(gray_name)
print(enhanced_name)
print(color_name)
print(gray_large_name)
print(color_large_name)
print()
print("==========================================")

try:
    gray_large.show()
except Exception:
    pass