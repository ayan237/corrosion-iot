# Hardware Module: OV7670 Camera & Arduino Integration

This directory contains the firmware, capture scripts, and enhancement pipeline for the **OV7670 Camera Module (No-FIFO)** interfaced with an **Arduino Uno (ATmega328P)**.

---

## 📌 Pinout & Wiring Configuration

Connect the OV7670 camera module to the Arduino Uno pins as follows:

| OV7670 Pin | Arduino Pin | Description |
|:---|:---|:---|
| **3.3V / VCC** | **3.3V** | Sensor Power (⚠️ Do NOT connect to 5V!) |
| **GND** | **GND** | Ground reference |
| **D0** | **A0 (PC0)** | Camera Data Bit 0 |
| **D1** | **A1 (PC1)** | Camera Data Bit 1 |
| **D2** | **A2 (PC2)** | Camera Data Bit 2 |
| **D3** | **A3 (PC3)** | Camera Data Bit 3 |
| **D4** | **D4 (PD4)** | Camera Data Bit 4 |
| **D5** | **D5 (PD5)** | Camera Data Bit 5 |
| **D6** | **D6 (PD6)** | Camera Data Bit 6 |
| **D7** | **D7 (PD7)** | Camera Data Bit 7 |
| **VSYNC** | **D3 (PD3)** | Vertical Synchronization Pulse |
| **HREF** | **D10 (PB2)** | Horizontal Reference |
| **PCLK** | **D12 (PB4)** | Pixel Clock Output |
| **XCLK** | **D11 (PB3)** | 8 MHz Master Clock Input (Timer2 PWM) |
| **SIOD (SDA)** | **A4 (PC4)** | I2C / SCCB Data (4.7kΩ pullup to 3.3V recommended) |
| **SIOC (SCL)** | **A5 (PC5)** | I2C / SCCB Clock (4.7kΩ pullup to 3.3V recommended) |
| **RESET** | **3.3V** | Active Low Reset (Tie HIGH) |
| **PWDN** | **GND** | Power Down Mode (Tie LOW) |

---

## 🚀 Quick Start Guide

### 1. Requirements
Ensure the backend virtual environment is active or dependencies are installed:
```powershell
pip install pyserial opencv-python pillow numpy requests
```

### 2. Capture an Image
Run the capture script. The COM port (`COM5` / `CH340`) will be **auto-detected automatically**:
```powershell
# Using backend Python environment
..\backend\venv\Scripts\python.exe capture_final.py
```
This saves three versions in `hardware/captures/`:
1. `ov7670_<timestamp>_160x120_raw.png`: Raw monochrome sensor data
2. `ov7670_<timestamp>_160x120_color.png`: Unprocessed YUV422 color
3. `ov7670_<timestamp>_640x480_enhanced.png`: Multi-stage clarity-enhanced image

---

## 🔍 How to Improve Image Clarity

### Step 1: Manually Focus the Camera Lens (Most Important!)
The OV7670 features a **manual screw-thread lens barrel**. Modules almost always arrive completely unfocused from the factory.
Run the live Focus Assistant:
```powershell
..\backend\venv\Scripts\python.exe capture_final.py --focus
```
* Gently twist the circular camera lens barrel clockwise or counter-clockwise with your fingers.
* Watch the **Sharpness Score** gauge on the screen in real time.
* When the score transitions to **`SHARP!`** (>300), press `Ctrl+C` to lock focus.

### Step 2: Flash the Enhanced Firmware
Open the Arduino IDE (`arduino-ide_2.3.10_Windows_64bit.exe`) and flash:
* `hardware/arduino_firmware/ov7670_enhanced.ino`

**Key firmware improvements:**
- **Edge Enhancement**: Enables DSP sharpening registers (`0x3F = 0x08`, `COM16 = 0x38`) to crisply define corrosion boundaries.
- **Averaged Downsampling**: Uses smoothing filter (`0x72 = 0x11`) instead of harsh truncation to eliminate jagged pixel aliasing.
- **Auto UV Saturation (`0xC8`)**: Removes the CMOS green tint and restores natural metal/rust color tones.
- **Denoise Filter (`0x4C = 0x04`)**: Dampens high-frequency CMOS sensor grain.

### Step 3: Proper Inspection Lighting
* The OV7670 sensor performs best under bright, even white lighting.
* Avoid backlighting or pointing directly into bright light bulbs (which causes AGC blowout).
* Position an external white LED or work lamp ~15–30 cm above the metal surface.

---

## 🤖 End-to-End AI Inspection Integration

You can capture a photo and send it directly into the AI Corrosion Inspection pipeline in one command:
```powershell
..\backend\venv\Scripts\python.exe capture_final.py --inspect
```
This automatically:
1. Captures the frame from the camera.
2. Applies color balancing, CLAHE contrast enhancement, and Lanczos upscaling.
3. Submits the photo to `http://localhost:8000/api/inspection`.
4. Runs YOLO corrosion detection and severity analysis.
5. Displays the corrosion percentage and engineering recommendations right in the terminal!
