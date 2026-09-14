"""Veiculo Braitenberg com comportamento de atracao a obstaculos."""

import math
import sys

import numpy as np
import pygame


WIDTH, HEIGHT = 1000, 700
MAX_DISTANCE = 600.0
V0 = 45.0
ALPHA = 100.0
WHEEL_BASE = 58.0
SENSOR_ANGLE = math.radians(12.0)
SENSOR_OFFSET = 20.0

BACKGROUND = (18, 24, 32)
OBSTACLE_COLOR = (220, 95, 80)
ROBOT_COLOR = (75, 180, 235)
SENSOR_COLOR = (255, 205, 80)
TEXT_COLOR = (235, 240, 245)

OBSTACLE = pygame.Rect(650, 365, 210, 110)


class Robot:
    """Robo com duas rodas e um sensor associado a cada roda."""

    def __init__(self) -> None:
        self.position = np.array([210.0, 350.0])
        self.heading = 0.0
        self.wheel_speeds = (V0, V0)
        self.sensor_distances = (MAX_DISTANCE, MAX_DISTANCE)

    def sensor_position(self, side: float) -> np.ndarray:
        """Retorna a posicao do sensor esquerdo (-1) ou direito (+1)."""
        side_vector = np.array([-math.sin(self.heading), math.cos(self.heading)])
        return self.position + side_vector * side * SENSOR_OFFSET

    def read_sensor(self, side: float) -> float:
        """Mede a distancia ate o obstaculo ao longo do raio do sensor."""
        origin = self.sensor_position(side)
        angle = self.heading + side * SENSOR_ANGLE
        direction = np.array([math.cos(angle), math.sin(angle)])

        for distance in np.arange(0.0, MAX_DISTANCE, 2.0):
            point = origin + direction * distance
            if OBSTACLE.collidepoint(float(point[0]), float(point[1])):
                return float(distance)
        return MAX_DISTANCE

    def update(self, delta_time: float) -> None:
        """Le os sensores, calcula as rodas e atualiza a pose do robo."""
        left_distance = self.read_sensor(-1.0)
        right_distance = self.read_sensor(1.0)
        self.sensor_distances = (left_distance, right_distance)

        # Cada sensor esta conectado diretamente a sua roda.
        left_speed = V0 + ALPHA * (1.0 - left_distance / MAX_DISTANCE)
        right_speed = V0 + ALPHA * (1.0 - right_distance / MAX_DISTANCE)
        self.wheel_speeds = (left_speed, right_speed)

        linear_speed = (left_speed + right_speed) / 2.0
        angular_speed = (right_speed - left_speed) / WHEEL_BASE
        self.heading += angular_speed * delta_time
        self.position += np.array(
            [math.cos(self.heading), math.sin(self.heading)]
        ) * linear_speed * delta_time

        self.position[0] = np.clip(self.position[0], 25.0, WIDTH - 25.0)
        self.position[1] = np.clip(self.position[1], 25.0, HEIGHT - 25.0)

    def draw(self, screen: pygame.Surface) -> None:
        """Desenha o robo, as rodas, sensores e seus raios."""
        forward = np.array([math.cos(self.heading), math.sin(self.heading)])
        side_vector = np.array([-math.sin(self.heading), math.cos(self.heading)])
        nose = self.position + forward * 24.0
        left_wheel = self.position - side_vector * 17.0
        right_wheel = self.position + side_vector * 17.0

        pygame.draw.circle(
            screen, ROBOT_COLOR, (int(self.position[0]), int(self.position[1])), 25
        )
        pygame.draw.polygon(
            screen,
            TEXT_COLOR,
            [
                (int(nose[0]), int(nose[1])),
                (int((self.position - side_vector * 16)[0]), int((self.position - side_vector * 16)[1])),
                (int((self.position + side_vector * 16)[0]), int((self.position + side_vector * 16)[1])),
            ],
        )
        for wheel in (left_wheel, right_wheel):
            pygame.draw.circle(screen, (35, 40, 48), (int(wheel[0]), int(wheel[1])), 7)

        for side, distance in zip((-1.0, 1.0), self.sensor_distances):
            origin = self.sensor_position(side)
            angle = self.heading + side * SENSOR_ANGLE
            endpoint = origin + np.array([math.cos(angle), math.sin(angle)]) * distance
            pygame.draw.line(
                screen,
                SENSOR_COLOR,
                (int(origin[0]), int(origin[1])),
                (int(endpoint[0]), int(endpoint[1])),
                2,
            )
            pygame.draw.circle(screen, SENSOR_COLOR, (int(origin[0]), int(origin[1])), 4)


def draw_panel(screen: pygame.Surface, font: pygame.font.Font, robot: Robot) -> None:
    left_distance, right_distance = robot.sensor_distances
    left_speed, right_speed = robot.wheel_speeds
    lines = [
        "Braitenberg: comportamento de atracao/agressao",
        f"Sensor esquerdo: {left_distance:6.1f} px   |   Roda esquerda: {left_speed:6.1f} px/s",
        f"Sensor direito:  {right_distance:6.1f} px   |   Roda direita:  {right_speed:6.1f} px/s",
        "ESC para sair",
    ]
    for index, line in enumerate(lines):
        screen.blit(font.render(line, True, TEXT_COLOR), (30, 25 + index * 26))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Lab 4 - Veiculo Braitenberg")
    font = pygame.font.Font(None, 25)
    clock = pygame.time.Clock()
    robot = Robot()
    running = True

    while running:
        delta_time = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        robot.update(delta_time)
        screen.fill(BACKGROUND)
        pygame.draw.rect(screen, OBSTACLE_COLOR, OBSTACLE)
        robot.draw(screen)
        draw_panel(screen, font, robot)
        pygame.display.flip()

        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
