// 40 Hz square wave generator for teensy 4.0
// clock speed: 600 MHz

#define ENABLE_PIN 2
#define LASER_PIN 3
#define START_PIN 5

// laser timer
const unsigned long LASER_PULSE_DURATION = 5000; // 5 ms
const unsigned long LASER_INTERVAL_DURATION = 20000; // 20 ms
unsigned long laserFinishDuration = 500000; // 0.5 seconds
unsigned long laserLatency = 0;

unsigned long now = 0;
unsigned long laserStartTime = 0;
unsigned long laserIntervalTime = 0;

// start state
bool startState = false; 

enum LaserState {
    STANDBY,
    WAITING,
    LASERON,
    LASEROFF,
    DONE,
    PULSE
};

LaserState state = STANDBY;
bool enable = false;

// Fast digital write macros for better performance
#define enableOn()  {digitalWriteFast(ENABLE_PIN, HIGH); enable = true;}
#define enableOff() {digitalWriteFast(ENABLE_PIN, LOW);  enable = false;}
#define laserOn()   {digitalWriteFast(LASER_PIN, HIGH); digitalWriteFast(LED_BUILTIN, HIGH);}
#define laserOff()  {digitalWriteFast(LASER_PIN, LOW); digitalWriteFast(LED_BUILTIN, LOW);}
#define startOn()   digitalWriteFast(START_PIN, HIGH)
#define startOff()  digitalWriteFast(START_PIN, LOW)

void setup() { 
    Serial.begin(115200);
    pinMode(ENABLE_PIN, OUTPUT);
    pinMode(LASER_PIN, OUTPUT);
    pinMode(START_PIN, OUTPUT);
    pinMode(LED_BUILTIN, OUTPUT);
    reset();
    printHelp();
}

void loop() {
    now = micros();
    checkSerial();
    checkLaser();
}

void checkSerial() {
    if (Serial.available() > 0) {
        char cmd = Serial.read();
        handleCommand(cmd);
    }
}

void reset() {
    state = STANDBY;
    startState = false;
    laserOff();
    enableOff();
    startOff();
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
                toggleStart();
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
            reset();
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
        case 'l':
            setLaserLatency();
            break;
        case 'p':
            printParams();
            break;
        case 'h':
            printHelp();
            break;
    }
}

void printHelp() {
    Serial.println("========== Commands ==========");
    Serial.println("1: single pulse");
    Serial.println("a: start laser");
    Serial.println("A: abort laser");
    Serial.println("e: enable laser");
    Serial.println("E: disable laser");
    Serial.println("c: constantly on");
    Serial.println("C: constantly off");
    Serial.println("d: set laser duration");
    Serial.println("l: set laser latency");
    Serial.println("p: print params");
    Serial.println("h: print help");
}

void printParams() {
    Serial.println("Laser duration: " + String(laserFinishDuration));
    Serial.println("Laser latency: " + String(laserLatency));
    Serial.println("Laser pulse duration: " + String(LASER_PULSE_DURATION));
    Serial.println("Laser interval duration: " + String(LASER_INTERVAL_DURATION));
    Serial.println("ENABLE PIN: " + String(ENABLE_PIN));
    Serial.println("LASER PIN: " + String(LASER_PIN));
    Serial.println("START PIN: " + String(START_PIN));
}

void laserPulse() {
    state = PULSE;
    laserStartTime = now;
    laserOn();
}

void toggleStart() {
    startState = !startState;
    if (startState) {
        startOn();
    } else {
        startOff();
    }
}

void startLaser() {
    laserOff();
    state = WAITING;
    laserStartTime = now;
}

void abortLaser() {
    state = STANDBY;
    laserOff();
}

void setLaserDuration() {
    int duration = Serial.parseInt(); // read in ms ## this can be very slow (~1s)!!!
    laserFinishDuration = duration * 1000UL; // write in us
    Serial.print("Laser duration is set to " + String(duration));
    Serial.println(" ms");
}

void setLaserLatency() {
    int latency = Serial.parseInt(); // read in ms ## this can be very slow (~1s)!!!
    laserLatency = latency * 1000UL; // write in us
    Serial.print("Laser latency is set to " + String(latency));
    Serial.println(" ms");
}

void checkLaser() {
    switch (state) {
        case WAITING:
            if (now - laserStartTime >= laserLatency) {
                state = LASERON;
                laserStartTime = now;
                laserIntervalTime = now;
                laserOn();
            }
            break;
        case LASERON:
            if (now - laserStartTime >= laserFinishDuration) {
                state = DONE;
                laserOff();
                durationOff();
            } else if (now - laserIntervalTime >= LASER_PULSE_DURATION) {
                state = LASEROFF;
                laserIntervalTime = now;
                laserOff();
            }
            break;
        case LASEROFF:
            if (now - laserIntervalTime >= LASER_INTERVAL_DURATION) {
                state = LASERON;
                laserIntervalTime = now;
                laserOn();
            }
            break;
        case PULSE:
            if (now - laserStartTime >= laserFinishDuration) {
                state = DONE;
                laserOff();
                durationOff();
            }
            break;
        default:
            break;
    }
}