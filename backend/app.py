#!/usr/bin/env python3
"""
Backend Flask con WebSocket para aplicación de reciclaje inteligente
Migración de OpenCV GUI a aplicación web
"""
import os
import sys
import ssl
import time
import cv2
import json
import numpy as np
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from ultralytics import YOLO
import paho.mqtt.client as mqtt
from smartcard.System import readers
from smartcard.Exceptions import NoCardException, CardConnectionException
import firebase_admin
from firebase_admin import credentials, db
import threading
import math
import signal
import base64
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config['SECRET_KEY'] = 'reciclaje_inteligente_2024'

# Configurar SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ---------- CONFIG MQTT ----------
MQTT_BROKER = os.getenv("MQTT_BROKER", "2e139bb9a6c5438b89c85c91b8cbd53f.s1.eu.hivemq.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_USER", "ramsi")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "Erikram2025")
MQTT_MATERIAL_TOPIC = os.getenv("MQTT_MATERIAL_TOPIC", "material/detectado")
MQTT_NIVEL_TOPIC = "reciclaje/esp32-01/nivel"

# Cliente MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
mqtt_client.tls_insecure_set(True)

# ---------- CONFIG FIREBASE ----------
SERVICE_ACCOUNT_PATH = "../config/resiclaje-39011-firebase-adminsdk-fbsvc-433ec62b6c.json"
DATABASE_URL = "https://resiclaje-39011-default-rtdb.firebaseio.com"

try:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
    
    nfc_index_ref = db.reference('nfc_index')
    usuarios_ref = db.reference('usuarios')
    contenedor_ref = db.reference('contenedor')
    logger.info("✅ Firebase inicializado correctamente")
except Exception as e:
    logger.error(f"❌ Error inicializando Firebase: {e}")

GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]

# ---------- ESTADO GLOBAL ----------
app_state = {
    'material_detectado': None,
    'deteccion_activa': None,
    'inicio_deteccion': None,
    'progreso_deteccion': 0,
    'usuario_actual': None,
    'puntos_ganados': 0,
    'fps': 0,
    'camera_active': True,
    'nfc_active': True,
    'mqtt_connected': False,
    'contenedores': {},
    'stats': {
        'total_reciclado': 0,
        'puntos_totales': 0,
        'materiales_hoy': 0
    }
}

lock = threading.Lock()

# ---------- COLORES Y CONFIGURACIÓN ----------
COLORS = {
    'primary': '#00BCD4',
    'secondary': '#4CAF50',
    'accent': '#FFC107',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'error': '#F44336',
    'plastico': '#2196F3',
    'aluminio': '#9E9E9E'
}

TARGET_W, TARGET_H = 320, 480

# ---------- FUNCIONES MQTT ----------
def on_mqtt_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        logger.info("[MQTT] ✅ Conectado al broker")
        client.subscribe(MQTT_NIVEL_TOPIC, qos=1)
        logger.info(f"[MQTT] 📥 Suscrito a: {MQTT_NIVEL_TOPIC}")
        with lock:
            app_state['mqtt_connected'] = True
        socketio.emit('mqtt_status', {'connected': True})
    else:
        logger.error(f"[MQTT] ❌ Error de conexión: {reason_code}")
        with lock:
            app_state['mqtt_connected'] = False
        socketio.emit('mqtt_status', {'connected': False})

def on_mqtt_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        topic = msg.topic
        
        logger.info(f"[MQTT] 📨 Mensaje recibido en {topic}")
        data = json.loads(payload)
        
        if topic == MQTT_NIVEL_TOPIC:
            handle_nivel_update(data)
            
    except json.JSONDecodeError:
        logger.error(f"[MQTT] ❌ Error al parsear JSON: {msg.payload}")
    except Exception as e:
        logger.error(f"[MQTT] ❌ Error procesando mensaje: {e}")

def handle_nivel_update(data):
    try:
        target = data.get('target')
        device_id = data.get('deviceId')
        distance_cm = data.get('distance_cm')
        percent = data.get('percent')
        state = data.get('state')
        ts = data.get('ts')
        
        if not target:
            logger.error("[Firebase] ❌ Campo 'target' no encontrado")
            return
            
        firebase_data = {
            'deviceId': device_id,
            'distance_cm': round(distance_cm, 3) if distance_cm else 0,
            'estado': state,
            'porcentaje': percent,
            'timestamp': ts,
            'updatedAt': int(time.time() * 1000)
        }
        
        contenedor_ref.child(target).update(firebase_data)
        
        # Actualizar estado local y notificar frontend
        with lock:
            app_state['contenedores'][target] = firebase_data
        
        # Comentado: Ya no se muestra en el frontend
        # socketio.emit('contenedor_update', {
        #     'target': target,
        #     'data': firebase_data
        # })
        
        logger.info(f"[Firebase] ✅ Actualizado: contenedor/{target}")
        
    except Exception as e:
        logger.error(f"[Firebase] ❌ Error guardando datos: {e}")

def setup_mqtt():
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    
    logger.info("[MQTT] 🔗 Intentando conectar...")
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        mqtt_client.loop_start()
    except Exception as e:
        logger.error(f"[MQTT] ❌ Error conectando: {e}")

# ---------- FUNCIONES NFC ----------
def get_reader():
    try:
        r = readers()
        if not r:
            raise RuntimeError("No se detectaron lectores PC/SC.")
        return r[0]
    except Exception as e:
        logger.warning(f"[NFC] ⚠️  No hay lector disponible: {e}")
        return None

def bytes_to_hex_str(data_bytes):
    return ''.join('{:02X}'.format(b) for b in data_bytes)

def buscar_usuario_por_uid(uid_hex):
    try:
        mapping = nfc_index_ref.get() or {}
        user_id = mapping.get(uid_hex.upper())
        if not user_id:
            return None, None
        user = usuarios_ref.child(user_id).get()
        return user_id, user
    except Exception as e:
        logger.error(f"[NFC] Error buscando usuario: {e}")
        return None, None

def loop_nfc():
    """Thread para manejo de NFC"""
    lector = get_reader()
    if not lector:
        logger.error("[NFC] ❌ Lector NFC no disponible")
        with lock:
            app_state['nfc_active'] = False
        return
    
    conn = lector.createConnection()
    last_uid = None
    logger.info("[NFC] ✅ Esperando tarjetas...")
    
    while app_state['nfc_active']:
        try:
            conn.connect()
            data, sw1, sw2 = conn.transmit(GET_UID_APDU)
            
            if sw1 == 0x90 and sw2 == 0x00 and data:
                uid = bytes_to_hex_str(data)
                if uid != last_uid:
                    logger.info(f"[NFC] UID detectado: {uid}")
                    user_id, user = buscar_usuario_por_uid(uid)
                    
                    if user:
                        nombre = user.get('usuario_nombre', 'Sin nombre')
                        logger.info(f"[DB] Usuario: {nombre}")
                        
                        with lock:
                            if app_state['material_detectado']:
                                # Calcular puntos
                                puntos = 20 if app_state['material_detectado'] == "plastico" else 30
                                puntos_actuales = user.get("usuario_puntos", 0)
                                nuevos_puntos = puntos_actuales + puntos
                                
                                # Actualizar en Firebase
                                usuarios_ref.child(user_id).update({"usuario_puntos": nuevos_puntos})
                                
                                # Actualizar estado local
                                app_state['usuario_actual'] = {
                                    'id': user_id,
                                    'nombre': nombre,
                                    'puntos_anteriores': puntos_actuales,
                                    'puntos_nuevos': nuevos_puntos,
                                    'puntos_ganados': puntos
                                }
                                app_state['puntos_ganados'] = puntos
                                app_state['stats']['puntos_totales'] += puntos
                                app_state['stats']['materiales_hoy'] += 1
                                
                                # Notificar al frontend
                                socketio.emit('material_procesado', {
                                    'material': app_state['material_detectado'],
                                    'usuario': app_state['usuario_actual'],
                                    'puntos': puntos,
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                # Limpiar estado
                                app_state['material_detectado'] = None
                                
                                logger.info(f"[PROCESO] ✅ {nombre} ganó {puntos} puntos por {app_state['material_detectado']}")
                    else:
                        logger.warning("[DB] UID no registrado")
                        socketio.emit('nfc_error', {'message': 'Tarjeta no registrada'})
                    
                    last_uid = uid
            else:
                last_uid = None
                
            time.sleep(0.5)
            
        except (NoCardException, CardConnectionException):
            last_uid = None
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"[NFC ERROR] {e}")
            last_uid = None
            time.sleep(1)

# ---------- FUNCIONES YOLO ----------
def frame_to_base64(frame):
    """Convierte frame de OpenCV a base64 para envío por WebSocket"""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{frame_base64}"

def loop_yolo():
    """Thread principal para detección YOLO y cámara"""
    weights = Path("../modelo/best.onnx")
    if not weights.exists():
        logger.error(f"No se encontró {weights.resolve()}")
        return
    
    try:
        model = YOLO(str(weights), task="detect")
        logger.info("✅ Modelo YOLO cargado")
    except Exception as e:
        logger.error(f"❌ Error cargando modelo YOLO: {e}")
        return
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("❌ No se pudo abrir la cámara")
        with lock:
            app_state['camera_active'] = False
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    prev_time = time.time()
    logger.info("✅ Iniciando detección YOLO")
    
    while app_state['camera_active']:
        ret, frame = cap.read()
        if not ret:
            logger.error("❌ Error leyendo frame de cámara")
            break
        
        current_time = time.time()
        
        with lock:
            if app_state['material_detectado'] is None:
                # Realizar detección
                try:
                    results = model.predict(frame, conf=0.5, imgsz=320, verbose=False)
                    annotated = results[0].plot()
                    
                    clase_detectada = None
                    detection_boxes = []
                    
                    for r in results:
                        for box in r.boxes:
                            cls_id = int(box.cls[0])
                            class_name = model.names[cls_id]
                            if class_name in ["plastico", "aluminio"]:
                                clase_detectada = class_name
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                detection_boxes.append((x1, y1, x2, y2, class_name))
                    
                    # Procesar detección
                    if clase_detectada:
                        if app_state['deteccion_activa'] == clase_detectada:
                            tiempo_transcurrido = current_time - app_state['inicio_deteccion']
                            app_state['progreso_deteccion'] = min(tiempo_transcurrido / 5.0, 1.0)
                            
                            if tiempo_transcurrido >= 5:
                                app_state['material_detectado'] = clase_detectada
                                logger.info(f"[YOLO] {clase_detectada} detectado por 5s")
                                
                                # Publicar a MQTT
                                mqtt_client.publish(MQTT_MATERIAL_TOPIC, clase_detectada, qos=1)
                                
                                # Notificar al frontend
                                socketio.emit('material_detectado', {
                                    'material': clase_detectada,
                                    'timestamp': datetime.now().isoformat()
                                })
                        else:
                            app_state['deteccion_activa'] = clase_detectada
                            app_state['inicio_deteccion'] = current_time
                            app_state['progreso_deteccion'] = 0
                    else:
                        app_state['deteccion_activa'] = None
                        app_state['inicio_deteccion'] = None
                        app_state['progreso_deteccion'] = 0
                    
                    # Calcular FPS
                    fps = 1 / (current_time - prev_time)
                    app_state['fps'] = fps
                    prev_time = current_time
                    
                    # Enviar frame al frontend
                    frame_data = frame_to_base64(annotated)
                    socketio.emit('camera_frame', {
                        'frame': frame_data,
                        'fps': round(fps, 1),
                        'deteccion_activa': app_state['deteccion_activa'],
                        'progreso': app_state['progreso_deteccion'],
                        'timestamp': current_time
                    })
                    
                except Exception as e:
                    logger.error(f"[YOLO] Error en detección: {e}")
            else:
                # Modo esperando NFC
                socketio.emit('waiting_nfc', {
                    'material': app_state['material_detectado'],
                    'timestamp': current_time
                })
        
        time.sleep(0.1)  # Control de FPS
    
    cap.release()
    logger.info("✅ Cámara liberada")

# ---------- RUTAS API REST ----------
@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Estado general del sistema"""
    with lock:
        return jsonify({
            'status': 'active',
            'camera_active': app_state['camera_active'],
            'nfc_active': app_state['nfc_active'],
            'mqtt_connected': app_state['mqtt_connected'],
            'material_detectado': app_state['material_detectado'],
            'deteccion_activa': app_state['deteccion_activa'],
            'progreso_deteccion': app_state['progreso_deteccion'],
            'fps': app_state['fps'],
            'stats': app_state['stats'],
            'timestamp': datetime.now().isoformat()
        })

# Comentado: Ya no se usa en el frontend simplificado
# @app.route('/api/contenedores')
# def api_contenedores():
#     """Estado de contenedores"""
#     with lock:
#         return jsonify(app_state['contenedores'])

@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Resetear estado del sistema"""
    with lock:
        app_state['material_detectado'] = None
        app_state['deteccion_activa'] = None
        app_state['inicio_deteccion'] = None
        app_state['progreso_deteccion'] = 0
        app_state['usuario_actual'] = None
        app_state['puntos_ganados'] = 0
    
    socketio.emit('system_reset')
    return jsonify({'status': 'reset_complete'})

# ---------- EVENTOS WEBSOCKET ----------
@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    logger.info(f"[WebSocket] Cliente conectado: {request.sid}")
    
    # Enviar estado inicial
    with lock:
        emit('initial_state', {
            'app_state': app_state,
            'colors': COLORS,
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    logger.info(f"[WebSocket] Cliente desconectado: {request.sid}")

@socketio.on('request_status')
def handle_request_status():
    """Solicitud de estado"""
    with lock:
        emit('status_update', app_state)

# ---------- MANEJO DE SEÑALES ----------
def handle_sigterm(signum, frame):
    """Manejo de señal de terminación"""
    logger.info("🛑 Cerrando aplicación...")
    
    with lock:
        app_state['camera_active'] = False
        app_state['nfc_active'] = False
    
    try:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    except:
        pass
    
    sys.exit(0)

# ---------- MAIN ----------
if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    # Inicializar servicios
    setup_mqtt()
    
    # Iniciar threads
    nfc_thread = threading.Thread(target=loop_nfc, daemon=True)
    yolo_thread = threading.Thread(target=loop_yolo, daemon=True)
    
    nfc_thread.start()
    yolo_thread.start()
    
    logger.info("🚀 Iniciando servidor web...")
    
    # Iniciar servidor
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=False,
        allow_unsafe_werkzeug=True
    )
