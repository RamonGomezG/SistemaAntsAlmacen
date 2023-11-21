import random

import mesa

from .model import Habitacion, RobotLimpieza, Celda, Mueble, Cargador, Llegada, Salida, Estanteria

MAX_NUMBER_ROBOTS = 10


def agent_portrayal(agent):
    if isinstance(agent, RobotLimpieza):
        return {"Shape": "circle", "Filled": "false", "Color": "black", "Layer": 1, "r": 1,
                "text": f"{agent.carga}", "text_color": "yellow"}
    elif isinstance(agent, Mueble):
        return {"Shape": "rect", "Filled": "true", "Color": "white", "Layer": 0,
                "w": 0.9, "h": 0.9, "text_color": "Black", "text": "🪑"}
    elif isinstance(agent, Llegada):
        if agent.sensor_paquete == False:
            return {"Shape": "rect", "Filled": "true", "Color": "white", "Layer": 0,
                    "w": 0.4, "h": 0.4, "text_color": "Black", "text": "🔷"}
        else:
            return {"Shape": "rect", "Filled": "true", "Color": "white", "Layer": 0,
                  "w": 0.4, "h": 0.4, "text_color": "Black", "text": "📦"}
    elif isinstance(agent, Salida):
        if agent.sensor_paquete == False:
            return {"Shape": "rect", "Filled": "true", "Color": "white", "Layer": 0,
                    "w": 0.4, "h": 0.4, "text_color": "Black", "text": "🦠"}
        else:
            return {"Shape": "rect", "Filled": "true", "Color": "white", "Layer": 0,
                  "w": 0.4, "h": 0.4, "text_color": "Black", "text": "📦"}
    elif isinstance(agent, Cargador):
        return {"Shape": "rect", "Filled": "true", "Color": "white", "Layer": 0,
                "w": 0.5, "h": 0.5, "text_color": "Black", "text": "🔌"}
    elif isinstance(agent, Estanteria):
        return {"Shape": "rect", "Filled": "true", "Color": "yellow", "Layer": 0,
                "w": 1, "h": 1, "text_color": "Black", "text": "🗄️"}
    elif isinstance(agent, Celda):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 0.9, "h": 0.9, "text_color": "Black"}
        if agent.sucia:
            portrayal["Color"] = "white"
            portrayal["text"] = "🦠"
        else:
            portrayal["Color"] = "white"
            portrayal["text"] = ""
        return portrayal


grid = mesa.visualization.CanvasGrid(
    agent_portrayal, 50, 50, 400, 400)
"""
chart_celdas = mesa.visualization.ChartModule(
    [{"Label": "CeldasSucias", "Color": '#36A2EB', "label": "Celdas Sucias"}],
    50, 200,
    data_collector_name="datacollector"
)"""

model_params = {
    "num_agentes": mesa.visualization.Slider(
        "Número de Robots",
        5,
        2,
        MAX_NUMBER_ROBOTS,
        1,
        description="Escoge cuántos robots deseas implementar en el modelo",
    ),
    "porc_muebles": mesa.visualization.Slider(
        "Porcentaje de Muebles",
        0.1,
        0.0,
        0.25,
        0.01,
        description="Selecciona el porcentaje de muebles",
    ),
    "modo_pos_inicial": mesa.visualization.Choice(
        "Posición Inicial de los Robots",
        "Fija",
        ["Fija", "Aleatoria"],
        "Selecciona la forma se posicionan los robots"
    ),
    "M": 50,
    "N": 50,
}

server = mesa.visualization.ModularServer(
    Habitacion, [grid],
    "Ants Almacenistas", model_params, 8521
)
