"""
Serviço de Validação de Localização

Implementa a Fórmula de Haversine para calcular a distância entre dois pontos GPS
e validar se o usuário está dentro do raio permitido do ponto de coleta.
"""

import math


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância em metros entre dois pontos usando a Fórmula de Haversine.
    
    Args:
        lat1: Latitude do primeiro ponto (em graus decimais)
        lon1: Longitude do primeiro ponto (em graus decimais)
        lat2: Latitude do segundo ponto (em graus decimais)
        lon2: Longitude do segundo ponto (em graus decimais)
    
    Returns:
        Distância em metros
    """
    # Raio da Terra em metros
    RAIO_TERRA = 6371000  # 6.371 km em metros
    
    # Converter graus para radianos
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferenças
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    # Distância em metros
    distancia = RAIO_TERRA * c
    
    return distancia


def validar_localizacao(user_lat: float, user_long: float, ponto_lat: float, ponto_long: float, raio_permitido: float = 1000.0) -> bool:
    """
    Verifica se o usuário está dentro do raio permitido do ponto de coleta.
    
    RF010 + RN005: Validação de GPS (Geofencing)
    - Calcula a distância usando Haversine
    - Retorna True se distância <= raio_permitido (padrão: 1km)
    
    Args:
        user_lat: Latitude do usuário
        user_long: Longitude do usuário
        ponto_lat: Latitude do ponto de coleta
        ponto_long: Longitude do ponto de coleta
        raio_permitido: Raio permitido em metros (padrão: 1000m = 1km)
    
    Returns:
        True se o usuário está dentro do raio, False caso contrário
    """
    distancia = calcular_distancia_haversine(user_lat, user_long, ponto_lat, ponto_long)
    return distancia <= raio_permitido