import pygame
import math
import numpy as np
from enum import Enum

# Constantes de Configuração
LARGURA_TELA = 800
ALTURA_TELA = 600
FPS = 60
COR_FUNDO = (30, 30, 30)
COR_ROBO = (0, 180, 255)
COR_DIRECAO = (255, 50, 50)
COR_TRAJETORIA = (100, 200, 100)

# Definindo os estados da máquina de estados
class RobotState(Enum):
    MOVE_FORWARD = 1
    ROTATE = 2
    FINISHED = 3

class DiffDriveRobot:
    def __init__(self, x, y, theta=0.0, wheelbase=30.0, radius=15.0):
        # Estado do robô: [x, y, theta]
        self.x = float(x)
        self.y = float(y)
        self.theta = float(theta)  # em radianos
        
        # Parâmetros físicos (em pixels)
        self.L = float(wheelbase)  
        self.radius = float(radius)
        
        # Entradas de controle
        self.v = 0.0      
        self.omega = 0.0  
        
        # Histórico de posições para plotar rastro
        self.history = []

    def set_wheel_velocities(self, v_left, v_right):
       
        self.v = (v_right + v_left) / 2.0
        self.omega = (v_right - v_left) / self.L

    def set_direct_velocity(self, v, omega):
        
        self.v = v
        self.omega = omega

    def update(self, dt):
        
        self.theta += self.omega * dt
        
        self.theta = (self.theta + math.pi) % (2 * math.pi) - math.pi
        
        # Atualização de posição cartesiana
        self.x += self.v * math.cos(self.theta) * dt
        self.y += self.v * math.sin(self.theta) * dt
        
        # Guarda histórico para desenhar o rastro
        if len(self.history) == 0 or np.hypot(self.x - self.history[-1][0], self.y - self.history[-1][1]) > 5:
            self.history.append((self.x, self.y))
            if len(self.history) > 500:
                self.history.pop(0)

    def draw(self, surface):
        # 1. Desenha o rastro
        if len(self.history) > 1:
            pygame.draw.lines(surface, COR_TRAJETORIA, False, self.history, 2)
            
        # 2. Desenha o corpo do robô
        pos_int = (int(self.x), int(self.y))
        pygame.draw.circle(surface, COR_ROBO, pos_int, int(self.radius))
        
        # 3. Desenha a linha indicadora da direção (orientação theta)
        linha_frente_x = self.x + (self.radius + 10) * math.cos(self.theta)
        linha_frente_y = self.y + (self.radius + 10) * math.sin(self.theta)
        pygame.draw.line(surface, COR_DIRECAO, pos_int, (int(linha_frente_x), int(linha_frente_y)), 3)

def main():
    pygame.init()
    screen = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.display.set_caption("Aula 01: Fundamentos de Robótica Móvel")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 14)

    robot = DiffDriveRobot(x=LARGURA_TELA // 4, y=ALTURA_TELA // 2, theta=0.0) 

    # Variáveis da Máquina de Estados
    current_state = RobotState.MOVE_FORWARD
    state_timer = 0.0
    side_count = 0
    
    # Parâmetros de movimento
    linear_speed = 100.0 
    angular_speed = math.pi / 2.0 
    
    move_time = 2.0 
    turn_time = 1.0 

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        v_cmd = 0.0
        omega_cmd = 0.0
        
        # Lógica da Máquina de Estados
        if current_state == RobotState.MOVE_FORWARD:
            v_cmd = linear_speed
            omega_cmd = 0.0
            state_timer += dt
            if state_timer >= move_time:
                current_state = RobotState.ROTATE
                state_timer = 0.0
                side_count += 1
        elif current_state == RobotState.ROTATE:
            v_cmd = 0.0
            omega_cmd = angular_speed 
            state_timer += dt
            if state_timer >= turn_time:
                if side_count < 4: 
                    current_state = RobotState.MOVE_FORWARD
                    state_timer = 0.0
                else:
                    current_state = RobotState.FINISHED
                    robot.set_direct_velocity(0.0, 0.0) 

        if current_state == RobotState.FINISHED:
            v_cmd = 0.0
            omega_cmd = 0.0
            


        # Aplica comando de velocidade e atualiza física
        robot.set_direct_velocity(v_cmd, omega_cmd)
        robot.update(dt)

        # Renderização
        screen.fill(COR_FUNDO)
        robot.draw(screen)

        # Painel de Telemetria
        info_txt = [
            f"Estado: {current_state.name}",
            f"Lado {side_count}/4",
            f"Timer: {state_timer:.2f} s",
            f"Pose X: {robot.x:.1f} px | Y: {robot.y:.1f} px | Theta: {math.degrees(robot.theta):.1f} deg",
            f"Comandos: v = {robot.v:.1f} px/s | omega = {robot.omega:.2f} rad/s"
        ]
        for i, txt in enumerate(info_txt):
            rendered = font.render(txt, True, (220, 220, 220))
            screen.blit(rendered, (15, 15 + i * 20))

        pygame.display.flip()
        
    pygame.quit()

if __name__ == "__main__":
    main()