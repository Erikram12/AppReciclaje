/**
 * Aplicación Web de Reciclaje Inteligente
 * Cliente JavaScript con WebSocket para comunicación en tiempo real
 */

class ReciclajeApp {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.currentState = 'searching';
        this.detectionTimeout = null;
        this.modalTimeout = null;
        
        // Referencias DOM
        this.elements = {
            // Status indicators
            cameraStatus: document.getElementById('camera-status'),
            nfcStatus: document.getElementById('nfc-status'),
            mqttStatus: document.getElementById('mqtt-status'),
            
            // Camera
            cameraFeed: document.getElementById('camera-feed'),
            fpsDisplay: document.getElementById('fps-display'),
            detectionInfo: document.getElementById('detection-info'),
            materialName: document.getElementById('material-name'),
            progressFill: document.getElementById('progress-fill'),
            progressText: document.getElementById('progress-text'),
            
            
            // Modals
            materialModal: document.getElementById('material-modal'),
            successModal: document.getElementById('success-modal'),
            errorModal: document.getElementById('error-modal'),
            
            // Modal content
            modalMaterialIcon: document.getElementById('modal-material-icon'),
            modalMaterialName: document.getElementById('modal-material-name'),
            userName: document.getElementById('user-name'),
            pointsEarned: document.getElementById('points-earned'),
            pointsTotal: document.getElementById('points-total'),
            errorMessage: document.getElementById('error-message'),
            
            // Loading
            loadingOverlay: document.getElementById('loading-overlay')
        };
        
        // Configuración de materiales
        this.materialConfig = {
            plastico: {
                name: 'Plástico',
                icon: 'fas fa-bottle-water',
                color: '#2196F3',
                points: 20
            },
            aluminio: {
                name: 'Aluminio',
                icon: 'fas fa-can-food',
                color: '#9E9E9E',
                points: 30
            }
        };
        
        this.init();
    }
    
    /**
     * Inicializar aplicación
     */
    init() {
        console.log('🚀 Iniciando aplicación de reciclaje...');
        this.showLoading();
        this.initSocket();
        this.bindEvents();
        this.startHeartbeat();
    }
    
    /**
     * Inicializar conexión WebSocket
     */
    initSocket() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                timeout: 5000,
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionAttempts: 5
            });
            
            this.bindSocketEvents();
            console.log('🔌 Conectando WebSocket...');
            
        } catch (error) {
            console.error('❌ Error inicializando WebSocket:', error);
            this.showError('Error de conexión', 'No se pudo conectar al servidor');
        }
    }
    
    /**
     * Vincular eventos WebSocket
     */
    bindSocketEvents() {
        // Conexión establecida
        this.socket.on('connect', () => {
            console.log('✅ WebSocket conectado');
            this.isConnected = true;
            this.hideLoading();
            this.updateConnectionStatus();
        });
        
        // Desconexión
        this.socket.on('disconnect', (reason) => {
            console.log('❌ WebSocket desconectado:', reason);
            this.isConnected = false;
            this.updateConnectionStatus();
            this.showLoading();
        });
        
        // Error de conexión
        this.socket.on('connect_error', (error) => {
            console.error('❌ Error de conexión WebSocket:', error);
            this.showError('Error de Conexión', 'No se pudo conectar al servidor');
        });
        
        // Estado inicial
        this.socket.on('initial_state', (data) => {
            console.log('📊 Estado inicial recibido:', data);
            this.updateAppState(data.app_state);
            this.hideLoading();
        });
        
        // Frame de cámara
        this.socket.on('camera_frame', (data) => {
            this.updateCameraFrame(data);
        });
        
        // Material detectado
        this.socket.on('material_detectado', (data) => {
            console.log('🔍 Material detectado:', data);
            this.showMaterialDetected(data.material);
        });
        
        // Esperando NFC
        this.socket.on('waiting_nfc', (data) => {
            console.log('💳 Esperando NFC para:', data.material);
            // El modal ya debería estar abierto
        });
        
        // Material procesado exitosamente
        this.socket.on('material_procesado', (data) => {
            console.log('✅ Material procesado:', data);
            this.showProcessingSuccess(data);
        });
        
        // Error NFC
        this.socket.on('nfc_error', (data) => {
            console.log('❌ Error NFC:', data);
            this.showError('Error NFC', data.message);
        });
        
        
        // Estado MQTT
        this.socket.on('mqtt_status', (data) => {
            console.log('📡 Estado MQTT:', data);
            this.updateMqttStatus(data.connected);
        });
        
        // Reset del sistema
        this.socket.on('system_reset', () => {
            console.log('🔄 Sistema reseteado');
            this.closeAllModals();
        });
        
        // Actualización de estado
        this.socket.on('status_update', (data) => {
            this.updateAppState(data);
        });
    }
    
    /**
     * Vincular eventos DOM
     */
    bindEvents() {
        // Cerrar modales al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
        
        // Tecla ESC para cerrar modales
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
        
        // Botones de cerrar modal
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }
    
    /**
     * Actualizar frame de cámara
     */
    updateCameraFrame(data) {
        if (this.elements.cameraFeed && data.frame) {
            this.elements.cameraFeed.src = data.frame;
        }
        
        if (this.elements.fpsDisplay) {
            this.elements.fpsDisplay.textContent = `${data.fps} FPS`;
        }
        
        // Actualizar información de detección
        if (data.deteccion_activa) {
            this.showDetectionProgress(data.deteccion_activa, data.progreso);
        } else {
            this.hideDetectionProgress();
        }
        
        // Actualizar estado de cámara
        this.updateCameraStatus(true);
    }
    
    /**
     * Mostrar progreso de detección
     */
    showDetectionProgress(material, progress) {
        if (!this.elements.detectionInfo) return;
        
        const config = this.materialConfig[material];
        if (!config) return;
        
        this.elements.detectionInfo.style.display = 'block';
        
        if (this.elements.materialName) {
            this.elements.materialName.textContent = config.name;
            this.elements.materialName.style.color = config.color;
        }
        
        if (this.elements.progressFill) {
            this.elements.progressFill.style.width = `${progress * 100}%`;
            this.elements.progressFill.style.background = `linear-gradient(90deg, ${config.color}, #4CAF50)`;
        }
        
        if (this.elements.progressText) {
            this.elements.progressText.textContent = `${Math.round(progress * 100)}%`;
        }
    }
    
    /**
     * Ocultar progreso de detección
     */
    hideDetectionProgress() {
        if (this.elements.detectionInfo) {
            this.elements.detectionInfo.style.display = 'none';
        }
    }
    
    /**
     * Mostrar modal de material detectado
     */
    showMaterialDetected(material) {
        const config = this.materialConfig[material];
        if (!config) return;
        
        // Actualizar contenido del modal
        if (this.elements.modalMaterialName) {
            this.elements.modalMaterialName.textContent = config.name;
        }
        
        if (this.elements.modalMaterialIcon) {
            this.elements.modalMaterialIcon.innerHTML = `<i class="${config.icon}"></i>`;
            this.elements.modalMaterialIcon.style.background = 
                `linear-gradient(45deg, ${config.color}, #4CAF50)`;
        }
        
        // Mostrar modal
        this.showModal('material-modal');
        
    }
    
    /**
     * Mostrar éxito de procesamiento
     */
    showProcessingSuccess(data) {
        // Cerrar modal anterior
        this.closeModal('material-modal');
        
        // Actualizar contenido del modal de éxito
        if (this.elements.userName) {
            this.elements.userName.textContent = data.usuario.nombre;
        }
        
        if (this.elements.pointsEarned) {
            this.elements.pointsEarned.textContent = data.puntos;
        }
        
        if (this.elements.pointsTotal) {
            this.elements.pointsTotal.textContent = `${data.usuario.puntos_nuevos} puntos`;
        }
        
        // Mostrar modal de éxito
        this.showModal('success-modal');
        
        
        // Auto-cerrar después de 5 segundos
        this.modalTimeout = setTimeout(() => {
            this.closeModal('success-modal');
        }, 5000);
        
    }
    
    /**
     * Mostrar modal
     */
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }
    
    /**
     * Cerrar modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
        
        // Limpiar timeout si existe
        if (this.modalTimeout) {
            clearTimeout(this.modalTimeout);
            this.modalTimeout = null;
        }
    }
    
    /**
     * Cerrar todos los modales
     */
    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
        document.body.style.overflow = '';
        
        if (this.modalTimeout) {
            clearTimeout(this.modalTimeout);
            this.modalTimeout = null;
        }
    }
    
    /**
     * Mostrar error
     */
    showError(title, message) {
        if (this.elements.errorMessage) {
            this.elements.errorMessage.textContent = message;
        }
        
        const errorModal = document.getElementById('error-modal');
        if (errorModal) {
            const titleElement = errorModal.querySelector('.modal-header h2');
            if (titleElement) {
                titleElement.textContent = title;
            }
        }
        
        this.showModal('error-modal');
    }
    
    /**
     * Actualizar estado de la aplicación
     */
    updateAppState(state) {
        if (!state) return;
        
        
        // Actualizar estados de conexión
        this.updateCameraStatus(state.camera_active);
        this.updateNfcStatus(state.nfc_active);
        this.updateMqttStatus(state.mqtt_connected);
        
    }
    
    
    /**
     * Actualizar estados de conexión
     */
    updateConnectionStatus() {
        // Actualizar indicador general basado en WebSocket
        document.querySelectorAll('.status-item').forEach(item => {
            if (this.isConnected) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }
    
    updateCameraStatus(active) {
        if (this.elements.cameraStatus) {
            if (active) {
                this.elements.cameraStatus.classList.add('active');
            } else {
                this.elements.cameraStatus.classList.remove('active');
            }
        }
    }
    
    updateNfcStatus(active) {
        if (this.elements.nfcStatus) {
            if (active) {
                this.elements.nfcStatus.classList.add('active');
            } else {
                this.elements.nfcStatus.classList.remove('active');
            }
        }
    }
    
    updateMqttStatus(connected) {
        if (this.elements.mqttStatus) {
            if (connected) {
                this.elements.mqttStatus.classList.add('active');
            } else {
                this.elements.mqttStatus.classList.remove('active');
            }
        }
    }
    
    /**
     * Mostrar loading
     */
    showLoading() {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.classList.remove('hidden');
        }
    }
    
    /**
     * Ocultar loading
     */
    hideLoading() {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.classList.add('hidden');
        }
    }
    
    /**
     * Animar número
     */
    animateNumber(element, targetValue) {
        if (!element) return;
        
        const currentValue = parseInt(element.textContent) || 0;
        const increment = Math.ceil((targetValue - currentValue) / 20);
        
        if (increment === 0) return;
        
        const timer = setInterval(() => {
            const current = parseInt(element.textContent) || 0;
            const next = current + increment;
            
            if ((increment > 0 && next >= targetValue) || (increment < 0 && next <= targetValue)) {
                element.textContent = targetValue;
                clearInterval(timer);
            } else {
                element.textContent = next;
            }
        }, 50);
    }
    
    /**
     * Heartbeat para mantener conexión
     */
    startHeartbeat() {
        setInterval(() => {
            if (this.socket && this.isConnected) {
                this.socket.emit('request_status');
            }
        }, 30000); // Cada 30 segundos
    }
    
    /**
     * Solicitar reset del sistema
     */
    resetSystem() {
        if (this.socket && this.isConnected) {
            fetch('/api/reset', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('🔄 Sistema reseteado:', data);
                })
                .catch(error => {
                    console.error('❌ Error reseteando sistema:', error);
                });
        }
    }
}

// Función global para cerrar modales (usada en HTML)
window.closeModal = function(modalId) {
    if (window.app) {
        window.app.closeModal(modalId);
    }
};

// Inicializar aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌟 DOM cargado, inicializando aplicación...');
    window.app = new ReciclajeApp();
});

// Manejar errores globales
window.addEventListener('error', (event) => {
    console.error('❌ Error global:', event.error);
    if (window.app) {
        window.app.showError('Error de Aplicación', 'Ha ocurrido un error inesperado');
    }
});

// Manejar errores de promesas no capturadas
window.addEventListener('unhandledrejection', (event) => {
    console.error('❌ Promesa rechazada:', event.reason);
    if (window.app) {
        window.app.showError('Error de Conexión', 'Error en comunicación con el servidor');
    }
});
