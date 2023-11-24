from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
import random

import numpy as np
import math

#Variables globales utilizadas para simular la logistica de llegada y salida de articulos 
#Estos aluden a la restriccion de: Solo se ofertan los articulos que existen en almacén, por lo que 
#si no hay un articulo N
#No sale un articulo N

class Llegada(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.ocupada = False
        self.sensor_paquete = False #Define si llegó un tipo de paquete
        self.contiene = None #Tipo de paquete que llegó 
        self.recolector_id = None #Id del robot que esta más cerca del paquete que llegó y recogerá el paquete 
        self.min_dist_recolector = float('inf') #Variable que decidirá quien va por el paquete mediante un proceso de subasta por distancia 
        self.paquetes_por_llegar = [] #Arreglo que contendrá la cantidad y tipo de paquete que irá llegando x steps {tipo:step}
        self.horas_de_llegada = []
        self.paso = 0

    def step(self):
        self.paso += 1
        self.llega_paquete()

    def llega_paquete(self):
        llega_paquete = random.randint(0, 10)
        if llega_paquete == 2 and len(self.model.paquetes_en_almacen) < 16 and self.sensor_paquete == False:
            #Se obtiene el tipo de paquete que llegara
            paquete_entrante = random.randint(0,15)
            while paquete_entrante in self.model.paquetes_en_almacen:
                paquete_entrante = random.randint(0, 15)
            self.paquetes_por_llegar.append(paquete_entrante)
            print(f"Llega paquete {paquete_entrante}")

    def advance(self):
        print(self.model.paquetes_en_almacen)
        if len(self.paquetes_por_llegar) > 0:
            print('----Llamada de paquete entrante----')
            self.contiene = self.paquetes_por_llegar.pop(0)  # Remover y obtener el primer paquete de la lista
            self.sensor_paquete = True
            
        x, y = self.pos

        # Obtener todos los agentes en la misma celda
        agentes_en_misma_celda = self.model.grid.get_cell_list_contents([(x, y)])

        ocupada = False
        # Iterar sobre los agentes en la misma celda
        for otro_agente in agentes_en_misma_celda:
            # Verificar si el otro agente no es el mismo que el agente actual
            if isinstance(otro_agente, RobotLimpieza):
                ocupada = True

        if ocupada:
            self.ocupada = True
        else: 
            self.ocupada = False

    def liberar_tarima(self):
        self.sensor_paquete = False
        #self.contiene = None
        self.recolector_id = None
        self.min_dist_recolector = float('inf')

class Salida(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.ocupada = False
        self.sensor_pedido = False #Define si llegó un tipo de paquete
        self.pedido = None #Tipo de paquete que llegó 
        self.pedidos = [] #Arreglo que contendrá la cantidad y tipo de paquete que irá llegando x steps {tipo:step}
        self.recolector_id = None #Id del robot que esta más cerca del paquete que llegó y recogerá el paquete 
        self.min_dist_recolector = float('inf') #Variable que decidirá quien va por el paquete media
        self.paso = 0 
        self.pedidos_recibidos = []
        
    def step(self):
        self.paso += 1
        self.llega_pedido()

        x, y = self.pos

        # Obtener todos los agentes en la misma celda
        agentes_en_misma_celda = self.model.grid.get_cell_list_contents([(x, y)])

        ocupada = False
        # Iterar sobre los agentes en la misma celda
        for otro_agente in agentes_en_misma_celda:
            # Verificar si el otro agente no es el mismo que el agente actual
            if isinstance(otro_agente, RobotLimpieza):
                ocupada = True

        if ocupada:
            self.ocupada = True
        else: 
            self.ocupada = False

    def advance(self):
        if len(self.pedidos) > 0 and self.sensor_pedido != True:
            print('----Llamada de pedido----')
            self.pedido = self.pedidos.pop(0)  # Remover y obtener el primer paquete de la lista
            self.sensor_pedido = True

    def llega_pedido(self):
        llega_pedido = random.randint(0, 10)
        if llega_pedido == 2 and len(self.model.paquetes_en_almacen) > 4 and self.pedido == None and self.sensor_pedido == False:
            #Se obtiene el tipo de pedido que saldra
            pedido_saliente = random.randint(0,15)
            while pedido_saliente not in self.model.paquetes_en_almacen:
                pedido_saliente = random.randint(0, 15)
            self.pedidos.append(pedido_saliente)
            print(f"Sale pedido {pedido_saliente}")

    def liberar_tarima(self):
        self.sensor_pedido = False
        self.recolector_id = None
        self.min_dist_recolector = float('inf')

    def recibir_pedido(self, pedido):
        self.pedidos_recibidos.append(pedido)
        self.pedido = None
        self.model.paquetes_en_almacen.remove(pedido)

class Celda(Agent):
    def __init__(self, unique_id, model, suciedad: bool = False):
        super().__init__(unique_id, model)
        self.sucia = suciedad
        self.ocupada = False
    
    def step(self):
        x, y = self.pos

        # Obtener todos los agentes en la misma celda
        agentes_en_misma_celda = self.model.grid.get_cell_list_contents([(x, y)])

        ocupada = False
        # Iterar sobre los agentes en la misma celda
        for otro_agente in agentes_en_misma_celda:
            # Verificar si el otro agente no es el mismo que el agente actual
            if isinstance(otro_agente, RobotLimpieza):
                ocupada = True

        if ocupada:
            self.ocupada = True
        else: 
            self.ocupada = False

class Mueble(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.ocupada = True

# Agente cargador
class Cargador(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carga = 100
        self.ocupada = False

    def pos_cargador(i, j):
        pos_x = i
        pos_y = j
        return pos_x, pos_y
    
    def set_ocupada(self, value):
        self.ocupada = value

class Estanteria(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.ocupada = True
        self.tipo_estanteria = 0
        self.disponible = True

    def pos_estanteria(i, j):
        pos_x = i
        pos_y = j
        return pos_x, pos_y
    
    def almacenar_paquete(self):
        self.disponible = False
    
    def vaciar(self):
        self.disponible = True

class Sitio_espera(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.ocupada = False
        self.disponible = True
        self.seleccionado = False

    def step(self):
        x, y = self.pos

        # Obtener todos los agentes en la misma celda
        agentes_en_misma_celda = self.model.grid.get_cell_list_contents([(x, y)])

        es_robot = False
        # Iterar sobre los agentes en la misma celda
        for otro_agente in agentes_en_misma_celda:
            #print(otro_agente)
            # Verificar si el otro agente no es el mismo que el agente actual
            if isinstance(otro_agente, RobotLimpieza) :
                es_robot = True

        if es_robot == False and self.seleccionado == False: 
            self.disponible = True
        else: 
            self.disponible = False


class RobotLimpieza(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model) 
        self.ocupada = True
        self.sig_pos = None
        self.movimientos = 0
        self.carga = 100
        self.recarga = 0
        self.contiene = None
        self.busca = None
        self.estanteria_destino = None
        self.destination = (0,0) #variable que almacenará el cargador al que se debe dirigir si su batería llega a un nivel crítico
        self.destino_paquete = None
        self.carga_optima = True 
        self.esta_cargando = False
        self.esta_formado = False
        self.esta_esperando = True
        self.esta_recolectando = False 
        self.esta_almacenando = False
        self.esta_ofertando = False
        self.esta_ofertando_pedido = False
        self.esta_desalojando_area = False
        self.esta_despachando_pedido = False
        self.esta_entregando_pedido = False
        self.esta_formandose = False
    
    def desalojar_area(self):
        x, y = self.pos
        self.esta_desalojando_area = True
        self.destino_paquete = (x, y - 4)

    def buscar_estanteria(self, tipo_paquete):
        lista_estanterias = [agent for agent in self.model.schedule.agents if isinstance(agent, Estanteria) and agent.tipo_estanteria == tipo_paquete]
        for estanteria in lista_estanterias: 
            return estanteria.pos

    def tomar_paquete(self):
        lista_tarima_llegada = [agent for agent in self.model.schedule.agents if isinstance(agent, Llegada)] #Arreglo de entrada para la lista de cargadores
        for tarima_llegada in lista_tarima_llegada:
            tarima_llegada.unique_id
            tipo_paquete = tarima_llegada.contiene
            self.contiene = tipo_paquete
            print(f'{self.contiene} unidad {self.unique_id}')
            #funcion que define el detino_paquete a la posicion de la estanteria que corresponde
            self.destino_paquete = self.buscar_estanteria(self.contiene)
            #libera la tarima
            tarima_llegada.liberar_tarima()

    def tomar_pedido(self):
        lista_estanterias = [agent for agent in self.model.schedule.agents if isinstance(agent, Estanteria) and agent.tipo_estanteria == self.busca]
        for estanteria in lista_estanterias: 
            estanteria.vaciar()
            self.busca = None
            self.contiene = estanteria.tipo_estanteria
            lista_tarima_salida = [agent for agent in self.model.schedule.agents if isinstance(agent, Salida)] #Arreglo de entrada para la lista de cargadores
            for tarima_salida in lista_tarima_salida:
                self.destino_paquete = tarima_salida.pos
    
    @staticmethod
    def distancia_euclidiana(punto1, punto2):
        x1, y1 = punto1
        x2, y2 = punto2
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def comprobar_pedidos(self):
        #print(f'{self.unique_id} comprobando pedido...')
        lista_tarima_salida = [agent for agent in self.model.schedule.agents if isinstance(agent, Salida)] #Arreglo de entrada para la lista de cargadores
        for tarima_salida in lista_tarima_salida:
            #print('comprobando distancia')
            if tarima_salida.sensor_pedido == True:
                tipo_pedido = tarima_salida.pedido
                estanteria_x, estanteria_y = self.buscar_estanteria(tipo_pedido)
                distancia_a_salida = self.distancia_euclidiana(self.pos, (estanteria_x, estanteria_y))
                if tarima_salida.min_dist_recolector > distancia_a_salida:
                    print(f'{self.unique_id} ofertando despacho de pedido...')
                    tarima_salida.min_dist_recolector = distancia_a_salida
                    tarima_salida.recolector_id = self.unique_id

    def comprobar_paquetes(self):
        #print(f'{self.unique_id} comprobando paquete...')
        lista_tarima_llegada = [agent for agent in self.model.schedule.agents if isinstance(agent, Llegada)] #Arreglo de entrada para la lista de cargadores
        for tarima_llegada in lista_tarima_llegada:
            #print('comprobando distancia')
            if tarima_llegada.sensor_paquete == True:
                distancia_a_llegada = self.distancia_euclidiana(self.pos, tarima_llegada.pos)
                if tarima_llegada.min_dist_recolector > distancia_a_llegada:
                    #print(f'{self.unique_id} ofertando...')
                    tarima_llegada.min_dist_recolector = distancia_a_llegada
                    tarima_llegada.recolector_id = self.unique_id

    def despachar_pedido(self):
        #print('verificando ganador de despacho de pedido...')
        lista_tarima_salida = [agent for agent in self.model.schedule.agents if isinstance(agent, Salida)] #Arreglo de entrada para la lista de cargadores
        for tarima in lista_tarima_salida:
            if tarima.recolector_id == self.unique_id:
                tarima.liberar_tarima()
                self.esta_despachando_pedido = True
                self.esta_esperando = False
                self.busca = tarima.pedido
                self.estanteria_destino = tarima.pedido
                self.destino_paquete = self.buscar_estanteria(self.busca)
                print(f'Robot {self.unique_id} escogido para despachar pedido')
            
    def entregar_pedido(self):
        lista_tarima_salida = [agent for agent in self.model.schedule.agents if isinstance(agent, Salida)] #Arreglo de entrada para la lista de cargadores
        for tarima in lista_tarima_salida:
            tarima.recibir_pedido(self.contiene)
            self.contiene = None 
            self.busca = None
            self.estanteria_destino = None
            self.esta_entregando_pedido = False

    def recoger_paquete(self):
        lista_tarima_llegada = list()
        lista_tarima_llegada = [agent for agent in self.model.schedule.agents if isinstance(agent, Llegada)] #Arreglo de entrada para la lista de cargadores
        for tarima in lista_tarima_llegada:
            if tarima.recolector_id == self.unique_id:
                self.esta_recolectando = True
                self.esta_esperando = False
                self.destino_paquete = tarima.pos
                self.estanteria_destino = tarima.contiene
                print(f'Robot {self.unique_id} escogido para recoger paquete')  
            # else: 
            #     print('No hay paquete que recoger...')           

    def ir_por_paquete(self):
        # Dirigirse al cargador considerando al entorno
        vecinos = self.model.grid.get_neighbors(
                self.pos, moore=True, include_center=False)

        if self.destino_paquete == None:
            print(f'{self.unique_id} es el erroneo')

        for vecino in vecinos:
            if vecino.ocupada == True and not(isinstance(vecino, Estanteria)):
                vecinos.remove(vecino)
                
        minDist = float('inf')
        for vecino in vecinos:
            # Verificar si la celda contiene un RobotBarredora o Estanteria con tipo incorrecto
            if not isinstance(vecino, (RobotLimpieza, Estanteria)) or (isinstance(vecino, Estanteria) and vecino.tipo_estanteria == self.estanteria_destino):
                dist = self.distancia_euclidiana(vecino.pos, self.destino_paquete)
                if dist < minDist:
                    minDist = dist
                    self.sig_pos = vecino.pos
    
    def almacenar_paquete(self):
        lista_estanterias = [agent for agent in self.model.schedule.agents if isinstance(agent, Estanteria) and agent.tipo_estanteria == self.contiene]
        for estanteria in lista_estanterias: 
            if self.contiene not in self.model.paquetes_en_almacen:
                self.model.paquetes_en_almacen.append(self.contiene)
            self.contiene = None
            self.esta_almacenando = False
            self.estanteria_destino = None
            estanteria.almacenar_paquete()

    def buscar_cargador(self, origin):
        lista_cargadores = list()
        lista_cargadores = [agent for agent in self.model.schedule.agents if isinstance(agent, Cargador)] #Arreglo de entrada para la lista de cargadores
        minDistance = float('inf')
        closestCharger = None
        cargador_destino = None
        x, y = origin
        # Iterar sobre la lista de cargadores
        for cargador in lista_cargadores:
            cargador_pos = cargador.pos
            print(cargador.ocupada)
            distancia = self.distancia_euclidiana((x, y), cargador_pos)
            if abs(distancia) < abs(minDistance) and cargador.ocupada == False:
                minDistance = distancia
                closestCharger = cargador_pos
                cargador_destino = cargador
                d_x, d_y = closestCharger
                
        if cargador_destino != None:
            self.destination = (d_x, d_y)#Establecemos un destino para que el robot se dirija ahi
            cargador_destino.set_ocupada(True)
            self.esta_esperando = False
        # Si no encuentra cargador desocupado se detiene y entra en estado de espera
        if self.destination == (0, 0):
            self.esta_esperando = True
        # print(self.destination)

    def ir_a_cargador(self):
        # Dirigirse al cargador considerando al entorno
        vecinos = self.model.grid.get_neighbors(
                self.pos, moore=True, include_center=False)

        for vecino in vecinos:
            if vecino.ocupada == True:
                vecinos.remove(vecino)

        minDist = float('inf')
        for vecino in vecinos:
            if not isinstance(vecino, (RobotLimpieza, Estanteria)):
                dist = self.distancia_euclidiana(vecino.pos, self.destination)
                if dist < minDist:
                    minDist = dist
                    self.sig_pos = vecino.pos
        

        # print(f"SIGUIENTE PASO: {self.sig_pos}")
    
    def agentes_en_posicion(self, x, y):
        cell_contents = self.model.grid.get_cell_list_contents((x, y))
        return cell_contents
    
    def cargar_bateria(self):
        if self.carga > 90:
            x, y = self.pos  # Obtén la posición del agente principal
            celdas = self.model.grid.get_cell_list_contents([(x, y)])
            for contenido in celdas:
                if isinstance(contenido, Cargador):
                    # Modifica el atributo "ocupada" del Cargador
                    contenido.set_ocupada(False)
                    print(f"Se modificó 'ocupada' del Cargador en la posición {contenido.pos} a False")
                    
            self.carga_optima = True
            self.destination = (0,0)
            x, y = self.pos
            # agentes_en_celda = self.agentes_en_posicion(x, y)
            # cargador = [agent for agent in agentes_en_celda if isinstance(agent, Cargador)]
            # cargador[0].ocupada = False;    
        elif self.carga + 25 > 100:
            self.carga += 100 - self.carga
        else: 
            self.carga += 25

    def deseleccionar_sitio(self):
        x, y = self.pos

        # Obtener todos los agentes en la misma celda
        agentes_en_misma_celda = self.model.grid.get_cell_list_contents([(x, y)])

        # Iterar sobre los agentes en la misma celda
        for otro_agente in agentes_en_misma_celda:
            # Verificar si el otro agente es un RobotLimpieza
            if isinstance(otro_agente, Sitio_espera):
                otro_agente.seleccionado = False
                
    def ir_a_formacion(self):
        # print(f'{self.unique_id} yendo a formaciòn')
        lista_sitios_espera = [agent for agent in self.model.schedule.agents if isinstance(agent, Sitio_espera) and agent.disponible == True] #Arreglo de entrada para la lista de cargadores
        sitios = list()
        for sitio in lista_sitios_espera:
            # print(sitio.unique_id)
            sitios.append(sitio)
        #     print(sitio.unique_id)
        #     if sitio.unique_id < max:
        #         max = sitio.unique_id
        
        # print(max)
        
        # lista_sitios_espera = [agent for agent in self.model.schedule.agents if isinstance(agent, Sitio_espera) and agent.unique_id == max] #Arreglo de entrada para la lista de cargadores
        # for sitio in lista_sitios_espe ra:
        sitio = sitios[0]
        self.destino_paquete = sitio.pos
        sitio.disponible = False
        sitio.seleccionado = True
            
    def step(self):
        if self.carga > 25 and self.carga_optima:
            self.esta_cargando = False
            #En caso de terminar una tarea, desocupa el área para no estorbar a otros ants
            if self.esta_desalojando_area == True and self.destino_paquete != self.pos: 
                self.ir_por_paquete()

            if self.esta_desalojando_area == True and self.destino_paquete == self.pos:
                self.esta_desalojando_area = False
                self.esta_formandose = True 
                self.esta_esperando = False
                self.ir_a_formacion()
                #self.esta_esperando = True #aqui tambien irse a formar

            #ofertando despacho de pedido
            if self.esta_ofertando_pedido == True: 
                self.despachar_pedido()
                self.esta_ofertando_pedido = False
                if self.esta_despachando_pedido == False and self.destino_paquete != None and self.esta_formado == False and self.esta_formandose == False:
                    self.esta_formandose = True 
                    self.esta_esperando = False
                    self.ir_a_formacion()
                    #print(f'{self.unique_id} yendo a formarse')
                    #self.esta_esperando = True
            
            #En caso de que en el step anterior si haya habido un paquete en la banda, el robot define si ganó la subasta para ir por el paquete 
            if self.esta_ofertando == True:
                self.recoger_paquete() 
                self.esta_ofertando = False
                if self.esta_recolectando == False:
                    self.comprobar_pedidos()   
                    self.esta_ofertando_pedido = True
                    #print(f'HOLA: {self.esta_ofertando} Adios: {self.esta_ofertando_pedido}')
                          
            #Este codigo se ejecuta siempre que el robot no esta ocupado, de manera que comprueba si no hay un paquete en la banda 
            if self.esta_esperando == True:
                self.comprobar_paquetes()
                self.esta_ofertando = True

            #Se esta yendo a formar a la lista de espera
            if self.esta_formandose == True and self.destino_paquete != self.pos:
                self.ir_por_paquete() 

            if self.esta_formandose == True and self.destino_paquete == self.pos:
                self.esta_formandose = False
                self.esta_esperando = True
                self.deseleccionar_sitio()  
                self.esta_formado = True

            #Cuando un robot gana la subasta para recoger un paquete, se dirige hacia la traima de llegada
            if self.esta_recolectando == True and self.pos != self.destino_paquete:
                self.esta_esperando = False
                self.ir_por_paquete()

            #Una vez que el robot llega a la tarima de salida, entra en modo de almacenamiento, por lo que buscará la estantería correspondiente al articulo
            if self.esta_recolectando == True and self.pos == self.destino_paquete:
                self.esta_recolectando = False
                self.esta_almacenando = True
                self.tomar_paquete()
            
            #Robot yendo a la estanteria correspondiente y depositandolo cuando llega 
            if self.esta_almacenando == True and self.pos != self.destino_paquete:
                self.ir_por_paquete()
            
            if self.esta_almacenando == True and self.pos == self.destino_paquete:
                self.almacenar_paquete()
                self.desalojar_area()

            #Recoger un paquete a la estantería donde se encuentra
            if self.esta_despachando_pedido == True and self.pos != self.destino_paquete:
                self.esta_esperando = False
                self.ir_por_paquete()
            
            #LLega a estanteria y toma el paquete
            if self.esta_despachando_pedido == True and self.pos == self.destino_paquete:
                self.esta_despachando_pedido = False
                self.esta_entregando_pedido = True
                self.tomar_pedido()
            
            #Ya que recoge un pedido de la estanteria, lo va a dejar a la banda
            if self.esta_entregando_pedido == True and self.pos != self.destino_paquete:
                self.ir_por_paquete()
            
            if self.esta_entregando_pedido == True and self.pos == self.destino_paquete:
                self.entregar_pedido() 
                self.desalojar_area()

        else: 
            self.carga_optima = False
            if self.destination == (0,0):
                print("BATTERY RUNNING OUT!")
                self.buscar_cargador(self.pos)
            elif self.destination != (0,0) and self.pos != self.destination: 
                self.ir_a_cargador()
            else:
                self.esta_cargando = True
                self.cargar_bateria()
                self.recarga += 1

    def advance(self):
        # En caso de querer meter una negociación con otros agentes, se debería de colocar aqui
        if self.esta_esperando == False:
            if self.pos != self.sig_pos:
                self.movimientos += 1

        if self.carga > 0:
            if self.esta_cargando == False and self.esta_esperando == False:
                self.carga -= 0.5
                self.model.grid.move_agent(self, self.sig_pos)


class Habitacion(Model):
    def __init__(self, M: int, N: int,
                 num_agentes: int = 5,
                 porc_celdas_sucias: float = 0.6,
                 porc_muebles: float = 0.1,
                 modo_pos_inicial: str = 'Fija',
                 time: int = 0,
                 num_cuadrantesX: int = 2, 
                 num_cuadrantesY: int = 2
                 ):

        self.num_agentes = num_agentes
        self.porc_celdas_sucias = porc_celdas_sucias
        self.porc_muebles = porc_muebles
        self.num_cuadrantesX = num_cuadrantesX
        self.num_cuadrantesY = num_cuadrantesY
        self.time = time
        self.paquetes_en_almacen = []

        self.grid = MultiGrid(M, N, False) #multigrid permite que haya varios agentes en la misma celda 
        self.schedule = SimultaneousActivation(self)

        posiciones_disponibles = [pos for _, pos in self.grid.coord_iter()]

        # Posicionamiento de estanterias
        ubicacion_estanterias_x = {8, 16, 35, 43}
        ubicacion_estanterias_y = {10, 20, 30, 40}
        tipo_estanteria = 0
        for pos_x in ubicacion_estanterias_x:
            for pos_y in ubicacion_estanterias_y:
                estanteria = Estanteria(f"Estanteria_{pos_x}_{pos_y}", self)
                estanteria.tipo_estanteria = tipo_estanteria
                tipo_estanteria += 1
                self.schedule.add(estanteria)
                self.grid.place_agent(estanteria, (pos_x, pos_y))
                posiciones_disponibles.remove((pos_x, pos_y))

        # Posicionamiento de celdas 
        for id, pos in enumerate(posiciones_disponibles):
            celda = Celda(int(f"{num_agentes}{id}") + 1, self, False)
            self.grid.place_agent(celda, pos)
            self.schedule.add(celda)

        #Posicionamiento de tarima de llegada 
        tarima_llegada = Llegada("Llegada", self)
        self.grid.place_agent(tarima_llegada, (44, 48))
        self.schedule.add(tarima_llegada)

        #Posicionamiento de la tarima de salida
        tarima_salida = Salida("Salida", self)
        self.grid.place_agent(tarima_salida, (5, 48) )
        self.schedule.add(tarima_salida)

        # Posicionamiento de agentes robot
        if modo_pos_inicial == 'Aleatoria':
            pos_inicial_robots = self.random.sample(posiciones_disponibles, k=num_agentes)
            for id in range(num_agentes):
                robot = RobotLimpieza(id, self)
                self.grid.place_agent(robot, pos_inicial_robots[id])
                self.schedule.add(robot)

        #posicionamiento de sitios de espera
        sitio_x_derecho = 48
        sitio_x_izquierdo = 1
        sitio_y_inicial = 44
        for id in range(10):
            sitio_espera = Sitio_espera(f'sitio_espera{id}', self)
            #sitio_x_inicial -= 1
            if id < 5: 
                self.grid.place_agent(sitio_espera, (sitio_x_derecho, sitio_y_inicial))
                self.schedule.add(sitio_espera)
                sitio_y_inicial -= 1

            if id == 5:
                sitio_y_inicial = 44

            if id >= 5: 
                self.grid.place_agent(sitio_espera, (sitio_x_izquierdo, sitio_y_inicial))
                self.schedule.add(sitio_espera)
                sitio_y_inicial -= 1                

        else:  # 'Fija'
            posicion_inicial = 49
            cambio_en_posicion = 1
            for id in range(num_agentes):
                robot = RobotLimpieza(id, self)
                self.grid.place_agent(robot, (posicion_inicial, 46))
                posicion_inicial = posicion_inicial - cambio_en_posicion
                if posicion_inicial == 44:
                    posicion_inicial = 0
                    cambio_en_posicion = -1
                self.schedule.add(robot)

        self.datacollector = DataCollector(
            model_reporters={"Grid": get_grid, "Cargas": get_cargas},
        )

        #Posicionamiento de cargadores
        ubicaciones_cargadores_x = {23, 24, 25, 26, 27, 28}
        for pos in ubicaciones_cargadores_x:
            pos_x, pos_y = Cargador.pos_cargador(pos, 49) #eliminar para que no haga llamadas innecesarias xd
            cargador = Cargador(f"{pos_x}", self)
            self.schedule.add(cargador)
            self.grid.place_agent(cargador, (pos_x, pos_y))


    def step(self):
        self.running = True
        self.datacollector.collect(self)
        self.schedule.step()
        self.time += 1

    def todoLimpio(self):
        for (content, pos) in self.grid.coord_iter():
            for obj in content:
                if isinstance(obj, Celda) and obj.sucia:
                    return False
        return True


def get_grid(model: Model) -> np.ndarray:
    """
    Método para la obtención de la grid y representarla en un notebook
    :param model: Modelo (entorno)
    :return: grid
    """
    grid = np.zeros((model.grid.width, model.grid.height))
    for cell in model.grid.coord_iter():
        cell_content, pos = cell
        x, y = pos
        for obj in cell_content:
            if isinstance(obj, RobotLimpieza):
                grid[x][y] = 2
            elif isinstance(obj, Celda):
                grid[x][y] = int(obj.sucia)
    return grid

def get_cargas(model: Model):
    return [(agent.unique_id, agent.carga) for agent in model.schedule.agents if isinstance(agent, RobotLimpieza)]

def get_movimientos(agent: Agent) -> dict:
    if isinstance(agent, RobotLimpieza):
        return {agent.unique_id: agent.movimientos}
    # else:
    #    return 0
