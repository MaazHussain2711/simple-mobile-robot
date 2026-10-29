import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'simple_mobile_robot'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rafael',
    maintainer_email='rafael@example.com',
    description='A simple differential drive robot controlled with teleop_twist_keyboard and visualized in RViz.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'diff_drive_sim = simple_mobile_robot.diff_drive_sim:main',
            'ultrasonic_threshold = simple_mobile_robot.ultrasonic_threshold:main',
        ],
    },
)
