#include "Keyboard.h"

#define ENCODER1_PIN_A 2    // First encoder pin A
#define ENCODER1_PIN_B 3    // First encoder pin B 
#define ENCODER2_PIN_A 7    // Second encoder pin A
#define ENCODER2_PIN_B 9    // Second encoder pin B
#define BUTTON_ENTER 10     // Enter key button
#define BUTTON_SLASH 11     // Slash key button

// Variables to keep track of the encoder states
uint8_t encoder1State = 0;
uint8_t encoder1LastState = 0;
uint8_t encoder2State = 0;
uint8_t encoder2LastState = 0;

// Counter variables for pulse division
int encoder1Counter = 0;
int encoder2Counter = 0;
const int PULSE_DIVISOR = 4;    // Number of pulses per keystroke

// Direction tracking (to ensure consistent direction for counting)
int8_t encoder1LastDirection = 0;
int8_t encoder2LastDirection = 0;

// Debounce variables for buttons
bool lastEnterState = HIGH;  // Assuming pull-up, so HIGH is not pressed
bool lastSlashState = HIGH;  // Assuming pull-up, so HIGH is not pressed
unsigned long lastEnterDebounceTime = 0;
unsigned long lastSlashDebounceTime = 0;
const unsigned long buttonDebounceDelay = 50;  // Button debounce time in ms

// Timing variables for polling
unsigned long lastEncoder1ReadTime = 0;
unsigned long lastEncoder2ReadTime = 0;
const unsigned long encoderReadInterval = 1; // Poll encoders every 1ms

void setup() {
  // Set pin modes for encoders
  pinMode(ENCODER1_PIN_A, INPUT_PULLUP);
  pinMode(ENCODER1_PIN_B, INPUT_PULLUP);
  pinMode(ENCODER2_PIN_A, INPUT_PULLUP);
  pinMode(ENCODER2_PIN_B, INPUT_PULLUP);
  pinMode(BUTTON_ENTER, INPUT_PULLUP);
  pinMode(BUTTON_SLASH, INPUT_PULLUP);
  
  // Initialize encoder states
  encoder1LastState = (digitalRead(ENCODER1_PIN_A) << 1) | digitalRead(ENCODER1_PIN_B);
  encoder2LastState = (digitalRead(ENCODER2_PIN_A) << 1) | digitalRead(ENCODER2_PIN_B);
  
  // Initialize keyboard
  Keyboard.begin();
  Serial.begin(9600); // For debugging
}

void loop() {
  unsigned long currentTime = millis();
  
  // Poll first encoder (left/right arrows)
  if (currentTime - lastEncoder1ReadTime >= encoderReadInterval) {
    lastEncoder1ReadTime = currentTime;
    checkEncoder1();
  }
  
  // Poll second encoder (up/down arrows)
  if (currentTime - lastEncoder2ReadTime >= encoderReadInterval) {
    lastEncoder2ReadTime = currentTime;
    checkEncoder2();
  }

  // Process Enter button
  processButton(BUTTON_ENTER, 'r', &lastEnterState, &lastEnterDebounceTime, "ENTER");
  
  // Process Slash button
  processButton(BUTTON_SLASH, '\\', &lastSlashState, &lastSlashDebounceTime, "SLASH");
}

// Check first encoder state
void checkEncoder1() {
  // Read current state
  encoder1State = (digitalRead(ENCODER1_PIN_A) << 1) | digitalRead(ENCODER1_PIN_B);
  
  // If state changed
  if (encoder1State != encoder1LastState) {
    // This look-up table gives the correct direction based on the state transition
    // The 16 possible transitions are represented: (oldState << 2) | newState
    static const int8_t encoderTable[16] = {
      0,  // 0000 - no change
      -1, // 0001 - CCW
      1,  // 0010 - CW
      0,  // 0011 - invalid
      1,  // 0100 - CW
      0,  // 0101 - no change
      0,  // 0110 - invalid
      -1, // 0111 - CCW
      -1, // 1000 - CCW
      0,  // 1001 - invalid
      0,  // 1010 - no change
      1,  // 1011 - CW
      0,  // 1100 - invalid
      1,  // 1101 - CW
      -1, // 1110 - CCW
      0   // 1111 - no change
    };
    
    // Lookup the direction from the table
    int8_t direction = encoderTable[((encoder1LastState << 2) | encoder1State) & 0x0F];
    
    // Process the direction
    if (direction != 0) {
      // If direction changed, reset counter
      if (direction != encoder1LastDirection && encoder1LastDirection != 0) {
        encoder1Counter = 0;
      }
      
      // Increment counter in the current direction
      encoder1Counter++;
      encoder1LastDirection = direction;
      
      // Send keystroke only after PULSE_DIVISOR pulses in the same direction
      if (encoder1Counter >= PULSE_DIVISOR) {
        encoder1Counter = 0;  // Reset counter
        
        if (direction > 0) {
          Keyboard.press(KEY_RIGHT_ARROW);
          Keyboard.release(KEY_RIGHT_ARROW);
          Serial.println("RIGHT");
        } else {
          Keyboard.press(KEY_LEFT_ARROW);
          Keyboard.release(KEY_LEFT_ARROW);
          Serial.println("LEFT");
        }
      }
    }
    
    // Save the current state for next comparison
    encoder1LastState = encoder1State;
  }
}

// Check second encoder state
void checkEncoder2() {
  // Read current state
  encoder2State = (digitalRead(ENCODER2_PIN_A) << 1) | digitalRead(ENCODER2_PIN_B);
  
  // If state changed
  if (encoder2State != encoder2LastState) {
    // This look-up table gives the correct direction based on the state transition
    static const int8_t encoderTable[16] = {
      0,  // 0000 - no change
      -1, // 0001 - CCW
      1,  // 0010 - CW
      0,  // 0011 - invalid
      1,  // 0100 - CW
      0,  // 0101 - no change
      0,  // 0110 - invalid
      -1, // 0111 - CCW
      -1, // 1000 - CCW
      0,  // 1001 - invalid
      0,  // 1010 - no change
      1,  // 1011 - CW
      0,  // 1100 - invalid
      1,  // 1101 - CW
      -1, // 1110 - CCW
      0   // 1111 - no change
    };
    
    // Lookup the direction from the table
    int8_t direction = encoderTable[((encoder2LastState << 2) | encoder2State) & 0x0F];
    
    // Process the direction
    if (direction != 0) {
      // If direction changed, reset counter
      if (direction != encoder2LastDirection && encoder2LastDirection != 0) {
        encoder2Counter = 0;
      }
      
      // Increment counter in the current direction
      encoder2Counter++;
      encoder2LastDirection = direction;
      
      // Send keystroke only after PULSE_DIVISOR pulses in the same direction
      if (encoder2Counter >= PULSE_DIVISOR) {
        encoder2Counter = 0;  // Reset counter
        
        if (direction > 0) {
          Keyboard.press(KEY_DOWN_ARROW);
          Keyboard.release(KEY_DOWN_ARROW);
          Serial.println("DOWN");
        } else {
          Keyboard.press(KEY_UP_ARROW);
          Keyboard.release(KEY_UP_ARROW);
          Serial.println("UP");
        }
      }
    }
    
    // Save the current state for next comparison
    encoder2LastState = encoder2State;
  }
}

// Button processing function with added label parameter for serial output
void processButton(uint8_t pin, char key, bool* lastState, unsigned long* lastDebounceTime, const char* buttonLabel) {
  // Read the current state of the button
  bool currentState = digitalRead(pin);
  
  // If the state has changed, reset the debounce timer
  if (currentState != *lastState) {
    *lastDebounceTime = millis();
  }
  
  // If enough time has passed since the last state change
  // if ((millis() - *lastDebounceTime) > buttonDebounceDelay) {
    // If the button state has changed from HIGH (not pressed) to LOW (pressed)
    if (currentState == LOW && *lastState == HIGH) {
      // Button was just pressed, send the key
      Keyboard.press(key);
      Keyboard.release(key);
      
      // Serial output for debugging
      Serial.print(buttonLabel);
      Serial.println(" key pressed");
    }
  // }
  
  // Update the last state
  *lastState = currentState;
}