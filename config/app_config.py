#!/usr/bin/env python3
"""
Configuración centralizada para la aplicación de reciclaje inteligente
"""

import os
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
FRONTEND_DIR = BASE_DIR / "frontend"
BACKEND_DIR = BASE_DIR / "backend"
MODELO_DIR = BASE_DIR / "modelo"

class Config:
    """Configuración base"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'reciclaje_inteligente_2024_raspberry_pi')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Servidor
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # MQTT
    MQTT_BROKER = os.getenv('MQTT_BROKER', '2e139bb9a6c5438b89c85c91b8cbd53f.s1.eu.hivemq.cloud')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 8883))
    MQTT_USER = os.getenv('MQTT_USER', 'ramsi')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'Erikram2025')
    MQTT_MATERIAL_TOPIC = os.getenv('MQTT_MATERIAL_TOPIC', 'material/detectado')
    MQTT_NIVEL_TOPIC = os.getenv('MQTT_NIVEL_TOPIC', 'reciclaje/esp32-01/nivel')
    MQTT_USE_TLS = os.getenv('MQTT_USE_TLS', 'True').lower() == 'true'
    
    # Firebase
    FIREBASE_SERVICE_ACCOUNT = os.getenv(
        'FIREBASE_SERVICE_ACCOUNT', 
        str(CONFIG_DIR / 'resiclaje-39011-firebase-adminsdk-fbsvc-433ec62b6c.json')
    )
    FIREBASE_DATABASE_URL = os.getenv(
        'FIREBASE_DATABASE_URL', 
        'https://resiclaje-39011-default-rtdb.firebaseio.com'
    )
    
    # Cámara
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
    CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', 640))
    CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', 480))
    CAMERA_FPS = int(os.getenv('CAMERA_FPS', 30))
    
    # YOLO
    YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', str(MODELO_DIR / 'best.onnx'))
    YOLO_CONFIDENCE = float(os.getenv('YOLO_CONFIDENCE', 0.5))
    YOLO_IMG_SIZE = int(os.getenv('YOLO_IMG_SIZE', 320))
    
    # Detección
    DETECTION_TIME_THRESHOLD = float(os.getenv('DETECTION_TIME_THRESHOLD', 5.0))  # segundos
    DETECTION_CLASSES = os.getenv('DETECTION_CLASSES', 'plastico,aluminio').split(',')
    
    # NFC
    NFC_ENABLED = os.getenv('NFC_ENABLED', 'True').lower() == 'true'
    NFC_TIMEOUT = float(os.getenv('NFC_TIMEOUT', 0.5))
    
    # Puntos por material
    PUNTOS_PLASTICO = int(os.getenv('PUNTOS_PLASTICO', 20))
    PUNTOS_ALUMINIO = int(os.getenv('PUNTOS_ALUMINIO', 30))
    
    # WebSocket
    WEBSOCKET_ASYNC_MODE = os.getenv('WEBSOCKET_ASYNC_MODE', 'threading')
    WEBSOCKET_CORS_ORIGINS = os.getenv('WEBSOCKET_CORS_ORIGINS', '*')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', str(BASE_DIR / 'logs' / 'app.log'))
    
    # Autoarranque
    AUTOSTART_ENABLED = os.getenv('AUTOSTART_ENABLED', 'True').lower() == 'true'
    CHROMIUM_KIOSK = os.getenv('CHROMIUM_KIOSK', 'True').lower() == 'true'
    CHROMIUM_URL = os.getenv('CHROMIUM_URL', f'http://localhost:{PORT}')
    
    # Raspberry Pi específico
    RASPBERRY_PI = os.getenv('RASPBERRY_PI', 'True').lower() == 'true'
    GPIO_ENABLED = os.getenv('GPIO_ENABLED', 'False').lower() == 'true'
    
    @classmethod
    def validate_config(cls):
        """Validar configuración"""
        errors = []
        
        # Validar archivos requeridos
        if not Path(cls.FIREBASE_SERVICE_ACCOUNT).exists():
            errors.append(f"Archivo Firebase no encontrado: {cls.FIREBASE_SERVICE_ACCOUNT}")
        
        if not Path(cls.YOLO_MODEL_PATH).exists():
            errors.append(f"Modelo YOLO no encontrado: {cls.YOLO_MODEL_PATH}")
        
        # Validar configuración MQTT
        if not cls.MQTT_BROKER:
            errors.append("MQTT_BROKER no configurado")
        
        if not cls.MQTT_USER or not cls.MQTT_PASSWORD:
            errors.append("Credenciales MQTT no configuradas")
        
        # Validar Firebase
        if not cls.FIREBASE_DATABASE_URL:
            errors.append("FIREBASE_DATABASE_URL no configurada")
        
        return errors

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    AUTOSTART_ENABLED = False

class ProductionConfig(Config):
    """Configuración para producción en Raspberry Pi"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    AUTOSTART_ENABLED = True
    CHROMIUM_KIOSK = True

class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    NFC_ENABLED = False
    CAMERA_INDEX = -1  # Desactivar cámara en tests
    MQTT_ENABLED = False

# Mapeo de configuraciones
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}

def get_config(config_name=None):
    """Obtener configuración según el entorno"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    return config_map.get(config_name, ProductionConfig)

# Configuración de materiales
MATERIAL_CONFIG = {
    'plastico': {
        'name': 'Plástico',
        'color': '#2196F3',
        'points': Config.PUNTOS_PLASTICO,
        'icon': 'fas fa-bottle-water',
        'description': 'Botellas, envases y recipientes plásticos'
    },
    'aluminio': {
        'name': 'Aluminio',
        'color': '#9E9E9E',
        'points': Config.PUNTOS_ALUMINIO,
        'icon': 'fas fa-can-food',
        'description': 'Latas, envases y objetos de aluminio'
    }
}

# Configuración de colores para la interfaz
UI_COLORS = {
    'primary': '#00BCD4',
    'secondary': '#4CAF50',
    'accent': '#FFC107',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'error': '#F44336',
    'plastico': '#2196F3',
    'aluminio': '#9E9E9E',
    'background': {
        'primary': '#0a0a0a',
        'secondary': '#1a1a1a',
        'card': '#2a2a2a'
    },
    'text': {
        'primary': '#ffffff',
        'secondary': '#b0b0b0',
        'muted': '#666666'
    }
}
