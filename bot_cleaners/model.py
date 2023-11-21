from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

import numpy as np
import math

class Llegada(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.ocupada = False
        self.sensor_paquete = False #Define si llegó un tipo de paquete
        self.contiene = 0 #Tipo de paquete que llegó 
        self.recolector_id = None #Id del robot que esta más cerca del paquete que llegó y recogerá el paquete 
        self.min_dist_recolector = float('inf') #Variable que decidirá quien va por el paquete mediante un proceso de subasta por distancia 
        self.paquetes_por_llegar = [1, 2, 3, 4] #Arreglo que contendrá la cantidad y tipo de paquete que irá llegando x steps {tipo:step}
        self.horas_de_llegada = [10, 50, 100, 200]
        self.paso = 0

    def step(self):
        self.paso += 1

    def advance(self):
        if self.paso in self.horas_de_llegada:
            print('----Llamada de paquete entrante----')
            self.horas_de_llegada.remove(self.paso)  # Remover el paso actual de las horas de llegada
            self.contiene = self.paquetes_por_llegar.pop(0)  # Remover y obtener el primer paquete de la lista
            self.sensor_paquete = True
        

    def liberar_tarima(self):
        self.sensor_paquete = False
        self.contiene = None
        self.recolector_id = None
        self.min_dist_recolector = float('inf')


class Salida(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.ocupada = False
        self.sensor_paquete = False #Define si llegó un tipo de paquete
        self.pide = None #Tipo de paquete que llegó 

class Celda(Agent):
    def __init__(self, unique_id, model, suciedad: bool = False):
        super().__init__(unique_id, model)
        self.sucia = suciedad
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


class RobotLimpieza(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.ocupada = True
        self.sig_pos = None
        self.movimientos = 0
        self.carga = 100
        self.recarga = 0
        self.contiene = None
        self.destination = (0,0) #variable que almacenará el cargador al que se debe dirigir si su batería llega a un nivel crítico
        self.destino_paquete = None
        self.carga_optima = True 
        self.esta_cargando = False
        self.esta_esperando = True
        self.esta_recolectando = False 
        self.esta_almacenando = False
        self.esta_ofertando = False

    def limpiar_una_celda(self, lista_de_celdas_sucias):
        celda_a_limpiar = self.random.choice(lista_de_celdas_sucias)
        celda_a_limpiar.sucia = False
        self.sig_pos = celda_a_limpiar.pos

    def tomar_paquete(self):
        lista_tarima_llegada = [agent for agent in self.model.schedule.agents if isinstance(agent, Llegada)] #Arreglo de entrada para la lista de cargadores
        for tarima_llegada in lista_tarima_llegada:
            tipo_paquete = tarima_llegada.contiene
            self.contiene = tipo_paquete
            #funcion que define el detino_paquete a la posicion de la estanteria que corresponde
            self.destino_paquete = (5, 48)
            #libera la tarima
            tarima_llegada.liberar_tarima()

    def ir_a_estanteria(self):
        pass
    
    # cuando no tiene una celda sucia cerca se mueve de manera aleatoria (?)
    def seleccionar_nueva_pos(self, lista_de_vecinos):
        possible_pos = self.random.choice(lista_de_vecinos)
        while possible_pos.ocupada == True: # aqui nos aseguramos que al b|uscar una posición random no tome alguna ya ocupada
            possible_pos = self.random.choice(lista_de_vecinos)
        self.sig_pos = possible_pos.pos

    @staticmethod
    def buscar_celdas_sucia(lista_de_vecinos):
        celdas_sucias = list()
        for vecino in lista_de_vecinos:
            if isinstance(vecino, Celda) and vecino.sucia:
                celdas_sucias.append(vecino)
        return celdas_sucias
    
    @staticmethod
    def distancia_euclidiana(punto1, punto2):
        x1, y1 = punto1
        x2, y2 = punto2
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def comprobar_paquetes(self):
        #print(f'{self.unique_id} comprobando paquete...')
        lista_tarima_llegada = [agent for agent in self.model.schedule.agents if isinstance(agent, Llegada)] #Arreglo de entrada para la lista de cargadores
        for tarima_llegada in lista_tarima_llegada:
            #print('comprobando distancia')
            if tarima_llegada.sensor_paquete == True:
                distancia_a_llegada = self.distancia_euclidiana(self.pos, tarima_llegada.pos)
                if tarima_llegada.min_dist_recolector > distancia_a_llegada:
                    print(f'{self.unique_id} ofertando...')
                    tarima_llegada.min_dist_recolector = distancia_a_llegada
                    tarima_llegada.recolector_id = self.unique_id

    def recoger_paquete(self):
        lista_tarima_llegada = list()
        lista_tarima_llegada = [agent for agent in self.model.schedule.agents if isinstance(agent, Llegada)] #Arreglo de entrada para la lista de cargadores
        for tarima in lista_tarima_llegada:
            if tarima.recolector_id == self.unique_id:
                self.esta_recolectando = True
                self.esta_esperando = False
                self.destino_paquete = tarima.pos
                print(f'Robot {self.unique_id} escogido para recoger paquete')

    def ir_por_paquete(self):
        print(f'Robot {self.unique_id} yendo por paquete...')
        x_cargador, y_cargador = self.destino_paquete
        print(f"DESTINO: {self.destino_paquete}")

        # Dirigirse al cargador considerando al entorno
        vecinos = self.model.grid.get_neighbors(
                self.pos, moore=True, include_center=False)

        for vecino in vecinos:
            if isinstance(vecino, (Mueble, RobotLimpieza)):
                vecinos.remove(vecino)

        minDist = float('inf')
        for vecino in vecinos:
            dist = self.distancia_euclidiana(vecino.pos, self.destino_paquete)
            if dist < minDist:
                minDist = dist
                self.sig_pos = vecino.pos


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
        # cambiarlo a que dentro de sus vecinos escoja la celda desocupada más cercana al cargador y se dirija hacia alla
        print("YENDO A CARGAR...")
        x_cargador, y_cargador = self.destination
        print(f"DESTINO: {self.destination}")
        
        # Dirigirse al cargador considerando al entorno
        vecinos = self.model.grid.get_neighbors(
                self.pos, moore=True, include_center=False)

        for vecino in vecinos:
            if isinstance(vecino, (Mueble, RobotLimpieza)):
                vecinos.remove(vecino)
        celdas = list()
        minDist = float('inf')
        for vecino in vecinos:
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
        
            
    def step(self):
        if self.carga > 25 and self.carga_optima:
            self.esta_cargando = False

            #En caso de que en el step anterior si haya habido un paquete en la banda, el robot define si ganó la subasta para ir por el paquete 
            if self.esta_ofertando == True:
                self.recoger_paquete()
                self.esta_ofertando = False

            #Este codigo se ejecuta siempre que el robot no esta ocupado, de manera que comprueba si no hay un paquete en la banda 
            if self.esta_esperando == True:
                self.comprobar_paquetes()
                self.esta_ofertando = True

            #Cuando un robot gana la subasta para recoger un paquete, se dirige hacia la traima de llegada
            if self.esta_recolectando == True and self.pos != self.destino_paquete:
                self.esta_esperando = False
                self.ir_por_paquete()

            #Una vez que el robot llega a la tarima de salida, entra en modo de almacenamiento, por lo que buscará la estantería correspondiente al articulo
            if self.esta_recolectando == True and self.pos == self.destino_paquete:
                self.esta_recolectando = False
                self.esta_almacenando = True
                self.tomar_paquete()
            
            if self.esta_almacenando == True and self.pos != self.destino_paquete:
                self.ir_por_paquete()
            
            if self.esta_almacenando == True and self.pos == self.destino_paquete:
                self.esta_esperando = True


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
                print(f"Cantidad de recargas: {self.recarga}")


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

        self.grid = MultiGrid(M, N, False) #multigrid permite que haya varios agentes en la misma celda 
        self.schedule = SimultaneousActivation(self)

        posiciones_disponibles = [pos for _, pos in self.grid.coord_iter()]

        # Posicionamiento de muebles
        num_muebles = int(M * N * porc_muebles)
        #posiciones_muebles = self.random.sample(posiciones_disponibles, k=num_muebles)

        """for id, pos in enumerate(posiciones_muebles):
            mueble = Mueble(int(f"{num_agentes}0{id}") + 1, self)
            self.grid.place_agent(mueble, pos)
            posiciones_disponibles.remove(pos)"""

        
        # Posicionamiento de celdas sucias
        self.num_celdas_sucias = int(M * N * porc_celdas_sucias)

        for id, pos in enumerate(posiciones_disponibles):
            celda = Celda(int(f"{num_agentes}{id}") + 1, self, False)
            self.grid.place_agent(celda, pos)

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
