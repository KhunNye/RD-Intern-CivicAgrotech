# วิธีการใช้งานแบบ auto
# กดรัน และพิมพ์ auto ที่ Serial monitor จากนั้นรอเพื่อใส่ค่า offset รอชมการดำเนินการได้เลย
#
# วิธีการใช้งานแบบ manual
# คำสั้งควบคุมความสูงดวงโคม
# BA (flr) (dir) (dis) FF FF FF
# flr (Floor) สามารถใส่: 01, 02, 03, 04, 05
# dir (direction) สามารถใส่: 6C, 72
# dis (distance) สามารถใส่เลขฐาน 16 ได้ตั้งแต่: 10, 11, 12, ..., FD, FE, FF
# คำสั้งใช้บ่อย (Set Zero)
# BA 01 72 00 FF FF FF
# BA 02 72 00 FF FF FF
# BA 03 72 00 FF FF FF
# BA 04 72 00 FF FF FF
# BA 05 72 00 FF FF FF
#
# คำสั้งควบคุมลิฟผ่าน pulse
# 0x4D (dir) (pul) 0x00 0xFF 0xFF 0xFF
# dir (direction) สามารถใส่: 6C, 72
# pul (pulse) สามารถใส่เลขฐาน 16 2 หลักได้ตั้งแต่: 00 00, 00 01, ..., FF FE, FF FF
# คำสั้งใช้บ่อย
# 4D 6C F4 01 00 FF FF FF (up 500 pulse)
# 4D 6C D0 07 00 FF FF FF (up 2000 pulse)
# 4D 6C 10 27 00 FF FF FF (up 10000 pulse)
# 4D 6C 20 4E 00 FF FF FF (up 20000 pulse)
#
# คำสั้งระบุว่าลิฟอยู่ที่ชั้นไหน
# (บางทีลิฟมันเข้าใจว่าอยู่ที่ชั้นอื่นไม่ใช่ชั้นที่มันจอดอยู่)
# FA (flr) 00 00 FF FF FF ช่องว่างใส่ตำแหน่งลิฟต์ปัจจุบัน
# flr (Floor) สามารถใส่: 01, 02, 03, 04, 05
# คำสั้งใช้บ่อย 
# FA 01 00 00 FF FF FF (บอกว่าลิฟอยู่ชั้น 1 นะ)
# FA 02 00 00 FF FF FF (บอกว่าลิฟอยู่ชั้น 2 นะ)
#
# คำสั้งควบคุมลิฟอาศัย limitor
# 6C (flr) FF FF FF ช่องว่างใส่ตำแหน่งลิฟต์ที่จะให้จอด
# flr (Floor) สามารถใส่: 01, 02, 03, 04, 05
# คำสั้งใช้บ่อย 
# 6C 01 FF FF FF (เคลื่อนลิฟไปชั้น 1)
# 6C 02 FF FF FF (เคลื่อนลิฟไปชั้น 2)

import serial
import time

from Image_processing import green_Detection

file_path = 'tempValue.txt'

Serial = serial.Serial(port='COM3', baudrate=115200, timeout=0.1)

Layer_totals = 5  # กำหนดจำนวนของชั้นปลูกพืชทั้งหมดกี่ชั้น

def Read_lamp_distance(Layer):
    """
    ฟังก์ชันนี้จะอ่านค่าระยะห้อยของดวงโคมที่ชั้นปลูกพืชทั้ง 5 ชั้น (บรรทัดที่ 1-5 คือ ชั้นที่ 1-5) ที่บันทึกไว้ออกมาใช้
    """

    with open(file_path, 'r') as file: # เปิดไฟล์ที่เก็บระยะห้อยของดวงโคมที่ชั้นปลูกพืชแต่ละชั้น
        lines = file.readlines() # อ่านตัวเลขแต่ละบรรทัดออกมา โดยแต่ละบรรทัดจะแทนระยะห้อยแต่ละชั้นของชั้นปลูก
    
    return lines[Layer - 1] # Array เริ่มที่ 0 แต่บรรทัดเริ่มที่ 1 จึงลบ 1 ให้เริ่มที่ 0

def Backup_lamp_distance(Layer, Replace_value):
    """
    ฟังก์ชันนี้จะอัพเดทค่าตำแหน่งระยะห้อยที่โคมไฟเลื่อนไปแต่ละชั้นอยู่เสมอ เขียนลงไปใน file_path 
    """

    # อ่านข้อมูลจากระยะห้อยตั้งแต่ชั้นที่ 1-5 มาใส่ Array lines
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # แทนค่าระยะห้อยปัจจุบันลงไปใน Array ที่เก็บข้อมูลของระยะห้อยแต่ละชั้น (บรรทัด) แทนค่าที่กำหนดมาลงไป
    lines[Layer - 1] = str(Replace_value) + '\n'  # ปรับ index เนื่องจาก Array เริ่มที่ 0

    # เขียนค่าจาก Array กลับลงไปที่ file_path
    with open(file_path, 'w') as file:
        file.writelines(lines)

def MotorControl(Text_serial):
    """
    ฟังก์ชันนี้จะรับข้อความจาก serial มาเป็นข้อมูลเป็นเลขฐาน 16 อยู่ในรูปของ String โดยจะทำการแบ่ง Byte ออกมา
    เพื่อแปลความหมายจากนั้นทำการอัพเดทค่าลงไปใน file path
    จากนั้นจะทำการ write serial อนุกรมลงไปใน tx rx เพื่อส่ง serial ไปสั่งการ board ให้บอร์ดตัดสินใจสั่งการ Slave
    ตามรหัส serial ที่่ส่งไป
    """

    Text_hex_list = Text_serial.split(" ") # แบ่ง Byte ออกมาด้วยช่องว่าง
    # สร้าง Array เก็บเลขฐาน 16 โดยจะแปลงเลขฐาน 16 ในรูป String แปลงเป็นเลขฐาน 16 ในรูป int16
    Hex_list = [int(x, 16) for x in Text_hex_list]

    # BA เป็นรหัสสำหรับสั่งควบคุมโคมขึ้นลง
    if Text_hex_list[0] == "BA":
        # ถ้า Byte ที่ 3 เป็นไปตามเงื่อนไข
        if Text_hex_list[2] == "6C": # 6C จะสั่งให้มอเตอร์เคลื่อนโคมขึ้น
            Current_height = int(Read_lamp_distance(Hex_list[1])) - Hex_list[3] # อัพเดทค่า
        elif Text_hex_list[2] == "72": # 72 จะสั่งให้มอเตอร์เคลื่อนโคมลง
            Current_height = int(Read_lamp_distance(Hex_list[1])) + Hex_list[3] # อัพเดทค่า

        time_to_move = int(abs(Hex_list[3])/8) # คำนวณเวลาที่โคมเคลื่อนที่โดยประมาณ

        if Current_height < 0: # หากคำนวณค่าที่อัพเดทแล้วติดลบ จะปรับเป็น 0
            Current_height = 0

        Backup_lamp_distance(Hex_list[1], Current_height) # เก็บค่าที่สั่งการล่าสุดไปที่ file_path
        Serial.write(bytes(Hex_list)) # สั่งมอเตอร์ทำงานผ่านการ write Serial
        print("The lamp is adjusting its height, please wait...")
        time.sleep(time_to_move) # รอเวลาโคมเคลื่อนที่ไประยะห้อยที่กำหนด
        print("The lamp stop at: ", Hex_list[3])

    # 6C เป็นรหัสสำหรับสั่งควบคุมลิฟขึ้นลง สามารถสั่งด้วยเลขขอลชั้นที่ต้องการไปถึงได้เลย
    elif Text_hex_list[0] == "6C":
        Current_layer = int(Read_lamp_distance(6)) # อ่านบรรทัดที่ 6 ของ file_path ซึ่งเป็นค่าที่จำว่าปัจจุบันลิฟอยู่ชั้นไหน
        Serial.write(bytes(Hex_list)) # สั่งลิฟเคลื่อนที่ไปชั้นที่กำหนด
        Backup_lamp_distance(6, Hex_list[1]) # อัพเดทค่า
        print("Elevator in motion, please wait...")
        time.sleep(13*abs(Current_layer-Hex_list[1])) # รอลิฟเคลื่อนที่ไปที่ชั้นถัดไป
        print("The Elevator stop at: ", Hex_list[1])
    
    # 4D เป็นรหัสสำหรับสั่งควบคุมลิฟขึ้นลง ผ่าน pulse ของมอเตอร์
    elif Text_hex_list[0] == "4D":
        Serial.write(bytes(Hex_list)) # สั่งลิฟเคลื่อนที่ไปชั้นที่กำหนด
        print("Elevator in motion, please wait...")
        time.sleep(6) # รอลิฟเคลื่อนที่ไปที่ชั้นถัดไป
        print("Warnted! The Elevator stop in half layer")
    else:
        Serial.write(bytes(Hex_list))

    print("Write Serial: ", Hex_list)
    print("\n")

#def Serial_Reading():
#    Height = []
#
#    while True:
#        time.sleep(1)
#        if Serial.in_waiting > 0:
#            SerialRead = Serial.read(Serial.in_waiting)
#            print("serialRead: ", SerialRead)
#
#            decodeRead = SerialRead.decode('latin-1')
#            print("decodeRead: ", decodeRead)
#
#            Height = re.findall(r'\d+', decodeRead)
#            print("Height: ", Height)
#        else:
#            if len(Height) > 1:
#                print("_End_sub_function_______________________________________")
#                return float(Height[-2])
#            else:
#                return 0

def Reset_moving_lamp(Layer):
    """
    ฟังก์ชันนี้จะทำการปรับระยะห้อยของโคมกลับไปที่จุดเริ่มต้น โดยอาศัยค่าที่บันทึกใน file_path ว่าล่าสุดอยู่ห้อยลงมาที่ตำแหน่งไหน
    จากนั้นจะทำการสั่งให้มอเตอร์หมุนขึ้นเท่ากับระยะทางที่ห้อยลงมาเท่าระยะทางนั้น
    """

    lamp_distance = int(Read_lamp_distance(Layer)) # อ่านค่าระยะห้อยปัจจุบันที่เก็บไว้ใน file_path ของแต่ละชั้น
    
    if lamp_distance > 0: # ถ้าระยะห้อยไม่เท่ากับ 0
        time_to_wait = int(int(Read_lamp_distance(Layer))/16) # คำนวณค่าเวลาที่โคมใช้เคลื่อนที่โดยประมาณ

        # เปลี่ยนเลขฐาน 16 ที่เป็น String เป็น int จากนั้นส่ง Hex String ไปที่ฟังก์ชั่นควบคุมมอเตอร์
        # เพื่อสั่งให้โคมเคลื่อนที่ไปที่ระยะเริ่มต้น หรือระยะ Zero
        MotorControl("BA " + format(Layer, '02X')  + " 6C " + format(lamp_distance, '02X') + " FF FF FF")
        time.sleep(1 + 2*time_to_wait) # รอเวลาโคมเคลื่อนที่ไประยะห้อยที่กำหนด
        print("Stop at: -", format(lamp_distance, '02X'))

def cmToHex(Calibration):
    """
    ฟังก์ชั่นนี้จะแปลงระยะห้อยโคมจากหน่วย cm เป็นเลขฐาน 16 เพื่อใช้ส่ง Serial ไปควบคุมมอเตอร์ซึ่งจากการทดลองเก็บข้อมูล
    จะพบค่าความสัมพันธ์ระหว่างเลขฐาน 16 ที่สั่งการไปกับระยะห้อยที่วัดได้จริงในหน่วย cm เป็นไปดังตารางบันทึกข้อมูล

    บันทึกข้อมูล
    ---------------------------------------------------------------------
    |   0x      |   10     |   20     | 30      |   40      |   50      | (เลขฐาน 16 ที่ส่ง Serial ไปควบคุมมอเตอร์)
    |   int-16  |   16     |   32     | 48      |   64      |   80      | (เลขฐาน 10 ที่แปลงจากฐาน 16)
    |   cm:     |   1.5    |   3.5    | 6.7     |   9.4     |   12.2    | (ระยะห้อยจริงหน่วย cm เมื่อสั่งชั้นไปตามเลขฐาน 16 ที่ส่ง Serial ไป)
    |   0x/cm:  |   10.67  |   9.143  | 7.164   |   6.809   |   6.557   | (สร้างตัวคูณปรับค่าจาก cm เป็นเลขฐาน 16)
    ---------------------------------------------------------------------
    """  

     # เมื่อระยะห้อยที่ประมาณจาก Image processing มีค่าตามเงื่อนไข
    if Calibration < 0: # หากระยะห้อยที่คำนวณได้ติดลบ
        Calibration = 0 # ปรับเป็น 0 เสมอ
    elif Calibration < 1: # ระยะห้อยอยู่ในช่วง 0 - 1 cm
        Calibration *= 10.67 # 0x/cm  
    elif Calibration < 4: # ระยะห้อยอยู่ในช่วง 1 - 4 cm
        Calibration *= 9.143 # 0x/cm  
    elif Calibration < 7: # ระยะห้อยอยู่ในช่วง 4 - 7 cm
        Calibration *= 7.164 # 0x/cm  
    elif Calibration < 10: # ระยะห้อยอยู่ในช่วง 7 - 10 cm
        Calibration *= 6.809 # 0x/cm  
    else: # ระยะห้อยมากกว่า 10 cm
        Calibration *= 6.557 # 0x/cm  

    return Calibration

try:
    while True:
        user_input = input("fiveHex: ") # รับค่า input จาก serial monitor

        if user_input == "exit":
             # (exit) คำสั่งจบการทำงานของโปรแกรม
            print("exit")
            break
        elif user_input == "auto":
             # (auto) คำสั่งเคลื่อนโคมแต่ละชั้น

            for i in range(0,5): # Set Zero ระยะห้อยของดวงโคมทั้ง 5 ชั้น
                Reset_moving_lamp(i+1)
            
            Offset_direction = input("Offset (cm): ") # กำหนดระยะที่ต้องการให้โคมไฟห่างจากพืช

            if Offset_direction == "exit": # หากพิมพ์ exit ใส่ค่า Offset จะสั้งจบการทำงานของโปรแกรมทันที
                break

            for i in range(0,Layer_totals): # วน loop จาก 0 ถึงชั้นสูงสุดที่กำหนดไว้
                print("Layer: ", i+1)
                
                MotorControl("6C " + format(i+1, '02X') + " FF FF FF") # เคลื่อนลิฟขึ้นไปทีละชั้นเริ่มจากชั้นหนึ่งถึงชั้นสุดท้ายที่กำหนดตาม Layer_totals
                # เคลื่อนลิฟลงมา 20000 pulse จะเป็นระยะระหว่างชั้นปัจจุบันกับชั้นข้างล่างโดยประมาณ
                MotorControl("4D 72 20 4E 00 FF FF FF")
                time.sleep(5) # หน่วงเวลารอกล้องหยุดสั่นโดยประมาณ

                Count = 0

                while Count < 3:
                    time.sleep(0.2) # หน่วงเวลาเล็กๆให้ลูป
                    Green_tree_Detection_List = green_Detection() # วัดพื้นที่สีเขียวในภาพ และวัดความสูงยอดไม้ด้วย Image processing

                    if Green_tree_Detection_List: # เช็คว่ามีค่า return กลับมาไหม
                        Percentage_of_Green, tree_height = Green_tree_Detection_List # รับค่า % พื้นที่สีเขียวในภาพ และความสูงยอดต้นไม้

                        if Percentage_of_Green > 0: # ถ้ามีพื้นที่สีเขียวในภาพแม้เพียงนิด

                            print("Percentage of Green pass: ", Percentage_of_Green)
                            # tree_height เป็นค่าทีวัดจากตำแหน่ง Zero ของโคมไฟลงมาถึงยอดสูงสุดของต้นไม้
                            # และค่า offset คือ ค่าที่ต้องการให้โคมห่างจากต้นไม้เป็นระยะเท่านั้น
                            # ดังนั้นจะต้องเคลื่อนโคมลง tree_height ลบด้วย 
                            Move_Lamp_to = float(tree_height - int(Offset_direction)) # คำนวณระยะที่โคมจะเคลื่อนลงมา
                            Move_Lamp_to = cmToHex(Move_Lamp_to) # แปลงระยะเคลื่อนจาก cm เป็นเลขฐาน16

                            Move_Lamp_hex = format(int(Move_Lamp_to), '02X') # แปลงเลขฐาน 16 ที่อยู่ในรูป int16 เป็น string
                            # ส่ง hex string ไป backup ข้อมูล และ write serial เพื่อควบคุมมอเตอร์
                            MotorControl("BA " + format(5-i, '02X') + " 72 " + Move_Lamp_hex + " 10 FF FF FF")
                            print("Move Lamp to (cm), (hex): ",str(Move_Lamp_to), Move_Lamp_hex)
                            break
                        else:
                            print("Percentage of Green too low: ", Percentage_of_Green)
                    Count += 1 # นับเวลา
                
                if Count == 15: # ใน 3 วิถ้ายังคงไม่สามารถตรวจหาวัตถุสีเขียวในภาพได้จะจบการทำงานเงื่อนไขนี้
                    print("Time out please try again!")

                MotorControl("4D 6C 20 4E 00 FF FF FF") # เคลื่อนลิฟขึ้นไป 20000 pulse ที่ชั้นเดิมที่มันควรจะอยู่

            MotorControl("6C 01 FF FF FF") # เมื่อวนลูปจนถึงชั้นสุดท้ายแล้วจะสั่งลิฟให้กลับลงมาที่ชั้นหนึ่ง
            print("_______________________________________")

        elif user_input == "lift":
             # (lift) คำสั่งเคลื่อนลิฟขึ้น หรือลงตามจำนวน step ที่กำหนดเอง โดยแต่ละ step จะเคลื่อนที่ไป 2000 pulse

            step = int(input("step: ")) # กำหนดจำนวน step ที่ต้องการ

            direction = int(input("Up(1) Down(0): ")) # เลือกว่าจะสั่งให้ลิฟขึ้น(1) หรือลง(0)

            if direction == 1: # สั่งให้ลิฟขึ้น
                for i in range(0, step):
                    MotorControl("4D 6C D0 07 00 FF FF FF") # เคลื่อนลิฟขึ้นทีละ 2000 step
                    time.sleep(1) # รอเวลาลิฟเคลื่อนไปยังจุดหมายโดยประมาณ
            elif direction == 0: # สั่งให้ลิฟลง
                for i in range(0, step):
                    MotorControl("4D 72 D0 07 00 FF FF FF") # เคลื่อนลิฟลงทีละ 2000 step
                    time.sleep(1) # รอเวลาลิฟเคลื่อนไปยังจุดหมายโดยประมาณ
        else: # นอกเหนือจากเงื่อนไขที่กำหนดจะเป็นการควบคุมผ่าน Serial โดยตรง กรุณาใส่เลขฐาน 16 เท่านั้น
            MotorControl(user_input)# ส่ง hex string ไป backup ข้อมูล และ write serial เพื่อควบคุมมอเตอร์
            print("________________________________________")

finally:
    Serial.close() # ปิดการเชื่อมต่อ port สำหรับการสื่อสารแบบ Serial