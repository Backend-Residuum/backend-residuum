# Este arquivo contém as regras de validação para os dados de entrada do sistema.

def validar_quantidade(quantidade: float) -> bool:
    """
    Valida se a quantidade informada pelo usuário é válida.
    Regras: 
    - Não pode ser zero.
    - Não pode ser negativa.
    - Definimos um limite 'absurdo' de 1000kg para o MVP.
    """
    if quantidade <= 0:
        return False
    
    if quantidade > 1000: # Exemplo de valor 'absurdo' para controle manual
        return False
        
    return True

def validar_residuo(tipo_residuo: str) -> bool:
    """
    Valida se o tipo de resíduo é aceito pelo sistema no estágio atual (MVP).
    Regra: Inicialmente apenas 'garrafa pet'.
    """
    # Usamos .lower() para garantir que 'Garrafa PET' ou 'garrafa pet' sejam aceitos
    residuo_formatado = tipo_residuo.strip().lower()
    return residuo_formatado == "garrafa pet"