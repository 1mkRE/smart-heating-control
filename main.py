from time import sleep
from machine import Pin, I2C, ADC, PWM, UART
import _thread as th
import network
import urequests
import BME280
import sh1106
import esp
import gc
import machine
try:
  import usocket as socket
except:
  import socket

uart = UART(2, 9600, bits=8, parity=None, stop=1, tx=17, rx= 16, timeout=500) 

esp.osdebug(None)
gc.collect()

timer = machine.Timer(0)

s = None
waterlevel = 0.0
waterlevelval = 0
temp = 0.0
pres = 0.0
hum = 0.0
frequency = 5000
manual_mode = True
automatic_mode = False
api_key = 'd3oONdz8Eaw1SbJTn2_67b'

try:
  i2c = I2C(scl=Pin(22), sda=Pin(21), freq=10000)
  display = sh1106.SH1106_I2C(128, 64, i2c)
  display.sleep(False)
except:
  pass

wat = ADC(Pin(36))
wat.atten(ADC.ATTN_11DB) 
controle = Pin(4, Pin.OUT)
status = Pin(2, Pin.OUT)
level_led = PWM(Pin(5), frequency)
warning_switch = Pin(34, Pin.IN)
alarm_switch = Pin(35,Pin.IN)


def web_page():
  bme = BME280.BME280(i2c=i2c)
  global waterlevel
  #waterlevel = wat.read()
  if controle.value() == 1:
    Pump_state="ON"
  else:
    Pump_state="OFF"
  if automatic_mode == True:
    Pump_mode="Automatic"
  elif manual_mode == True:
    Pump_mode="Manual"
  else:
    Pump_mode="Error"
  if warning_switch.value() == 0:
    gpio_warning_state="ON"
  else:
    gpio_warning_state="OFF"
    
  if alarm_switch.value() == 0:
    gpio_alarm_state="ON"
  else:
    gpio_alarm_state="OFF"
  
  html = """<html><head><title>ESP Web Server</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta charset="UTF-8">
  <meta name="description" content="ESP32 Web Server">
  <meta name="keywords" content="HTML">
  <meta name="author" content="Matthias Krawczynski">
  <meta http-equiv="refresh" content="60">
  <link rel="icon" href="data:,">
  <style>
  body { text-align: center; font-family: "Trebuchet MS", Arial;}
  .button{display: inline-block; background-color: #313c48; border: none; border-radius:
  4px; color: white; padding: 16px 70px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
  table { border-collapse: collapse; width:35%; margin-left:auto; margin-right:auto; }
  th { padding: 12px; background-color: #554f4a; color: white; }
  tr { border: 1px solid #ddd; padding: 12px; }
  td { border: none; padding: 12px; }
  .sensor { color:white; font-weight: bold; background-color: #bcbcbc; padding: 1px;}
  </style>
  </head>

  <body>
  <h1><b>Home weather station and water warning</b></h1>
  <table>
  <tr>
  <th>MEASUREMENT</th>
  <th>VALUE</th>
  </tr>
  <tr><td><b>Temperatur</b></td><td><span class="sensor">""" + str(bme.temperature) + """ 閹虹煰</span></td></tr>
  <tr><td><b>Barometric pressure</b></td><td><span class="sensor">""" + str(bme.pressure) + """ hPa</span></td></tr>
  <tr><td><b>Humidity</b></td><td><span class="sensor">""" + str(bme.humidity) + """ %</span></td></tr>
  <tr><td><b>Water level</b></td><td><span class="sensor">""" + str(waterlevel) + """ mm</span></td></tr>
  <tr><td><b>Warning water</b></td><td><span class="sensor">""" + gpio_warning_state + """</span></td></tr>
  <tr><td><b>Alarm water</b></td><td><span class="sensor">""" + gpio_alarm_state + """</span></td></tr>
  <tr><td><b>Pump Mode</b></td><td><span class="sensor">""" + Pump_mode + """</span></td></tr>
  <tr><td><b>Pump Status</b></td><td><span class="sensor">""" + Pump_state + """</span></td></tr>
  <table>
  <tr>
  <th>CONTROLE</th>
  </tr>
  <tr><td>
  <p><a href="/?system=on"><button class="button">AUTO</button> </a>
  <a href="/?system=off"><button class="button">HAND</button> </a></p>
  <p><a href="/?output=on"><button class="button">ON</button> </a>
  <a href="/?output=off"><button class="button">OFF</button> </a></p>
  </td></tr>
  </body></html>"""
  return html

def PumpControle(auto,warning,alarming):
  if automatic_mode:
    if not warning and not alarming:
      controle.value(1)
      status.value(1)
    elif warning and alarming:
      controle.value(0)
      status.value(0)
    else:
      pass

def InterruptWaterAlarm(p):
  global waterlevel  
  sleep(0.5)
  request_headers = {'Content-Type': 'application/json'}
  strwaterlevel = str(waterlevel)
  if not alarm_switch.value() and not warning_switch.value() and automatic_mode:
    sensor_values = {'value1': strwaterlevel + ' mm'}
    urequests.post('http://maker.ifttt.com/trigger/Vodni alarm/with/key/' + api_key,json=sensor_values,headers=request_headers)
    print(sensor_values)

def OledInterrupt(timer):
  global waterlevel 
  global waterlevelval
  global display
  global temp
  global pres
  global hum
  
  watread = wat.read()
  waterlevel = watread*0.0097680097680098
  print(waterlevel)
  waterlevelval = int(waterlevel*100/40)
  print(waterlevelval)
  strwaterlevel = str(waterlevel)
  try:
    bme = BME280.BME280(i2c=i2c)
    display.fill(0)
    display.text(str(bme.temperature)+ ' Celsius', 0, 0)
    display.text(str(bme.pressure)+' hPa', 0, 10)
    display.text(str(bme.humidity)+' %', 0, 20)
    display.text(strwaterlevel+' mm', 0, 30)
    temp = bme.temperature
    pres = bme.pressure
    hum = bme.humidity
  except:
    pass
  
  if not warning_switch.value():
    display.text('Warning = On', 0, 40)
  else:
    display.text('Warning = Off', 0, 40)
    
  if not alarm_switch.value():
    display.text('Alarm = On', 0, 50)
  else:
    display.text('Alarm = Off', 0, 50)
  display.show()
  duty_cycle = int(round(waterlevel*0.25))
  level_led.duty(duty_cycle)
  
def ConrolLoop():
  global automatic_mode
  while True:
    PumpControle(automatic_mode,warning_switch.value(),alarm_switch.value())
  
def send(cmd):
    global response1
    end_cmd=b'\xFF\xFF\xFF'
    uart.write(cmd)
    uart.write(end_cmd)
    sleep(0.1)
    response1 = uart.read()
    #print("Response:", response1)

def send_and_get():
    global processlist
    myframe = bytearray(7)
    #time.sleep_ms(100)
    uart.readinto(myframe)
    #print(myframe)  #Enable this for debugging
    processlist = list(myframe)
    #print(processlist) #Enable this for debugging
    #print(processlist[2]) #Enable this for debugging

def HMI_Loop():
  global waterlevel
  global waterlevelval
  global temp
  global pres
  global hum
  while True:
    sleep(0.1)
    send_and_get()
    if processlist[2] == 1:
      status.value(1)
    else:
      status.value(0)
    
    send("tTempVal.txt=\""+str(temp)+"\"")
    send("tHumVal.txt=\""+str(hum)+"\"")
    send("tPressVal.txt=\""+str(pres)+"\"")
    send("tWaterVal1.txt=\""+str("{0:.2f}".format(waterlevel))+"\"")
    send("nLevel1.val="+str(waterlevelval))
    send("nLevel2.val="+str(0))
    send("nLevel3.val="+str(0))
    send("jLevel1.val="+str(waterlevelval))
    send("jLevel2.val="+str(0))
    send("jLevel3.val="+str(0))

def OpenSocket():
  global s
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('', 80))
  s.listen(5)

def WebConrole():
  global automatic_mode
  global manual_mode
  global s
  
  ssid = 'Hausnetz_2_Patro_Admin'
  password = 'Matrix_1402'
  station = network.WLAN(network.STA_IF)
  station.active(True)
  station.connect(ssid, password)

  while station.isconnected() == False:
    pass

  print('Connection successful')
  print(station.ifconfig())
  
  while True:
    try:
      if gc.mem_free() < 102000:
        gc.collect()
      conn, addr = s.accept()
      conn.settimeout(3.0)
      print('Got a connection from %s' % str(addr))
      request = conn.recv(1024)
      conn.settimeout(None)
      request = str(request)
      print('Content = %s' % request)
      
      am = request.find('/?system=on')
      mm = request.find('/?system=off')
      pump_on = request.find('/?output=on')
      pump_off = request.find('/?output=off')
      
      if am == 6:
        manual_mode = False
        automatic_mode = True
        
      if mm == 6:
        automatic_mode = False      
        manual_mode = True
    
      if manual_mode == True:
        if pump_on == 6:
          controle.value(1)
          status.value(1)
        if pump_off == 6:
          controle.value(0)  
          status.value(0)
    
      response = web_page()
      conn.send('HTTP/1.1 200 OK\n')
      conn.send('Content-Type: text/html\n')
      conn.send('Connection: close\n\n')
      conn.sendall(response)
      conn.close()
    except OSError as e:
      conn.close()

#warning_switch.irq(trigger=Pin.IRQ_FALLING, handler=InterruptWaterAlarm)
#alarm_switch.irq(trigger=Pin.IRQ_FALLING, handler=InterruptWaterAlarm)
timer.init(period=10000, mode=machine.Timer.PERIODIC, callback=OledInterrupt)
OpenSocket()

th.start_new_thread(WebConrole,())
th.start_new_thread(ConrolLoop,())
th.start_new_thread(HMI_Loop,())
