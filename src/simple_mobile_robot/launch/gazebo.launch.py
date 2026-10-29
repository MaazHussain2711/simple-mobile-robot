import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def clean_gazebo_environment():
    passthrough_keys = [
        'AMENT_PREFIX_PATH',
        'CMAKE_PREFIX_PATH',
        'COLCON_PREFIX_PATH',
        'DBUS_SESSION_BUS_ADDRESS',
        'DISPLAY',
        'GZ_CONFIG_PATH',
        'GZ_SIM_RESOURCE_PATH',
        'GZ_SIM_SYSTEM_PLUGIN_PATH',
        'HOME',
        'LANG',
        'LC_ALL',
        'LD_LIBRARY_PATH',
        'PYTHONPATH',
        'QT_QPA_PLATFORM',
        'RMW_IMPLEMENTATION',
        'ROS_DISTRO',
        'ROS_DOMAIN_ID',
        'ROS_LOCALHOST_ONLY',
        'ROS_PYTHON_VERSION',
        'ROS_VERSION',
        'TERM',
        'USER',
        'WAYLAND_DISPLAY',
        'XAUTHORITY',
        'XDG_RUNTIME_DIR',
    ]
    env = {
        key: os.environ[key]
        for key in passthrough_keys
        if os.environ.get(key)
    }

    path_entries = [
        entry
        for entry in os.environ.get('PATH', '').split(os.pathsep)
        if entry and not entry.startswith('/snap') and '/snap/' not in entry
    ]
    env['PATH'] = os.pathsep.join(path_entries)

    plugin_paths = [
        env.get('GZ_SIM_SYSTEM_PLUGIN_PATH', ''),
        env.get('LD_LIBRARY_PATH', ''),
    ]
    env['GZ_SIM_SYSTEM_PLUGIN_PATH'] = os.pathsep.join(
        path for path in plugin_paths if path
    )
    return env


def generate_launch_description():
    package_share = Path(get_package_share_directory('simple_mobile_robot'))
    urdf_path = package_share / 'urdf' / 'simple_mobile_robot.urdf'
    world_path = package_share / 'worlds' / 'empty.sdf'

    gazebo = ExecuteProcess(
        cmd=[
            'env',
            '-i',
            *[f'{key}={value}' for key, value in clean_gazebo_environment().items()],
            'gz',
            'sim',
            '-r',
            '-v',
            '3',
            str(world_path),
        ],
        output='screen',
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name',
            'simple_mobile_robot',
            '-file',
            str(urdf_path),
            '-x',
            '0.0',
            '-y',
            '0.0',
            '-z',
            '0.05',
        ],
        output='screen',
    )

    cmd_vel_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/ultrasonic_scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        output='screen',
    )

    ultrasonic_threshold = Node(
        package='simple_mobile_robot',
        executable='ultrasonic_threshold',
        name='ultrasonic_threshold',
        parameters=[
            {'threshold_distance': 0.5},
            {'scan_topic': '/ultrasonic_scan'},
        ],
        output='screen',
    )

    return LaunchDescription([
        gazebo,
        spawn_robot,
        cmd_vel_bridge,
        ultrasonic_threshold,
    ])
