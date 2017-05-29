
/*  
 SCRIPT to trigger a Time-lapse camera using the UiO Tmie-Lapse v2 shield

Simon Filhol, May 2017, Oslo, Norway

Designed for Time-Lapse shield v2 attached to a Sony QX1

USE:
	- set the time step in minutes with variable timeStep. Default is 10 min 
	- download filename from SD Card to file



Further Development:
	- Include waspmoote to wireless network, send frame for confirming Picture taken
	- Sync time with Network GPS 

	- include sunrise sunset time switch with the library:
	https://github.com/chaeplin/Sunrise
		- add system to read battery voltage to make sure the battery load does not get below a threshold
 */


//================================================================
// Put your libraries here (#include ...)


//================================================================
// Define pin
const int focusPin = DIGITAL3;
const int shutterPin = DIGITAL2;
const int onoffPin = DIGITAL4;
const int camPowerPin = DIGITAL1;


//================================================================
//========== SET time step !! ====================================
//================================================================

//String imageFiles = "IMAGES.TXT";

//================================================================
//================================================================

char message2log[100];
char* logfile = "LOG.TXT";
//================================================================
void setup(){

	SD.ON();
	RTC.ON();
	USB.ON();

	// Create log file on SD card:
	SD.create(logfile);
	USB.print(logfile);
	USB.println(" created");

	pinMode(focusPin, OUTPUT);
	digitalWrite(focusPin, LOW);

	pinMode(shutterPin, OUTPUT);
	digitalWrite(shutterPin, LOW);

	pinMode(onoffPin, OUTPUT);
	digitalWrite(onoffPin, LOW);

	pinMode(camPowerPin, OUTPUT);
	digitalWrite(camPowerPin, HIGH); // Provide power to camera
	delay(10000);

	RTC.setTime("00:01:01:01:00:00:00");
	logActivity("=== Waspmote starting ===");


	camON();
	delay(120000);
	camTrigger();
	delay(1000);
	camOFF();

}

//================================================================
void loop(){

	logActivity("Mote to sleep ...");
	PWR.deepSleep("00:00:00:00", RTC_ABSOLUTE, RTC_ALM1_MODE4, ALL_OFF);
	//PWR.sleep(ALL_OFF);
	logActivity("Mote awaking");


	if (intFlag & RTC_INT){
		intFlag &= ~(RTC_INT); // Clear flag

		takePicture();
	}
}

//================================================================
// =========== Local functions
//================================================================

void logActivity(String message){
  SD.ON();
  RTC.ON();
  delay(50);
  uint8_t answer = 0;
  String message2write;


  char datetime[20];
  RTC.getTime();
  sprintf(datetime,"%02u-%02u-%02u %02u:%02u:%02u ----> ",RTC.year, RTC.month, RTC.date, RTC.hour, RTC.minute, RTC.second);
  

  message2write = String(datetime) + message;

  if(SD.isFile((const char*)&logfile[0]))
    { 
      if(SD.appendln((const char*)&logfile[0], (const char*)&message2write[0]))
      { 
        //frame.showFrame(); // Print frame to USB
        USB.print("------------>: ");
        USB.println((const char*)&message2write[0]);
        answer = 1;
        delay(50);
      }
      else
      {
        USB.print("--------> Failed to append message: ");
        USB.println((const char*)&message2write[0]);
      } 
    }
  SD.OFF();
}


void takePicture(){
    camON();
    delay(15000);
    camTrigger();
    delay(10000);
    camOFF();
    //collectImageName();
}

void camON(){
	// function to turn camera ON
	digitalWrite(onoffPin, HIGH);
	delay(20);
	digitalWrite(onoffPin, LOW);
	USB.println("Camera turned ON");
	logActivity("Cam ON");
}

void camOFF(){
	// function to turn camera OFF
	digitalWrite(onoffPin, HIGH);
	delay(60);
	digitalWrite(onoffPin, LOW);
	USB.println("Camera turned OFF");
	logActivity("Cam OFF");
}

void camTrigger(){
	// function to focus, and trigger the camera shutter
	//digitalWrite(focusPin, HIGH);	
	//delay(50);
	digitalWrite(shutterPin, HIGH);	
	delay(300);
	digitalWrite(shutterPin, LOW);	
	//digitalWrite(focusPin, LOW);	
	//delay(100);
	USB.println("Photo captured");
	logActivity("Photo captured");
}