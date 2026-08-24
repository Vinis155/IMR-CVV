1. Estado do Robô e POSE 2D
O Estado do Robô, ou POSE 2D, é a forma como o computador registra a localização e a postura do robô no mapa. Para isso, ele utiliza três informações básicas: a posição no eixo horizontal (X), a posição no eixo vertical (Y) e o ângulo para onde a frente do robô está apontando (θ ou Theta). Como um robô com rodas não anda de lado, saber a direção para onde ele "olha" é obrigatório para calcular qualquer movimento futuro.

Analogia: É como posicionar um carro em um mapa de GPS. Não basta saber que o carro está na Avenida Paulista (posição X e Y); você precisa saber para qual lado os faróis estão apontando (orientação θ) para saber para onde ele vai ao acelerar.

2. Cinemática Diferencial
É o sistema que permite ao robô se movimentar e fazer curvas utilizando apenas duas rodas independentes, sem precisar de um volante. A regra é simples: o controle do movimento é feito inteiramente pela variação de velocidade entre a roda da direita e a roda da esquerda. Se as duas giram iguais, ele vai reto; se giram em velocidades diferentes, ele faz uma curva; e se giram em direções opostas, ele gira no próprio eixo.

3. Odometria Discreta
É a técnica que o robô usa para calcular onde ele está com base nos seus próprios movimentos, registrando o quanto as rodas já giraram desde o ponto de partida. O termo "discreta" significa que o sistema não calcula isso de forma contínua, mas sim em pequenos "lotes" ou frações de segundo. Como o robô faz essa estimativa sem olhar para o ambiente ao redor, qualquer pequeno escorregão da roda ou arredondamento matemático gera um erro que se acumula, fazendo com que a posição calculada se distancie da posição real com o tempo.

4. Navegação “GO-TO-GOAL” (Ir para o Alvo)
É um sistema de direção automática onde não dizemos ao robô como ele deve se mover (ex: "ande para frente e vire"), mas sim para onde ele deve ir (uma coordenada final no mapa). A partir desse momento, o robô assume o controle: ele mede a distância até o alvo e o quanto ele está desalinhado. Automaticamente, ele corrige a própria rota para virar na direção certa, acelera em linha reta e freia sozinho quando alcança o destino.
