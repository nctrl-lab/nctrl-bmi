// 40 Hz square wave generator for teensy 4.0
// clock speed: 600 MHz

#define ENABLE_PIN 2
#define LASER_PIN 3

// PINS for spike pulses
// { 15, 14, 18, 19, 0, 1, 21, 20, 23, 22, 16, 17, 13, 11, 12, 10};
#define lsb0_3mask_8bit     0x0f             //                               0000 1111 in binary
#define lsb4_7mask_8bit     0xf0             //                               1111 0000 in binary
#define lsb4_9mask_16bit    0x03f0           //                     0000 0011 1111 0000 in binary
#define lsb10_11mask_16bit  0x0c00           //                     0000 1100 0000 0000 in binary
#define lsb12_15mask_16bit  0xf000           //                     1111 0000 0000 0000 in binary
#define lsb16_18mask_32bit  0x00070000       // 0000 0000 0000 0111 0000 0000 0000 0000 in binary
#define lsb19_19mask_32bit  0x00080000       // 0000 0000 0000 1000 0000 0000 0000 0000 in binary
#define lsb20_21mask_32bit  0x00300000       // 0000 0000 0011 0000 0000 0000 0000 0000 in binary
#define lsb22_23mask_32bit  0x00c00000       // 0000 0000 1100 0000 0000 0000 0000 0000 in binary

#define safe_clear6_8bit(n)  (n & 0xfc30ffff)// 1111 1100 0011 0000 1111 1111 1111 1111 in binary
#define safe_clear6_10bit(n) (n & 0xf030ffff)// 1111 0000 0011 0000 1111 1111 1111 1111 in binary
#define safe_clear6_12bit(n) (n & 0xf030fff3)// 1111 0000 0011 0000 1111 1111 1111 0011 in binary
#define safe_clear7_4bit(n)  (n & 0xfffffff0)// 1111 1111 1111 1111 1111 1111 1111 0000 in binary
#define safe_clear7_8bit(n)  (n & 0xfffcf3f0)// 1111 1111 1111 1100 1111 0011 1111 0000 in binary
#define safe_clear9_4bit(n)  (n & 0xfffffe8f)// 1111 1111 1111 1111 1111 1110 1000 1111 in binary 

// laser timer
const unsigned long LASER_DURATION = 5000; // 5 ms
const unsigned long INTERVAL_DURATION = 20000; // 20 ms
unsigned long finishDuration = 500000; // 0.5 seconds
unsigned long now = 0;
unsigned long startTime = 0;
unsigned long intervalTime = 0;

// spike timer
unsigned long spikeTimers = 0;
const unsigned long SPIKE_DURATION = 500;
int spikeStates = 0;

enum LaserState {
    STANDBY,
    LASERON,
    LASEROFF,
    DONE,
    PULSE
};

LaserState state = STANDBY;
bool enable = false;

#define enableOn()  {digitalWriteFast(ENABLE_PIN, HIGH); enable = true;}
#define enableOff() {digitalWriteFast(ENABLE_PIN, LOW);  enable = false;}
#define laserOn()   digitalWriteFast(LASER_PIN, HIGH)
#define laserOff()  digitalWriteFast(LASER_PIN, LOW)

void setup() { 
    // Serial.begin() is optional on Teensy.
    // USB hardware initialization is performed before setup() runs.
    // The baud rate input is ignored and only used for Arduino compatibility.
    // USB serial communication always occurs at full USB speed.
    // Serial.begin() may wait up to 2.5 seconds for USB serial communication to be ready.
    // For fastest program startup, do not use this unnecessary function.
    // Its only purpose is for compatibility with programs written for Arduino.
    // The delay is intended for programs which do not test the Serial boolean.

    set_16bit(OUTPUT);
    pinMode(ENABLE_PIN, OUTPUT);
    pinMode(LASER_PIN, OUTPUT);
}

void loop() {
    now = micros();
    checkSerial();
    checkLaser();
    checkSpike();
}

void checkSerial() {
    if (Serial.available() > 0) {
        char cmd = Serial.read();
        handleCommand(cmd);
    }
}

void handleCommand(char cmd) {
    switch (cmd) {
        case '1': // single pulse
            if (enable) {
                laserPulse();
            }
            break;
        case 'a': // start laser
            if (enable) {
                startLaser();
            }
            break;
        case 'A': // abort laser
            abortLaser();
            break;
        case 'e': // enable laser
            enableOn();
            Serial.println("Laser enabled");
            break;
        case 'E': // disable laser
            laserOff();
            enableOff();
            Serial.println("Laser disabled");
            break;
        case 'c': // constantly on
            if (enable) {
                laserOn();
                Serial.println("Laser is on");
            }
            break;
        case 'C': // constantly off
            laserOff();
            Serial.println("Laser is off");
            break;
        case 'd':
            setLaserDuration();
            break;
        case 's':
            readSpike();
            break;
    }
}

void laserPulse() {
    state = PULSE;
    startTime = now;
    laserOn();
}

void startLaser() {
    if (state == STANDBY || state == DONE) {
        state = LASERON;
        startTime = now;
        intervalTime = now;
        laserOn();
    } else {
        startTime = now; // just make it longer
    }
}

void abortLaser() {
    state = STANDBY;
    laserOff();
}

void setLaserDuration() {
    int duration = Serial.parseInt(); // read in ms ## this can be very slow (~1s)!!!
    finishDuration = duration * 1000; // write in us
    Serial.print("Laser duration is set to " + String(duration));
    Serial.println(" ms");
}

void checkLaser() {
    switch (state) {
        case LASERON:
            if (now - startTime >= finishDuration) {
                state = DONE;
                laserOff();
            } else if (now - intervalTime >= LASER_DURATION) {
                state = LASEROFF;
                intervalTime = now;
                laserOff();
            }
            break;
        case LASEROFF:
            if (now - intervalTime >= INTERVAL_DURATION) {
                state = LASERON;
                intervalTime = now;
                laserOn();
            }
            break;
        case PULSE:
            if (now - startTime >= finishDuration) {
                state = DONE;
                laserOff();
            }
            break;
        default:
            break;
    }
}

void readSpike() {
    uint16_t data = Serial.read() | (Serial.read() << 8);
    safe_write_16bit(data);
    spikeTimers = now;
    spikeStates = 1;
}

void checkSpike() {
    if (spikeStates == 1 && now - spikeTimers >= SPIKE_DURATION) {
        spikeStates = 0;
        safe_write_16bit(0);
    }
}

// ============================================================
// =============== For direct port manipulation ===============
// ============================================================
void set_16bit(uint8_t mode) {
  const int pins[16] = { 15, 14, 18, 19, 0, 1, 21, 20, 23, 22, 16, 17, 13, 11, 12, 10};
  for (int i = 0; i < 16; i++)
    pinMode(pins[i], mode);
}

inline uint16_t read_16bit() {
  uint32_t data0 = GPIO6_DR;
  uint32_t data1 = GPIO7_DR;
  return (data1 & lsb0_3mask_8bit) | ((data0 >> 18) & lsb4_9mask_16bit) | ((data0 << 8) & lsb10_11mask_16bit) | ((data0 >> 4) & lsb12_15mask_16bit);
}

inline void write_16bit(uint16_t data) {
  GPIO6_DR = ((data & lsb4_9mask_16bit) << 18) | ((data & lsb10_11mask_16bit) >> 8) | ((data & lsb12_15mask_16bit) << 4);
  GPIO7_DR = (data & lsb0_3mask_8bit);
}

inline void safe_write_16bit(uint16_t data) {
  GPIO6_DR = safe_clear6_12bit(GPIO6_DR) | ((data & lsb4_9mask_16bit) << 18) | ((data & lsb10_11mask_16bit) >> 8) | ((data & lsb12_15mask_16bit) << 4);
  GPIO7_DR = safe_clear7_4bit(GPIO7_DR)  |  (data & lsb0_3mask_8bit);
}