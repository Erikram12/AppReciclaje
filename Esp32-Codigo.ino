#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_PWMServoDriver.h>

// ====== CONFIGURACIÓN DE PINES ======
// Sensor Ultrasónico 1 - PLÁSTICO
#define TRIG_PIN_1 5      // Pin TRIG del sensor ultrasónico 1
#define ECHO_PIN_1 18     // Pin ECHO del sensor ultrasónico 1

// Sensor Ultrasónico 2 - ALUMINIO
#define TRIG_PIN_2 4      // Pin TRIG del sensor ultrasónico 2
#define ECHO_PIN_2 19     // Pin ECHO del sensor ultrasónico 2

// ====== CONFIGURACIÓN DE SERVOS ======
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// Canales de servos
#define CH_PUERTA1   0    // Canal 0 - Puerta 1 (NORMAL)
#define CH_PUERTA2   1    // Canal 1 - Puerta 2 (INVERTIDO)
#define CH_PLASTICO1 2    // Canal 2 - Plástico 1 (NORMAL)
#define CH_PLASTICO2 3    // Canal 3 - Plástico 2 (INVERTIDO)

// --- PUERTA 1 (CH_PUERTA1 - NORMAL) ---
uint16_t PUERTA1_REPOSO = 500;   // ~180°
uint16_t PUERTA1_ACTIVO = 310;   // ~90° (baja ~90°)

// --- PUERTA 2 (CH_PUERTA2 - INVERTIDO) ---
uint16_t PUERTA2_REPOSO = 100;   // ~180° (invertido)
uint16_t PUERTA2_ACTIVO = 290;   // ~90° (baja ~90°)

// --- PLÁSTICO 1 (CH_PLASTICO1 - NORMAL) ---
uint16_t PLASTICO1_REPOSO = 500;   // ~180°
uint16_t PLASTICO1_ACTIVO = 350;   // posición activa (~70°)

// --- PLÁSTICO 2 (CH_PLASTICO2 - INVERTIDO) ---
uint16_t PLASTICO2_REPOSO = 100;   // ~180° (invertido)
uint16_t PLASTICO2_ACTIVO = 250;   // posición activa (~70°)

// Variable para material detectado
String material = "";

// ====== CREDENCIALES ======
const char* WIFI_SSID  = "Tenda_5AE810";
const char* WIFI_PASS  = "Laxopa2025";
const char* MQTT_HOST  = "2e139bb9a6c5438b89c85c91b8cbd53f.s1.eu.hivemq.cloud";
const uint16_t MQTT_PORT = 8883;
const char* MQTT_USER   = "ramsi";
const char* MQTT_PASSWD = "Erikram2025";

String deviceId = "esp32-01";
String topic    = "reciclaje/" + deviceId + "/nivel";
#define MQTT_TOPIC "material/detectado"

// ====== CONFIGURACIÓN DEL SENSOR ======
const float MAX_DISTANCE  = 50.0;   // Distancia máxima en cm (contenedor vacío)
const float MIN_DISTANCE  = 5.0;    // Distancia mínima en cm (contenedor lleno)
const int   SENSOR_TIMEOUT = 10000; // Timeout del sensor en microsegundos

WiFiClientSecure net;
PubSubClient mqtt(net);

// Variables de control
unsigned long lastPub = 0;
const unsigned long PUBLISH_INTERVAL = 300000;  // Publicar cada 5 minutos (300000 ms)
bool lastConnectionStatus = false;

// Variables para validar mediciones
const int MEASUREMENT_SAMPLES          = 5;  // Tomar 5 muestras
const int VALID_MEASUREMENTS_REQUIRED  = 3;  // Necesitar al menos 3 válidas

// Variables para evitar spam de mensajes
String lastStatePlastico = "";
String lastStateAluminio = "";
int lastPercentPlastico  = -1;
int lastPercentAluminio  = -1;
const int CHANGE_THRESHOLD = 5;  // Solo enviar si el cambio es mayor a 5%

// Función para verificar si hay cambios significativos
bool hasSignificantChange(const char* target, int currentPercent, const String& currentState) {
    if (strcmp(target, "contePlastico") == 0) {
        // Verificar cambio de estado
        if (currentState != lastStatePlastico) {
            return true;
        }
        // Verificar cambio de porcentaje significativo
        if (lastPercentPlastico == -1 || abs(currentPercent - lastPercentPlastico) >= CHANGE_THRESHOLD) {
            return true;
        }
    } else if (strcmp(target, "conteAluminio") == 0) {
        // Verificar cambio de estado
        if (currentState != lastStateAluminio) {
            return true;
        }
        // Verificar cambio de porcentaje significativo
        if (lastPercentAluminio == -1 || abs(currentPercent - lastPercentAluminio) >= CHANGE_THRESHOLD) {
            return true;
        }
    }
    return false;
}

// Función para actualizar el estado anterior
void updateLastState(const char* target, int currentPercent, const String& currentState) {
    if (strcmp(target, "contePlastico") == 0) {
        lastStatePlastico  = currentState;
        lastPercentPlastico = currentPercent;
    } else if (strcmp(target, "conteAluminio") == 0) {
        lastStateAluminio  = currentState;
        lastPercentAluminio = currentPercent;
    }
}

// Función para calcular el estado del contenedor
String calcState(int percent) {
    if (percent >= 70) return "Lleno";
    if (percent >= 10) return "Medio";
    return "Vacio";
}

// Función para medir distancia con el sensor ultrasónico
// sensorNumber: 1 para sensor de plástico, 2 para sensor de aluminio
float measureDistance(int sensorNumber) {
    int trigPin, echoPin;
    
    // Seleccionar los pines según el sensor
    if (sensorNumber == 1) {
        trigPin = TRIG_PIN_1;
        echoPin = ECHO_PIN_1;
    } else if (sensorNumber == 2) {
        trigPin = TRIG_PIN_2;
        echoPin = ECHO_PIN_2;
    } else {
        Serial.println("Número de sensor inválido");
        return -1;
    }
    
    // Limpiar el pin TRIG
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    
    // Enviar pulso de 10 microsegundos
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    
    // Medir el tiempo de respuesta
    long duration = pulseIn(echoPin, HIGH, SENSOR_TIMEOUT);
    
    // Calcular distancia en cm
    float distance = duration * 0.034 / 2;
    
    // Validar la medición
    if (distance == 0 || distance > MAX_DISTANCE) {
        Serial.printf("Error en medición del sensor %d\n", sensorNumber);
        return -1;
    }
    
    return distance;
}

// Función para calcular el porcentaje de llenado
int calculatePercent(float distance) {
    if (distance < MIN_DISTANCE) return 100;
    if (distance > MAX_DISTANCE) return 0;
    
    // Calcular porcentaje basado en la distancia
    float percent = ((MAX_DISTANCE - distance) / (MAX_DISTANCE - MIN_DISTANCE)) * 100;
    return (int)percent;
}

// ====== FUNCIONES DE CONTROL DE SERVOS ======

// Inicializar servos en posición REPOSO (180°)
void inicializarServos() {
    Serial.println("Inicializando servos en REPOSO (180°)...");

    pwm.setPWM(CH_PUERTA1,   0, PUERTA1_REPOSO);
    pwm.setPWM(CH_PUERTA2,   0, PUERTA2_REPOSO);
    pwm.setPWM(CH_PLASTICO1, 0, PLASTICO1_REPOSO);
    pwm.setPWM(CH_PLASTICO2, 0, PLASTICO2_REPOSO);

    delay(500);
    Serial.println("Servos en REPOSO (180°)");
}

// Función para abrir/cerrar compuerta según material
// Movimiento: 180° (REPOSO) -> ACTIVO (baja) -> 180° (REPOSO)
void abrirCompuerta() {
    Serial.println("Movimiento 180° → ACTIVO → 180°...");

    if (material == "plastico") {
        // ⬅️ AHORA: SOLO PUERTAS para PLÁSTICO
        pwm.setPWM(CH_PUERTA1, 0, PUERTA1_ACTIVO);
        pwm.setPWM(CH_PUERTA2, 0, PUERTA2_ACTIVO);

    } else if (material == "aluminio") {
        // ⬅️ AHORA: 4 SERVOS para ALUMINIO (puertas + plásticos)
        pwm.setPWM(CH_PUERTA1,   0, PUERTA1_ACTIVO);
        pwm.setPWM(CH_PUERTA2,   0, PUERTA2_ACTIVO);
        pwm.setPWM(CH_PLASTICO1, 0, PLASTICO1_ACTIVO);
        pwm.setPWM(CH_PLASTICO2, 0, PLASTICO2_ACTIVO);

    } else {
        Serial.println("Material no válido");
        return;
    }

    delay(3000); // tiempo en posición ACTIVO

    // Regresar exactamente a REPOSO (180°)
    Serial.println("Regresando a REPOSO (180°)...");
    pwm.setPWM(CH_PUERTA1,   0, PUERTA1_REPOSO);
    pwm.setPWM(CH_PUERTA2,   0, PUERTA2_REPOSO);
    pwm.setPWM(CH_PLASTICO1, 0, PLASTICO1_REPOSO);
    pwm.setPWM(CH_PLASTICO2, 0, PLASTICO2_REPOSO);
}

// ====== CALLBACK MQTT ======
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    // Convertir payload a string
    String message = "";
    for (int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    
    Serial.printf("Mensaje recibido en tópico: %s\n", topic);
    Serial.printf("Contenido: %s\n", message.c_str());
    
    // Verificar si es detección de material
    if (String(topic) == MQTT_TOPIC) {
        // Convertir a minúsculas y limpiar
        message.toLowerCase();
        message.trim();
        
        Serial.printf("🔍 Material detectado: %s\n", message.c_str());
        
        if (message == "plastico" || message == "plástico" || message == "plastic") {
            material = "plastico";
            Serial.println("Procesando PLÁSTICO - Activando SOLO PUERTAS");
            abrirCompuerta();
        } else if (message == "aluminio" || message == "aluminum") {
            material = "aluminio";
            Serial.println("Procesando ALUMINIO - Activando PUERTAS + PLÁSTICOS");
            abrirCompuerta();
        } else {
            Serial.printf("Material no reconocido: %s\n", message.c_str());
            Serial.println("Materiales válidos: plastico, aluminio");
        }
    }
}

void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;
    
    Serial.printf("Conectando a WiFi: %s\n", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n WiFi conectado. IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n Error conectando WiFi");
    }
}

void connectMQTT() {
    if (mqtt.connected()) return;
    
    // Configurar TLS
    net.setInsecure();
    mqtt.setServer(MQTT_HOST, MQTT_PORT);
    mqtt.setBufferSize(512);
    mqtt.setCallback(mqttCallback);  // Configurar callback
    
    String willTopic = "reciclaje/" + deviceId + "/status";
    String clientId  = "esp32-" + String((uint32_t)ESP.getEfuseMac(), HEX);
    
    Serial.print("🔗 Conectando MQTT...");
    
    bool ok = mqtt.connect(
        clientId.c_str(),
        MQTT_USER,
        MQTT_PASSWD,
        willTopic.c_str(),
        0,
        false,
        "offline"
    );
    
    if (ok) {
        mqtt.publish(willTopic.c_str(), "online", false);
        
        // Suscribirse al tópico de detección de material
        mqtt.subscribe(MQTT_TOPIC);
        Serial.printf("MQTT conectado y suscrito a: %s\n", MQTT_TOPIC);
    } else {
        Serial.printf("Error MQTT (%d)\n", mqtt.state());
    }
}

void publishNivel(const char* target, float dist_cm, int percent, const String& state) {
    // Verificar si hay cambios significativos antes de enviar
    if (!hasSignificantChange(target, percent, state)) {
        Serial.printf("⏭️ %s: Sin cambios significativos (%d%% %s) - Omitiendo envío\n",
                     target, percent, state.c_str());
        return;
    }
    
    StaticJsonDocument<256> doc;
    doc["deviceId"]    = deviceId;
    doc["target"]      = target;
    doc["distance_cm"] = dist_cm;
    doc["percent"]     = percent;
    doc["state"]       = state;
    doc["ts"]          = (long long)millis();
    
    char buf[256];
    size_t n = serializeJson(doc, buf, sizeof(buf));
    
    bool ok = mqtt.publish(topic.c_str(), (const uint8_t*)buf, (unsigned int)n, false);
    
    if (ok) {
        Serial.printf("📤 %s: %d%% (%s) - %.1fcm [CAMBIO DETECTADO]\n", 
                      target, percent, state.c_str(), dist_cm);
        // Actualizar el estado anterior después de enviar exitosamente
        updateLastState(target, percent, state);
    } else {
        Serial.println("Error publicando mensaje");
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("Iniciando ESP32 - Sistema de Reciclaje");
    
    // Configurar pines del sensor 1 (Plástico)
    pinMode(TRIG_PIN_1, OUTPUT);
    pinMode(ECHO_PIN_1, INPUT);
    
    // Configurar pines del sensor 2 (Aluminio)
    pinMode(TRIG_PIN_2, OUTPUT);
    pinMode(ECHO_PIN_2, INPUT);
    
    // Inicializar driver de servos PCA9685
    Serial.println("🔧 Inicializando driver de servos...");
    pwm.begin();
    pwm.setOscillatorFrequency(27000000);  // Frecuencia del oscilador interno
    pwm.setPWMFreq(50);                    // Frecuencia PWM para servos (50Hz)
    
    // Inicializar servos en REPOSO (180°)
    inicializarServos();
    
    // Conectar WiFi y MQTT
    connectWiFi();
    connectMQTT();
    
    Serial.println("Sistema iniciado correctamente");
    Serial.println("Tópicos MQTT:");
    Serial.printf("Publicar datos: reciclaje/%s/nivel\n", deviceId.c_str());
    Serial.printf("Detección material: %s\n", MQTT_TOPIC);
    Serial.printf("Estado: reciclaje/%s/status\n", deviceId.c_str());
    Serial.println("Configuración de sensores:");
    Serial.println("Sensor 1 (PLÁSTICO): TRIG=5, ECHO=18");
    Serial.println("Sensor 2 (ALUMINIO): TRIG=4, ECHO=19");
    Serial.println("Configuración de servos (todos MG995):");
    Serial.println("CH_PUERTA1: Normal (dirección estándar)");
    Serial.println("CH_PUERTA2: Invertido (dirección opuesta)");
    Serial.println("CH_PLASTICO1: Normal (dirección estándar)");
    Serial.println("CH_PLASTICO2: Invertido (dirección opuesta)");
}

void loop() {
    // Mantener conexiones
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }
    
    if (!mqtt.connected()) {
        connectMQTT();
    }
    
    mqtt.loop();
    
    // Publicar datos cada intervalo
    if (millis() - lastPub > PUBLISH_INTERVAL) {
        lastPub = millis();
        
        // Medir distancia del sensor 1 (Plástico)
        float distance1 = measureDistance(1);
        
        if (distance1 > 0) {
            int    percent1 = calculatePercent(distance1);
            String state1   = calcState(percent1);
            publishNivel("contePlastico", distance1, percent1, state1);
        } else {
            Serial.println("No se pudo medir distancia en sensor 1 (Plástico)");
        }
        
        delay(100);
        
        // Medir distancia del sensor 2 (Aluminio)
        float distance2 = measureDistance(2);
        
        if (distance2 > 0) {
            int    percent2 = calculatePercent(distance2);
            String state2   = calcState(percent2);
            publishNivel("conteAluminio", distance2, percent2, state2);
        } else {
            Serial.println("No se pudo medir distancia en sensor 2 (Aluminio)");
        }
    }
    
    delay(100);
}
