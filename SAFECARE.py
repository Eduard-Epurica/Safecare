import spidev
import os
import math
import time
import pigpio
import math
import subprocess
import Adafruit_DHT
import json
import RPi.GPIO as GPIO
import paho.mqtt.publish as publicare

MQTT_HOST = 'mqtt.beia-telemetrie.ro'
MQTT_TOPIC = 'odsi/mari-anais'

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
Fan_pin = 20
maxTMP = 29.5
UV_pin = 5
UV_power = 6
spi=spidev.SpiDev()
spi.open(0,0) 
spi.max_speed_hz=1000000
logfile = "data.txt"
GPIO.setmode(GPIO.BCM)
def fanON():
    setPin(True)
    return()
def fanOFF():
    setPin(False)
    return()
def setPin(mode):
    GPIO.output(Fan_pin, mode)
    return()
def ReadInput(channel):
    adc = spi.xfer2([6|(channel&4)>>2, (channel&3)<<6,0])
    data = ((adc[1]&15)<<8)+adc[2]
    return data
def ConvertVolts (data, places):   
    volts = (data*3.3)/float(4095)
    volts = round(volts,places)
    return volts
def local_save(data):
    file = open(logfile, "a+")
    file.write(data + "\r\n");
    file.close()
def local_delete():
    file = open(logfile, "a+")
    file.truncate(0);
    file.close()
    fire=0
    fire1=0
def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(Fan_pin, GPIO.OUT)
    GPIO.setwarnings(False)
    return()
def setupUV():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(UV_pin, GPIO.IN)
    GPIO.setup(UV_power, GPIO.IN)
    GPIO.setwarnings(False)
    return()
try:
    setup()
    setupUV()
    while True:
        cont=0
        inundatie=0
        spargere=0
        channel = 0
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        channeldata = ReadInput(channel)
        light=ConvertVolts(ReadInput(3),2)
        sound = ReadInput(2)
        print(sound)
        voltage = ConvertVolts (ReadInput(0),2)
        voltage1 = ConvertVolts (ReadInput(1),2)
        fire1 = ConvertVolts (ReadInput(4),2)
        uv1 = ConvertVolts (ReadInput(UV_pin),2)
        #print('Data        : {}'.format(channeldata))
        #print('Voltage (V): {}'.format(voltage1))
        #print("Light={0:0.1f} lux".format(light*1000))
        #print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))
#        print (sound)
        print(uv1)
        if (fire1<1):
            fire=1
        elif (fire1>=1):
            fire=0
        if (voltage1>=2.55):
            spargere=0
            #print("Safe")
        elif (voltage1<2.55):
            spargere=1
            #print("Danger!")
        if (voltage>=0.5):
            inundatie=1
        elif (voltage<0.5):
            inundatie=0
        if temperature>maxTMP:
            setup()
            fanON()
            z=1
        elif temperature<maxTMP:
            setup()
            fanOFF()
            z=0
            GPIO.cleanup(20)
       # print('Inundatie: {}'.format(inundatie))
        payload_dict={"Temperature_in_degrees":round(temperature,2),
                      "Humidity_level":round(humidity,2),
                      "Flood":inundatie,
                      "Glass_Break" :spargere,
                      "Fire" : fire,
                      "Light_level" :(light*1000),
                      "Sound" : sound,
                      "Fan_Power":z}
        message = "Flood " + str(inundatie) + " Glas_Break  " + str(spargere) + "Fire " + str(fire) +"Light_level" +str(light*1000) +"Sound " +str(sound)
        print(payload_dict)
        try:
            publicare.single(MQTT_TOPIC,qos = 1,hostname = MQTT_HOST,payload = json.dumps(payload_dict))
        except:
            GPIO.cleanup()
            cont=cont+1
        if (cont==1):
            cont=0
            local_save(message)
        time.sleep(10)
except KeyboardInterrupt:              
    GPIO.cleanup()
    
