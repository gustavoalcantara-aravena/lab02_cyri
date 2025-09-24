# Análisis de Códigos LAB_02 - Sistema Profinet Industrial

## 📋 Resumen General

El LAB_02 implementa un sistema de comunicación industrial basado en el protocolo Profinet, simulando una planta industrial completa con análisis de red en tiempo real.

## 🏭 **planta_industrial.py** - Servidor de Proceso Industrial

### **Propósito**
Simula una planta industrial real con sensores, actuadores y comunicación Profinet.

### **Arquitectura del Sistema**

#### **Clase SensorIndustrial**
```python
class SensorIndustrial:
    def __init__(self, id, tipo, unidad, rango_min, rango_max, ruido=0.1)
```

**Características:**
- **Simulación realista** de sensores industriales
- **Rangos configurables** para cada tipo de sensor
- **Simulación de ruido** y fallos
- **Dinámica temporal** con cambios graduales

**Sensores Implementados:**
- `temp_reactor`: Temperatura (0-150°C)
- `presion_reactor`: Presión (0-10 bar)
- `nivel_tanque`: Nivel (0-100%)
- `flujo_entrada`: Flujo (0-50 L/min)
- `ph_reactor`: pH (0-14)
- `conductividad`: Conductividad (0-200 mS/cm)

#### **Clase ProcesoIndustrial**
```python
class ProcesoIndustrial:
    def __init__(self, nombre, port=5000)
```

**Funcionalidades:**

1. **Simulación Física Realista:**
   ```python
   # Ecuación diferencial para temperatura
   dT = (potencia_calentador - 0.1 * (temp_actual - temp_ambiente)) * dt
   
   # Ecuación de balance de masa
   dnivel = (flujo_entrada - flujo_salida) * dt
   ```

2. **Sistema de Control:**
   - **Setpoints** configurables
   - **Actuadores** (válvulas, calentador, agitador)
   - **Control de lazo cerrado** implícito

3. **Comunicación Profinet:**
   ```python
   def crear_trama_profinet(self, datos):
       header = struct.pack('!6B', ...)  # Cabecera Ethernet
       payload = json.dumps(datos).encode()  # Datos JSON
       length = struct.pack('!H', len(payload))  # Longitud
       return header + length + payload
   ```

### **Características Técnicas**

#### **Protocolo de Comunicación**
- **Puerto**: 5000 (TCP)
- **Formato**: Ethernet + JSON
- **Ciclo de actualización**: 100ms
- **Manejo de errores**: Robusto con reintentos

#### **Simulación Matemática**
- **Ecuaciones diferenciales** para dinámica de procesos
- **Acoplamiento físico** entre variables (temp ↔ presión)
- **Efectos de temperatura** en pH y conductividad
- **Balance de masa** para nivel de tanque

---

## 📊 **analizador_profinet.py** - Cliente de Análisis

### **Propósito**
Interfaz gráfica para monitoreo, análisis y educación sobre redes Profinet.

### **Arquitectura de la Interfaz**

#### **Componentes Principales**
1. **Panel de Gráficos** (4 subplots)
2. **Panel de Control** (conexión, fallos)
3. **Panel de Métricas Profinet**
4. **Panel Educativo**
5. **Log de Comunicación**

#### **Gráficos en Tiempo Real**
```python
# 4 gráficos simultáneos
self.ax1.plot(tiempo, self.datos_historicos["temp_reactor"])
self.ax2.plot(tiempo, self.datos_historicos["presion_reactor"])
self.ax3.plot(tiempo, self.datos_historicos["nivel_tanque"])
self.ax4.plot(tiempo, self.datos_historicos["ph_reactor"])
```

### **Análisis de Red Profinet**

#### **Métricas Calculadas**
- **Latencia**: Tiempo de ida y vuelta
- **Jitter**: Variación de latencia
- **Tramas**: Contador de paquetes
- **Errores**: Detección de fallos
- **Ciclo de actualización**: Tiempo entre actualizaciones

#### **Simulación de Protocolo**
```python
def analizar_trama(self, data):
    # Extraer cabecera Ethernet
    header = data[:6]
    length_bytes = data[6:8]
    payload = data[8:]
    # Decodificar JSON
    datos = json.loads(payload.decode())
```

### **Características Educativas**

#### **Panel Educativo**
- **Introducción a Profinet**
- **Glosario de términos**
- **Estructura de tramas**
- **Características del protocolo**

#### **Funcionalidades de Aprendizaje**
```python
def profinet_intro_text(self):
    return (
        "PROFINET es un protocolo de comunicación industrial...\n"
        "- Comunicación determinística\n"
        "- Diagnóstico y alarmas\n"
        "- Tramas de datos IO\n"
    )
```

---

## 🔄 **Flujo de Comunicación**

### **Secuencia de Operación**

1. **Inicio del Servidor:**
   ```
   planta_industrial.py → Puerto 5000 → Espera conexiones
   ```

2. **Conexión del Cliente:**
   ```
   analizador_profinet.py → Conecta a 127.0.0.1:5000
   ```

3. **Ciclo de Datos:**
   ```
   Servidor: Simular proceso → Crear trama → Enviar
   Cliente: Recibir → Analizar → Actualizar gráficos
   ```

4. **Comandos de Control:**
   ```
   Cliente: Enviar comando JSON
   Servidor: Procesar → Actualizar actuadores
   ```

### **Formato de Trama Profinet Simulada**

```
| Cabecera Ethernet (6 bytes) | Longitud (2 bytes) | Datos JSON |
|-----------------------------|-------------------|------------|
| MAC destino/origen + EtherType | Tamaño payload | Variables del proceso |
```

---

## 🎯 **Características Destacadas**

### **Simulación Realista**
- **Física de procesos** con ecuaciones diferenciales
- **Acoplamiento entre variables** (temp → presión → pH)
- **Dinámica temporal** con inercia térmica
- **Balance de masa** para tanques

### **Comunicación Industrial**
- **Protocolo Profinet** simulado
- **Análisis de red** en tiempo real
- **Métricas de calidad** (latencia, jitter)
- **Detección de errores**

### **Interfaz Educativa**
- **Visualización en tiempo real**
- **Panel educativo** con información del protocolo
- **Glosario de términos**
- **Estructura de telegramas**

### **Robustez del Sistema**
- **Manejo de errores** robusto
- **Reconexión automática**
- **Timeouts configurables**
- **Logging detallado**

---

## 📊 **Comparación con LAB_01**

| Aspecto | LAB_01 (Modbus) | LAB_02 (Profinet) |
|---------|----------------|-------------------|
| **Protocolo** | Modbus TCP | Profinet simulado |
| **Complejidad** | Básico | Avanzado |
| **Simulación** | Variables simples | Proceso físico realista |
| **Interfaz** | SCADA industrial | Analizador + educativo |
| **Métricas** | Datos de proceso | Red + proceso |
| **Educación** | No | Sí (panel educativo) |

---

## 🚀 **Casos de Uso**

### **Para Aprendizaje**
- Entender protocolos industriales
- Análisis de redes Profinet
- Visualización de procesos industriales
- Conceptos de control de procesos

### **Para Desarrollo**
- Prototipo de sistema SCADA
- Simulador de planta industrial
- Herramienta de análisis de red
- Base para sistemas reales

### **Para Investigación**
- Análisis de rendimiento de red
- Simulación de fallos
- Optimización de procesos
- Estudios de latencia

---

## ⚠️ **Consideraciones Técnicas**

### **Limitaciones**
- **Simulación simplificada** del protocolo Profinet
- **Sin sincronización** de tiempo real estricta
- **Red local** únicamente (127.0.0.1)

### **Mejoras Posibles**
- Implementar **sincronización IEEE 1588**
- Agregar **topología de red** más compleja
- Incluir **diagnósticos avanzados**
- **Persistencia de datos** históricos

---

## 📝 **Conclusión**

El LAB_02 representa un **sistema educativo avanzado** que combina:

1. **Simulación realista** de procesos industriales
2. **Comunicación Profinet** educativa
3. **Análisis de red** en tiempo real
4. **Interfaz gráfica** completa
5. **Componente educativo** integrado

Es una **herramienta excelente** para aprender sobre:
- Protocolos de comunicación industrial
- Análisis de redes de automatización
- Simulación de procesos industriales
- Desarrollo de interfaces SCADA

**Calificación técnica**: ⭐⭐⭐⭐⭐ (Excelente para fines educativos)
