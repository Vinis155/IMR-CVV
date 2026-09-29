import math


def calcular_orientacao_alvo(x, y, theta, x_alvo, y_alvo, Kp=1.5):
    theta_alvo = math.atan2(y_alvo - y, x_alvo - x)
    e_theta = math.atan2(
        math.sin(theta_alvo - theta),
        math.cos(theta_alvo - theta),
    )
    omega = Kp * e_theta
    return omega