#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
import socket
import json
import struct
import random
from datetime import datetime

class AnalizadorProfinet:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador de Red Profinet")
        self.root.geometry("1400x800")
        
        # Variables de control
        self.running = True
        self.connected = False
        self.socket = None
        self.start_time = time.time()
        self.ultima_actualizacion = 0
        
        # Datos para análisis
        self.max_points = 100
        self.datos_historicos = {
            "tiempo": [],
            "temp_reactor": [],
            "presion_reactor": [],
            "nivel_tanque": [],
            "flujo_entrada": [],
            "ph_reactor": [],
            "conductividad": []
        }
        
        # Variables de proceso
        self.var_labels = {}
        
        # Estadísticas
        self.paquetes_recibidos = 0
        self.errores_detectados = 0
        self.bytes_transferidos = 0
        
        # Variables de estado
        self.stats_vars = {
            "estado": tk.StringVar(value="Desconectado"),
            "paquetes": tk.StringVar(value="0"),
            "errores": tk.StringVar(value="0"),
            "bytes": tk.StringVar(value="0 B")
        }
        
        # Métricas Profinet
        self.profinet_tramas = 0
        self.profinet_errores = 0
        self.profinet_latencias = []
        self.profinet_jitters = []
        self.profinet_ciclo = 0.0
        self.profinet_alarmas = []
        self.profinet_diagnostico = "Sin alarmas"
        self.profinet_io_estado = True
        
        
        self.setup_gui()
        self.setup_plots()
        self.setup_profinet_educativo()
        
        # Iniciar monitoreo
        self.monitor_thread = threading.Thread(target=self.monitor_network)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Iniciar actualización periódica
        self.actualizar_periodicamente()
        
    def setup_gui(self):
        # PANEL PRINCIPAL: Gráficos a la izquierda, panel educativo y botones a la derecha
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Panel de gráficos a la izquierda
        self.plot_frame = ttk.LabelFrame(main_frame, text="Gráficos de Proceso", padding="10")
        self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel derecho: botones, métricas y educativo
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)
        
        # Botones centrados arriba
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(pady=10)
        self.connect_btn = ttk.Button(btn_frame, text="Conectar",
                                    command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Simular Fallo",
                  command=self.simular_fallo).pack(side=tk.LEFT, padx=5)
        
        # Panel de estado
        estado_frame = ttk.LabelFrame(right_frame, text="Estado", padding="6")
        estado_frame.pack(fill=tk.X, pady=8)
        
        # Indicador de estado (círculo de color)
        self.estado_indicador = tk.Canvas(estado_frame, width=20, height=20)
        self.estado_indicador.pack(side=tk.LEFT, padx=5)
        self.estado_indicador.create_oval(5, 5, 15, 15, fill='red', tags='estado')
        
        # Etiqueta de estado
        ttk.Label(estado_frame, textvariable=self.stats_vars["estado"]).pack(side=tk.LEFT, padx=5)
        
        # Panel de estadísticas Profinet
        self.stats_profinet = ttk.LabelFrame(right_frame, text="Métricas Profinet", padding="6")
        self.stats_profinet.pack(fill=tk.X, pady=8)

        # Panel de log
        log_frame = ttk.LabelFrame(self.root, text="Log de Comunicación", padding="5")
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        self.log_text = tk.Text(log_frame, height=5, width=50)
        self.log_text.pack(fill=tk.X)
        
        # Panel educativo
        self.edu_frame = ttk.LabelFrame(right_frame, text="Panel Educativo Profinet", padding="10")
        self.edu_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.edu_text = tk.Text(self.edu_frame, height=18, width=48, wrap=tk.WORD, font=("Segoe UI", 9))
        self.edu_text.pack(fill=tk.BOTH, expand=True)
        self.edu_text.insert(tk.END, self.profinet_intro_text())
        self.edu_text.config(state=tk.DISABLED)

        # Botón para mostrar glosario y estructura de trama
        btn_glosario = ttk.Button(self.edu_frame, text="Glosario Profinet", command=self.mostrar_glosario)
        btn_glosario.pack(pady=5)
        btn_trama = ttk.Button(self.edu_frame, text="Estructura de Trama", command=self.mostrar_trama)
        btn_trama.pack(pady=5)

        # Variables de proceso
        self.var_labels = {}
        for label_name in ["Temperatura", "Presión", "Nivel", "Flujo", "pH", "Conductividad"]:
            self.var_labels[label_name] = tk.StringVar(value="0.0")
            ttk.Label(self.stats_profinet, text=f"{label_name}:").pack(anchor=tk.W, padx=5)
            ttk.Label(self.stats_profinet, textvariable=self.var_labels[label_name]).pack(anchor=tk.W, padx=20)

        self.profinet_vars = {
            "tramas": tk.StringVar(value="0"),
            "latencia": tk.StringVar(value="0.0 ms"),
            "jitter": tk.StringVar(value="0.0 ms"),
            "errores": tk.StringVar(value="0"),
            "ciclo": tk.StringVar(value="0.0 ms"),
            "io": tk.StringVar(value="OK"),
            "diagnostico": tk.StringVar(value="Sin alarmas")
        }
        for label, var in [
            ("Tramas:", "tramas"),
            ("Latencia Promedio:", "latencia"),
            ("Jitter:", "jitter"),
            ("Errores de Comunicación:", "errores"),
            ("Tiempo de Ciclo:", "ciclo"),
            ("Estado IO:", "io"),
            ("Diagnóstico:", "diagnostico")
        ]:
            frame = ttk.Frame(self.stats_profinet)
            frame.pack(anchor="w")
            ttk.Label(frame, text=label).pack(side=tk.LEFT)
            ttk.Label(frame, textvariable=self.profinet_vars[var], width=18, anchor="w").pack(side=tk.LEFT, padx=2)

    def actualizar_estadisticas(self):
        # Método vacío para evitar errores en la actualización periódica
        pass

    def actualizar_graficos(self):
        # Actualiza los datos de los gráficos con los datos históricos en tiempo real
        tiempo = self.datos_historicos["tiempo"]
        # Verifica que todas las listas tengan la misma longitud
        variables = ["temp_reactor", "presion_reactor", "nivel_tanque", "flujo_entrada", "ph_reactor", "conductividad"]
        lens = [len(self.datos_historicos[v]) for v in variables]
        if not tiempo or any(l == 0 for l in lens):
            self.log("No hay datos históricos suficientes para graficar todavía.")
            return
        if not all(len(self.datos_historicos[v]) == len(tiempo) for v in variables):
            self.log(f"Desincronización en históricos: tiempo={len(tiempo)}, " + ", ".join(f"{v}={len(self.datos_historicos[v])}" for v in variables))
            return
        # Limpiar cada eje antes de graficar (y reponer títulos, etiquetas y leyendas)
        self.ax1.cla()
        self.ax2.cla()
        self.ax3.cla()
        self.ax4.cla()
        # Temperatura
        self.ax1.plot(tiempo, self.datos_historicos["temp_reactor"], color='tab:red', label='Temperatura')
        self.ax1.set_title("Temperatura del Reactor", pad=10, fontsize=10)
        self.ax1.set_xlabel("Tiempo (s)", fontsize=9)
        self.ax1.set_ylabel("Temperatura (°C)", fontsize=9)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend(loc='upper right')
        # Presión
        self.ax2.plot(tiempo, self.datos_historicos["presion_reactor"], color='tab:blue', label='Presión')
        self.ax2.set_title("Presión del Sistema", pad=10, fontsize=10)
        self.ax2.set_xlabel("Tiempo (s)", fontsize=9)
        self.ax2.set_ylabel("Presión (bar)", fontsize=9)
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend(loc='upper right')
        # Nivel y Flujo
        self.ax3.plot(tiempo, self.datos_historicos["nivel_tanque"], color='tab:green', label='Nivel')
        self.ax3.plot(tiempo, self.datos_historicos["flujo_entrada"], color='tab:orange', label='Flujo')
        self.ax3.set_title("Nivel y Flujo", pad=10, fontsize=10)
        self.ax3.set_xlabel("Tiempo (s)", fontsize=9)
        self.ax3.set_ylabel("Nivel (%)", fontsize=9)
        self.ax3.grid(True, alpha=0.3)
        self.ax3.legend(loc='upper right')
        # pH y Conductividad
        self.ax4.plot(tiempo, self.datos_historicos["ph_reactor"], color='tab:purple', label='pH')
        self.ax4.plot(tiempo, self.datos_historicos["conductividad"], color='tab:brown', label='Conductividad')
        self.ax4.set_title("pH y Conductividad", pad=10, fontsize=10)
        self.ax4.set_xlabel("Tiempo (s)", fontsize=9)
        self.ax4.set_ylabel("pH", fontsize=9)
        self.ax4.grid(True, alpha=0.3)
        self.ax4.legend(loc='upper right')
        self.fig.tight_layout()
        self.canvas.draw()


    def actualizar_periodicamente(self):
        """Programa la actualización periódica de los gráficos"""
        if self.running:
            tiempo_actual = time.time()
            if tiempo_actual - self.ultima_actualizacion >= 0.5:  # Actualizar cada 500ms
                try:
                    self.actualizar_estadisticas()
                    self.ultima_actualizacion = tiempo_actual
                except Exception as e:
                    self.log(f"Error en actualización periódica: {e}")
            self.root.after(50, self.actualizar_periodicamente)  # Verificar cada 50ms
    
    def setup_profinet_educativo(self):
        # Variables para simulación de métricas
        self.profinet_tramas = 0
        self.profinet_latencias = []
        self.profinet_jitters = []
        self.profinet_errores = 0
        self.profinet_ciclo = 10.0  # ms
        self.profinet_alarmas = []
        self.profinet_io_estado = True
        self.profinet_diagnostico = "Sin alarmas"

    def profinet_intro_text(self):
        return (
            "PROFINET es un protocolo de comunicación industrial basado en Ethernet, utilizado para la automatización de procesos y fábricas.\n\n"
            "Características clave:\n"
            "- Comunicación determinística (cíclica y acíclica)\n"
            "- Diagnóstico y alarmas\n"
            "- Tramas de datos IO\n"
            "- Sincronización precisa\n\n"
            "En este analizador puedes observar métricas típicas de una red PROFINET, ver la estructura de tramas y consultar el glosario de términos.\n\n"
            "¿Sabías que PROFINET permite detectar fallos en tiempo real y diagnosticar dispositivos de campo? ¡Explora los paneles y aprende más!"
        )

    def mostrar_glosario(self):
        glosario = (
            "GLOSARIO PROFINET\n\n"
            "Trama: Paquete de datos enviado por la red.\n"
            "Latencia: Tiempo que tarda una trama en ir de origen a destino.\n"
            "Jitter: Variación de la latencia entre tramas sucesivas.\n"
            "Ciclo de actualización: Intervalo entre envíos cíclicos de datos IO.\n"
            "Diagnóstico: Información sobre fallos o estados anómalos en la red o dispositivos.\n"
            "IO: Entradas y salidas digitales/analógicas transmitidas por PROFINET.\n"
            "Alarmas: Mensajes especiales que indican eventos críticos.\n"
            "Topología: Forma en que se conectan los dispositivos en la red.\n"
            "MRP: Protocolo de redundancia de medios para alta disponibilidad.\n"
        )
        self.edu_text.config(state=tk.NORMAL)
        self.edu_text.delete(1.0, tk.END)
        self.edu_text.insert(tk.END, glosario)
        self.edu_text.config(state=tk.DISABLED)

    def mostrar_trama(self):
        estructura = (
            "ESTRUCTURA BÁSICA DE UNA TRAMA PROFINET\n\n"
            "| Cabecera Ethernet | PROFINET Header | Datos IO | Diagnóstico |\n"
            "---------------------------------------------------------------\n"
            "- Cabecera Ethernet: MAC destino, MAC origen, tipo\n"
            "- PROFINET Header: Tipo de trama, longitud, identificador\n"
            "- Datos IO: Estados de entradas/salidas cíclicos\n"
            "- Diagnóstico: Alarmas, eventos, información de fallo\n\n"
            "En este analizador simulamos la llegada de tramas y puedes ver cómo cambian las métricas de red en tiempo real."
        )
        self.edu_text.config(state=tk.NORMAL)
        self.edu_text.delete(1.0, tk.END)
        self.edu_text.insert(tk.END, estructura)
        self.edu_text.config(state=tk.DISABLED)

        # Configurar estilo
        style = ttk.Style()
        style.configure('TLabelframe', background='#f0f0f0')
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        
        # Panel superior
        control_frame = ttk.LabelFrame(self.root, text="Panel de Control SCADA", padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # --- NUEVO: Botones de control a la izquierda ---
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side=tk.LEFT, padx=10)
        self.connect_btn = ttk.Button(btn_frame, text="Conectar",
                                    command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Simular Fallo",
                  command=self.simular_fallo).pack(side=tk.LEFT, padx=5)
        
        # Marco de estado y estadísticas
        stats_frame = ttk.Frame(control_frame)
        stats_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Indicador de estado con color
        estado_frame = ttk.Frame(stats_frame)
        estado_frame.pack(side=tk.LEFT, padx=10)
        self.estado_indicador = tk.Canvas(estado_frame, width=15, height=15)
        self.estado_indicador.pack(side=tk.LEFT, padx=5)
        self.estado_indicador.create_oval(2, 2, 13, 13, fill='red', tags='estado')
        
        # Variables de estadísticas con formato mejorado
        self.stats_vars = {
            "estado": tk.StringVar(value="Desconectado"),
            "paquetes": tk.StringVar(value="0"),
            "errores": tk.StringVar(value="0"),
            "bytes": tk.StringVar(value="0 B")
        }
        
        # Etiquetas de estadísticas con mejor formato
        ttk.Label(estado_frame, text="Estado:").pack(side=tk.LEFT)
        ttk.Label(estado_frame, textvariable=self.stats_vars["estado"]).pack(side=tk.LEFT, padx=5)
        
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(side=tk.LEFT, padx=20)
        
        stats_labels = [
            ("Paquetes Recibidos:", "paquetes"),
            ("Errores Detectados:", "errores"),
            ("Datos Transferidos:", "bytes")
        ]
        
        for i, (label, var) in enumerate(stats_labels):
            container = ttk.Frame(stats_container)
            container.pack(side=tk.LEFT, padx=10)
            ttk.Label(container, text=label).pack(side=tk.LEFT)
            ttk.Label(container, textvariable=self.stats_vars[var],
                      width=10, anchor='e').pack(side=tk.LEFT, padx=5)
        
        # Panel de variables
        vars_frame = ttk.LabelFrame(self.root, text="Variables de Proceso", padding="10")
        vars_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.var_labels = {}
        for i, var in enumerate(["Temperatura", "Presión", "Nivel", "Flujo", "pH", "Conductividad"]):
            frame = ttk.Frame(vars_frame)
            frame.grid(row=i//3, column=i%3, padx=10, pady=5, sticky="nsew")
            ttk.Label(frame, text=f"{var}:").pack(side=tk.LEFT)
            self.var_labels[var] = tk.StringVar(value="--")
            ttk.Label(frame, textvariable=self.var_labels[var]).pack(side=tk.LEFT, padx=5)
            
        # Panel de log
        log_frame = ttk.LabelFrame(self.root, text="Log de Comunicación", padding="5")
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=5, width=50)
        self.log_text.pack(fill=tk.X)
        
        # Panel de gráficos
        self.plot_frame = ttk.Frame(self.root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_plots(self):
        # Buscar el main_frame para ubicar los gráficos correctamente
        main_frame = None
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame) and str(child.cget('class')) == 'TFrame':
                main_frame = child
                break
        if main_frame is None:
            main_frame = self.root
        # Crear el frame para los gráficos si no existe
        if not hasattr(self, 'plot_frame'):
            self.plot_frame = ttk.LabelFrame(main_frame, text="Gráficos de Proceso", padding="10")
            self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurar estilo de los gráficos
        plt.style.use('ggplot')
        self.fig, axs = plt.subplots(2, 2, figsize=(12, 8))
        self.ax1 = axs[0, 0]
        self.ax2 = axs[0, 1]
        self.ax3 = axs[1, 0]
        self.ax4 = axs[1, 1]
        self.fig.patch.set_facecolor('#f0f0f0')
        
        self.ax1.set_title("Temperatura del Reactor", pad=10, fontsize=10)
        self.ax1.set_xlabel("Tiempo (s)", fontsize=9)
        self.ax1.set_ylabel("Temperatura (°C)", fontsize=9)
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.set_title("Presión del Sistema", pad=10, fontsize=10)
        self.ax2.set_xlabel("Tiempo (s)", fontsize=9)
        self.ax2.set_ylabel("Presión (bar)", fontsize=9)
        self.ax2.grid(True, alpha=0.3)
        
        self.ax3.set_title("Nivel y Flujo", pad=10, fontsize=10)
        self.ax3.set_xlabel("Tiempo (s)", fontsize=9)
        self.ax3.set_ylabel("Nivel (%)", fontsize=9)
        self.ax3.grid(True, alpha=0.3)
        
        self.ax4.set_title("pH y Conductividad", pad=10, fontsize=10)
        self.ax4.set_xlabel("Tiempo (s)", fontsize=9)
        self.ax4.set_ylabel("pH", fontsize=9)
        self.ax4.grid(True, alpha=0.3)
        
        # Crear canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    def toggle_connection(self):
        if not self.connected:
            try:
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(1.0)
                self.socket.connect(("127.0.0.1", 5000))
                self.connected = True
                self.connect_btn.config(text="Desconectar")
                self.start_time = time.time()
                self.estado_indicador.itemconfig('estado', fill='green')
                self.stats_vars["estado"].set("Conectado")
                self.log("Conectado a la planta")
            except Exception as e:
                self.log(f"Error al conectar: {e}")
                self.estado_indicador.itemconfig('estado', fill='red')
                self.stats_vars["estado"].set("Error de conexión")
        else:
            self.disconnect()
            
    def disconnect(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None
        self.connect_btn.configure(text="Conectar")
        self.stats_vars["estado"].set("Estado: Desconectado")
        self.log("Desconectado del proceso")
        
    def simular_fallo(self):
        if self.connected and self.socket:
            cmd = {
                "simular_fallo": True,
                "sensor": "temp_reactor"
            }
            try:
                self.socket.send(json.dumps(cmd).encode())
                self.log("Simulando fallo en sensor de temperatura")
            except:
                self.disconnect()
                
    def analizar_trama(self, data):
        try:
            # Decodificar trama Profinet simulada
            if len(data) < 8:  # Verificar longitud mínima
                raise ValueError("Trama demasiado corta")
            # Extraer cabecera (6 bytes MAC + 2 bytes longitud)
            header = data[:6]
            length_bytes = data[6:8]
            payload = data[8:]
            longitud = int.from_bytes(length_bytes, byteorder='big')
            if len(payload) != longitud:
                raise ValueError(f"Longitud de payload incorrecta: esperada {longitud}, recibida {len(payload)}")
            try:
                datos = json.loads(payload.decode())
                return datos
            except json.JSONDecodeError:
                self.log("Error al decodificar JSON del payload")
                self.errores_detectados += 1
                return None
        except Exception as e:
            self.log(f"Error al analizar trama: {e}")
            self.errores_detectados += 1
            return None
            
        if self.paquetes_recibidos > 0:
            error_rate = (self.errores_detectados / self.paquetes_recibidos) * 100
        else:
            error_rate = 0
        
        # Actualizar variables
        self.stats_vars["paquetes"].set(f"{self.paquetes_recibidos}")
        self.stats_vars["errores"].set(f"{self.errores_detectados} ({error_rate:.1f}%)")
        self.stats_vars["bytes"].set(bytes_str)
        
    def log(self, mensaje):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {mensaje}\n")
        self.log_text.see(tk.END)
        
    def monitor_network(self):
        import random
        while self.running:
            if self.connected and self.socket:
                try:
                    # Configurar timeout más corto para lectura más frecuente
                    self.socket.settimeout(0.1)
                    
                    t_inicio = time.time()
                    data = self.socket.recv(1024)
                    t_fin = time.time()
                    
                    if not data:
                        raise ConnectionError("Conexión cerrada por el servidor")
                        
                    # Calcular métricas de red
                    latencia = (t_fin - t_inicio) * 1000  # ms
                    self.profinet_latencias.append(latencia)
                    if len(self.profinet_latencias) > 100:
                        self.profinet_latencias.pop(0)
                        
                    # Calcular jitter
                    if len(self.profinet_latencias) > 1:
                        jitter = abs(self.profinet_latencias[-1] - self.profinet_latencias[-2])
                        self.profinet_jitters.append(jitter)
                        if len(self.profinet_jitters) > 100:
                            self.profinet_jitters.pop(0)
                    
                    # Procesar datos recibidos
                    datos = self.analizar_trama(data)
                    if datos:
                        self.log(f"Datos recibidos: {datos}")
                        # Chequeo de cada variable esperada
                        todos_validos = True
                        for var in ["temp_reactor", "presion_reactor", "nivel_tanque", "flujo_entrada", "ph_reactor", "conductividad"]:
                            if var not in datos:
                                self.log(f"FALTA variable en datos: {var}")
                                todos_validos = False
                            else:
                                valor = datos[var]["valor"]
                                self.log(f"{var}: {valor}")
                                if valor is None:
                                    self.log(f"VALOR NULO para {var}")
                                    todos_validos = False
                        if todos_validos:
                            # Solo si todos los valores son válidos, agregamos a históricos
                            current_time = time.time() - self.start_time
                            self.datos_historicos["tiempo"].append(current_time)
                            for var in ["temp_reactor", "presion_reactor", "nivel_tanque", "flujo_entrada", "ph_reactor", "conductividad"]:
                                valor = datos[var]["valor"]
                                self.datos_historicos[var].append(valor)
                                # Actualizar etiqueta correspondiente
                                label_map = {
                                    "temp_reactor": "Temperatura",
                                    "presion_reactor": "Presión",
                                    "nivel_tanque": "Nivel",
                                    "flujo_entrada": "Flujo",
                                    "ph_reactor": "pH",
                                    "conductividad": "Conductividad"
                                }
                                if var in label_map and label_map[var] in self.var_labels:
                                    self.var_labels[label_map[var]].set(
                                        f"{valor:.1f} {datos[var]['unidad']}")
                        else:
                            self.log("No se agregó a históricos por datos faltantes o nulos.")
                            
                        # Mantener solo los últimos max_points
                        if len(self.datos_historicos["tiempo"]) > self.max_points:
                            for key in self.datos_historicos:
                                self.datos_historicos[key] = self.datos_historicos[key][-self.max_points:]
                        
                        # Actualizar métricas Profinet
                        self.profinet_tramas += 1
                        self.profinet_vars["tramas"].set(str(self.profinet_tramas))
                        if self.profinet_latencias:
                            self.profinet_vars["latencia"].set(f"{sum(self.profinet_latencias)/len(self.profinet_latencias):.1f} ms")
                        if self.profinet_jitters:
                            self.profinet_vars["jitter"].set(f"{sum(self.profinet_jitters)/len(self.profinet_jitters):.1f} ms")
                        self.profinet_vars["errores"].set(str(self.profinet_errores))
                        self.profinet_ciclo = latencia
                        self.profinet_vars["ciclo"].set(f"{self.profinet_ciclo:.1f} ms")
                        
                        # Actualizar gráficos y estadísticas
                        try:
                            self.root.after_idle(self.actualizar_graficos)
                            self.root.after_idle(self.actualizar_estadisticas)
                        except Exception as e:
                            self.log(f"Error al actualizar interfaz: {e}")
                        
                        # Actualizar bytes transferidos
                        self.bytes_transferidos += len(data)
                        self.paquetes_recibidos += 1
                        self.stats_vars["paquetes"].set(str(self.paquetes_recibidos))
                        self.stats_vars["bytes"].set(f"{self.bytes_transferidos} B")
                            
                except socket.timeout:
                    # Timeout es normal, continuamos
                    continue
                except Exception as e:
                    if self.running:
                        self.log(f"Error de comunicación: {e}")
                        self.disconnect()
                        break
            time.sleep(0.01)  # Reducir el tiempo de espera para actualizaciones más frecuentes
            
    def on_closing(self):
        self.running = False
        if self.connected:
            self.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = AnalizadorProfinet(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
