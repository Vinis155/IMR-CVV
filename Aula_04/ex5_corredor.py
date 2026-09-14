import math
import random
import sys

import pygame

# ------------------------------------------------------------------
# Configurações gerais
# ------------------------------------------------------------------
LARGURA, ALTURA = 900, 600
FPS = 60

# Paredes do corredor (linhas horizontais infinitas em X)
PAREDE_TOPO = 150      # y da parede de cima
PAREDE_BASE = 450      # y da parede de baixo
CENTRO_Y = (PAREDE_TOPO + PAREDE_BASE) / 2.0

# Parâmetros do robô / controlador
V_LINEAR = 40.0        # px/s, velocidade linear constante
KP = 0.01              # ganho proporcional
RAIO_ROBO = 10
ALCANCE_SENSOR_MAX = 1000.0

# Cores
COR_FUNDO = (20, 22, 30)
COR_PAREDE = (230, 230, 230)
COR_ROBO = (80, 200, 255)
COR_SENSOR_ESQ = (255, 120, 120)
COR_SENSOR_DIR = (120, 255, 150)
COR_TEXTO = (240, 240, 240)
COR_MARCACAO = (60, 63, 75)


def direcao(angulo_graus):
    """Retorna o vetor unitário (dx, dy) para um ângulo em graus,
    usando a convenção dy = -sin(a) descrita no cabeçalho do arquivo."""
    rad = math.radians(angulo_graus)
    return math.cos(rad), -math.sin(rad)


def distancia_parede(pos, angulo_graus):
    """Lança um raio a partir de 'pos' na direção 'angulo_graus' e
    retorna a distância até a parede (topo ou base) que ele atinge.

    Como as paredes são linhas horizontais infinitas em X, basta
    testar a interseção do raio com y = PAREDE_TOPO e y = PAREDE_BASE
    e ficar com a interseção positiva (na frente do robô)."""
    px, py = pos
    dx, dy = direcao(angulo_graus)

    candidatos = []
    if abs(dy) > 1e-6:
        t_topo = (PAREDE_TOPO - py) / dy
        if t_topo > 0:
            candidatos.append(t_topo)

        t_base = (PAREDE_BASE - py) / dy
        if t_base > 0:
            candidatos.append(t_base)

    if not candidatos:
        # Raio praticamente paralelo às paredes (não deveria ocorrer
        # em operação normal, já que os sensores são perpendiculares
        # à direção de movimento do robô)
        return ALCANCE_SENSOR_MAX

    return min(candidatos)


def ponto_final(pos, angulo_graus, distancia):
    """Calcula o ponto onde um raio termina, para fins de desenho."""
    dx, dy = direcao(angulo_graus)
    return pos[0] + dx * distancia, pos[1] + dy * distancia


def reposicionar_robo():
    """Sorteia uma posição vertical (possivelmente desalinhada) dentro
    do corredor, deixando uma margem de segurança das paredes."""
    margem = 30
    y = random.uniform(PAREDE_TOPO + margem, PAREDE_BASE - margem)
    return y


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Exercício 5 - Centralização em Corredor (Controle P)")
    relogio = pygame.time.Clock()
    fonte = pygame.font.SysFont("consolas", 18)

    # Estado do robô: posição no "mundo" (x cresce indefinidamente ao
    # longo do corredor) e orientação theta em graus.
    robo_x = 0.0
    robo_y = reposicionar_robo()
    theta = 0.0  # 0° = robô apontando para a direita (sentido do corredor)

    rodando = True
    while rodando:
        dt = relogio.tick(FPS) / 1000.0  # delta-tempo em segundos

        # ---------------- Eventos ----------------
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif evento.key == pygame.K_r:
                    robo_y = reposicionar_robo()
                    theta = random.uniform(-20, 20)  # também desalinha a orientação

        # ---------------- Sensores ----------------
        # Feixes laterais fixos em relação ao robô: -90° e +90°
        angulo_esq = theta + 90.0
        angulo_dir = theta - 90.0

        d_esq = distancia_parede((robo_x, robo_y), angulo_esq)
        d_dir = distancia_parede((robo_x, robo_y), angulo_dir)

        # ---------------- Lei de controle (Proporcional) ----------------
        erro = d_esq - d_dir           # e = d_esq - d_dir
        omega = KP * erro              # ω = Kp * e   (graus/s)

        # ---------------- Atualização do estado (cinemática) ----------------
        theta += omega * dt
        dx, dy = direcao(theta)
        robo_x += V_LINEAR * dt * dx
        robo_y += V_LINEAR * dt * dy

        # Segurança pedagógica: impede que o robô "atravesse" a parede
        # por conta de algum desalinhamento inicial extremo
        robo_y = max(PAREDE_TOPO + 2, min(PAREDE_BASE - 2, robo_y))

        # ---------------- Câmera (segue o robô no eixo X) ----------------
        camera_x = robo_x - LARGURA / 2.0
        robo_tela_x = LARGURA / 2.0
        robo_tela_y = robo_y

        # ---------------- Desenho ----------------
        tela.fill(COR_FUNDO)

        # Marcações verticais no corredor, para dar noção de deslocamento
        espaco_marcacao = 100
        inicio = -(camera_x % espaco_marcacao)
        x_marc = inicio
        while x_marc < LARGURA:
            pygame.draw.line(tela, COR_MARCACAO, (x_marc, PAREDE_TOPO), (x_marc, PAREDE_BASE), 1)
            x_marc += espaco_marcacao

        # Paredes
        pygame.draw.line(tela, COR_PAREDE, (0, PAREDE_TOPO), (LARGURA, PAREDE_TOPO), 4)
        pygame.draw.line(tela, COR_PAREDE, (0, PAREDE_BASE), (LARGURA, PAREDE_BASE), 4)
        pygame.draw.line(tela, (90, 90, 90), (0, int(CENTRO_Y)), (LARGURA, int(CENTRO_Y)), 1)

        # Raios dos sensores (na tela, a partir da posição do robô)
        fim_esq = ponto_final((robo_tela_x, robo_tela_y), angulo_esq, d_esq)
        fim_dir = ponto_final((robo_tela_x, robo_tela_y), angulo_dir, d_dir)
        pygame.draw.line(tela, COR_SENSOR_ESQ, (robo_tela_x, robo_tela_y), fim_esq, 2)
        pygame.draw.line(tela, COR_SENSOR_DIR, (robo_tela_x, robo_tela_y), fim_dir, 2)

        # Robô (círculo + linha indicando orientação)
        pygame.draw.circle(tela, COR_ROBO, (int(robo_tela_x), int(robo_tela_y)), RAIO_ROBO)
        ponta_x, ponta_y = ponto_final((robo_tela_x, robo_tela_y), theta, RAIO_ROBO * 2)
        pygame.draw.line(tela, (255, 255, 255), (robo_tela_x, robo_tela_y), (ponta_x, ponta_y), 3)

        # ---------------- HUD (dados de telemetria) ----------------
        linhas = [
            f"d_esq = {d_esq:6.1f} px    d_dir = {d_dir:6.1f} px",
            f"erro (e) = d_esq - d_dir = {erro:6.1f}",
            f"omega = Kp * e = {omega:6.3f} graus/s",
            f"theta = {theta:6.2f} graus     v = {V_LINEAR:.1f} px/s",
            "[R] reposiciona o robô desalinhado   [ESC] sair",
        ]
        for i, linha in enumerate(linhas):
            texto_render = fonte.render(linha, True, COR_TEXTO)
            tela.blit(texto_render, (12, 10 + i * 22))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()