// LittleArm 2C arduino code
// Allows serial control of the LittleArm 2C 3D printed robot arm 
// Created by Slant Concepts
// Butchered by Ovidiu

#include <Servo.h> //arduino library

//#define DEBUG

Servo baseServo;
Servo shoulderServo;
Servo elbowServo;
Servo gripperServo;

struct jointAngle {
  int base;
  int shoulder;
  int elbow;
  int grip;
};

const byte numChars = 32;
char receivedChars[numChars];
char tempChars[numChars];
boolean newData = false;


void setup() // Setup prepared the Arduino board for operation
  {
    Serial.begin(38400); // Turn on USB communication (Serial Port)

    baseServo.attach(5); // attaches the servo on pin 5 to the servo object 
    shoulderServo.attach(4); // attaches the servo on pin 4 to the servo object 
    elbowServo.attach(3); // attaches the servo on pin 3 to the servo object 
    gripperServo.attach(2); // attaches the servo on pin 2 to the servo object 

    baseServo.write(90);
    shoulderServo.write(45);
    elbowServo.write(179);
    gripperServo.write(10);

    Serial.setTimeout(100); //Stops attempting to talk to computer is no response after X milisenconds. Ensures the the arduino does not read serial for too long
    Serial.println("started"); // Print to the computer "Started"
  }

//primary arduino loop. This is where all of you primary program must be placed.
void loop() {
  recvWithStartEndMarkers();
  if (newData == true) {
    strcpy(tempChars, receivedChars);
#ifdef DEBUG
    Serial.print("arduino >");
    Serial.println(tempChars);
#endif
    processData();
    newData = false;
  }
}

//https://forum.arduino.cc/index.php?topic=288234.0
void recvWithStartEndMarkers() {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();

    if (recvInProgress == true) {
      if (rc != endMarker) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      } else {
        receivedChars[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    } else if (rc == startMarker) {
      recvInProgress = true;
    }
  }
}

void processData() { // split the data into its parts based on the protocol code
  char * strtokIndx;
  int precision;
  struct jointAngle desiredDirection;

  //first char is the protocol code definition
  char code = tempChars[0];
  //remove code
  strtokIndx = strtok(tempChars, ":");

  switch (code) {
  case 'R': //relative move - receives directions as 0, 1 or 2 for each servo 
    strtokIndx = strtok(NULL, ",");
    desiredDirection.base = atoi(strtokIndx);
    strtokIndx = strtok(NULL, ",");
    desiredDirection.shoulder = atoi(strtokIndx);
    strtokIndx = strtok(NULL, ",");
    desiredDirection.elbow = atoi(strtokIndx);
    strtokIndx = strtok(NULL, ",");
    desiredDirection.grip = atoi(strtokIndx);
    strtokIndx = strtok(NULL, ",");
    precision = atoi(strtokIndx);
    relativeMove(desiredDirection, precision);
    Serial.println("R:D"); //done
    break;

  case 'A': //absolute move - receive position for each servo  
    strtokIndx = strtok(NULL, ",");
    desiredDirection.base = atoi(strtokIndx);
    strtokIndx = strtok(NULL, ",");
    desiredDirection.shoulder = atoi(strtokIndx);
    strtokIndx = strtok(NULL, ",");
    desiredDirection.elbow = atoi(strtokIndx);
    strtokIndx = strtok(NULL, ",");
    desiredDirection.grip = atoi(strtokIndx);
    strtokIndx = strtok(NULL, ",");
    precision = atoi(strtokIndx);
    if (precision == 0) {
        delay(1000); //delay 1 sec
     } else {
        absoluteMove(desiredDirection, precision);
    }
    Serial.println("A:N"); // ask for next 
    break;

  case 'P': //querry curent position for each servo 
    sendCurrentPosition();
    break;
  case 'C': //connected
    Serial.println("started"); 
    break;
  }
}

void sendCurrentPosition() {
  String msg = "P:";
  msg.concat(baseServo.read());
  msg.concat(",");
  msg.concat(shoulderServo.read());
  msg.concat(",");
  msg.concat(elbowServo.read());
  msg.concat(",");
  msg.concat(gripperServo.read());
  Serial.println(msg);
}

void relativeMove(jointAngle desiredDirection, int precision) {
  int distance = int(map(precision, 1, 100, 1, 6));
#ifdef DEBUG
  Serial.print("arduino >");
  Serial.print(precision);
  Serial.print(" -> ");
  Serial.println(distance);
#endif
  for (int i = 0; i < distance; i++) {
    if (desiredDirection.base > 0) servoParallelRelative(desiredDirection.base, baseServo, 1, 179);
    if (desiredDirection.shoulder > 0) servoParallelRelative(desiredDirection.shoulder, shoulderServo, 1, 179);
    if (desiredDirection.elbow > 0) servoParallelRelative(desiredDirection.elbow, elbowServo, 1, 179);
    if (desiredDirection.grip > 0) servoParallelRelative(desiredDirection.grip, gripperServo, 10, 75);
  }
}

void servoParallelRelative(int theDir, Servo theServo, int min_position, int max_position) {
  int startPos = theServo.read();
  if (theDir == 1) { // 01
    if (startPos > min_position) {
      theServo.write(startPos - 1);
    }
  } else { //10
    if (startPos < max_position) {
      theServo.write(startPos + 1);
    }
  }
}

void absoluteMove(jointAngle desiredDirection, int precision) {
  int theSpeed = int(map(precision, 1, 100, 6, 1));
#ifdef DEBUG
  Serial.print("arduino >");
  Serial.print(precision);
  Serial.print(" -> ");
  Serial.println(theSpeed);
#endif

  int status1 = 0; //base status
  int status2 = 0; //shoulder status
  int status3 = 0; //elbow status
  int status4 = 0; //gripper status

  int done = 0; // this value tells when all the joints have reached thier positions

  while (done == 0) {
    status1 = servoParallelControl(desiredDirection.base, baseServo, theSpeed);
    status2 = servoParallelControl(desiredDirection.shoulder, shoulderServo, theSpeed);
    status3 = servoParallelControl(desiredDirection.elbow, elbowServo, theSpeed);
    status4 = servoParallelControl(desiredDirection.grip, gripperServo, theSpeed);
    if (status1 == 1 & status2 == 1 & status3 == 1 & status4 == 1) {
      done = 1;
    }
  }
}

int servoParallelControl(int thePos, Servo theServo, int theSpeed) {
  int startPos = theServo.read();
  int newPos = startPos;
  if (startPos < thePos) {
    newPos = newPos + 1;
    theServo.write(newPos);
    delay(theSpeed);
    return 0;
  } else if (newPos > thePos) {
    newPos = newPos - 1;
    theServo.write(newPos);
    delay(theSpeed);
    return 0;
  } else {
    return 1;
  }

}
