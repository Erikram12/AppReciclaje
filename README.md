# 🌱 Aplicación de Reciclaje Inteligente

Aplicación web desarrollada en **Python (Flask)** que utiliza **inteligencia artificial** para detectar automáticamente materiales reciclables como plástico y aluminio. Interfaz web intuitiva con procesamiento en tiempo real para clasificación de residuos.

---

## ✨ Características Principales

- **Detección de IA**: Clasifica automáticamente materiales reciclables (plástico, aluminio, vidrio, papel, etc.)
- **Interfaz Web Responsiva**: Acceso desde cualquier dispositivo
- **Procesamiento en Tiempo Real**: Análisis instantáneo de imágenes
- **Precisión Mejorada**: Modelo entrenado con miles de imágenes

---

## 📋 Requisitos Previos

- **Python** 3.11 o superior
- **Git** (para clonar el repositorio)
- **pip** (gestor de paquetes Python)
- **Sistema operativo**: Linux o Windows

---

## 🚀 Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone https://github.com/Erikram12/AppReciclaje.git
cd AppReciclaje
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
```

### 3. Activar entorno virtual

**En Linux:**
```bash
source venv/bin/activate
```

**En Windows:**
```bash
venv\Scripts\activate
```

### 4. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ▶️ Ejecución

Con el entorno virtual activado, ejecuta:

```bash
python backend/app.py
```

**Resultado esperado:**
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

Abre tu navegador en: **[http://localhost:5000](http://localhost:5000)**

---

## 📁 Estructura del Proyecto

```
AppReciclaje/
├── backend/
│   ├── app.py                    # Servidor Flask principal                
├── frontend/
│   ├── templates/
│   │   ├── index.html            # Página principal
│   └── static/
│       ├── css/
│       │   └── style.css         # Estilos
│       └── js/
│           └── app.js         # Lógica del cliente
├── modelo/
│   ├── best.onnx       # Modelo entrenado
├── config/
│   └── config.py                 # Configuración de la aplicación
├── requirements.txt              # Dependencias del proyecto
└── README.md                     # Este archivo
```

---

## 🛠️ Tecnologías Utilizadas

| Tecnología               | Uso |
|--------------------------|-----|
| **Flask**                | Framework web backend |
| **Ultralytics**          | Modelo de IA para clasificación |
| **OpenCV**               | Procesamiento de imágenes |
| **NumPy**          | Análisis de datos |
| **HTML5/CSS3/JavaScript** | Frontend responsivo |

---

## 📦 Dependencias Principales

Las dependencias se encuentran en `requirements.txt`:

```
Flask==3.0.0
TensorFlow==2.13.0
OpenCV-python==4.8.0
Pillow==10.0.0
NumPy==1.24.0
```

Para ver todas las dependencias:
```bash
cat requirements.txt
```

---


## 📚 Documentación Adicional

- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Ultralytics HUB](https://docs.ultralytics.com/hub/)
- [OpenCV](https://docs.opencv.org/)

---


## 👤 Autores

**Tu Nombre**
- GitHub: [@Erikram12](https://github.com/Erikram12)
- GitHub: [@AnySeyer](https://github.com/AnySeyer)
---