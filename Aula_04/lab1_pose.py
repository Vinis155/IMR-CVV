import math
import pygame

LARGURA = 800
ALTURA = 600
ESCALA = 100

# (tempo, velocidade linear, velocidade angular)
trechos = [
    (4.0, 0.5, 0.0),
    (2.0, 0.0, 0.7854),
    (3.0, 0.4, 0.0),
]


def atualizar_pose(pose, velocidade, velocidade_angular, dt):
    x, y, theta = pose
    x += velocidade * math.cos(theta) * dt
    y += velocidade * math.sin(theta) * dt
    theta += velocidade_angular * dt
    return x, y, theta


def graus(angulo):
    return math.degrees(angulo)


def imprimir_pose(nome, pose):
    x, y, theta = pose
    print(f"{nome}: x={x:.4f} m, y={y:.4f} m, theta={theta:.4f} rad ({graus(theta):.2f} graus)")


def desenhar_robo(tela, pose):
    x, y, theta = pose
    centro = (int(LARGURA / 2 + x * ESCALA), int(ALTURA / 2 - y * ESCALA))
    frente = (
        int(centro[0] + 25 * math.cos(theta)),
        int(centro[1] - 25 * math.sin(theta)),
    )

    pygame.draw.circle(tela, (30, 120, 220), centro, 15)
    pygame.draw.line(tela, (220, 40, 40), centro, frente, 4)


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Validador de Pose")
    relogio = pygame.time.Clock()

    pose_teorica = (0.0, 0.0, 0.0)
    for tempo, velocidade, velocidade_angular in trechos:
        pose_teorica = atualizar_pose(
            pose_teorica, velocidade, velocidade_angular, tempo
        )

    pose_simulada = (0.0, 0.0, 0.0)
    rastro = []
    trecho_atual = 0
    tempo_no_trecho = 0.0
    executando = True

    while executando:
        dt = relogio.tick(60) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False

        if trecho_atual < len(trechos):
            duracao, velocidade, velocidade_angular = trechos[trecho_atual]
            passo = min(dt, duracao - tempo_no_trecho)
            pose_simulada = atualizar_pose(
                pose_simulada, velocidade, velocidade_angular, passo
            )
            tempo_no_trecho += passo

            if tempo_no_trecho >= duracao:
                trecho_atual += 1
                tempo_no_trecho = 0.0
        else:
            pose_simulada = pose_teorica

        rastro.append(pose_simulada[:2])
        if len(rastro) > 2000:
            rastro.pop(0)

        tela.fill((245, 245, 245))
        pygame.draw.line(tela, (180, 180, 180), (0, ALTURA // 2), (LARGURA, ALTURA // 2), 1)
        pygame.draw.line(tela, (180, 180, 180), (LARGURA // 2, 0), (LARGURA // 2, ALTURA), 1)

        if len(rastro) > 1:
            pontos_tela = [
                (
                    int(LARGURA / 2 + x * ESCALA),
                    int(ALTURA / 2 - y * ESCALA),
                )
                for x, y in rastro
            ]
            pygame.draw.lines(tela, (120, 120, 120), False, pontos_tela, 2)

        desenhar_robo(tela, pose_simulada)
        pygame.display.flip()

    pygame.quit()
    imprimir_pose("Pose final teorica", pose_teorica)
    imprimir_pose("Pose final simulada", pose_simulada)


if __name__ == "__main__":
    main()
