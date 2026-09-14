"""Simulacao de varredura de distancia com filtro de limiar."""

import math
import sys

import numpy as np
import pygame


WIDTH, HEIGHT = 1000, 700
MAX_DISTANCE = 200.0
MIN_DISTANCE = 10.0
SENSOR_POSITION = np.array([WIDTH / 2, HEIGHT / 2], dtype=float)
BEAM_ANGLES = np.linspace(-math.pi / 2, math.pi / 2, 7)

BACKGROUND = (18, 24, 32)
WALL_COLOR = (210, 214, 220)
SENSOR_COLOR = (255, 190, 70)
BEAM_COLOR = (70, 170, 220)
RAW_COLOR = (255, 125, 105)
FILTERED_COLOR = (110, 225, 150)
TEXT_COLOR = (235, 240, 245)

# Retangulos usados para produzir as distancias reais da cena.
OBSTACLES = [
    pygame.Rect(190, 165, 150, 28),
    pygame.Rect(645, 145, 175, 30),
    pygame.Rect(250, 460, 190, 32),
    pygame.Rect(565, 405, 130, 35),
]


def distance_to_obstacles(angle: float) -> float:
    """Retorna a distancia real ate o primeiro obstaculo, ou o alcance maximo."""
    direction = np.array([math.cos(angle), math.sin(angle)], dtype=float)
    distance = 0.0
    step = 1.0

    while distance <= MAX_DISTANCE:
        point = SENSOR_POSITION + direction * distance
        if any(obstacle.collidepoint(float(point[0]), float(point[1])) for obstacle in OBSTACLES):
            return distance
        distance += step

    return MAX_DISTANCE


def apply_threshold_filter(noisy_distance: float) -> float | None:
    """Descarta leituras abaixo do minimo e limita as acima do alcance."""
    if noisy_distance < MIN_DISTANCE:
        return None
    return min(noisy_distance, MAX_DISTANCE)


def draw_measurements(
    screen: pygame.Surface,
    font: pygame.font.Font,
    raw_distances: list[float],
    filtered_distances: list[float | None],
) -> None:
    """Desenha os raios e uma tabela com os valores bruto e filtrado."""
    sensor = (int(SENSOR_POSITION[0]), int(SENSOR_POSITION[1]))
    pygame.draw.circle(screen, SENSOR_COLOR, sensor, 8)

    for angle, raw_distance, filtered_distance in zip(
        BEAM_ANGLES, raw_distances, filtered_distances
    ):
        direction = np.array([math.cos(angle), math.sin(angle)])
        raw_endpoint = SENSOR_POSITION + direction * min(raw_distance, MAX_DISTANCE)
        pygame.draw.line(
            screen,
            BEAM_COLOR,
            sensor,
            (int(raw_endpoint[0]), int(raw_endpoint[1])),
            2,
        )

        if filtered_distance is not None:
            filtered_endpoint = SENSOR_POSITION + direction * filtered_distance
            pygame.draw.circle(
                screen,
                FILTERED_COLOR,
                (int(filtered_endpoint[0]), int(filtered_endpoint[1])),
                5,
            )

    table_x, table_y = 40, 55
    header = font.render("Feixe       Bruta (px)       Tratada (px)", True, TEXT_COLOR)
    screen.blit(header, (table_x, table_y))

    for index, (raw_distance, filtered_distance) in enumerate(
        zip(raw_distances, filtered_distances), start=1
    ):
        filtered_text = "DESCARTADA" if filtered_distance is None else f"{filtered_distance:7.2f}"
        row = font.render(
            f"{index:>2}          {raw_distance:7.2f}          {filtered_text}",
            True,
            RAW_COLOR if filtered_distance is None else FILTERED_COLOR,
        )
        screen.blit(row, (table_x, table_y + index * 25))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Lab 3 - Filtro de Limiar do Sensor")
    font = pygame.font.Font(None, 25)
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BACKGROUND)
        for obstacle in OBSTACLES:
            pygame.draw.rect(screen, WALL_COLOR, obstacle)

        real_distances = [distance_to_obstacles(angle) for angle in BEAM_ANGLES]
        raw_distances = [
            distance + np.random.normal(0, 5.0) for distance in real_distances
        ]
        filtered_distances = [
            apply_threshold_filter(distance) for distance in raw_distances
        ]
        draw_measurements(screen, font, raw_distances, filtered_distances)

        title = font.render(
            "Varredura: 7 feixes | Campo de visao: 180 graus | ESC para sair",
            True,
            TEXT_COLOR,
        )
        screen.blit(title, (40, HEIGHT - 45))
        pygame.display.flip()

        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            running = False
        clock.tick(10)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
