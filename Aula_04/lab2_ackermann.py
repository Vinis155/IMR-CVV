import math
import pygame

LARGURA = 900
ALTURA = 700
ESCALA = 80
L = 2.0
PHI_MAX = math.radians(30)


class SimulacaoAckermann:
    def __init__(self):
        # Velocidade linear do veículo (m/s)
        # Defina aqui o valor inicial: v = 2.0 m/s
        self.v = 2.0

        # Ângulo de esterço das rodas dianteiras (rad)
        # Valor inicial igual ao limite máximo do enunciado: 30°
        self.phi = math.radians(30)

        self.pose = (0.0, 0.0, 0.0)
        self.rastro = []
        self.rodando = True

    def atualizar_pose(self, dt):
        x, y, theta = self.pose
        omega = (self.v / L) * math.tan(self.phi)

        # Modelo Ackermann: o veículo avança como um carro com curva de raio R = L / tan(phi)
        x += self.v * math.cos(theta) * dt
        y += self.v * math.sin(theta) * dt
        theta += omega * dt

        self.pose = (x, y, theta)
        self.rastro.append((x, y))

        if len(self.rastro) > 2000:
            self.rastro.pop(0)

    def desenhar_robo(self, tela):
        x, y, theta = self.pose
        centro = (
            int(LARGURA / 2 + x * ESCALA),
            int(ALTURA / 2 - y * ESCALA),
        )
        frente = (
            int(centro[0] + 24 * math.cos(theta)),
            int(centro[1] - 24 * math.sin(theta)),
        )
        pygame.draw.circle(tela, (40, 90, 200), centro, 16)
        pygame.draw.line(tela, (220, 40, 40), centro, frente, 4)

    def desenhar_trajetoria(self, tela):
        if len(self.rastro) > 1:
            pontos = [
                (
                    int(LARGURA / 2 + x * ESCALA),
                    int(ALTURA / 2 - y * ESCALA),
                )
                for x, y in self.rastro
            ]
            pygame.draw.lines(tela, (120, 120, 120), False, pontos, 2)

    def desenhar_info(self, tela, fonte):
        omega = (self.v / L) * math.tan(self.phi)
        raio = L / math.tan(self.phi) if abs(self.phi) > 1e-6 else float("inf")

        texto_v = fonte.render(f"v = {self.v:.2f} m/s", True, (30, 30, 30))
        texto_phi = fonte.render(f"phi = {math.degrees(self.phi):.1f} deg", True, (30, 30, 30))
        texto_omega = fonte.render(f"omega = {omega:.4f} rad/s", True, (30, 30, 30))
        texto_raio = fonte.render(f"R = {raio:.2f} m" if math.isfinite(raio) else "R = infinito", True, (30, 30, 30))

        tela.blit(texto_v, (20, 20))
        tela.blit(texto_phi, (20, 50))
        tela.blit(texto_omega, (20, 80))
        tela.blit(texto_raio, (20, 110))

    def processar_teclas(self):
        teclas = pygame.key.get_pressed()

        # Teclas do teclado:
        #   ↑ / ↓ definem a velocidade linear v
        #   ← / → definem o ângulo de esterço phi
        if teclas[pygame.K_UP]:
            self.v = min(self.v + 0.25, 8.0)
        if teclas[pygame.K_DOWN]:
            self.v = max(self.v - 0.25, 0.0)
        if teclas[pygame.K_LEFT]:
            self.phi = max(self.phi - math.radians(3), -PHI_MAX)
        if teclas[pygame.K_RIGHT]:
            self.phi = min(self.phi + math.radians(3), PHI_MAX)
        if teclas[pygame.K_r]:
            # Reset para valores iniciais
            self.v = 2.0
            self.phi = math.radians(30)
            self.pose = (0.0, 0.0, 0.0)
            self.rastro = []

        self.phi = max(min(self.phi, PHI_MAX), -PHI_MAX)


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Ackermann vs Diferencial")
    relogio = pygame.time.Clock()
    fonte = pygame.font.SysFont(None, 26)

    simulacao = SimulacaoAckermann()

    while simulacao.rodando:
        dt = relogio.tick(60) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                simulacao.rodando = False

        simulacao.processar_teclas()
        simulacao.atualizar_pose(dt)

        tela.fill((245, 245, 245))
        pygame.draw.line(tela, (180, 180, 180), (0, ALTURA // 2), (LARGURA, ALTURA // 2), 1)
        pygame.draw.line(tela, (180, 180, 180), (LARGURA // 2, 0), (LARGURA // 2, ALTURA), 1)

        simulacao.desenhar_trajetoria(tela)
        simulacao.desenhar_robo(tela)
        simulacao.desenhar_info(tela, fonte)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
