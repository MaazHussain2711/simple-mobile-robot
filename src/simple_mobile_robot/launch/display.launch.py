import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def clean_rviz_environment():
    passthrough_keys = [
        'AMENT_PREFIX_PATH',
        'CMAKE_PREFIX_PATH',
        'COLCON_PREFIX_PATH',
        'DBUS_SESSION_BUS_ADDRESS',
        'DISPLAY',
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
    return env


def generate_launch_description():
    package_share = Path(get_package_share_directory('simple_mobile_robot'))
    urdf_path = package_share / 'urdf' / 'simple_mobile_robot.urdf'
    rviz_config_path = package_share / 'rviz' / 'simple_mobile_robot.rviz'

    robot_description = urdf_path.read_text()
    use_sim_time = LaunchConfiguration('use_sim_time')

    rviz_environment = clean_rviz_environment()

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true.',
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[
                {'robot_description': robot_description},
                {'use_sim_time': use_sim_time},
            ],
            output='screen',
        ),
        Node(
            package='simple_mobile_robot',
            executable='diff_drive_sim',
            name='diff_drive_sim',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),
        ExecuteProcess(
            cmd=[
                'env',
                '-i',
                *[f'{key}={value}' for key, value in rviz_environment.items()],
                'rviz2',
                '-d',
                str(rviz_config_path),
            ],
            output='screen',
        ),
    ])
