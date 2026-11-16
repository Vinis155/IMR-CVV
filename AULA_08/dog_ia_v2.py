import argparse
import heapq
import math
import os
import random
from array import array
from collections import deque

import pygame

LARGURA, ALTURA = 1050, 680
MAPA_L = LARGURA - 260
FPS = 60
DT = 1.0 / FPS

RUA_Y = 250
RUA_ALTURA = 170
FAIXA_X = 580
FAIXA_L = 95
GUIA = 42
VEL = 156.0
VEL_TUTOR = 140.0
CELULA = 10
COLS = MAPA_L // CELULA
LINHAS = ALTURA // CELULA

ALCANCE = 165
NUM_RAIOS = 19
FOV = math.radians(150)
RUIDO = 1.5
DROPOUT = 0.02

ACEL = 90.0
DESACEL = 160.0
VEL_CARRO = 130.0
VEL_INFRATOR = 150.0
PROB_INFRATOR = 0.12

FASES = [
    ("VERDE", 9.0),
    ("AMARELO", 2.5),
    ("TODOS_VERM_1", 1.5),
    ("PEDESTRE", 9.0),
    ("TODOS_VERM_2", 1.5),
]
CICLO = sum(d for _, d in FASES)
LIMITE_TRAVESSIA = (RUA_ALTURA + 24 + GUIA) / VEL * 1.35 + 0.4

INICIO = (100, 165)
DESTINOS = {
    1: ("Mercado", (100, 525)),
    2: ("Farmácia", (735, 165)),
    3: ("Padaria", (735, 525)),
    4: ("Casa", (100, 165)),
}
MARGENS = {"solo": 30, "predio": 22, "suspenso": 38, "parede": 24}
PASSAGEM = (FAIXA_X + 22, FAIXA_X + FAIXA_L - 22)
TATIL = [
    pygame.Rect(100, 158, 640, 14),
    pygame.Rect(621, 172, 14, 78),
    pygame.Rect(621, RUA_Y + RUA_ALTURA, 14, 100),
    pygame.Rect(100, 518, 640, 14),
]
TEMPO_MAX = 150.0

BRANCO = (245, 245, 245)
PRETO = (20, 22, 28)
ASFALTO = (62, 66, 98)
CALCADA = (160, 160, 170)
MEIO_FIO = (175, 180, 188)
PISO_TATIL = (235, 190, 20)
GRAMA = (60, 150, 90)
CORPO_ROBO = (30, 136, 229)
DETALHE_ROBO = (15, 76, 129)
CABECA_ROBO = (230, 236, 245)
ARNES = (255, 215, 0)
VERDE = (46, 204, 113)
LARANJA = (255, 140, 0)
VERMELHO = (225, 55, 55)
ROXO = (155, 89, 182)
AMARELO_COR = (241, 196, 15)


def rotacionar_ponto(cx, cy, px, py, angulo):
    s = math.sin(angulo)
    c = math.cos(angulo)
    dx = px - cx
    dy = py - cy
    return (int(cx + dx * c - dy * s), int(cy + dx * s + dy * c))


def diff_angulo(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def em_rua(y):
    return RUA_Y <= y <= RUA_Y + RUA_ALTURA


def aplicar_barreira(antigo, novo, autorizado):
    x, y = novo
    if em_rua(y):
        if not autorizado:
            return antigo
        x = max(FAIXA_X + 10, min(FAIXA_X + FAIXA_L - 10, x))
    return (x, y)


def criar_cenario():
    return [
        {"rect": pygame.Rect(-30, 0, 30, ALTURA), "tipo": "parede", "nome": "Limite"},
        {"rect": pygame.Rect(MAPA_L, 0, 30, ALTURA), "tipo": "parede", "nome": "Limite"},
        {"rect": pygame.Rect(0, 0, MAPA_L, 28), "tipo": "parede", "nome": "Limite"},
        {"rect": pygame.Rect(0, ALTURA - 28, MAPA_L, 28), "tipo": "parede", "nome": "Limite"},
        {"rect": pygame.Rect(25, 45, 130, 80), "tipo": "predio", "nome": "CASA"},
        {"rect": pygame.Rect(690, 45, 90, 65), "tipo": "predio", "nome": "FARMÁCIA"},
        {"rect": pygame.Rect(25, 570, 130, 70), "tipo": "predio", "nome": "MERCADO"},
        {"rect": pygame.Rect(690, 570, 90, 70), "tipo": "predio", "nome": "PADARIA"},
        {"rect": pygame.Rect(300, 118, 76, 34), "tipo": "solo", "nome": "OBSTÁCULO"},
        {"rect": pygame.Rect(470, 190, 60, 30), "tipo": "solo", "nome": "LIXEIRA"},
        {"rect": pygame.Rect(260, 455, 66, 34), "tipo": "suspenso", "nome": "ALTO"},
        {"rect": pygame.Rect(440, 498, 76, 34), "tipo": "solo", "nome": "OBSTÁCULO"},
    ]


def construir_grade(obstaculos):
    bloq = [[False] * COLS for _ in range(LINHAS)]
    for o in obstaculos:
        m = MARGENS[o["tipo"]]
        r = o["rect"].inflate(2 * m, 2 * m)
        c0 = max(0, r.left // CELULA)
        c1 = min(COLS - 1, r.right // CELULA)
        l0 = max(0, r.top // CELULA)
        l1 = min(LINHAS - 1, r.bottom // CELULA)
        for j in range(l0, l1 + 1):
            for i in range(c0, c1 + 1):
                if r.collidepoint(i * CELULA + 5, j * CELULA + 5):
                    bloq[j][i] = True
    for j in range(LINHAS):
        cy = j * CELULA + 5
        if RUA_Y - 8 <= cy <= RUA_Y + RUA_ALTURA + 8:
            for i in range(COLS):
                cx = i * CELULA + 5
                if not (PASSAGEM[0] <= cx <= PASSAGEM[1]):
                    bloq[j][i] = True
    custo = [[1.0] * COLS for _ in range(LINHAS)]
    for j in range(LINHAS):
        for i in range(COLS):
            if any(t.collidepoint(i * CELULA + 5, j * CELULA + 5) for t in TATIL):
                custo[j][i] = 0.45
    return bloq, custo


def celula_livre_proxima(bloq, c):
    i, j = c
    i = max(0, min(COLS - 1, i))
    j = max(0, min(LINHAS - 1, j))
    if not bloq[j][i]:
        return (i, j)
    melhor = None
    for r in range(1, 20):
        for dj in range(-r, r + 1):
            for di in range(-r, r + 1):
                ni, nj = i + di, j + dj
                if 0 <= ni < COLS and 0 <= nj < LINHAS and not bloq[nj][ni]:
                    d = di * di + dj * dj
                    if melhor is None or d < melhor[0]:
                        melhor = (d, (ni, nj))
        if melhor:
            return melhor[1]
    return None


def astar(bloq, custo, ini, fim):
    s = celula_livre_proxima(bloq, (int(ini[0]) // CELULA, int(ini[1]) // CELULA))
    g = celula_livre_proxima(bloq, (int(fim[0]) // CELULA, int(fim[1]) // CELULA))
    if s is None or g is None:
        return []

    def h(c):
        dx = abs(c[0] - g[0])
        dy = abs(c[1] - g[1])
        return 0.45 * ((dx + dy) + (math.sqrt(2) - 2) * min(dx, dy))

    abertos = [(h(s), 0, s)]
    custo_g = {s: 0.0}
    pai = {}
    fechados = set()
    cont = 0
    vizinhos = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
    while abertos:
        _, _, atual = heapq.heappop(abertos)
        if atual in fechados:
            continue
        fechados.add(atual)
        if atual == g:
            caminho = [atual]
            while atual in pai:
                atual = pai[atual]
                caminho.append(atual)
            caminho.reverse()
            return [(i * CELULA + 5, j * CELULA + 5) for i, j in caminho]
        for di, dj in vizinhos:
            ni, nj = atual[0] + di, atual[1] + dj
            if not (0 <= ni < COLS and 0 <= nj < LINHAS) or bloq[nj][ni]:
                continue
            if di != 0 and dj != 0 and (bloq[atual[1]][ni] or bloq[nj][atual[0]]):
                continue
            passo = math.sqrt(2) if di != 0 and dj != 0 else 1.0
            novo = custo_g[atual] + passo * custo[nj][ni]
            if novo < custo_g.get((ni, nj), 1e18):
                custo_g[(ni, nj)] = novo
                pai[(ni, nj)] = atual
                cont += 1
                heapq.heappush(abertos, (novo + h((ni, nj)), cont, (ni, nj)))
    return []


class Semaforo:
    def __init__(self, offset):
        self.t = offset % CICLO

    def avancar(self, dt):
        self.t = (self.t + dt) % CICLO

    def fase(self):
        acc = 0.0
        for nome, d in FASES:
            if self.t < acc + d:
                return nome, acc + d - self.t
            acc += d
        return FASES[0][0], FASES[0][1]


class Carro:
    contador = 0

    def __init__(self, x, y, direcao, infrator):
        Carro.contador += 1
        self.id = Carro.contador
        self.x = x
        self.y = y
        self.dir = direcao
        self.inf = infrator
        self.vmax = VEL_INFRATOR if infrator else VEL_CARRO
        self.v = self.vmax
        self.comp = 52
        self.larg = 26

    def rect(self):
        return pygame.Rect(int(self.x - self.comp / 2), int(self.y - self.larg / 2), self.comp, self.larg)

    def frente(self):
        return self.x + self.dir * self.comp / 2

    def dist_linha(self):
        linha = FAIXA_X - 8 if self.dir > 0 else FAIXA_X + FAIXA_L + 8
        return (linha - self.frente()) * self.dir

    def varrido(self, dt):
        r = self.rect()
        ext = int(self.v * dt)
        if self.dir > 0:
            return pygame.Rect(r.left, r.top, r.width + ext, r.height)
        return pygame.Rect(r.left - ext, r.top, r.width + ext, r.height)

    def atualizar(self, dt, fase, lider, pedestres):
        d_freio = self.v * self.v / (2 * DESACEL)
        folga = 6 if self.v < 5 else 0
        freia = False
        dl = self.dist_linha()
        if not self.inf and fase != "VERDE" and dl > -2:
            if not (fase == "AMARELO" and dl < d_freio):
                if dl < d_freio + 20 + folga:
                    freia = True
        if lider is not None:
            gap = (lider.x - self.x) * self.dir - self.comp
            if lider.v < self.v + 0.1:
                if gap < d_freio + 14 + folga:
                    freia = True
            elif gap < 16 + folga:
                freia = True
            if gap < 6:
                self.v = 0.0
        frente = self.varrido_ate(d_freio + 25)
        for p in pedestres:
            if frente.colliderect(p):
                freia = True
        if freia:
            self.v = max(0.0, self.v - DESACEL * dt)
        else:
            self.v = min(self.vmax, self.v + ACEL * dt)
        self.x += self.dir * self.v * dt

    def varrido_ate(self, ext):
        r = self.rect()
        ext = int(ext)
        if self.dir > 0:
            return pygame.Rect(r.left, r.top, r.width + ext, r.height)
        return pygame.Rect(r.left - ext, r.top, r.width + ext, r.height)


class Tutor:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def rect(self):
        return pygame.Rect(int(self.x - 10), int(self.y - 10), 20, 20)


class Robo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angulo = 0.0
        self.leituras = []
        self.buffers = [deque(maxlen=3) for _ in range(NUM_RAIOS)]
        self.passo_anim = 0.0

    def rect(self):
        return pygame.Rect(int(self.x - 16), int(self.y - 16), 32, 32)

    def ler_lidar(self, itens, rng):
        self.leituras = []
        ang0 = self.angulo - FOV / 2
        passo = FOV / (NUM_RAIOS - 1)
        ox, oy = int(self.x), int(self.y)
        for i in range(NUM_RAIOS):
            ang = ang0 + i * passo
            fx = int(self.x + math.cos(ang) * ALCANCE)
            fy = int(self.y + math.sin(ang) * ALCANCE)
            melhor = float(ALCANCE)
            tipo = None
            for rect, t in itens:
                seg = rect.clipline((ox, oy), (fx, fy))
                if seg:
                    (px, py), _ = seg
                    d = math.hypot(px - self.x, py - self.y)
                    if d < melhor:
                        melhor = d
                        tipo = t
            if rng.random() < DROPOUT:
                melhor = float(ALCANCE)
                tipo = None
            elif tipo is not None:
                melhor = max(0.0, min(float(ALCANCE), melhor + rng.gauss(0, RUIDO)))
            buf = self.buffers[i]
            buf.append((melhor, tipo))
            med = sorted(buf, key=lambda b: b[0])[len(buf) // 2]
            dist, tp = med
            if dist >= ALCANCE - 1:
                tp = None
            self.leituras.append({"angulo": ang, "dist": dist, "tipo": tp})


class Mundo:
    def __init__(self, rng, destino=None, offset=None):
        self.rng = rng
        self.obstaculos = criar_cenario()
        if offset is None:
            offset = rng.uniform(0, CICLO)
        self.sem = Semaforo(offset)
        self.carros = []
        self.timers = [rng.uniform(0.2, 2.0), rng.uniform(0.2, 2.0)]
        self.robo = Robo(*INICIO)
        self.tutor = Tutor(INICIO[0] - GUIA, INICIO[1])
        self.t = 0.0
        self.tempo_viagem = 0.0
        self.estado = "PARADO"
        self.historico = []
        self.destino = None
        self.caminho = []
        self.idx = 0
        self.idx_entrada = None
        self.atravessando = False
        self.entrou = False
        self.freio_t = 0.0
        self.desvio_t = 0.0
        self.preso = 0.0
        self.t_ref = 0.0
        self.p_ref = 0
        self.tensao = 0.0
        self.dist_percorrida = 0.0
        self.alertas = 0
        self.alerta_prev = False
        self.freios = 0
        self.colisoes = 0
        self.quase = 0
        self.replans = 0
        self.viagens = 0
        self.colididos = set()
        self.proximos = set()
        self.cor = VERDE
        self.status = "Pressione 1-4 para escolher o destino."
        self.som = None
        for _ in range(int(15 * FPS)):
            self.passo_transito()
        if destino is not None:
            self.definir_destino(destino)

    def mudar_estado(self, e):
        if e != self.estado:
            self.estado = e
            self.historico.append((round(self.tempo_viagem, 1), e))

    def definir_destino(self, n):
        self.destino = n
        self.tempo_viagem = 0.0
        self.historico = []
        self.mudar_estado("PLANEJANDO")
        self.planejar()
        self.mudar_estado("NAVEGANDO")

    def planejar(self):
        bloq, custo = construir_grade(self.obstaculos)
        alvo = DESTINOS[self.destino][1]
        self.caminho = astar(bloq, custo, (self.robo.x, self.robo.y), alvo)
        self.idx = 0
        self.idx_entrada = None
        if not self.atravessando:
            for i, p in enumerate(self.caminho):
                if em_rua(p[1]):
                    self.idx_entrada = max(1, i)
                    break

    def adicionar_obstaculo(self, pos, tipo=None):
        tipo = tipo or self.rng.choice(["solo", "suspenso"])
        self.obstaculos.append({
            "rect": pygame.Rect(pos[0] - 22, pos[1] - 22, 44, 44),
            "tipo": tipo,
            "nome": "Obstáculo",
        })

    def obstaculo_a_frente(self):
        r = self.robo
        self.adicionar_obstaculo((r.x + math.cos(r.angulo) * 95, r.y + math.sin(r.angulo) * 95), "solo")

    def itens_lidar(self):
        itens = []
        for o in self.obstaculos:
            if o["rect"].inflate(2 * ALCANCE, 2 * ALCANCE).collidepoint(self.robo.x, self.robo.y):
                itens.append((o["rect"], o["tipo"]))
        for c in self.carros:
            itens.append((c.rect(), "veiculo"))
        return itens

    def passo_transito(self):
        self.sem.avancar(DT)
        fase = self.sem.fase()[0]
        for faixa in (0, 1):
            self.timers[faixa] -= DT
            if self.timers[faixa] <= 0:
                self.timers[faixa] = self.rng.uniform(1.8, 4.0)
                direcao = 1 if faixa == 0 else -1
                x = -40 if direcao > 0 else MAPA_L + 40
                y = RUA_Y + 42 if faixa == 0 else RUA_Y + RUA_ALTURA - 42
                if all(abs(c.x - x) > 90 for c in self.carros if c.dir == direcao):
                    self.carros.append(Carro(x, y, direcao, self.rng.random() < PROB_INFRATOR))
        pedestres = [self.robo.rect().inflate(6, 6), self.tutor.rect().inflate(6, 6)]
        for c in self.carros:
            lideres = [o for o in self.carros if o is not c and o.dir == c.dir and (o.x - c.x) * c.dir > 0]
            lider = min(lideres, key=lambda o: abs(o.x - c.x)) if lideres else None
            c.atualizar(DT, fase, lider, pedestres)
        self.carros = [c for c in self.carros if -90 < c.x < MAPA_L + 90]

    def via_livre(self):
        faixa = pygame.Rect(FAIXA_X, RUA_Y, FAIXA_L, RUA_ALTURA)
        for c in self.carros:
            if c.v > 8 and c.varrido(2.5).colliderect(faixa):
                return False
        return True

    def pode_atravessar(self):
        fase, resta = self.sem.fase()
        return fase == "PEDESTRE" and resta > LIMITE_TRAVESSIA and self.via_livre()

    def ameaca(self):
        alvos = [self.robo.rect(), self.tutor.rect()]
        for c in self.carros:
            if c.v < 5:
                continue
            sw = c.varrido(1.0)
            for a in alvos:
                if sw.colliderect(a):
                    return c
        return None

    def pan_para(self, x, y):
        rel = diff_angulo(math.atan2(y - self.robo.y, x - self.robo.x), self.robo.angulo)
        return max(-1.0, min(1.0, math.sin(rel)))

    def reativo(self):
        L = self.robo.leituras
        d = [ALCANCE if l["tipo"] == "veiculo" else l["dist"] for l in L]
        esq = min(d[:7])
        cen = min(d[7:12])
        dire = min(d[12:])
        if cen < 50:
            suspenso = any(l["tipo"] == "suspenso" for l in L[7:12] if l["dist"] < 80)
            msg = "ALERTA CABEÇA: galho/toldo baixo! Desviando..." if suspenso else "Obstáculo à frente. Contornando..."
            giro = -4.0 if esq > dire else 4.0
            return giro, 0.5, VERMELHO, msg
        if esq < 20:
            return 2.7, 0.85, LARANJA, "Obstáculo à esquerda. Deslocando à direita."
        if dire < 20:
            return -2.7, 0.85, LARANJA, "Obstáculo à direita. Deslocando à esquerda."
        return None

    def pan_obstaculo(self):
        melhor = min(self.robo.leituras, key=lambda l: l["dist"])
        rel = diff_angulo(melhor["angulo"], self.robo.angulo)
        return max(-1.0, min(1.0, rel / (FOV / 2)))

    def passo(self):
        self.t += DT
        self.passo_transito()
        self.passo_robo()
        self.checar_colisoes()

    def mover_tutor(self):
        r, t = self.robo, self.tutor
        dist = math.hypot(r.x - t.x, r.y - t.y)
        if dist > GUIA:
            mv = min(VEL_TUTOR * DT, dist - GUIA)
            nx = t.x + (r.x - t.x) / dist * mv
            ny = t.y + (r.y - t.y) / dist * mv
            t.x, t.y = aplicar_barreira((t.x, t.y), (nx, ny), self.atravessando)
        self.tensao = max(0.0, math.hypot(r.x - t.x, r.y - t.y) - GUIA)

    def checar_colisoes(self):
        alvos = [self.robo.rect(), self.tutor.rect()]
        for c in self.carros:
            cr = c.rect()
            if any(cr.colliderect(a) for a in alvos):
                if c.id not in self.colididos:
                    self.colididos.add(c.id)
                    self.colisoes += 1
            elif c.id not in self.proximos and c.id not in self.colididos:
                if any(cr.colliderect(a.inflate(24, 24)) for a in alvos):
                    self.proximos.add(c.id)
                    self.quase += 1

    def passo_robo(self):
        r = self.robo
        r.ler_lidar(self.itens_lidar(), self.rng)
        if self.destino is None or self.estado == "CHEGOU":
            self.mover_tutor()
            return
        self.tempo_viagem += DT

        c = self.ameaca()
        if c is not None:
            if self.freio_t <= 0:
                self.freios += 1
                self.som = (self.pan_para(c.x, c.y), 1320)
            self.freio_t = 0.5
        elif self.freio_t > 0:
            self.freio_t = max(0.0, self.freio_t - DT)

        if em_rua(r.y) or em_rua(self.tutor.y):
            if self.atravessando:
                self.entrou = True
        elif self.atravessando and self.entrou:
            self.atravessando = False
            self.entrou = False

        alvo = DESTINOS[self.destino][1]
        vel = 0.0
        cor = VERDE
        status = "Caminho livre. Seguindo rota A*."

        if math.hypot(alvo[0] - r.x, alvo[1] - r.y) < 20:
            self.mudar_estado("CHEGOU")
            self.viagens += 1
            self.cor = VERDE
            self.status = "DESTINO ALCANÇADO COM SEGURANÇA!"
            self.mover_tutor()
            return

        if self.freio_t > 0:
            self.mudar_estado("FREIO_EMERGENCIA")
            cor = VERMELHO
            status = "FREIO DE EMERGÊNCIA: veículo em rota de colisão!"
            self.preso = 0.0
            self.t_ref = 0.0
            self.p_ref = self.idx
        elif not self.caminho:
            self.mudar_estado("SEM_ROTA")
            cor = LARANJA
            status = "Sem rota até o destino."
            self.planejar()
        else:
            esperar = False
            if self.idx_entrada is not None and not self.atravessando:
                curb = self.caminho[self.idx_entrada - 1]
                if math.hypot(r.x - curb[0], r.y - curb[1]) < 12:
                    if self.pode_atravessar():
                        self.atravessando = True
                        self.entrou = False
                        self.idx_entrada = None
                    else:
                        esperar = True
            if esperar:
                self.mudar_estado("AGUARDANDO_SINAL")
                cor = LARANJA
                fase, resta = self.sem.fase()
                status = f"Aguardando sinal de pedestre ({fase})."
                self.preso = 0.0
                self.t_ref = 0.0
                self.p_ref = self.idx
            else:
                lim = len(self.caminho) - 1
                if self.idx_entrada is not None and not self.atravessando:
                    lim = self.idx_entrada - 1
                cam = self.caminho
                while self.idx < lim:
                    d0 = math.hypot(cam[self.idx][0] - r.x, cam[self.idx][1] - r.y)
                    d1 = math.hypot(cam[self.idx + 1][0] - r.x, cam[self.idx + 1][1] - r.y)
                    if d0 < 20 or d1 < d0:
                        self.idx += 1
                    else:
                        break
                j = self.idx
                while j < lim and math.hypot(self.caminho[j][0] - r.x, self.caminho[j][1] - r.y) < 40:
                    j += 1
                ponto = self.caminho[j]
                reat = self.reativo()
                if reat is not None and not self.atravessando:
                    giro, fator, cor, status = reat
                    r.angulo += giro * DT
                    vel = VEL * fator
                    self.desvio_t = 0.5
                    self.mudar_estado("DESVIANDO")
                else:
                    ang = math.atan2(ponto[1] - r.y, ponto[0] - r.x)
                    d = diff_angulo(ang, r.angulo)
                    r.angulo += max(-5.0 * DT, min(5.0 * DT, d))
                    vel = VEL
                    if self.desvio_t > 0:
                        self.desvio_t -= DT
                        self.mudar_estado("DESVIANDO")
                    else:
                        self.mudar_estado("ATRAVESSANDO" if self.atravessando else "NAVEGANDO")
                    if self.atravessando:
                        status = "Atravessando na faixa com sinal aberto."
                fator_t = 1.0 if self.tensao <= 10 else max(0.15, 1 - (self.tensao - 10) / 25)
                vel *= fator_t
                if fator_t < 1.0 and cor == VERDE:
                    status = "Tensão no arnês: reduzindo velocidade."
                self.t_ref += DT
                if self.t_ref >= 0.5:
                    if self.idx <= self.p_ref:
                        self.preso += 0.5
                    else:
                        self.preso = 0.0
                    self.p_ref = self.idx
                    self.t_ref = 0.0
                    if self.preso >= 3.5:
                        self.planejar()
                        self.replans += 1
                        self.preso = 0.0

        if vel > 0:
            nx = r.x + math.cos(r.angulo) * vel * DT
            ny = r.y + math.sin(r.angulo) * vel * DT
            nx, ny = aplicar_barreira((r.x, r.y), (nx, ny), self.atravessando)
            self.dist_percorrida += math.hypot(nx - r.x, ny - r.y)
            r.x, r.y = nx, ny
            r.passo_anim += vel * DT * 0.25

        self.mover_tutor()
        self.cor = cor
        self.status = status
        vermelho = cor == VERMELHO
        if vermelho and not self.alerta_prev:
            self.alertas += 1
        self.alerta_prev = vermelho
        if cor in (VERMELHO, LARANJA) and self.estado in ("DESVIANDO", "FREIO_EMERGENCIA"):
            if self.estado == "DESVIANDO":
                self.som = (self.pan_obstaculo(), 880)

    def terminou(self):
        return self.estado == "CHEGOU"

    def resumo(self):
        return {
            "sucesso": self.terminou(),
            "tempo": self.tempo_viagem,
            "colisoes": self.colisoes,
            "quase": self.quase,
            "freios": self.freios,
            "alertas": self.alertas,
            "replans": self.replans,
            "dist": self.dist_percorrida,
        }


class Audio:
    def __init__(self, ativo):
        self.ativo = False
        self.cache = {}
        self.ultimo = -1.0
        if ativo:
            try:
                pygame.mixer.init(22050, -16, 2, 512)
                self.ativo = True
            except pygame.error:
                self.ativo = False

    def tocar(self, pan, freq, agora):
        if not self.ativo or agora - self.ultimo < 0.45:
            return
        self.ultimo = agora
        chave = (round(pan * 4), freq)
        if chave not in self.cache:
            esq = min(1.0, 1.0 - pan)
            dire = min(1.0, 1.0 + pan)
            n = int(22050 * 0.15)
            buf = array("h")
            for i in range(n):
                v = math.sin(2 * math.pi * freq * i / 22050) * 9000 * (1 - i / n)
                buf.append(int(v * esq))
                buf.append(int(v * dire))
            self.cache[chave] = pygame.mixer.Sound(buffer=buf.tobytes())
        self.cache[chave].play()


def desenhar_robo(tela, robo, tutor):
    for l in robo.leituras:
        fx = robo.x + math.cos(l["angulo"]) * l["dist"]
        fy = robo.y + math.sin(l["angulo"]) * l["dist"]
        cor = VERDE if l["dist"] >= ALCANCE - 5 else VERMELHO
        pygame.draw.line(tela, cor, (robo.x, robo.y), (fx, fy), 1)
        if l["tipo"]:
            pygame.draw.circle(tela, BRANCO, (int(fx), int(fy)), 3)
    pygame.draw.line(tela, ARNES, (robo.x, robo.y), (tutor.x, tutor.y), 4)
    pygame.draw.circle(tela, (235, 235, 240), (int(tutor.x), int(tutor.y)), 12)
    pygame.draw.circle(tela, PRETO, (int(tutor.x), int(tutor.y)), 12, 2)
    balanco = math.sin(robo.passo_anim) * 5
    patas = [(10 + balanco, -14), (10 - balanco, 14), (-12 - balanco, -14), (-12 + balanco, 14)]
    for ox, oy in patas:
        px, py = rotacionar_ponto(robo.x, robo.y, robo.x + ox, robo.y + oy, robo.angulo)
        pygame.draw.circle(tela, DETALHE_ROBO, (px, py), 5)
    corpo = [
        rotacionar_ponto(robo.x, robo.y, robo.x + 16, robo.y - 11, robo.angulo),
        rotacionar_ponto(robo.x, robo.y, robo.x + 16, robo.y + 11, robo.angulo),
        rotacionar_ponto(robo.x, robo.y, robo.x - 18, robo.y + 11, robo.angulo),
        rotacionar_ponto(robo.x, robo.y, robo.x - 18, robo.y - 11, robo.angulo),
    ]
    pygame.draw.polygon(tela, CORPO_ROBO, corpo)
    pygame.draw.polygon(tela, BRANCO, corpo, 2)
    cab = rotacionar_ponto(robo.x, robo.y, robo.x + 21, robo.y, robo.angulo)
    pygame.draw.circle(tela, CABECA_ROBO, cab, 9)
    pygame.draw.circle(tela, DETALHE_ROBO, cab, 9, 2)
    lidar = rotacionar_ponto(robo.x, robo.y, robo.x + 3, robo.y, robo.angulo)
    pygame.draw.circle(tela, LARANJA, lidar, 5)


def desenhar_semaforo(tela, fase):
    bx = FAIXA_X + FAIXA_L + 12
    for by in (RUA_Y - 58, RUA_Y + RUA_ALTURA + 12):
        pygame.draw.rect(tela, PRETO, (bx, by, 16, 46), border_radius=4)
        carro_cor = {"VERDE": 2, "AMARELO": 1}.get(fase, 0)
        for i, cor in enumerate([VERMELHO, AMARELO_COR, VERDE]):
            c = cor if i == carro_cor else (60, 60, 60)
            pygame.draw.circle(tela, c, (bx + 8, by + 9 + i * 14), 5)
        px = bx + 20
        pygame.draw.rect(tela, PRETO, (px, by, 16, 32), border_radius=4)
        ped = fase == "PEDESTRE"
        pygame.draw.circle(tela, (60, 60, 60) if ped else VERMELHO, (px + 8, by + 9), 5)
        pygame.draw.circle(tela, VERDE if ped else (60, 60, 60), (px + 8, by + 23), 5)


def desenhar_ambiente(tela):
    tela.fill(CALCADA)
    pygame.draw.rect(tela, GRAMA, (0, 0, MAPA_L, 28))
    pygame.draw.rect(tela, GRAMA, (0, ALTURA - 28, MAPA_L, 28))
    pygame.draw.rect(tela, ASFALTO, (0, RUA_Y, MAPA_L, RUA_ALTURA))
    pygame.draw.line(tela, MEIO_FIO, (0, RUA_Y), (MAPA_L, RUA_Y), 4)
    pygame.draw.line(tela, MEIO_FIO, (0, RUA_Y + RUA_ALTURA), (MAPA_L, RUA_Y + RUA_ALTURA), 4)
    for x in range(15, MAPA_L - 20, 45):
        if not (FAIXA_X - 10 <= x <= FAIXA_X + FAIXA_L + 5):
            pygame.draw.line(tela, BRANCO, (x, RUA_Y + RUA_ALTURA // 2), (x + 22, RUA_Y + RUA_ALTURA // 2), 3)
    for y in range(RUA_Y + 12, RUA_Y + RUA_ALTURA - 12, 22):
        pygame.draw.rect(tela, BRANCO, (FAIXA_X, y, FAIXA_L, 12))
    pygame.draw.line(tela, BRANCO, (FAIXA_X - 8, RUA_Y + 4), (FAIXA_X - 8, RUA_Y + RUA_ALTURA // 2 - 2), 3)
    pygame.draw.line(tela, BRANCO, (FAIXA_X + FAIXA_L + 8, RUA_Y + RUA_ALTURA // 2 + 2), (FAIXA_X + FAIXA_L + 8, RUA_Y + RUA_ALTURA - 4), 3)
    for t in TATIL:
        pygame.draw.rect(tela, PISO_TATIL, t)


def desenhar(tela, mundo, fontes):
    titulo, texto, pequena = fontes
    desenhar_ambiente(tela)
    fase, resta = mundo.sem.fase()
    desenhar_semaforo(tela, fase)

    for pos in [(500, 120), (330, 490), (240, 330)]:
        pygame.draw.circle(tela, (240, 150, 190), pos, 4)

    cores_predio = {
        "CASA": (60, 100, 200),
        "FARMÁCIA": (205, 65, 105),
        "MERCADO": (35, 170, 130),
        "PADARIA": (200, 140, 110),
    }
    for o in mundo.obstaculos:
        if o["tipo"] == "parede":
            continue
        rect = o["rect"]
        nome = o["nome"]
        if o["tipo"] == "predio":
            pygame.draw.rect(tela, (90, 90, 100), rect.move(5, 5), border_radius=4)
            pygame.draw.rect(tela, cores_predio.get(nome, (95, 85, 80)), rect, border_radius=4)
            pygame.draw.rect(tela, BRANCO, rect, 2, border_radius=4)
            if nome == "CASA":
                pygame.draw.polygon(tela, VERMELHO, [(rect.left, rect.top), (rect.right, rect.top), (rect.centerx, rect.top - 22)])
            else:
                pygame.draw.rect(tela, LARANJA if nome == "MERCADO" else (240, 240, 245), (rect.left, rect.top, rect.width, 10))
        else:
            if o["tipo"] == "suspenso":
                cor = ROXO
            elif nome == "LIXEIRA":
                cor = (50, 150, 100)
            else:
                cor = (60, 64, 90)
            pygame.draw.rect(tela, (90, 90, 100), rect.move(4, 4), border_radius=8)
            pygame.draw.rect(tela, cor, rect, border_radius=8)
            pygame.draw.rect(tela, BRANCO, rect, 2, border_radius=8)
        lbl = pequena.render(nome.upper(), True, BRANCO)
        tela.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - 7))

    for n, (nome, pos) in DESTINOS.items():
        if n == mundo.destino:
            pygame.draw.circle(tela, VERDE, pos, 14, 3)
            pygame.draw.circle(tela, VERDE, pos, 4)

    if len(mundo.caminho) > 1:
        pygame.draw.lines(tela, (80, 170, 255), False, mundo.caminho, 2)

    for c in mundo.carros:
        r = c.rect()
        paleta = [(240, 190, 40), (70, 140, 220), (235, 235, 240), (60, 170, 120)]
        pygame.draw.rect(tela, (210, 50, 50) if c.inf else paleta[c.id % 4], r, border_radius=6)
        pygame.draw.rect(tela, PRETO, r, 2, border_radius=6)
        vx = r.right - 18 if c.dir > 0 else r.left + 6
        pygame.draw.rect(tela, (40, 50, 70), (vx, r.top + 4, 12, r.height - 8), border_radius=3)
        fx = r.right - 6 if c.dir > 0 else r.left + 6
        pygame.draw.circle(tela, AMARELO_COR, (fx, r.top + 5), 3)
        pygame.draw.circle(tela, AMARELO_COR, (fx, r.bottom - 5), 3)

    desenhar_robo(tela, mundo.robo, mundo.tutor)

    px = MAPA_L
    pygame.draw.rect(tela, PRETO, (px, 0, LARGURA - px, ALTURA))
    pygame.draw.line(tela, BRANCO, (px, 0), (px, ALTURA), 2)
    y = 14
    tela.blit(titulo.render("TELEMETRIA DOG-IA V2", True, CORPO_ROBO), (px + 12, y))
    y += 34
    destino = DESTINOS[mundo.destino][0] if mundo.destino else "-"
    min_d = min(l["dist"] for l in mundo.robo.leituras) if mundo.robo.leituras else ALCANCE
    linhas = [
        f"Estado: {mundo.estado}",
        f"Destino: {destino}",
        f"Semáforo: {fase} ({resta:.1f}s)",
        f"LiDAR mín: {min_d:.0f} px",
        f"Tensão arnês: {mundo.tensao:.1f} px",
        f"Tempo: {mundo.tempo_viagem:.1f} s",
        f"Distância: {mundo.dist_percorrida:.0f} px",
        f"Alertas verm.: {mundo.alertas}",
        f"Freios emerg.: {mundo.freios}",
        f"Colisões: {mundo.colisoes}  Quase: {mundo.quase}",
        f"Replanejamentos: {mundo.replans}",
        f"Viagens concluídas: {mundo.viagens}",
    ]
    for ln in linhas:
        tela.blit(texto.render(ln, True, BRANCO), (px + 12, y))
        y += 21
    y += 8
    pygame.draw.rect(tela, mundo.cor, (px + 12, y, 236, 84), border_radius=8)
    linha = ""
    ya = y + 8
    for p in mundo.status.split(" "):
        if len(linha + p) < 27:
            linha += p + " "
        else:
            tela.blit(texto.render(linha, True, PRETO), (px + 20, ya))
            ya += 19
            linha = p + " "
    tela.blit(texto.render(linha, True, PRETO), (px + 20, ya))
    y += 100
    ajuda = [
        "1 Mercado  2 Farmácia",
        "3 Padaria  4 Casa",
        "Clique dir: obstáculo",
        "ESPAÇO: pausa   R: reiniciar",
        "Azul: rota A*  Amarelo: tátil",
    ]
    for ln in ajuda:
        tela.blit(pequena.render(ln, True, BRANCO), (px + 12, y))
        y += 18


def criar_tela():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("DOG-IA V2 — Simulador Urbano de Cão-Guia Autônomo")
    fontes = (
        pygame.font.SysFont("arial", 18, bold=True),
        pygame.font.SysFont("arial", 14),
        pygame.font.SysFont("arial", 12, bold=True),
    )
    return tela, fontes


def executar_interativo():
    tela, fontes = criar_tela()
    audio = Audio(True)
    clock = pygame.time.Clock()
    rng = random.Random()
    mundo = Mundo(rng, None)
    pausado = False
    rodando = True
    teclas_destino = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4}
    while rodando:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                rodando = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                if ev.pos[0] < MAPA_L:
                    mundo.adicionar_obstaculo(ev.pos)
            elif ev.type == pygame.KEYDOWN:
                if ev.key in teclas_destino:
                    mundo.definir_destino(teclas_destino[ev.key])
                elif ev.key == pygame.K_SPACE:
                    pausado = not pausado
                elif ev.key == pygame.K_r:
                    mundo = Mundo(rng, None)
                elif ev.key == pygame.K_ESCAPE:
                    rodando = False
        if not pausado:
            mundo.passo()
            if mundo.som:
                audio.tocar(mundo.som[0], mundo.som[1], mundo.t)
                mundo.som = None
        desenhar(tela, mundo, fontes)
        pygame.display.flip()
    pygame.quit()


def executar_demo(pasta, destinos, seed):
    os.makedirs(pasta, exist_ok=True)
    tela, fontes = criar_tela()
    rng = random.Random(seed)
    mundo = Mundo(rng, destinos[0], offset=0.0)
    fila = list(destinos[1:])
    vistos = set()
    trecho = 1
    contador = 0
    espera = 0.0

    def salvar(nome):
        nonlocal contador
        desenhar(tela, mundo, fontes)
        pygame.image.save(tela, os.path.join(pasta, f"{contador:02d}_{nome}.png"))
        contador += 1

    mundo.adicionar_obstaculo((205, 160), "solo")
    salvar("inicio")
    while mundo.t < 400:
        mundo.passo()
        chave = (trecho, mundo.estado)
        if chave not in vistos:
            vistos.add(chave)
            salvar(f"viagem{trecho}_{mundo.estado}")
        if mundo.estado == "CHEGOU":
            espera += DT
            if espera > 1.5:
                espera = 0.0
                print(f"Viagem {trecho} -> {DESTINOS[mundo.destino][0]}: {mundo.historico}")
                if not fila:
                    break
                mundo.definir_destino(fila.pop(0))
                trecho += 1
    print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in mundo.resumo().items()})
    pygame.quit()


def benchmark(n, seed, destino):
    rng = random.Random(seed)
    res = []
    for _ in range(n):
        m = Mundo(rng, destino)
        while not m.terminou() and m.tempo_viagem < TEMPO_MAX:
            m.passo()
        res.append(m.resumo())
    ok = [r for r in res if r["sucesso"]]
    tempo = sum(r["tempo"] for r in ok) / len(ok) if ok else 0.0
    print(f"Benchmark: {n} viagens ao destino {destino} ({DESTINOS[destino][0]}) | seed {seed}")
    print(f"Taxa de sucesso: {len(ok)}/{n} ({100 * len(ok) / n:.1f}%)")
    print(f"Tempo médio (sucessos): {tempo:.1f} s")
    print(f"Colisões: {sum(r['colisoes'] for r in res)}")
    print(f"Quase-colisões: {sum(r['quase'] for r in res)}")
    print(f"Freios de emergência: {sum(r['freios'] for r in res)}")
    print(f"Alertas vermelhos: {sum(r['alertas'] for r in res)}")
    print(f"Replanejamentos: {sum(r['replans'] for r in res)}")
    print(f"Distância média: {sum(r['dist'] for r in res) / n:.0f} px")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--destino", type=int, default=1)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--salvar", default="prints")
    args = ap.parse_args()
    if args.benchmark:
        benchmark(args.benchmark, args.seed, args.destino)
    elif args.demo:
        executar_demo(args.salvar, [1, 4], args.seed)
    else:
        executar_interativo()


if __name__ == "__main__":
    main()
