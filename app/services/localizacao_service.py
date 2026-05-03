# Este arquivo contém a lógica para verificar a proximidade do usuário ao ponto de coleta.

def validar_localizacao(user_lat: float, user_long: float, ponto_lat: float, ponto_long: float) -> bool:
    """
    Verifica se o usuário está próximo o suficiente do ponto de coleta para descartar.
    Cálculo simples de distância euclidiana para o MVP.
    """
    # Cálculo da distância entre dois pontos (fórmula simplificada)
    distancia = ((user_lat - ponto_lat)**2 + (user_long - ponto_long)**2)**0.5
    
    # Limite de 0.01 graus (aproximadamente 1km dependendo da região)
    LIMITE_DISTANCIA = 0.01
    
    return distancia <= LIMITE_DISTANCIA