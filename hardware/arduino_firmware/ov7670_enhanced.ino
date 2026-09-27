/*
  ============================================================
  OV7670 FINAL REAL IMAGE CAPTURE
  Arduino UNO / UNO SMD
  OV7670 NO-FIFO
  160 x 120 YUV422
  ============================================================

  YOUR WIRING

  OV7670 D0 -> A0
  OV7670 D1 -> A1
  OV7670 D2 -> A2
  OV7670 D3 -> A3
  OV7670 D4 -> D4
  OV7670 D5 -> D5
  OV7670 D6 -> D6
  OV7670 D7 -> D7

  OV7670 VSYNC -> D3
  OV7670 HREF  -> D10
  OV7670 XCLK  -> D11
  OV7670 PCLK  -> D12

  OV7670 SDA -> A4
  OV7670 SCL -> A5

  OV7670 RESET -> 3.3V
  OV7670 PWDN  -> GND

  ============================================================
*/

#define F_CPU 16000000UL

#include <Arduino.h>
#include <stdint.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>
#include <util/twi.h>
#include <util/delay.h>


// ============================================================
// CAMERA
// ============================================================

#define OV7670_ADDR 0x21

#define WIDTH  160
#define HEIGHT 120

#define BYTES_PER_LINE 320


// ============================================================
// REGISTER DEFINITIONS
// ============================================================

#define REG_GAIN       0x00
#define REG_BLUE       0x01
#define REG_RED        0x02
#define REG_VREF       0x03
#define REG_COM1       0x04

#define REG_COM3       0x0C
#define REG_COM4       0x0D
#define REG_COM5       0x0E
#define REG_COM6       0x0F

#define REG_CLKRC      0x11
#define REG_COM7       0x12
#define REG_COM8       0x13
#define REG_COM9       0x14
#define REG_COM10      0x15

#define REG_HSTART     0x17
#define REG_HSTOP      0x18
#define REG_VSTART     0x19
#define REG_VSTOP      0x1A

#define REG_MVFP       0x1E

#define REG_AEW        0x24
#define REG_AEB        0x25
#define REG_VPT        0x26

#define REG_HREF       0x32

#define REG_TSLB       0x3A
#define REG_COM11      0x3B
#define REG_COM12      0x3C
#define REG_COM13      0x3D
#define REG_COM14      0x3E

#define REG_EDGE       0x3F
#define REG_COM15      0x40
#define REG_COM16      0x41
#define REG_COM17      0x42

#define REG_RGB444     0x8C

#define REG_HAECC1     0x9F
#define REG_HAECC2     0xA0
#define REG_HAECC3     0xA6
#define REG_HAECC4     0xA7
#define REG_HAECC5     0xA8
#define REG_HAECC6     0xA9
#define REG_HAECC7     0xAA

#define REG_BD50MAX    0xA5
#define REG_BD60MAX    0xAB

#define REG_MTX1       0x4F
#define REG_MTX2       0x50
#define REG_MTX3       0x51
#define REG_MTX4       0x52
#define REG_MTX5       0x53
#define REG_MTX6       0x54
#define REG_MTXS       0x58

#define REG_BRIGHT     0x55
#define REG_CONTRAS    0x56

#define REG_GFIX       0x69
#define REG_REG76      0x76


// ============================================================
// BIT DEFINITIONS
// ============================================================

#define COM7_RESET     0x80

#define COM8_FASTAEC   0x80
#define COM8_AECSTEP   0x40
#define COM8_AGC       0x04
#define COM8_AEC       0x01
#define COM8_AWB       0x02

#define COM10_VS_NEG   0x02

#define COM16_AWBGAIN  0x08

#define COM15_R00FF    0xC0

#define COM13_UVSAT    0x40

#define COM11_EXP      0x02
#define COM11_HZAUTO   0x10


// ============================================================
// REGISTER TABLE
// ============================================================

struct RegValue
{
  uint8_t reg;
  uint8_t value;
};


const RegValue defaultRegs[] PROGMEM =
{
  {REG_COM7, COM7_RESET},
  {REG_TSLB, 0x04},
  {REG_COM7, 0x00},

  {REG_HSTART, 0x13},
  {REG_HSTOP,  0x01},
  {REG_HREF,   0xB6},

  {REG_VSTART, 0x02},
  {REG_VSTOP,  0x7A},
  {REG_VREF,   0x0A},

  {REG_COM3, 0x00},
  {0x3E, 0x00},

  {0x70, 0x3A},
  {0x71, 0x35},
  {0x72, 0x11},
  {0x73, 0xF0},
  {0xA2, 0x01},

  {REG_COM10, COM10_VS_NEG},

  // Gamma
  {0x7A, 0x20},
  {0x7B, 0x10},
  {0x7C, 0x1E},
  {0x7D, 0x35},
  {0x7E, 0x5A},
  {0x7F, 0x69},
  {0x80, 0x76},
  {0x81, 0x80},
  {0x82, 0x88},
  {0x83, 0x8F},
  {0x84, 0x96},
  {0x85, 0xA3},
  {0x86, 0xAF},
  {0x87, 0xC4},
  {0x88, 0xD7},
  {0x89, 0xE8},

  // AGC / AEC
  {REG_COM8, COM8_FASTAEC | COM8_AECSTEP},
  {REG_GAIN, 0x00},
  {0x10, 0x00},

  {REG_COM4, 0x40},
  {REG_COM9, 0x18},

  {REG_BD50MAX, 0x05},
  {REG_BD60MAX, 0x07},

  {REG_AEW, 0x95},
  {REG_AEB, 0x33},
  {REG_VPT, 0xE3},

  {REG_HAECC1, 0x78},
  {REG_HAECC2, 0x68},

  {0xA1, 0x03},

  {REG_HAECC3, 0xD8},
  {REG_HAECC4, 0xD8},
  {REG_HAECC5, 0xF0},
  {REG_HAECC6, 0x90},
  {REG_HAECC7, 0x94},

  {REG_COM8,
   COM8_FASTAEC |
   COM8_AECSTEP |
   COM8_AGC |
   COM8_AEC},

  {0x30, 0x00},
  {0x31, 0x00},

  // Sensor tuning
  {REG_COM5, 0x61},
  {REG_COM6, 0x4B},

  {0x16, 0x02},
  {REG_MVFP, 0x07},

  {0x21, 0x02},
  {0x22, 0x91},
  {0x29, 0x07},
  {0x33, 0x0B},
  {0x35, 0x0B},
  {0x37, 0x1D},
  {0x38, 0x71},
  {0x39, 0x2A},

  {REG_COM12, 0x78},

  {0x4D, 0x40},
  {0x4E, 0x20},

  {REG_GFIX, 0x00},

  {0x74, 0x10},

  {0x8D, 0x4F},
  {0x8E, 0x00},
  {0x8F, 0x00},
  {0x90, 0x00},
  {0x91, 0x00},
  {0x96, 0x00},
  {0x9A, 0x00},

  {0xB0, 0x84},
  {0xB1, 0x0C},
  {0xB2, 0x0E},
  {0xB3, 0x82},
  {0xB8, 0x0A},

  // White balance
  {0x43, 0x0A},
  {0x44, 0xF0},
  {0x45, 0x34},
  {0x46, 0x58},
  {0x47, 0x28},
  {0x48, 0x3A},

  {0x59, 0x88},
  {0x5A, 0x88},
  {0x5B, 0x44},
  {0x5C, 0x67},
  {0x5D, 0x49},
  {0x5E, 0x0E},

  {0x6C, 0x0A},
  {0x6D, 0x55},
  {0x6E, 0x11},
  {0x6F, 0x9E},

  {0x6A, 0x40},

  {REG_BLUE, 0x40},
  {REG_RED,  0x60},

  {REG_COM8,
   COM8_FASTAEC |
   COM8_AECSTEP |
   COM8_AGC |
   COM8_AEC |
   COM8_AWB},

  // YUV matrix
  {REG_MTX1, 0x80},
  {REG_MTX2, 0x80},
  {REG_MTX3, 0x00},
  {REG_MTX4, 0x22},
  {REG_MTX5, 0x5E},
  {REG_MTX6, 0x80},

  {REG_MTXS, 0x9E},

  // Enhanced sharpness, denoise, and auto-white balance
  {REG_COM16, COM16_AWBGAIN | 0x20 | 0x10}, // Enable AWB gain + Auto edge threshold + Auto denoise
  {REG_EDGE, 0x08},                         // Edge enhancement strength factor (sharpness)

  {0x75, 0x05},                             // Edge lower threshold
  {REG_REG76, 0xE1},                        // Edge upper threshold

  {0x4C, 0x04},                             // Denoise threshold (removes CMOS grain)
  {0x77, 0x01},                             // Denoise offset

  {REG_COM13, 0xC8},                        // Enable auto UV saturation adjust (fixes green cast)
  {0x4B, 0x09},

  {0xC9, 0x60},

  {REG_CONTRAS, 0x48},                      // Slight contrast enhancement for surface texture
  {REG_BRIGHT, 0x00},                       // Neutral brightness

  {0x34, 0x11},

  {REG_COM11,
   COM11_EXP |
   COM11_HZAUTO},

  {0xA4, 0x82},
  {0x96, 0x00},

  {0x97, 0x30},
  {0x98, 0x20},
  {0x99, 0x30},
  {0x9A, 0x84},
  {0x9B, 0x29},
  {0x9C, 0x03},
  {0x9D, 0x4C},
  {0x9E, 0x3F},

  {0x78, 0x04},

  // Internal multiplexer
  {0x79, 0x01},
  {0xC8, 0xF0},

  {0x79, 0x0F},
  {0xC8, 0x00},

  {0x79, 0x10},
  {0xC8, 0x7E},

  {0x79, 0x0A},
  {0xC8, 0x80},

  {0x79, 0x0B},
  {0xC8, 0x01},

  {0x79, 0x0C},
  {0xC8, 0x0F},

  {0x79, 0x0D},
  {0xC8, 0x20},

  {0x79, 0x09},
  {0xC8, 0x80},

  {0x79, 0x02},
  {0xC8, 0xC0},

  {0x79, 0x03},
  {0xC8, 0x40},

  {0x79, 0x05},
  {0xC8, 0x30},

  {0x79, 0x26},

  {0xFF, 0xFF}
};


// ============================================================
// ERROR HANDLER
// ============================================================

void errorLed()
{
  DDRB |= _BV(5);

  while (1)
  {
    PORTB ^= _BV(5);
    _delay_ms(150);
  }
}


// ============================================================
// TWI START
// ============================================================

void twiStart()
{
  TWCR =
    _BV(TWINT) |
    _BV(TWSTA) |
    _BV(TWEN);

  while (!(TWCR & _BV(TWINT)))
  {
  }

  if ((TWSR & 0xF8) != TW_START)
  {
    errorLed();
  }
}


// ============================================================
// TWI WRITE
// ============================================================

void twiWrite(
  uint8_t value,
  uint8_t expectedStatus
)
{
  TWDR = value;

  TWCR =
    _BV(TWINT) |
    _BV(TWEN);

  while (!(TWCR & _BV(TWINT)))
  {
  }

  if ((TWSR & 0xF8) != expectedStatus)
  {
    errorLed();
  }
}


// ============================================================
// WRITE REGISTER
// ============================================================

void wrReg(
  uint8_t reg,
  uint8_t value
)
{
  twiStart();

  twiWrite(
    OV7670_ADDR << 1,
    TW_MT_SLA_ACK
  );

  twiWrite(
    reg,
    TW_MT_DATA_ACK
  );

  twiWrite(
    value,
    TW_MT_DATA_ACK
  );

  TWCR =
    _BV(TWINT) |
    _BV(TWEN) |
    _BV(TWSTO);

  _delay_ms(1);
}


// ============================================================
// READ REGISTER
// ============================================================

uint8_t twiReadNack()
{
  TWCR =
    _BV(TWINT) |
    _BV(TWEN);

  while (!(TWCR & _BV(TWINT)))
  {
  }

  if ((TWSR & 0xF8) != TW_MR_DATA_NACK)
  {
    errorLed();
  }

  return TWDR;
}


uint8_t rdReg(
  uint8_t reg
)
{
  uint8_t value;

  // Register address

  twiStart();

  twiWrite(
    OV7670_ADDR << 1,
    TW_MT_SLA_ACK
  );

  twiWrite(
    reg,
    TW_MT_DATA_ACK
  );

  TWCR =
    _BV(TWINT) |
    _BV(TWEN) |
    _BV(TWSTO);

  _delay_ms(1);

  // Repeated START

  twiStart();

  twiWrite(
    (OV7670_ADDR << 1) | 1,
    TW_MR_SLA_ACK
  );

  value = twiReadNack();

  TWCR =
    _BV(TWINT) |
    _BV(TWEN) |
    _BV(TWSTO);

  _delay_ms(1);

  return value;
}


// ============================================================
// WRITE DEFAULT REGISTER TABLE
// ============================================================

void writeDefaults()
{
  uint16_t i = 0;

  while (1)
  {
    uint8_t reg =
      pgm_read_byte(
        &defaultRegs[i].reg
      );

    uint8_t value =
      pgm_read_byte(
        &defaultRegs[i].value
      );

    if (reg == 0xFF && value == 0xFF)
    {
      break;
    }

    wrReg(
      reg,
      value
    );

    i++;
  }
}


// ============================================================
// CAMERA INIT
// ============================================================

void cameraInit()
{
  // Reset

  wrReg(
    REG_COM7,
    COM7_RESET
  );

  _delay_ms(100);

  // Complete defaults

  writeDefaults();

  // Suppress PCLK during horizontal blanking

  wrReg(
    REG_COM10,
    0x20
  );
}


// ============================================================
// QQVGA 160 x 120
// ============================================================

void setQQVGA()
{
  wrReg(
    REG_COM3,
    0x04
  );

  wrReg(
    REG_COM14,
    0x1A
  );

  wrReg(
    0x72,
    0x22
  );

  wrReg(
    0x73,
    0xF2
  );

  wrReg(
    REG_HSTART,
    0x16
  );

  wrReg(
    REG_HSTOP,
    0x04
  );

  wrReg(
    REG_HREF,
    0xA4
  );

  wrReg(
    REG_VSTART,
    0x02
  );

  wrReg(
    REG_VSTOP,
    0x7A
  );

  wrReg(
    REG_VREF,
    0x0A
  );
}


// ============================================================
// YUV422 / YUYV
// ============================================================

void setYUV422()
{
  // YUV mode

  wrReg(
    REG_COM7,
    0x00
  );

  // RGB444 off

  wrReg(
    REG_RGB444,
    0x00
  );

  // CCIR601

  wrReg(
    REG_COM1,
    0x00
  );

  // Full range

  wrReg(
    REG_COM15,
    0xC0
  );

  // Gain ceiling

  wrReg(
    REG_COM9,
    0x6A
  );

  // YUV matrix

  wrReg(0x4F, 0x80);
  wrReg(0x50, 0x80);
  wrReg(0x51, 0x00);
  wrReg(0x52, 0x22);
  wrReg(0x53, 0x5E);
  wrReg(0x54, 0x80);

  // YUYV order

  wrReg(
    REG_TSLB,
    0x04
  );

  // Keep auto UV saturation adjust enabled (0xC8)
  wrReg(
    REG_COM13,
    0xC8
  );
}


// ============================================================
// XCLK
//
// D11 = OC2A
// ~8 MHz
// ============================================================

void startXCLK()
{
  DDRB |= _BV(3);

  ASSR &= ~(
    _BV(EXCLK) |
    _BV(AS2)
  );

  TCCR2A =
    _BV(COM2A0) |
    _BV(WGM21) |
    _BV(WGM20);

  TCCR2B =
    _BV(WGM22) |
    _BV(CS20);

  OCR2A = 0;
}


// ============================================================
// UART 1 Mbps
// ============================================================

void startUART()
{
  UBRR0H = 0;
  UBRR0L = 1;

  UCSR0A =
    _BV(U2X0);

  UCSR0B =
    _BV(RXEN0) |
    _BV(TXEN0);

  UCSR0C =
    _BV(UCSZ01) |
    _BV(UCSZ00);
}


// ============================================================
// SEND ONE BYTE
// ============================================================

static inline void sendByte(
  uint8_t value
)
{
  while (!(UCSR0A & _BV(UDRE0)))
  {
  }

  UDR0 = value;
}


// ============================================================
// SEND STRING
// ============================================================

void sendText(
  const char *text
)
{
  while (*text)
  {
    sendByte(
      (uint8_t)*text
    );

    text++;
  }
}


// ============================================================
// WAIT FOR UART TRANSMISSION COMPLETE
// ============================================================

void waitUART()
{
  while (!(UCSR0A & _BV(UDRE0)))
  {
  }

  while (!(UCSR0A & _BV(TXC0)))
  {
  }

  UCSR0A |= _BV(TXC0);
}


// ============================================================
// WAIT FOR COMMAND "C"
// ============================================================

void waitCommand()
{
  while (1)
  {
    if (UCSR0A & _BV(RXC0))
    {
      uint8_t c = UDR0;

      if (c == 'C')
      {
        return;
      }
    }
  }
}


// ============================================================
// READ CAMERA DATA BUS
// ============================================================
//
// D0-D3 -> PC0-PC3
// D4-D7 -> PD4-PD7
//

static inline uint8_t readCamera()
{
  return
    (PINC & 0x0F) |
    (PIND & 0xF0);
}


// ============================================================
// WAIT FOR FRAME BOUNDARY
// ============================================================
//
// VSYNC -> D3 -> PD3
//
// We wait for a complete VSYNC pulse and return at
// the beginning of a new image period.
//

void waitFrameBoundary()
{
  // Wait for VSYNC HIGH

  while (!(PIND & _BV(3)))
  {
  }

  // Wait for VSYNC LOW

  while (PIND & _BV(3))
  {
  }
}


// ============================================================
// DISCARD ONE FRAME
// ============================================================
//
// There is no FIFO to "clear" in the OV7670.
//
// Instead we intentionally skip one complete camera
// frame before capturing the frame we send to Python.
//
// This gives the camera a clean frame boundary.
// ============================================================

void discardOneFrame()
{
  // Align to the beginning of a frame

  waitFrameBoundary();

  // Wait through the next complete frame

  while (!(PIND & _BV(3)))
  {
  }

  while (PIND & _BV(3))
  {
  }
}


// ============================================================
// CAPTURE ONE IMAGE
// ============================================================
//
// 160 x 120
// YUV422
// 320 bytes per line
//
// This is the same no-FIFO streaming strategy that
// produced your good image.
//
// PCLK:
// D12 = PB4
// ============================================================

void captureFrame()
{
  // One-line buffer only.
  //
  // 320 bytes = 160 pixels of YUV422.

  uint8_t buffer[BYTES_PER_LINE];


  // --------------------------------------------------------
  // IMPORTANT: FLUSH/SYNCHRONIZE
  // --------------------------------------------------------
  //
  // Skip one camera frame before the actual capture.
  //

  discardOneFrame();


  // --------------------------------------------------------
  // Align to the frame that we actually capture
  // --------------------------------------------------------

  waitFrameBoundary();


  // --------------------------------------------------------
  // Tell Python that binary data starts
  // --------------------------------------------------------

  sendText("FRM0");


  // --------------------------------------------------------
  // Capture 120 lines
  // --------------------------------------------------------

  for (uint16_t y = 0; y < HEIGHT; y++)
  {
    uint8_t *writePtr = buffer;
    uint8_t *sendPtr  = buffer;

    uint16_t groups = 64;


    // ======================================================
    // ACTIVE CAMERA DATA
    // ======================================================

    while (groups--)
    {
      // --------------------------------------------------
      // BYTE 1
      // --------------------------------------------------

      while (PINB & _BV(4))
      {
      }

      *writePtr++ = readCamera();

      while (!(PINB & _BV(4)))
      {
      }


      // --------------------------------------------------
      // BYTE 2
      // --------------------------------------------------

      while (PINB & _BV(4))
      {
      }

      *writePtr++ = readCamera();

      while (!(PINB & _BV(4)))
      {
      }


      // --------------------------------------------------
      // BYTE 3
      // --------------------------------------------------

      while (PINB & _BV(4))
      {
      }

      *writePtr++ = readCamera();

      while (!(PINB & _BV(4)))
      {
      }


      // --------------------------------------------------
      // BYTE 4
      // --------------------------------------------------

      while (PINB & _BV(4))
      {
      }

      *writePtr++ = readCamera();

      while (!(PINB & _BV(4)))
      {
      }


      // --------------------------------------------------
      // BYTE 5
      // --------------------------------------------------

      while (PINB & _BV(4))
      {
      }

      *writePtr++ = readCamera();


      // --------------------------------------------------
      // Send one already captured byte
      // --------------------------------------------------

      while (!(UCSR0A & _BV(UDRE0)))
      {
      }

      UDR0 = *sendPtr++;


      // --------------------------------------------------
      // Finish current PCLK
      // --------------------------------------------------

      while (!(PINB & _BV(4)))
      {
      }
    }


    // ======================================================
    // HORIZONTAL BLANKING
    //
    // 64 bytes have already been transmitted.
    //
    // 320 - 64 = 256 remaining bytes.
    // ======================================================

    uint16_t remaining = 256;

    while (!(UCSR0A & _BV(UDRE0)))
    {
    }

    while (remaining--)
    {
      UDR0 = *sendPtr++;

      while (!(UCSR0A & _BV(UDRE0)))
      {
      }
    }
  }


  // --------------------------------------------------------
  // Finish transmission
  // --------------------------------------------------------

  waitUART();
}


// ============================================================
// SETUP
// ============================================================

void setup()
{
  // ----------------------------------------------------------
  // DATA BUS
  // ----------------------------------------------------------

  DDRC &= ~0x0F;

  DDRD &= ~0xF0;


  // ----------------------------------------------------------
  // VSYNC D3
  // ----------------------------------------------------------

  DDRD &= ~_BV(3);


  // ----------------------------------------------------------
  // HREF D10
  // ----------------------------------------------------------

  DDRB &= ~_BV(2);


  // ----------------------------------------------------------
  // PCLK D12
  // ----------------------------------------------------------

  DDRB &= ~_BV(4);


  // ----------------------------------------------------------
  // XCLK D11
  // ----------------------------------------------------------

  startXCLK();

  _delay_ms(3000);


  // ----------------------------------------------------------
  // TWI / SCCB
  // ----------------------------------------------------------

  TWSR &= ~0x03;

  TWBR = 72;

  TWCR = _BV(TWEN);


  // ----------------------------------------------------------
  // UART
  // ----------------------------------------------------------

  startUART();


  // ----------------------------------------------------------
  // READ CAMERA ID
  // ----------------------------------------------------------

  uint8_t pid =
    rdReg(0x0A);

  uint8_t ver =
    rdReg(0x0B);


  // ----------------------------------------------------------
  // CAMERA INITIALIZATION
  // ----------------------------------------------------------

  cameraInit();

  setQQVGA();

  setYUV422();


  // ----------------------------------------------------------
  // CAMERA CLOCK DIVIDER
  // ----------------------------------------------------------

  wrReg(
    REG_CLKRC,
    3
  );


  // ----------------------------------------------------------
  // ALLOW SENSOR TO SETTLE
  // ----------------------------------------------------------

  _delay_ms(1000);


  // ----------------------------------------------------------
  // START MESSAGE
  // ----------------------------------------------------------

  sendText("\r\n");
  sendText("========================================\r\n");
  sendText("OV7670 FINAL REAL IMAGE CAPTURE\r\n");
  sendText("========================================\r\n");

  sendText("PID = 0x");

  const char hex[] =
    "0123456789ABCDEF";

  sendByte(
    hex[(pid >> 4) & 0x0F]
  );

  sendByte(
    hex[pid & 0x0F]
  );

  sendText("\r\nVER = 0x");

  sendByte(
    hex[(ver >> 4) & 0x0F]
  );

  sendByte(
    hex[ver & 0x0F]
  );

  sendText("\r\n");

  sendText("Resolution: 160 x 120\r\n");
  sendText("Format: YUV422 YUYV\r\n");
  sendText("XCLK: ~8 MHz\r\n");
  sendText("CLKRC: 3\r\n");
  sendText("UART: 1 Mbps\r\n");
  sendText("PCLK: D12\r\n");
  sendText("VSYNC: D3\r\n");
  sendText("DATA: A0-A3 + D4-D7\r\n");
  sendText("FRAME DISCARD: ON\r\n");
  sendText("TEST PATTERN: OFF\r\n");
  sendText("WAITING FOR C\r\n");

  waitUART();


  // ----------------------------------------------------------
  // Disable interrupts after setup.
  //
  // Camera capture uses polling/direct UART.
  // ----------------------------------------------------------

  cli();
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
  // Wait for Python

  waitCommand();


  // Capture fresh frame

  captureFrame();


  // Ready for next capture

  sendText("\r\nWAITING FOR C\r\n");

  waitUART();
}