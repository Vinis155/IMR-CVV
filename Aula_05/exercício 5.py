import math


def maquina_de_estados(x, y, theta, x_alvo, y_alvo, dist_frente, dist_esq, dist_dir):
	distancia_alvo = math.sqrt((x_alvo - x) ** 2 + (y_alvo - y) ** 2)

	if distancia_alvo < 0.2:
		return "OBJETIVO_ALCANÇADO", 0.0, 0.0

	if dist_frente < 0.5:
		if dist_esq > dist_dir:
			return "DESVIAR_OBSTACULO", 0.0, 1.0
		return "DESVIAR_OBSTACULO", 0.0, -1.0

	theta_alvo = math.atan2(y_alvo - y, x_alvo - x)
	erro_orientacao = math.atan2(
		math.sin(theta_alvo - theta),
		math.cos(theta_alvo - theta),
	)
	omega_cmd = 1.5 * erro_orientacao
	return "IR_PARA_ALVO", 0.2, omega_cmd
