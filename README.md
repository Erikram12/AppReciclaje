# 🌱 Aplicación de Reciclaje Inteligente

Una aplicación web moderna para Raspberry Pi que utiliza inteligencia artificial para detectar materiales reciclables, con interfaz web en tiempo real y autoarranque automático.

## 🚀 Características

### ✨ Funcionalidades Principales
- **Detección IA**: Reconocimiento de materiales (plástico, aluminio) usando YOLO
- **Interfaz Web Moderna**: Frontend responsive con WebSocket en tiempo real
- **Sistema NFC**: Identificación de usuarios mediante tarjetas NFC
- **Comunicación MQTT**: Integración con sensores IoT
- **Base de Datos Firebase**: Almacenamiento en tiempo real de usuarios y estadísticas
- **Autoarranque**: Inicio automático al encender la Raspberry Pi
- **Modo Kiosk**: Navegador Chromium en pantalla completa

### 🏗️ Arquitectura Simplificada
```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Frontend Web  │◄──────────────►│  Backend Flask  │
│   (Chromium)    │                 │   (Python)      │
└─────────────────┘                 └─────────────────┘
         │                                   │
         │ Autoarranque                      ▼
         │                          ┌─────────────────┐
         └─────────────────────────►│   Hardware      │
                                    │ Cámara + NFC    │
                                    └─────────────────┘
```

## 📋 Requisitos

### Hardware
- **Raspberry Pi 4** (recomendado) o Raspberry Pi 3B+
- **Cámara USB** o Raspberry Pi Camera Module
- **Lector NFC** compatible con PC/SC (PN532, ACR122U, etc.)
- **Pantalla** (HDMI, táctil opcional)
- **Tarjeta microSD** de al menos 32GB (Clase 10)

### Software
- **Raspberry Pi OS Lite** (sin interfaz gráfica)
- **Conexión a Internet** para descargas e instalación

## 🛠️ Instalación Ultra-Simplificada

### 1️⃣ Preparar Archivos en Raspberry Pi

```bash
# Copiar todos los archivos del proyecto a la Raspberry Pi
scp -r ReciclajeApp/ ramsi@IP_RASPBERRY:/home/ramsi/

# Conectar por SSH a la Raspberry Pi
ssh ramsi@IP_RASPBERRY
cd /home/ramsi/ReciclajeApp
```

### 2️⃣ Ejecutar Instalación Única

```bash
# Hacer ejecutable el instalador
chmod +x install_reciclaje_pi.sh

# Ejecutar instalación completa (¡UN SOLO COMANDO!)
./install_reciclaje_pi.sh
```

**¡ESO ES TODO!** 🎉

El script automáticamente:
- ✅ Instala X11 y entorno gráfico mínimo
- ✅ Instala Chromium Browser
- ✅ Instala todas las dependencias Python
- ✅ Configura OpenCV y YOLO
- ✅ Instala soporte NFC
- ✅ Crea la aplicación web
- ✅ Configura servicios systemd
- ✅ Configura autoarranque completo
- ✅ Optimiza Raspberry Pi
- ✅ Crea scripts de gestión

### 3️⃣ Archivos Opcionales (si los tienes)

```bash
# Copiar modelo YOLO (si ya lo tienes entrenado)
cp tu_modelo.onnx /home/ramsi/reciclaje-app/modelo/best.onnx

# Copiar credenciales Firebase (si ya las tienes)
cp firebase-credentials.json /home/ramsi/reciclaje-app/config/resiclaje-39011-firebase-adminsdk-fbsvc-433ec62b6c.json
```

### 4️⃣ Reiniciar y Listo

```bash
sudo reboot
```

## 🎮 Uso Diario

### Comandos de Gestión Rápida

```bash
cd /home/ramsi/reciclaje-app

# Control básico
./manage.sh start      # Iniciar aplicación
./manage.sh stop       # Detener aplicación  
./manage.sh restart    # Reiniciar aplicación
./manage.sh status     # Ver estado

# Monitoreo
./manage.sh logs       # Ver todos los logs
./manage.sh logs-app   # Solo logs del backend
./manage.sh logs-kiosk # Solo logs del navegador

# Diagnóstico
./manage.sh test-camera  # Probar cámara
./manage.sh test-nfc     # Probar NFC
./manage.sh check-temp   # Ver temperatura CPU

# Mantenimiento
./manage.sh update     # Actualizar dependencias
./manage.sh enable     # Habilitar autoarranque
./manage.sh disable    # Deshabilitar autoarranque
```

### Acceso Web

- **En la Raspberry Pi**: Se abre automáticamente en Chromium
- **Desde otro dispositivo**: http://IP_RASPBERRY:5000

## 🏗️ Estructura Final del Proyecto

```
ReciclajeApp/
├── backend/                    # Servidor Flask + WebSocket
│   └── app.py                 # Aplicación principal
├── frontend/                  # Interfaz web moderna
│   ├── templates/
│   │   └── index.html        # Página principal (simplificada)
│   └── static/
│       ├── css/style.css     # Estilos (solo cámara + navbar)
│       └── js/app.js         # Cliente WebSocket
├── config/                   # Configuración
│   ├── app_config.py        # Configuración Python
│   └── environment.env      # Variables de entorno ejemplo
├── modelo/                  # Modelo YOLO (copiar aquí)
├── requirements.txt         # Dependencias Python
├── install_reciclaje_pi.sh  # ⭐ INSTALADOR ÚNICO
└── README.md               # Esta documentación
```

## 🔧 Configuración Personalizada

### Editar Configuración

```bash
# Editar configuración principal
nano /home/ramsi/reciclaje-app/.env

# Configuraciones importantes:
MQTT_BROKER=tu-broker.com
MQTT_USER=tu-usuario  
MQTT_PASSWORD=tu-password
FIREBASE_DATABASE_URL=https://tu-proyecto.firebaseio.com
CAMERA_INDEX=0  # Cambiar si tienes múltiples cámaras
```

### Verificar Hardware

```bash
# Verificar cámara
ls /dev/video*
v4l2-ctl --list-devices

# Verificar NFC
pcsc_scan
opensc-tool --list-readers

# Verificar temperatura
vcgencmd measure_temp
```

## 🐛 Solución de Problemas

### Problemas Comunes y Soluciones Rápidas

#### 1. La aplicación no inicia
```bash
# Ver logs detallados
./manage.sh logs

# Verificar servicios
./manage.sh status

# Reiniciar servicios
./manage.sh restart
```

#### 2. Chromium no se abre
```bash
# Verificar que X11 está corriendo
sudo systemctl status lightdm

# Reiniciar entorno gráfico
sudo systemctl restart lightdm

# Ver logs específicos del kiosk
./manage.sh logs-kiosk
```

#### 3. Cámara no funciona
```bash
# Probar cámara
./manage.sh test-camera

# Verificar diferentes índices
nano /home/ramsi/reciclaje-app/.env
# Cambiar: CAMERA_INDEX=1 (o 2, 3, etc.)
```

#### 4. NFC no detecta tarjetas
```bash
# Probar NFC
./manage.sh test-nfc

# Reiniciar servicio PCSC
sudo systemctl restart pcscd

# Verificar permisos
sudo usermod -a -G scard ramsi
```

#### 5. Problemas de conectividad
```bash
# Verificar red
ping google.com

# Verificar servidor web local
curl http://localhost:5000

# Verificar puertos
netstat -tlnp | grep :5000
```

## 📊 Monitoreo del Sistema

### Logs Importantes

```bash
# Logs de la aplicación
tail -f /home/ramsi/reciclaje-app/logs/app.log
tail -f /home/ramsi/reciclaje-app/logs/startup.log
tail -f /home/ramsi/reciclaje-app/logs/kiosk.log

# Logs del sistema
sudo journalctl -u reciclaje-app -f
sudo journalctl -u reciclaje-kiosk -f
```

### Rendimiento

```bash
# Temperatura CPU
./manage.sh check-temp

# Uso de recursos
htop

# Espacio en disco
df -h

# Memoria
free -h
```

## 🔒 Seguridad y Mantenimiento

### Actualizaciones Regulares

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Actualizar dependencias de la aplicación
./manage.sh update

# Reiniciar después de actualizaciones importantes
sudo reboot
```

### Backup de Configuración

```bash
# Hacer backup de configuración
cp /home/ramsi/reciclaje-app/.env /home/ramsi/reciclaje-app/.env.backup

# Backup de logs importantes
tar -czf backup-logs-$(date +%Y%m%d).tar.gz /home/ramsi/reciclaje-app/logs/
```

## 🎯 Funcionalidades de la Interfaz

### Interfaz Simplificada
- **Navbar superior**: Indicadores de estado (Cámara, NFC, MQTT)
- **Feed de cámara**: Video en vivo con overlays de detección
- **Modales emergentes**: Para material detectado, éxito y errores
- **Responsive**: Se adapta a cualquier tamaño de pantalla

### Flujo de Uso
1. **Detección**: Coloca objeto frente a la cámara
2. **Reconocimiento**: Sistema detecta material (5 segundos)
3. **NFC**: Acerca tarjeta NFC al lector
4. **Confirmación**: Modal de éxito con puntos ganados
5. **Repetir**: Sistema listo para siguiente detección

## 🤝 Soporte

### Si tienes problemas:

1. **Revisa los logs**: `./manage.sh logs`
2. **Verifica el estado**: `./manage.sh status`
3. **Prueba hardware**: `./manage.sh test-camera` y `./manage.sh test-nfc`
4. **Reinicia servicios**: `./manage.sh restart`
5. **Reinicia sistema**: `sudo reboot`

### Archivos importantes para soporte:
- `/home/ramsi/reciclaje-app/.env` - Configuración
- `/home/ramsi/reciclaje-app/logs/` - Logs de la aplicación
- `/var/log/syslog` - Logs del sistema

---

## 🎉 ¡Instalación en 3 Pasos!

1. **Copiar archivos** a Raspberry Pi
2. **Ejecutar** `./install_reciclaje_pi.sh`
3. **Reiniciar** con `sudo reboot`

**¡Hecho con ❤️ para un mundo más sostenible! 🌍♻️**