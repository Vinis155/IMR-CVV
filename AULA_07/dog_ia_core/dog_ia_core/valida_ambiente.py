#!/usr/bin/env python3
"""No de validacao do ambiente DOG-IA (ROS 2 + OpenCV)."""

from cv_bridge import CvBridge
import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String


class ValidaAmbienteNode(Node):
    """Publica status em dog_ia/status a cada 2 s e testa o cv_bridge."""

    def __init__(self):
        """Cria publisher, timer e testa a ponte cv_bridge."""
        super().__init__('valida_ambiente_node')
        self.bridge = CvBridge()
        self.publisher_ = self.create_publisher(String, 'dog_ia/status', 10)
        self.timer = self.create_timer(2.0, self.publica_status)
        self.testa_cv_bridge()
        self.get_logger().info('Nó de Validação do DOG-IA iniciado com sucesso!')

    def testa_cv_bridge(self):
        """Ida e volta ndarray -> sensor_msgs/Image -> ndarray."""
        img = np.zeros((48, 64, 3), dtype=np.uint8)
        msg = self.bridge.cv2_to_imgmsg(img, encoding='bgr8')
        volta = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        ok = volta.shape == img.shape and np.array_equal(img, volta)
        self.get_logger().info(
            f'cv_bridge ida/volta: {"OK" if ok else "FALHOU"} '
            f'({msg.width}x{msg.height}, {msg.encoding})')

    def publica_status(self):
        """Publique a mensagem de status (callback do timer)."""
        msg = String()
        msg.data = 'DOG-IA Operacional: ROS 2 + OpenCV Prontos!'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Mensagem Publicada: "{msg.data}"')


def main(args=None):
    """Ponto de entrada do no."""
    rclpy.init(args=args)
    node = ValidaAmbienteNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
