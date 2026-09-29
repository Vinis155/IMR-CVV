import numpy as np


def processar_scan(leituras_lidar):
	leituras = np.asarray(leituras_lidar, dtype=float)
	if leituras.size != 360:
		raise ValueError("O scan deve conter exatamente 360 leituras.")

	setores = {
		"frente": np.concatenate((leituras[345:360], leituras[0:16])),
		"esquerda": leituras[45:136],
		"direita": leituras[225:316],
	}

	resultado = {}
	for nome, distancias in setores.items():
		validas = distancias[(distancias >= 0.1) & (distancias <= 5.0)]
		resultado[nome] = float(np.min(validas)) if validas.size else None

	return resultado
