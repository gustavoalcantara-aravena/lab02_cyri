#!/usr/bin/env python3
import socket
import threading
import time
import random
import json
import struct
import math

class SensorIndustrial:
    def __init__(self, id, tipo, unidad, rango_min, rango_max, ruido=0.1):
        self.id = id
        self.tipo = tipo
        self.unidad = unidad
        self.rango_min = rango_min
        self.rango_max = rango_max
        self.ruido = ruido
        self.valor = (rango_max + rango_min) / 2
        self.fallo = False
        
    def leer_valor(self):
        if self.fallo:
            return None
            
        # Simular dinámica del sensor
        cambio = random.uniform(-self.ruido, self.ruido)
        self.valor = max(self.rango_min, min(self.rango_max, self.valor + cambio))
        return round(self.valor, 2)
        
    def simular_fallo(self):
        self.fallo = True
        
    def reparar(self):
        self.fallo = False

class ProcesoIndustrial:
    def __init__(self, nombre, port=5000):
        self.nombre = nombre
        self.port = port
        self.running = True
        
        # Configurar sensores
        self.sensores = {
            "temp_reactor": SensorIndustrial("TR1", "temperatura", "°C", 0, 150, 0.5),
            "presion_reactor": SensorIndustrial("PR1", "presion", "bar", 0, 10, 0.1),
            "nivel_tanque": SensorIndustrial("NT1", "nivel", "%", 0, 100, 0.2),
            "flujo_entrada": SensorIndustrial("FE1", "flujo", "L/min", 0, 50, 0.3),
            "ph_reactor": SensorIndustrial("PH1", "ph", "pH", 0, 14, 0.05),
            "conductividad": SensorIndustrial("CD1", "conductividad", "mS/cm", 0, 200, 1)
        }
        
        # Variables de control
        self.setpoints = {
            "temp_reactor": 75.0,
            "presion_reactor": 5.0,
            "nivel_tanque": 80.0,
            "flujo_entrada": 25.0
        }
        
        # Estados de actuadores
        self.actuadores = {
            "valvula_entrada": False,
            "valvula_salida": False,
            "calentador": False,
            "agitador": False
        }
        
        # Configuración de red
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def iniciar_proceso(self):
        try:
            self.socket.bind(("127.0.0.1", self.port))
            self.socket.listen(1)
            print(f"[PLANTA] Proceso {self.nombre} iniciado en puerto {self.port}")
            
            while self.running:
                try:
                    # Configurar socket con timeout para poder cerrar limpiamente
                    self.socket.settimeout(1.0)
                    client_socket, addr = self.socket.accept()
                    client_socket.settimeout(0.1)  # Timeout más corto para operaciones
                    print(f"[PLANTA] Analizador conectado desde {addr}")
                    
                    # Bucle de comunicación
                    last_error_time = 0
                    error_count = 0
                    
                    while self.running:
                        try:
                            # Simular proceso
                            datos_proceso = self.simular_ciclo()
                            
                            # Crear y enviar trama Profinet
                            trama = self.crear_trama_profinet(datos_proceso)
                            bytes_enviados = client_socket.send(trama)
                            
                            if bytes_enviados == 0:
                                raise ConnectionError("Conexión cerrada por el cliente")
                            
                            # Recibir comandos (no bloqueante)
                            try:
                                comando = client_socket.recv(1024)
                                if comando:
                                    self.procesar_comando(comando)
                                else:
                                    raise ConnectionError("Cliente desconectado")
                            except socket.timeout:
                                pass  # Normal en operación no bloqueante
                            
                            # Resetear contadores de error si todo va bien
                            error_count = 0
                            
                            time.sleep(0.1)  # Ciclo de proceso
                            
                        except (ConnectionError, socket.error) as e:
                            current_time = time.time()
                            if current_time - last_error_time > 5:  # Limitar mensajes de error
                                print(f"[PLANTA] Error de comunicación: {e}")
                                last_error_time = current_time
                            
                            error_count += 1
                            if error_count > 3:  # Reintentar algunas veces antes de cerrar
                                break
                            
                            time.sleep(0.5)  # Esperar antes de reintentar
                            
                except socket.timeout:
                    continue  # Normal en operación de accept() con timeout
                except Exception as e:
                    print(f"[PLANTA] Error en conexión: {e}")
                    time.sleep(1)
                finally:
                    try:
                        client_socket.close()
                    except:
                        pass
                        
        except Exception as e:
            print(f"[PLANTA] Error crítico: {e}")
        finally:
            self.cleanup()
            
    def simular_ciclo(self):
        datos = {}
        
        # Simular proceso físico más realista
        dt = 0.1  # Intervalo de tiempo
        
        # 1. Simulación del reactor
        temp_actual = self.sensores["temp_reactor"].valor
        
        # Efecto del calentador (con inercia térmica)
        potencia_calentador = 2.0 if self.actuadores["calentador"] else 0.0
        temp_ambiente = 25.0
        
        # Ecuación diferencial simplificada para temperatura
        dT = (potencia_calentador - 0.1 * (temp_actual - temp_ambiente)) * dt
        nueva_temp = temp_actual + dT
        self.sensores["temp_reactor"].valor = max(temp_ambiente, min(150, nueva_temp))
        
        # 2. Simulación del tanque
        nivel_actual = self.sensores["nivel_tanque"].valor
        flujo_entrada = 5.0 if self.actuadores["valvula_entrada"] else 0.0
        flujo_salida = 3.0 if self.actuadores["valvula_salida"] else 0.0
        
        # Ecuación de balance de masa
        dnivel = (flujo_entrada - flujo_salida) * dt
        nuevo_nivel = nivel_actual + dnivel
        self.sensores["nivel_tanque"].valor = max(0, min(100, nuevo_nivel))
        
        # 3. Simulación de flujos
        self.sensores["flujo_entrada"].valor = flujo_entrada
        
        # 4. Simulación de presión (función de temperatura y nivel)
        temp_norm = self.sensores["temp_reactor"].valor / 150.0
        nivel_norm = self.sensores["nivel_tanque"].valor / 100.0
        nueva_presion = 1.0 + 3.0 * temp_norm + 2.0 * nivel_norm
        self.sensores["presion_reactor"].valor = nueva_presion
        
        # 5. Simulación de pH (afectado por temperatura)
        ph_base = 7.0
        ph_drift = 0.5 * math.sin(time.time() / 10.0)  # Oscilación lenta
        temp_effect = 0.2 * (temp_actual - 25) / 25
        self.sensores["ph_reactor"].valor = max(0, min(14, ph_base + ph_drift + temp_effect))
        
        # 6. Simulación de conductividad
        cond_base = 100.0
        temp_factor = 1.0 + 0.02 * (temp_actual - 25)  # Compensación de temperatura
        self.sensores["conductividad"].valor = cond_base * temp_factor
        
        # Recopilar datos de todos los sensores
        for sensor_id, sensor in self.sensores.items():
            datos[sensor_id] = {
                "valor": sensor.leer_valor(),
                "unidad": sensor.unidad,
                "estado": "ERROR" if sensor.fallo else "OK"
            }
        
        return datos
        
    def crear_trama_profinet(self, datos):
        """Crear una trama Profinet simulada con los datos del proceso"""
        # Cabecera Profinet simulada
        header = struct.pack('!6B',
            0x11, 0x22,  # MAC destino (simulado)
            0x33, 0x44,  # MAC origen (simulado)
            0x88, 0x92)  # EtherType Profinet
            
        # Datos en formato JSON
        payload = json.dumps(datos).encode()
        
        # Longitud total
        length = struct.pack('!H', len(payload))
        
        return header + length + payload
        
    def procesar_comando(self, comando):
        try:
            cmd = json.loads(comando.decode())
            if "actuador" in cmd:
                self.actuadores[cmd["actuador"]] = cmd["valor"]
            elif "setpoint" in cmd:
                self.setpoints[cmd["variable"]] = cmd["valor"]
            elif "simular_fallo" in cmd:
                self.sensores[cmd["sensor"]].simular_fallo()
            elif "reparar" in cmd:
                self.sensores[cmd["sensor"]].reparar()
        except:
            pass
            
    def cleanup(self):
        try:
            self.socket.close()
        except:
            pass
        self.running = False

def main():
    proceso = ProcesoIndustrial("Reactor Químico")
    try:
        proceso.iniciar_proceso()
    except KeyboardInterrupt:
        proceso.cleanup()

if __name__ == "__main__":
    main()
