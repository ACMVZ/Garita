import machine
from machine import Pin, PWM, SPI, ADC
from time import sleep, ticks_ms, sleep_ms, sleep_us
from mfrc522 import MFRC522
import _thread

# PINES
RC522_SCK_PIN = 2
RC522_MOSI_PIN = 3
RC522_MISO_PIN = 4
RC522_SDA_PIN = 1
RC522_RST_PIN = 0

# SPI PINES
SCK = Pin(RC522_SCK_PIN)
MOSI = Pin(RC522_MOSI_PIN)
MISO = Pin(RC522_MISO_PIN)
RST = Pin(RC522_RST_PIN)
SDA = Pin(RC522_SDA_PIN)

SERVO_PIN = 15

BOTON_PIN = 14

TRIG_PIN = 8
ECHO_PIN = 9

BUZZER_PIN = 10
POT_PIN = 28

# Servo PWN ===============
servo = PWM(Pin(SERVO_PIN))
servo.freq(50)

def set_angle(angle):
    # Mapea el ángulo (0–180) al ciclo de trabajo PWM (duty_u16)
    duty = int(((angle / 180) * 5000) + 2500)
    servo.duty_u16(duty)

# Botón ==================
button = Pin(BOTON_PIN, Pin.IN, Pin.PULL_UP)
last_button_time = 0
debounce_delay = 200  # ms

# BUzzer '/ Potenciómetro
buzzer = PWM(Pin(BUZZER_PIN))
buzzer.duty_u16(0) #inicio apagado
pot = ADC(Pin(POT_PIN))

def buzzer_on(freq = 1000):
    buzzer.freq(freq)
    buzzer.duty_u16(32768) # 1/2

def buzzer_off():
    buzzer.duty_u16(0)

# S Ultrasónico HC-SR0$ =============
#setup
trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
distancia_actual = 999  # (v inicial)
presencia_detectada = False

def medir_distancia_cm():
    trig.low()
    sleep(0.002)
    trig.high()
    sleep(0.00001)
    trig.low()
    try:
        duracion = machine.time_pulse_us(echo, 1, 30000)  # timeout de 30ms
        distancia = (duracion / 2) / 29.1  # cm
        return distancia
    except OSError:
        return None
    
def hay_presencia():
    dist = medir_distancia_cm()
    if dist is not None and dist < 20:
        return True
    return False

# RC522 RFID ===============
reader = MFRC522(spi_id=0,sck=2,miso=4,mosi=3,cs=1,rst=0)
#reader = MFRC522(
#     RC522_SCK_PIN,
#     RC522_MOSI_PIN,
#     RC522_MISO_PIN,
#     RC522_RST_PIN,
#     RC522_SDA_PIN)

#reader = MFRC522(
#    spi_id=0,
#    sck=RC522_SCK_PIN,
#    mosi=RC522_MOSI_PIN,
#    miso=RC522_MISO_PIN,
#    rst=RC522_RST_PIN,
#    cs=RC522_SDA_PIN


# IDs Autorizadas
ids_verificadas = [
    "[0xD9, 0x9C, 0xCD, 0x05]",
    "A3 4F 22 19",
    "91 0A 7C 3E",
    "D9 9C CD 05"
]

# --- Funciones ---
def abrir_puerta():
    print("Abriendo puerta...")
    for pos in range(0, 91, 1):
        set_angle(pos)
        sleep(0.015)
    sleep(5)
    print("Cerrando puerta...")
    for pos in range(90, -1, -1):
        set_angle(pos)
        sleep(0.015)
        while True:
            if hay_presencia():
                buzzer_on(2000)
                sleep(0.15)
                buzzer_off()
                sleep(0.1)
            else: 
                buzzer_off()
                break
    sleep(2)

def es_id_autorizado(uid):
    return uid in ids_verificadas

def leer_tarjeta():
    try:
        reader.init()
        
        (stat, tag_type) = reader.request(reader.REQIDL)
        if stat == reader.OK:
            (stat, uid) = reader.SelectTagSN()
            if stat == reader.OK and uid:
                uid_str = reader.tohexstring(uid)
                return uid_str
    except Exception as e:
        print("Error RFID", e) 
    return None

# Setup Servo
print("= = = Sistema listo = = =")
set_angle(0)

# Hilo RFID
def loop_Puerta():
    global last_button_time
    print("= = = Sistema de acceso listo = = =")
    set_angle(0)

    while True:
        # Lectura botón para apertura manual
        if not button.value():
            now = ticks_ms()
            if now - last_button_time > debounce_delay:
                last_button_time = now
                print("Acceso manual")
                abrir_puerta()

        # RFID
        uid = leer_tarjeta()
        if uid:
            print("Card UID:", uid)
            if es_id_autorizado(uid):
                print("Acceso autorizado")
                abrir_puerta()
            else:
                print("Acceso denegado")
            sleep(1)

        sleep(0.05)  # alivio de CPU

# Hilo Sensores varios
def loop_sensores():
    while True:
        sleep(5)  # alivio de CPU

_thread.start_new_thread(loop_sensores, ())
loop_Puerta()

