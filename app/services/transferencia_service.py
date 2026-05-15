def transferir_residuo_para_ponto_coleta(tipo_residuo: str, quantidade: float) -> dict:
    return {
        "tipo_residuo": tipo_residuo,
        "quantidade_transferida": quantidade,
        "status": "transferencia_registrada"
    }

print(
    transferir_residuo_para_ponto_coleta("papel", 5)
)