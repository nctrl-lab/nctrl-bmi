// Blink LED when receiving data from Serial

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
    if (Serial.available() > 0) {
        if (Serial.read() == '1') {
            blink();
        }
    }
}

void blink() {
    digitalWriteFast(LED_BUILTIN, HIGH);
    delayMicroseconds(100);
    digitalWriteFast(LED_BUILTIN, LOW);
}