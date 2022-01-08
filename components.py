from numpy import result_type
import RPi.GPIO as GPIO
from gpiozero import LineSensor, DistanceSensor
from time import sleep
from PIL import Image
from picamera import PiCamera
import pytesseract

class Motor:
    def __init__(self, pwm_pin, dir1, dir2):
        # initialize a motor object by setting the pwm and direction pins as outputs
        self.pwm_pin = pwm_pin
        self.dir1 = dir1
        self.dir2 = dir2
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(dir1,GPIO.OUT)
        GPIO.setup(dir2,GPIO.OUT)
        GPIO.setup(pwm_pin,GPIO.OUT)
        GPIO.output(dir1,GPIO.LOW)
        GPIO.output(dir2,GPIO.LOW)

        # assign a PWM signal to the pwm pin and set its frequency (1000 Hz)      
        self.pwm = GPIO.PWM(pwm_pin, 1000)
    
    def actuate(self, direction, duty_cycle):
        # actuate the motor in the clockwise or counter clockwise direction and set the speed using duty cycle
        if direction == "cw":
            GPIO.output(self.dir1, GPIO.HIGH)
            GPIO.output(self.dir2, GPIO.LOW)

        elif direction == "ccw":
            GPIO.output(self.dir1, GPIO.LOW)
            GPIO.output(self.dir2, GPIO.HIGH)

        else:
            print("direction must be cw or ccw")
            return

        # output a PWM signal on the pwm pin and set its duty cycle
        self.pwm.start(duty_cycle)
    
    def stop(self):
        # stop the motor by setting both direction pins to LOW
        GPIO.output(self.dir1, GPIO.LOW)
        GPIO.output(self.dir2, GPIO.LOW)

class Rover:
    def __init__(self, motorR, motorL, servomotor, right_sensor, left_sensor, distance_sensor):
        # initialize a rover object using its components
        self.motorR = motorR
        self.motorL = motorL
        self.servomotor = servomotor
        self.right_sensor = right_sensor
        self.left_sensor = left_sensor
        self.distance_sensor = distance_sensor
    
    def move(self, direction, duty_cycle = 50):
        # move the rover in a chosen direction and speed. the default duty cycle is 50%
        
        if direction == "forward":
            # right and left motors rotate in the clockise direction  
            self.motorR.actuate("cw", duty_cycle)
            self.motorL.actuate("cw", duty_cycle)     
        
        elif direction == "backward":
            # right and left motors rotate in the counter clockise direction  
            self.motorR.actuate("ccw", duty_cycle)
            self.motorL.actuate("ccw", duty_cycle)
                 
        elif direction == "right":
            # right motors rotate clockwise, left motors rotate clockwise
            self.motorR.actuate("ccw", duty_cycle)
            self.motorL.actuate("cw", duty_cycle)
            
        elif direction == "left":
            # left motors rotate clockwise, right motors rotate clockwise 
            self.motorR.actuate("cw", duty_cycle)
            self.motorL.actuate("ccw", duty_cycle)

        else:
            print("direction must be forward, backward, left, or right")
        
    def stop(self):
        # stop the rover by stopping the right and left motors
        self.motorR.stop()
        self.motorL.stop()
    
    def approach(self, data):
        # approach the target gradually until a distance of 13 cm is reached
        while self.distance_sensor.distance > 0.13:
            self.move("forward", 45)
            sleep(0.1)
            self.stop()
            sleep(0.05)
            # print("approach distance: " + str(self.distance_sensor.distance))

    def avoid(self, direction, data, duty_cycle = 50):
        # avoid the obstacle in a certain direction (right or left)

        self.move("backward", 55)
        sleep(0.7)
        self.stop()

        if direction == "right":
            self.move("right", 80)
            sleep(0.6)
            self.move("forward", duty_cycle)
            sleep(2.7)
            self.move("left", 80)
            sleep(1.1)
            self.stop()
            sleep(0.2)
            self.move("forward", 38)
            data.append(self.distance_sensor.distance)

            # continue moving forward until the right sensor detects the line (the line is centered between the IR sensors)
            while True:
               if int(self.right_sensor.value) == 0:
                   self.move("right",100)
                   sleep(0.3)
                   self.stop()
                   sleep(0.2)
                   break

        elif direction == "left":
            self.move("left", 80)
            sleep(0.6)
            self.move("forward", duty_cycle)
            sleep(2.3)
            self.move("right", 100)
            sleep(0.7)
            self.stop()
            sleep(0.2)
            self.move("forward", duty_cycle)

            # continue moving forward until the left sensor detects the line (the line is centered between the IR sensors)
            while True:
               if int(self.left_sensor.value) == 0:
                   self.move("left",100)
                   sleep(0.3)
                   self.stop()
                   sleep(0.2)
                   break

        else:
            print("direction should be right or left")

    def push(self):
        # push the object: rotate the arm of the servomotor by changing the pwm duty cycle
        self.servomotor.servo_pwm.start(2.5)
        self.servomotor.servo_pwm.ChangeDutyCycle(11)
        sleep(2)
        self.servomotor.servo_pwm.ChangeDutyCycle(5)
        sleep(2)
        self.servomotor.servo_pwm.ChangeDutyCycle(11)
        sleep(2)
        self.servomotor.servo_pwm.stop()

class ServoMotor:
    def __init__(self, servo_pin):
        # initialize the servomotor by selecting the signal pin as output
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(servo_pin, GPIO.OUT)
        # assign a PWM signal to the signal pin and set its frequency (50 Hz)
        self.servo_pwm = GPIO.PWM(servo_pin, 50)

class Camera:
    def __init__(self):
        # initialize a camera using the picamera library
        self.picamera = PiCamera()
    
    def read(self):
        print("camera reading...")
        self.picamera.start_preview()
        sleep(0.5)
        # capture an image and save it in the project folder
        self.picamera.capture('/home/pi/Desktop/MCE/sign.png')
        self.picamera.stop_preview()

        # detect a string in the image using the Tesseract library
        img =Image.open('sign.png')
        text = pytesseract.image_to_string(img, config='')
        print('Camera read: ' + text)
        command = text.split()[0] # return the first word in the detected string
        return command
    

