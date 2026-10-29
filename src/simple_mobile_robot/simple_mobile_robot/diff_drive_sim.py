import math

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster


def yaw_to_quaternion(yaw):
    half_yaw = yaw * 0.5
    return (0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw))


class DifferentialDriveSimulator(Node):
    def __init__(self):
        super().__init__('diff_drive_sim')

        self.declare_parameter('wheel_radius', 0.05)
        self.declare_parameter('wheel_separation', 0.32)
        self.declare_parameter('publish_rate', 30.0)
        self.declare_parameter('cmd_vel_timeout', 1.5)

        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        publish_rate = self.get_parameter('publish_rate').value
        self.cmd_vel_timeout = self.get_parameter('cmd_vel_timeout').value

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.left_wheel_position = 0.0
        self.right_wheel_position = 0.0
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0

        self.last_update_time = self.get_clock().now()
        self.last_cmd_time = self.last_update_time
        self.last_logged_command = None

        self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.joint_pub = self.create_publisher(JointState, 'joint_states', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.create_timer(1.0 / publish_rate, self.update)
        self.get_logger().info('Differential drive simulator listening on /cmd_vel')

    def cmd_vel_callback(self, msg):
        self.linear_velocity = msg.linear.x
        self.angular_velocity = msg.angular.z
        self.last_cmd_time = self.get_clock().now()
        command = (round(self.linear_velocity, 3), round(self.angular_velocity, 3))
        if command != self.last_logged_command:
            self.get_logger().info(
                f'Received /cmd_vel: linear.x={command[0]}, angular.z={command[1]}'
            )
            self.last_logged_command = command

    def update(self):
        now = self.get_clock().now()
        dt = (now - self.last_update_time).nanoseconds / 1e9
        self.last_update_time = now

        if dt <= 0.0:
            return

        time_since_command = (now - self.last_cmd_time).nanoseconds / 1e9
        if time_since_command > self.cmd_vel_timeout:
            linear_velocity = 0.0
            angular_velocity = 0.0
        else:
            linear_velocity = self.linear_velocity
            angular_velocity = self.angular_velocity

        delta_theta = angular_velocity * dt
        if abs(angular_velocity) < 1e-6:
            self.x += linear_velocity * math.cos(self.theta) * dt
            self.y += linear_velocity * math.sin(self.theta) * dt
        else:
            radius = linear_velocity / angular_velocity
            self.x += radius * (math.sin(self.theta + delta_theta) - math.sin(self.theta))
            self.y -= radius * (math.cos(self.theta + delta_theta) - math.cos(self.theta))

        self.theta = math.atan2(
            math.sin(self.theta + delta_theta),
            math.cos(self.theta + delta_theta),
        )

        left_velocity = (
            linear_velocity - angular_velocity * self.wheel_separation * 0.5
        ) / self.wheel_radius
        right_velocity = (
            linear_velocity + angular_velocity * self.wheel_separation * 0.5
        ) / self.wheel_radius
        self.left_wheel_position += left_velocity * dt
        self.right_wheel_position += right_velocity * dt

        self.publish_tf(now)
        self.publish_odom(now, linear_velocity, angular_velocity)
        self.publish_joint_states(now)

    def publish_tf(self, stamp):
        transform = TransformStamped()
        transform.header.stamp = stamp.to_msg()
        transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_footprint'
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.translation.z = 0.0
        qx, qy, qz, qw = yaw_to_quaternion(self.theta)
        transform.transform.rotation.x = qx
        transform.transform.rotation.y = qy
        transform.transform.rotation.z = qz
        transform.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(transform)

    def publish_odom(self, stamp, linear_velocity, angular_velocity):
        odom = Odometry()
        odom.header.stamp = stamp.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        qx, qy, qz, qw = yaw_to_quaternion(self.theta)
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = linear_velocity
        odom.twist.twist.angular.z = angular_velocity
        self.odom_pub.publish(odom)

    def publish_joint_states(self, stamp):
        joint_state = JointState()
        joint_state.header.stamp = stamp.to_msg()
        joint_state.name = ['left_wheel_joint', 'right_wheel_joint']
        joint_state.position = [self.left_wheel_position, self.right_wheel_position]
        self.joint_pub.publish(joint_state)


def main(args=None):
    rclpy.init(args=args)
    node = DifferentialDriveSimulator()

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
