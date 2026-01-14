#include <Arduino.h>
#include <EEPROM.h>
#include <avr/wdt.h>

#define LED_STAGE_REGISTER (1)
#define LED_START_REGISTER (10)
#define LED_END_REGISTER (18)
#define TON_LED_REGISTER (20)
#define TOFF_LED_REGISTER (40)

#define FAN_STAGE_REGISTER (2)
#define FAN_START_REGISTER (60)
#define FAN_END_REGISTER (62)
#define TON_FAN_REGISTER (80)
#define TOFF_FAN_REGISTER (100)

const uint8_t LED_PIN[] = {2,3,4,5,6,7,8,9};
const uint8_t FAN_PIN[] = {10,11};

const uint8_t NUMBER_OF_FAN_PIN = FAN_END_REGISTER - FAN_START_REGISTER;
const uint8_t NUMBER_OF_LED_PIN = LED_END_REGISTER - LED_START_REGISTER;

uint8_t adr = 0x00;

uint16_t Address_Register[102];

// สร้าง OS LED State
bool prevLedState = LOW;

uint8_t startPeriod = 100;// คาบเวลาเริ่มต้นสำหรับนับสเตปในการบวกค่า dim = 100 ms

struct PreventValues_t{
  /*
    สร้าง Object สำหรับใช้งานกับ Serial Communication
  */
  
  uint8_t led_stage;
  uint8_t fan_stage;
  
  uint16_t led[NUMBER_OF_LED_PIN];
  uint16_t step_led[NUMBER_OF_LED_PIN];
  uint32_t millis_led[NUMBER_OF_LED_PIN];
  uint32_t periodOn_led[NUMBER_OF_LED_PIN];
  uint32_t periodOff_led[NUMBER_OF_LED_PIN];

  uint8_t fan[NUMBER_OF_FAN_PIN];
  uint8_t step_fan[NUMBER_OF_FAN_PIN];
  uint32_t millis_fan[NUMBER_OF_LED_PIN];
  uint32_t periodOn_fan[NUMBER_OF_LED_PIN];
  uint32_t periodOff_fan[NUMBER_OF_FAN_PIN];
};

// สร้าง Object สำหรับใช้งาน Modbus RTU Server
struct PreventValues_t prevent_values;

void delayAndResetWDT(unsigned long ms){
  /*
    สร้าง Function สำหรับ Delay และ Reset Watchdog Timer
  */

  wdt_reset();
  delay(ms);
}

uint32_t convertToPeriod(uint32_t Time, uint32_t Max){
  /*
    สร้าง Function สำหรับสร้างคาบเวลาเพื่อจับเวลาและทำการ +1 step 
    ของการ dim โดยจะ vary ตามเวลา และค่าสูงสุด
  */

  return startPeriod*Time/(Max + 1);
}

uint32_t convertToTime(uint32_t Period, uint32_t Max){
  /*
    สร้าง Function สำหรับสร้างคาบเวลาเพื่อจับเวลาและทำการ +1 step 
    ของการ dim โดยจะ vary ตามเวลา และค่าสูงสุด
  */

  return Period*(Max + 1)/startPeriod;
}

void setup(){
  /*
    ตั้งค่าเริ่มต้นของ pinMode, RTS485, wdt
    กำหนดค่า Address ให้ Analog Pin
    กำหนดค่าเริ่มต้นให้ Modbus RTU Server
  	เช็ครับค่าจาก EEPROM
    Reset list Address_Register ที่เก็บค่าที่รับจาก Serial communication
  */
  
  pinMode(LED_BUILTIN, OUTPUT);
  
  for (uint8_t i = 0; i < NUMBER_OF_LED_PIN; i++){
    pinMode(LED_PIN[i], OUTPUT);
    analogWrite(LED_PIN[i], 0);
  }
  
  for (uint8_t i = 0; i < NUMBER_OF_FAN_PIN; i++){
    pinMode(FAN_PIN[i], OUTPUT);
    analogWrite(FAN_PIN[i], 0);
  }
  
  // กำหนดค่าเริ่มต้นให้ LED OS ติด
  digitalWrite(LED_BUILTIN, prevLedState = !prevLedState);
  
  // อ่านค่าจาก Analog Pin และกำหนดค่าให้ Address
  for (size_t i = 0; i < 4; i++){
    adr = (adr << 1) | !(analogRead(17 - i) > 0);
  }
  
  Serial.begin(115200);
  
  // อ่านค่าจาก EEPROM
  EEPROM.get(0, prevent_values);
  
  // ถ้าค่า led ที่อ่านมาเป็น false ให้กำหนดค่าเริ่มต้นให้ EEPROM
  if (prevent_values.led_stage == 0xFF){
    prevent_values.led_stage = 0;
    
    for (uint8_t i = 0; i < NUMBER_OF_LED_PIN; i++){
      prevent_values.led[i] = 0;
      prevent_values.step_led[i] = 0;
      prevent_values.millis_led[i] = 0;
      prevent_values.periodOn_led[i] = 0;
      prevent_values.periodOff_led[i] = 0;
    }
    
    EEPROM.put(0, prevent_values);
  } 
    
  // ถ้าค่า fan ที่อ่านมาเป็น false ให้กำหนดค่าเริ่มต้นให้ EEPROM
  if (prevent_values.fan_stage == 0xFF){ 
    prevent_values.fan_stage = 0;
    
    for (uint8_t i = 0; i < NUMBER_OF_FAN_PIN; i++){
      prevent_values.fan[i] = 0;
      prevent_values.step_fan[i] = 0;
      prevent_values.millis_fan[i] = 0;
      prevent_values.periodOn_fan[i] = 0;
      prevent_values.periodOff_fan[i] = 0;
    }
    
    EEPROM.put(0, prevent_values);
  }
  
  // ล้างข้อมูลใน Address_Register
  for (uint8_t i = 0; i < 102; i++){
    Address_Register[i] = 0;
  }
  
  delay(100);
  digitalWrite(LED_BUILTIN, prevLedState = !prevLedState);
}


void dimmingValue(uint8_t current_register){
  /*
  	ฟังก์ชั่นปรับระดับความเข้มแสงตามเวลาอ่านจาก Serial หน่วย วินาที (s)
  */

  // เช็คว่า current_register อยู่ในช่วงของ address เริ่มต้นถึงจบ ของพัดลมไหม
  if ((current_register < FAN_END_REGISTER) && (current_register >= FAN_START_REGISTER)){
    // ถ้า fan_stage เป็น 1 จะเริ่มโปรแกรมปรับระดับความเข้มแสง
    int zeros_index = current_register - FAN_START_REGISTER;
    uint8_t fan = prevent_values.fan[zeros_index];
    uint8_t Step = prevent_values.step_fan[zeros_index];
    uint32_t now = prevent_values.millis_fan[zeros_index];
    uint32_t OnPeriod = prevent_values.periodOn_fan[zeros_index];
    uint32_t OffPeriod = prevent_values.periodOff_fan[zeros_index];
    
    // Step < led: เมื่อค่า Step ของ led น้อยกว่าค่าที่ต้องการ
    // OnPeriod <= (millis() - now: เมื่อเวลาผ่านไปมากกว่าเท่ากับ คาบเวลาเปิด 
    if ((Step < fan) && (OnPeriod <= (millis() - now))){
      Step += 1;
      prevent_values.millis_fan[zeros_index] = millis();
    }
    // Step < led: เมื่อค่า Step ของ led มากกว่าค่าที่ต้องการ
    // OnPeriod <= (millis() - now: เมื่อเวลาผ่านไปมากกว่าเท่ากับ คาบเวลาปิด
    else if ((Step > fan) && (OffPeriod <= (millis() - now))){
      Step -= 1;
      prevent_values.millis_fan[zeros_index] = millis();
    }
          
      if (zeros_index < -1){
        Serial.print("fan ");
      	Serial.print(zeros_index);
      	Serial.println();
        Serial.print("Step_fan : ");
      	Serial.println(Step);
      }

    analogWrite(FAN_PIN[zeros_index], Step);
    prevent_values.step_fan[zeros_index] = Step;
  }
  // เช็คว่า current_register อยู่ในช่วงของ address เริ่มต้นถึงจบของ LED ไหม
  else if ((current_register < LED_END_REGISTER) && (current_register >= LED_START_REGISTER)){
    // ถ้า led_stage เป็น 1 จะเริ่มโปรแกรมปรับระดับความเข้มแสง
    uint8_t zeros_index = current_register - LED_START_REGISTER; // เปลี่ยนตัวนับตัวแรกที่เป็นค่าของ address เริ่มต้น เปลี่ยนเป็นเริ่มนับจาก 
    uint16_t led = prevent_values.led[zeros_index];
    uint16_t Step = prevent_values.step_led[zeros_index];
    uint32_t now = prevent_values.millis_led[zeros_index];
    uint32_t OnPeriod = prevent_values.periodOn_led[zeros_index];
    uint32_t OffPeriod = prevent_values.periodOff_led[zeros_index];

    // Step < led: เมื่อค่า Step ของ led น้อยกว่าค่าที่ต้องการ
    // OnPeriod <= (millis() - now: เมื่อเวลาผ่านไปมากกว่าเท่ากับ คาบเวลาเปิด 
    if ((Step < led) && (OnPeriod <= (millis() - now))){
      Step += 1;
      prevent_values.millis_led[zeros_index] = millis();
    }
    // Step < led: เมื่อค่า Step ของ led มากกว่าค่าที่ต้องการ
    // OnPeriod <= (millis() - now: เมื่อเวลาผ่านไปมากกว่าเท่ากับ คาบเวลาปิด
    else if ((Step > led) && (OffPeriod <= (millis() - now))){
      Step -= 1;
      prevent_values.millis_led[zeros_index] = millis();
    }
    if (zeros_index < -1){
        Serial.print("led ");
      	Serial.print(zeros_index);
      	Serial.println();
        Serial.print("Step_led: ");
      	Serial.println(Step);
      }

      analogWrite(LED_PIN[zeros_index], Step);
      prevent_values.step_led[zeros_index] = Step;
  }
}

void serial_read_address(){
  prevent_values.led_stage = Address_Register[LED_STAGE_REGISTER];

   // อ่านค่าจาก Input Register และ Holding Register
  	for (uint8_t i = LED_START_REGISTER; i < LED_END_REGISTER; i++){
      uint8_t zeros_index = i - LED_START_REGISTER;
      uint16_t holdingRegisterLEDValue = Address_Register[LED_START_REGISTER + zeros_index];  // อ่านค่าจาก Holding Register สำหรับ LED 
      uint16_t holdingRegisterLEDTimeOn = Address_Register[TON_LED_REGISTER + zeros_index];   // อ่านค่าจาก Holding Register สำหรับ Time On LED
      uint16_t holdingRegisterLEDTimeOff = Address_Register[TOFF_LED_REGISTER + zeros_index]; // อ่านค่าจาก Holding Register สำหรับ Time Off LED
      
      if (prevent_values.led_stage == 0){
        prevent_values.led[zeros_index] = 0;
        prevent_values.periodOn_led[zeros_index] = 0;
        prevent_values.periodOff_led[zeros_index] = 0;
        
      }else{
        // แปลงเวลาเป็น คาบเวลาเทียบกับ calspeed
        prevent_values.periodOn_led[zeros_index] = convertToPeriod(holdingRegisterLEDTimeOn, holdingRegisterLEDValue);
        prevent_values.periodOff_led[zeros_index] = convertToPeriod(holdingRegisterLEDTimeOff, prevent_values.led[zeros_index] + 1);
        // ตรวจสอบค่าที่อ่านมาจาก Holding Register สำหรับ LED
        // ถ้าค่าที่อ่านมาไม่เท่ากับค่าที่เคยอ่านมาก่อนหน้านี้ให้กำหนดค่าให้ Prevent Values และเขียนค่าลง EEPROM
        prevent_values.led[zeros_index] = holdingRegisterLEDValue; // กำหนดค่าให้ Prevent Values สำหรับ LED
        prevent_values.millis_led[zeros_index] = millis(); // Set เวลาเริ่มต้นให้เป็นปัจจุบัน
        EEPROM.put(0, prevent_values); // เขียนค่าลง EEPROM
        
        Serial.println("No, led, step, millis, Ton, Toff");
      	Serial.print(zeros_index);
        Serial.print(", ");
        Serial.print(prevent_values.led[zeros_index]);
        Serial.print(", ");
        Serial.print(prevent_values.step_led[zeros_index]);
        Serial.print(", ");
        Serial.print(prevent_values.millis_led[zeros_index]);
        Serial.print(", ");
        Serial.print(prevent_values.periodOn_led[zeros_index]);
        Serial.print(", ");
        Serial.println(prevent_values.periodOff_led[zeros_index]);
      }
    }
  
  	prevent_values.fan_stage = Address_Register[FAN_STAGE_REGISTER];

    for (uint8_t i = FAN_START_REGISTER; i < FAN_END_REGISTER; i++){
      // อ่านค่าจาก Holding Register สำหรับ FAN
      uint8_t zeros_index = i - FAN_START_REGISTER;
      uint8_t holdingRegisterFANValue = Address_Register[FAN_START_REGISTER + zeros_index]; // อ่านค่าจาก Holding Register สำหรับ FAN1
      uint16_t holdingRegisterFANTimeOn = Address_Register[TON_FAN_REGISTER + zeros_index];
      uint16_t holdingRegisterFANTimeOff = Address_Register[TOFF_FAN_REGISTER + zeros_index];

      if (prevent_values.fan_stage == 0){
        prevent_values.fan[zeros_index] = 0;
        prevent_values.periodOn_fan[zeros_index] = 0;
        prevent_values.periodOff_fan[zeros_index] = 0;
        
      }else{
        // แปลงเวลาเป็น คาบเวลาเทียบกับ calspeed
        prevent_values.periodOn_fan[zeros_index] = convertToPeriod(holdingRegisterFANTimeOn, holdingRegisterFANValue);
        prevent_values.periodOff_fan[zeros_index] = convertToPeriod(holdingRegisterFANTimeOff, prevent_values.fan[zeros_index]);
        // ตรวจสอบค่าที่อ่านมาจาก Holding Register สำหรับ FAN
        // ถ้าค่าที่อ่านมาไม่เท่ากับค่าที่เคยอ่านมาก่อนหน้านี้ให้กำหนดค่าให้ Prevent Values และเขียนค่าลง EEPROM
        prevent_values.fan[zeros_index] = holdingRegisterFANValue; // กำหนดค่าให้ Prevent Values สำหรับ LED
        prevent_values.millis_fan[zeros_index] = millis(); // Set เวลาเริ่มต้นให้เป็นปัจจุบัน
        EEPROM.put(0, prevent_values); // เขียนค่าลง EEPROM
        
        Serial.println("No, fan, step, millis, Ton, Toff");
      	Serial.print(zeros_index);
        Serial.print(", ");
        Serial.print(prevent_values.fan[zeros_index]);
        Serial.print(", ");
        Serial.print(prevent_values.step_fan[zeros_index]);
        Serial.print(", ");
        Serial.print(prevent_values.millis_fan[zeros_index]);
        Serial.print(", ");
        Serial.print(prevent_values.periodOn_fan[zeros_index]);
        Serial.print(", ");
        Serial.println(prevent_values.periodOff_fan[zeros_index]);
      }
      
      
    }
}

void update_status(){
  /*
  	อัพเดท status ของอุปกรณ์ทั้งหลอดไฟ LED และพัดลมโดยจะเริ่มนับ
    จาก address เริ่มต้นจนถึง address สุดท้ายที่เราได้กำหนดไว้
  */
  
  // วนลูปเริ่มจาก address เริ่มต้นจนจบของ LED
  for (uint8_t i = LED_START_REGISTER; i < LED_END_REGISTER; i++){
    dimmingValue(i); // อัพเดท status ของอุปกรณ์ LED
  }
	
  // วนลูปเริ่มจาก address เริ่มต้นจนจบของพัดลม
  for (uint8_t i = FAN_START_REGISTER; i < FAN_END_REGISTER; i++){
    dimmingValue(i); // อัพเดท status ของอุปกรณ์ FAN
  }

  digitalWrite(LED_BUILTIN, prevLedState = !prevLedState); // กำหนดค่าให้ LED OS ติด
  wdt_reset(); // reset watchdog timer
}

void serial_write_address(){
  /*
  	ฟังก์ชั่นจำลองการเขียนค่า โดยจะอ่านเพื่อรับค่าจาก Serial Monitor ใช้แทน modbus
  */
  
 if (Serial.available() > 0) {// เช็คว่ามี byte อยู่ใน ram ไหม
   String Serial_String = Serial.readStringUntil('x');  // อ่านค่า String และเก็บไว้จนถึงตัวอักษร x ตัวเล็ก
   
   // เช็คช่องว่างเพื่อแบ่ง String
   if (Serial_String.lastIndexOf(' ') > 0){
     unsigned int String_Split[2];
     uint8_t String_Count = 0;
     
     // แยก String จากช่องว่างเป็นชุด String ย่อยๆ
     while (Serial_String.length() > 0){
       int index = Serial_String.indexOf(' '); // หาตำแหน่งลำดับของช่องว่างที่แทรกอยู่ใน String
       
       if (index == -1){ // ถ้าไม่เจอช่องว่างใน String 
         String_Split[String_Count++] = Serial_String.toInt(); // เก็บ String ใน String_Split เลย
         break;
       }
       else { // ถ้าเจอช่องว่างใน String
         /* 
            1. substring(0, index): ตัด String โดยเริ่มจากตัวอักษรตัวแรกไล่ไปทางซ้ายถึงช่องว่างแรก (index)
         	2. toInt(): แปลง String เป็น integer
            3. String_Split[String_Count++]: ใส่ String ที่ตัดได้ลงใน String_Split
         */
         String_Split[String_Count++] = Serial_String.substring(0, index).toInt();
         // ลบ String ที่ตัดออกมาเก็บใน String_Split แล้วออกไป เพื่อตัด String ใหม่ของช่องว่างถัดไป
         Serial_String = Serial_String.substring(index+1);
       }
     }
     // ตัวเลขตัวแรกที่รับมาจาก Serial จะต้องไม่ถึง 102
     // ตัวเลขตัวที่สองที่รับมาจาก Serial จะต้องไม่เกิน 65535 
     if (String_Split[0] < 102 && String_Split[1] < 65535)
       Address_Register[String_Split[0]] = String_Split[1];
     
     Serial.print("Address(");
     Serial.print(String_Split[0]);
     Serial.print("): ");
     Serial.println(Address_Register[String_Split[0]]);
     
     serial_read_address(); // อ่านค่าจาก Serial
   }
 }
}


void loop(){
  /*
  	อ่านค่าจาก Serial และอัพเดทค่าแบบ Realtime
  */
  
  serial_write_address();
  update_status();
}

/*
----------------------------------------------------------------------------------
|				           |                   Input Register Parameter     		         |
|Address (Register)|-------------------------------------------------------------|
|				           |       Description       |               Value               |
|--------------------------------------------------------------------------------|
|						                         Coils							           			         |
|--------------------------------------------------------------------------------|
|	       1		     |         Mode LED        |  0 is Off, 1 is On with PWM Value |
|		     2		     |         Mode Fan        |  0 is Off, 1 is On with PWM Value |
|--------------------------------------------------------------------------------|
|					                    	 Input register		  	  		  		  		         |
|--------------------------------------------------------------------------------|
|	    	 1	       |      Device Address     |                 -                 |
|--------------------------------------------------------------------------------|
|				                     	 Holding register		  	      	 	   	  	         |
|--------------------------------------------------------------------------------|
|	     	 10	       |        PWM LED 1        |              MAX 4095             |
|		     11	       |        PWM LED 2        |              MAX 4095             |
|	    	 12	       |        PWM LED 3        |              MAX 4095             |
|	     	 13	       |        PWM LED 4        |              MAX 4095             |
|	    	 14	       |        PWM LED 5        |              MAX 4095             |
|		     15		     |        PWM LED 6        |              MAX 4095             |
|	    	 16		     |        PWM LED 7        |              MAX 4095             |
|		     17		     |        PWM LED 8        |              MAX 4095             |
|			    	       |                         |                 -                 |
|		     20		     |      Time on LED 1      |             MAX 65535             |
|		     21		     |      Time on LED 2      |             MAX 65535             |
|		     22		     |      Time on LED 3      |             MAX 65535             |
|	       23		     |      Time on LED 4      |             MAX 65535             |
|	       24		     |      Time on LED 5      |             MAX 65535             |
|	    	 25		     |      Time on LED 6      |             MAX 65535             |
|	    	 26		     |      Time on LED 7      |             MAX 65535             |
|	    	 27		     |      Time on LED 8      |             MAX 65535             |
|		               |                         |                 -                 |
|	    	 40		     |      Time off LED 1     |             MAX 65535             |
|	    	 41		     |      Time off LED 2     |             MAX 65535             |
|	    	 42		     |      Time off LED 3     |             MAX 65535             |
|	    	 43		     |      Time off LED 4     |             MAX 65535             |
|		     44		     |      Time off LED 5     |             MAX 65535             |
|	    	 45		     |      Time off LED 6     |             MAX 65535             |
|	    	 46		     |      Time off LED 7     |             MAX 65535             |
|		     47		     |      Time off LED 8     |             MAX 65535             |
|				           |                         |                 -                 |
|	    	 60		     |        PWM Fan 1        |              MAX 255              |
|	    	 61		     |        PWM Fan 2        |              MAX 255              |
|			    	       |                         |                 -                 |
|	    	 80		     |      Time on Fan 1      |             MAX 65535             |
|	    	 81		     |      Time on Fan 2      |             MAX 65535             |
|				           |                         |                 -                 |
|	    	100		     |      Time off Fan 1     |             MAX 65535             |
|	    	101	    	 |      Time off Fan 2     |             MAX 65535             |
----------------------------------------------------------------------------------
*/