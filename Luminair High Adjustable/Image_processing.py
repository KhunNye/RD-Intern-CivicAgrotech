# Lighting Height Adjustable

import cv2
import numpy as np

kernel = np.ones((3,3),np.uint8)

# ประกาศเป็น True หากจะทดสอบโปรแกรม หรือสอบเทียบค่าจริง
# ประกาศเป็น False หากจะนำไปใช้จริง
testProgram = True

def Actual_tree_scale(Pixel_mesurement):
    """
    ฟังก์ชั่นคูณปรับค่าจริงให้กับความสูงของต้นไม้ โดยจะเก็บข้อมูล pixel ที่ตรวจจับได้จากโปรแกรมนี้ และความสูงที่วัดได้จริงจากโคมไฟ
    ลงมาถึงยอดสูงสุดของต้นไม้ (อย่าลืมเซ็ตให้ขอบบนของภาพอยู่ที่ปลายล่างสุดของโคมพอดี) หลังจากทำการทดลองซ้ำๆ และนำผลมาเฉลี่ย
    กันก็จะได้สูตรข้างล่างนี้
    """

    # ถ้า pixel ที่วัดได้มากกว่า 300 จะปรับ Actual scale เป็น 0 เสมอ
    # เหตุการนี้มักจะเกิดขึ้นจากการที่ไม่มีถาดวางอยู่ที่ชั้นปัจจุบัน แต่ไป detect พืชที่วางอยู่ชั้นล่างของชั้นปัจจุบัน
    # ทำให้ pixel ที่วัดได้มีค่าเยอะมากๆ
    Calibration = 0

    if Pixel_mesurement < 150: # เมื่อ px อยู่ในช่วง 0 - 150
        # ที่ 138 px วัดความสูงจริงได้ 8.1 cm
        Calibration = abs(Pixel_mesurement*8.1/138)
    elif Pixel_mesurement < 170: # เมื่อ px อยู่ในช่วง 150 - 170
        # ที่ 153 px วัดความสูงจริงได้ 8.1 cm
        Calibration = abs(Pixel_mesurement*8.1/153)
    elif Pixel_mesurement < 190: # เมื่อ px อยู่ในช่วง 170 - 190
        # ที่ 153 px วัดความสูงจริงได้ 8.1 cm
        Calibration = abs(Pixel_mesurement*10.4/185)
    elif Pixel_mesurement < 200: # เมื่อ px อยู่ในช่วง 190 - 200
        # ที่ 173 px วัดความสูงจริงได้ 12.4 cm
        Calibration = abs(Pixel_mesurement*12.4/173)
    elif Pixel_mesurement < 300: # เมื่อ px อยู่ในช่วง 200 - 300
        # ที่ 210 px วัดความสูงจริงได้ 16.9 cm
        Calibration = abs(Pixel_mesurement*16.9/210)

    return Calibration

def find_percentage_and_distance_between_lamp_and_tree(upp, low):
    """
    ฟังก์ชั่นตรวจสอบความสูงของต้นไม้จากขอบบนของภาพลงมา ณ จุดสูงสุดของ pixel สีเขียวในภาพ
    """

    # cap = cv2.VideoCapture(0) # เอา Comment ออกหากต้องการใช้กล้องหน้าโน๊ตบุค หรือ Webcam

    # โหลดโปรแกรมกล้องวงจรปิดของกล้องมาก่อน จากนั้นตั้งรหัสและนำรหัสมาใส่แทน (12345678)
    # หาก error ให้ใช้ Advanced IP Scanner สแกนหา IP Address (192.168.20.150:10554) ใหม่และมาแทนลงในข้างล่างนี้
    # ถามให้พี่กายทำให้ง่ายสุด

    # เปิดกล้องวงจรปิดไวไฟ
    # ระวัง ภาพที่อ่านได้อยู่ในระบบพิกัด (Blue, Green, Red) (BGR) ไม่ใช่ (Red, Green, Blue) (RGB)
    cap = cv2.VideoCapture('rtsp://admin:12345678@192.168.20.150:10554/tcp/av0_0\'')
    check , Photo = cap.read() # รับภาพจากกล้อง frame ต่อ frame
    cap.release() # เคลียแรม, เคลียเฟรมที่เหลือของวีดีโอออก เนื่องจากเราต้องการแค่ภาพเดียว

    # หากเกิดความผิดพลาดในการอ่านภาพ จะสั่งจบฟังก์ชั่นนี้โดยส่งค่าตัวแปร เปอร์เซนสีเขียวในภาพ และความสูงต้นไม้ที่วัดได้
    if not check:
        return [0, 0]
    
    # กล้องวงจรปิดมี resolution 2688*1520 เนื่องจากมันใหญ่เกินไป และยังเป็นการเพิ่ม error ให้กับโปรแกรม
    # ตรวจจับความสูงจึงลด resolution เหลือ 1920*1080 แต่อันนี้ดีกว่า 1280*720
    Photo = cv2.resize(Photo,(1280,720))
    # Photo = Photo[0:720, 0:1280] # Comment ออกหากต้องการตัดภาพ
    # เก็บความกว้างของภาพ (แกน Y) และความยาวของภาพ (แกน X) 
    y_Size_of_image, x_Size_of_image, _ = Photo.shape
    # เปลี่ยนระบบพิกัดของภาพจาก BGR เป็น HSV เพราะง่ายต่อการเลือกช่วง Mask สี
    hsv = cv2.cvtColor(Photo, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv,low,upp) # Mask สี ตัดช่วงสีที่ไม่ได้อยู่ในขอบเขตที่เราต้องการในภาพออกทั้งหมด
    # ลด Noise ของภาพด้วยกระบวนการ Morphological ด้วยการเปิดภาพ
    # การเปิดภาพในขั้นแรกจะทำการกร่อนภาพ erosion ก่อนด้วย array kernel ที่กำหนด เพื่อลบจุด pixel noise เล็กๆออกไปก่อน
    # แต่เนื่องจากการกร่อนภาพจะทำให้ภาพเล็กลงจึงทำการบวมภาพ dilation กลับเพื่อขยายภาพเล็กน้อยทดแทนรอยกร่อนของภาพจริง
    # ที่เกิดจากการ ลด noise
    opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # สร้างเส้นเค้าโครงรอบๆ บริเวณที่ mask สีออกมา
    contour,_ = cv2.findContours(opening,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    y_max, y_min, x_max, x_min = None, None, None, None

    # หาจุดสูงสุดต่ำสุดของภาพเพื่อหาจุดกระจุกตัวของพื้นที่สีเขียวในภาพ
    for cn in contour:
        if len(cn) > 0:  # เช็คว่าในขอบเขตปัจจุบันมีจุด contour มากกว่า 1 จุดไหม
            x_min_contour = cn[cn[:, :, 0].argmin()][0][0]
            x_max_contour = cn[cn[:, :, 0].argmax()][0][0]
            y_min_contour = cn[cn[:, :, 1].argmin()][0][1]
            y_max_contour = cn[cn[:, :, 1].argmax()][0][1]

            # ถ้าเกิดว่าขอบเขตใดเป็นค่าว่างให้เอาค่าที่คำนวณได้ใส่ลงไปเลย
            if x_min is None or x_max is None or y_min is None or y_max is None:
                x_min, x_max, y_min, y_max = x_min_contour, x_max_contour, y_min_contour, y_max_contour
            else:
                # หากมีค่าอยู่แล้วจะทำการเช็คค่าปัจจุบันว่ามากกว่าหรือหน้อยกว่าค่าใหม่ หากเป็นไปตามเงื่อนไขจะแทนค่าใหม่
                x_min = min(x_min, x_min_contour) # เช็คว่าค่าใหม่(น้อยกว่า)ค่าปัจจุบันไหม
                x_max = max(x_max, x_max_contour) # เช็คว่าค่าใหม่(มากกว่า)ค่าปัจจุบันไหม
                y_min = min(y_min, y_min_contour) # เช็คว่าค่าใหม่(น้อยกว่า)ค่าปัจจุบันไหม
                y_max = max(y_max, y_max_contour) # เช็คว่าค่าใหม่(มากกว่า)ค่าปัจจุบันไหม

    # หากไม่มีการแทนค่าเลย หรือไม่เจอ contour จะกำหนดให้ขอบเขตนั้นๆเป็น 0
    if y_max == None:
        y_max = 0
    if y_min == None:
        y_min = 0
    if x_max == None:
        x_max = 0
    if x_min == None:
        x_min = 0

    print(x_max, x_min, y_max, y_min)

    # crop ภาพที่ผ่านการ mask สีมาแล้วด้วยขอบเขตที่คำนวณได้
    color_boundary = mask[y_min:y_max, x_min:x_max]
    # เนื่องจากภาพที่ไ้จากการ mask เป็นภาพ Binary คือ มีแค่ขาวและดำ
    # ดังนั้นเราจะนับจุดสีขาวที่อยู่ในภาพ crop ออกมาทั้งหมด
    color_pixels = cv2.countNonZero(color_boundary)
    # หาจุด pixel ทั้งหมดที่บริเวณ crop ภาพออกมา
    total_pixels = (x_max-x_min) * (y_max-y_min)

    # ปรับ Default ให้เป็น 0 เผื่อกรณีที่โปรแกรมหาเส้น contour ไม่เจอ
    percentage = 0
    Distance_from_top_to_tree = 0

    if len(contour) > 0: # หากมีเส้น contour อยู่จะเข้าเงื่อนไข
        percentage = (color_pixels / total_pixels) * 100 # คำนวณค่า % ของพื้นที่สีเขียวในขอบเขตที่กำหนด
        Distance_from_top_to_tree = Actual_tree_scale(y_min) # นำ px ที่วัดได้ไปคูณปรับค่าจริงเป็น cm

    print("total_pixels: ", total_pixels)
    print("x/y-Size:", x_Size_of_image, y_Size_of_image)
    print("x-max/min, y-max/min:", x_max, x_min, y_max, y_min)
    print("Percentage of color: ", percentage)
    print("Distance from top to tree: ", y_min,"px, ", Distance_from_top_to_tree,"cm")

    if testProgram:
        # วาดเส้น contour ทับภาพที่ถ่ายมา
        cv2.drawContours(Photo, contour, -1, (0,0,255), 2)
        # ตีเส้นหาจุดสูงสุดของยอดต้นไม้ที่ภาพเห็น
        cv2.line(Photo, (0,int(y_min)), (int(x_Size_of_image), int(y_min)), (0,0,255), 5)
        # แสดงผลจากการคำนวณออกมาเป็นรูปภาพ
        cv2.imshow("Color Detection", Photo)

        # รอให้ผู้ใช้กดปุ่มอะไรก็ได้เพื่อปิดหน้าต่างรูปภาพและดำเนินโปรแกรมต่อ
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    return [percentage, Distance_from_top_to_tree]

def green_Detection():
    """
    เลือก Hue, Saturation, Brightness ที่เหมาะสมในสภาพแวดล้อมที่ต้องการใช้โปรแกรมนี้ตรวจจับความสูงต้นไม้
    """

    # ค่าเหล่านี้ต้องปรับหน้างานหากมีการเปลี่ยนสภาพแวดล้อมของการตรวจจับ
    low = np.array([30, 20, 20]) # กำหนดขอบล่างของสีเขียวในระบบพิกัด HSV
    upp = np.array([85, 255, 255]) # กำหนดขอบบนของสีเขียวในระบบพิกัด HSV

     # เรียกใช้ฟังก์ชั่นตรวจจับความสูงของต้นไม้จากขอบเขตล่าง ละขอบเขตบนที่กำหนดไว้
    return find_percentage_and_distance_between_lamp_and_tree(upp, low)

# green_Detection() # Comment ออกเพื่อทดสอบ ทดลองปรับ Calibration ใหม่ของ function นี้
