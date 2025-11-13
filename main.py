from machine import Pin, PWN, SPI, ADC
from time import sleep, ticks_ms, time_pulse_us
from mfrc522 import MFRC522
import _thread

# PINES
RC522_SCK_PIN = 21
RC522_MOSI_PIN = 22
RC522_MISO_PIN = 26
RC522_SDA_PIN = 20
RC522_RST_PIN = 27

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
buzzer = PWN(Pin(BUZZER_PIN))
buzzer.deinit()
pot = ADC(Pin(POT_PIN))

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
        duracion = time_pulse_us(echo, 1, 30000)  # timeout de 30ms
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
spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(RC522_SCK_PIN), mosi=Pin(RC522_MOSI_PIN), miso=Pin(RC522_MISO_PIN))
reader = MFRC522(spi=spi, sda=Pin(RC522_SDA_PIN), rst=Pin(RC522_RST_PIN))

# IDs Autorizadas
ids_verificadas = [
    "BD 31 15 2B",
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
                sleep(0.5)
            else: 
                buzzer_off()
                break
    sleep(2)

def es_id_autorizado(uid):
    return uid in ids_verificadas

def leer_tarjeta():
    (stat, tag_type) = reader.request(reader.REQIDL)
    if stat == reader.OK:
        (stat, raw_uid) = reader.anticoll()
        if stat == reader.OK:
            uid_str = " ".join("{:02X}".format(x) for x in raw_uid)
            return uid_str
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
        
        sleep(5)  # alivio de CPU

_thread.start_new_thread(loop_sensores, ())
loop_Puerta()