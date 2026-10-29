import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, Float32


class UltrasonicThreshold(Node):
    def __init__(self):
        super().__init__('ultrasonic_threshold')

        self.declare_parameter('scan_topic', '/ultrasonic_scan')
        self.declare_parameter('threshold_distance', 0.5)
        self.declare_parameter('use_center_beam_only', True)

        self.scan_topic = self.get_parameter('scan_topic').value
        self.threshold_distance = self.get_parameter('threshold_distance').value
        self.use_center_beam_only = self.get_parameter('use_center_beam_only').value
        self.last_obstacle_state = None

        self.distance_pub = self.create_publisher(Float32, '/ultrasonic_distance', 10)
        self.obstacle_pub = self.create_publisher(Bool, '/ultrasonic_obstacle', 10)
        self.create_subscription(LaserScan, self.scan_topic, self.scan_callback, 10)

        self.get_logger().info(
            f'Listening on {self.scan_topic}; obstacle threshold = '
            f'{self.threshold_distance:.2f} m'
        )

    def scan_callback(self, msg):
        distance = self.get_distance(msg)
        obstacle_detected = math.isfinite(distance) and distance <= self.threshold_distance

        distance_msg = Float32()
        distance_msg.data = float(distance)
        self.distance_pub.publish(distance_msg)

        obstacle_msg = Bool()
        obstacle_msg.data = obstacle_detected
        self.obstacle_pub.publish(obstacle_msg)

        if obstacle_detected != self.last_obstacle_state:
            if obstacle_detected:
                self.get_logger().warn(
                    f'Obstacle detected at {distance:.2f} m '
                    f'(threshold {self.threshold_distance:.2f} m)'
                )
            else:
                self.get_logger().info('Path clear')
            self.last_obstacle_state = obstacle_detected

    def get_distance(self, msg):
        finite_ranges = [
            value
            for value in msg.ranges
            if math.isfinite(value) and msg.range_min <= value <= msg.range_max
        ]

        if not finite_ranges:
            return math.inf

        if self.use_center_beam_only:
            center_index = len(msg.ranges) // 2
            center_value = msg.ranges[center_index]
            if math.isfinite(center_value) and msg.range_min <= center_value <= msg.range_max:
                return center_value

        return min(finite_ranges)


def main(args=None):
    rclpy.init(args=args)
    node = UltrasonicThreshold()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
