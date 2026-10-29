# Simple Mobile Robot

This workspace contains a ROS 2 differential drive robot that is visualized in RViz and controlled from `teleop_twist_keyboard`.

The package includes:

- A URDF robot model with a base, two driven wheels, and a front caster.
- A front-facing ultrasonic-style range sensor simulated with a single-beam Gazebo lidar.
- A Python simulator node that subscribes to `/cmd_vel`.
- Published `/odom`, `/tf`, and `/joint_states` so the robot moves in RViz.
- A launch file that starts RViz, `robot_state_publisher`, and the simulator.

## Student Quick Start

Requires Ubuntu 24.04 with ROS 2 Jazzy installed.

```bash
sudo apt update
sudo apt install git python3-colcon-common-extensions ros-jazzy-teleop-twist-keyboard ros-jazzy-robot-state-publisher ros-jazzy-rviz2 ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge
source /opt/ros/jazzy/setup.bash
git clone https://github.com/MaazHussain2711/simple-mobile-robot.git
cd simple-mobile-robot
colcon build --symlink-install
source install/setup.bash
ros2 launch simple_mobile_robot display.launch.py
```

In a second terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Keep the second terminal focused. Use `i` forward, `,` backward, `j` left,
`l` right, and `k` stop. Close the RViz demo before running the Gazebo demo below.

## Folder Layout

```
SIMPLE_MOBILE_ROBOT/
├── README.md
└── src/
    └── simple_mobile_robot/
        ├── launch/
        │   └── display.launch.py
        ├── rviz/
        │   └── simple_mobile_robot.rviz
        ├── simple_mobile_robot/
        │   ├── __init__.py
        │   └── diff_drive_sim.py
        ├── urdf/
        │   └── simple_mobile_robot.urdf
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```

## Install Required ROS 2 Packages

Source ROS 2 first. Replace `jazzy` with your ROS 2 distro if needed.

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install ros-jazzy-teleop-twist-keyboard ros-jazzy-robot-state-publisher ros-jazzy-rviz2 ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge
```

## Build

From the workspace root:

```bash
cd ~/simple-mobile-robot
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
```

## Run the Robot in RViz

Terminal 1:

```bash
cd ~/simple-mobile-robot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch simple_mobile_robot display.launch.py
```

RViz opens with the robot spawned at the `odom` frame.

## Control with Teleop Keyboard

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Keep the teleop terminal focused and use the keys printed by teleop. The main movement keys are `i` for forward, `,` for backward, `j` for left turn, `l` for right turn, and `k` for stop. Arrow keys do not control this teleop node.

The simulator subscribes to `/cmd_vel`, updates odometry, publishes wheel joint states, and RViz shows the robot moving. The simulator terminal also prints every new `/cmd_vel` command it receives.

If RViz does not open from a VS Code Snap terminal, run the launch command from a normal system terminal. Snap terminals can inject runtime environment variables that make RViz load incompatible Snap libraries.

## Run the Robot in Gazebo

Terminal 1:

```bash
cd ~/simple-mobile-robot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch simple_mobile_robot gazebo.launch.py
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Use `i`, `,`, `j`, `l`, and `k` in the teleop terminal. In Gazebo, the robot is moved by Gazebo's DiffDrive system plugin. The launch file bridges ROS `/cmd_vel` into Gazebo.

The ultrasonic-style sensor publishes a single forward range beam as a ROS `LaserScan`:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 topic echo /ultrasonic_scan
```

The measured distance is in:

```text
ranges[2]
```

The sensor publishes five narrow forward beams. The middle beam is `ranges[2]`.

The Gazebo launch also starts an ultrasonic threshold node. By default, anything at or below `0.5 m` is considered an obstacle.

Check the processed distance:

```bash
ros2 topic echo /ultrasonic_distance
```

Check the threshold result:

```bash
ros2 topic echo /ultrasonic_obstacle
```

The threshold node publishes:

- `/ultrasonic_distance`: selected distance in meters
- `/ultrasonic_obstacle`: `true` when the distance is less than or equal to the threshold

Run the threshold node manually with a different threshold:

```bash
ros2 run simple_mobile_robot ultrasonic_threshold --ros-args -p threshold_distance:=0.75
```

## Make It From Scratch

These are the commands and files needed to recreate this project manually.

1. Create a ROS 2 workspace and package:

```bash
mkdir -p ~/simple_mobile_robot_ws/src
cd ~/simple_mobile_robot_ws/src
ros2 pkg create simple_mobile_robot --build-type ament_python --dependencies rclpy geometry_msgs nav_msgs sensor_msgs tf2_ros robot_state_publisher rviz2
```

2. Add folders for the robot description, launch file, and RViz config:

```bash
cd ~/simple_mobile_robot_ws/src/simple_mobile_robot
mkdir -p launch urdf rviz
```

3. Create `urdf/simple_mobile_robot.urdf`.

The URDF needs:

- `base_footprint`: ground reference frame.
- `base_link`: main robot body.
- `left_wheel_link` and `right_wheel_link`: wheel visuals.
- `left_wheel_joint` and `right_wheel_joint`: continuous joints with axis `0 1 0`.
- `front_caster_link`: fixed support wheel.
- `ultrasonic_link`: front range sensor link.

4. Create a Python node in `simple_mobile_robot/diff_drive_sim.py`.

The node should:

- Subscribe to `geometry_msgs/msg/Twist` on `/cmd_vel`.
- Integrate linear velocity `x` and angular velocity `z`.
- Publish `nav_msgs/msg/Odometry` on `/odom`.
- Broadcast the `odom -> base_footprint` transform.
- Publish `sensor_msgs/msg/JointState` for both wheel joints.

5. Update `setup.py`.

Install the launch, URDF, and RViz files:

```python
(os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
(os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
(os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
```

Add the simulator executable:

```python
'diff_drive_sim = simple_mobile_robot.diff_drive_sim:main',
```

6. Create `launch/display.launch.py`.

Launch these nodes:

- `robot_state_publisher` with the URDF loaded as `robot_description`.
- `simple_mobile_robot diff_drive_sim`.
- `rviz2` with the RViz config.

7. Build and run:

```bash
cd ~/simple_mobile_robot_ws
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
ros2 launch simple_mobile_robot display.launch.py
```

8. Start keyboard control:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Useful Checks

```bash
ros2 topic list
ros2 topic echo /cmd_vel
ros2 topic echo /odom
ros2 topic echo /ultrasonic_scan
ros2 topic echo /ultrasonic_distance
ros2 topic echo /ultrasonic_obstacle
ros2 run tf2_tools view_frames
```

If the robot does not move, open a third terminal and run:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic echo /cmd_vel
```

Press `i` in the teleop terminal. If `/cmd_vel` does not print a message, the teleop terminal is not receiving your key presses or it is running in a different ROS domain.

If `/ultrasonic_scan` appears but does not print data, check whether Gazebo is publishing the sensor topic:

```bash
gz topic -l | grep ultrasonic
gz topic -e -t /ultrasonic_scan
```

If Gazebo has no `/ultrasonic_scan` topic, confirm that Gazebo launched the packaged world file and that the log does not contain sensor plugin or render engine errors. The world must include `gz-sim-sensors-system`.




MODIFIED:
1. gazebo.launch.py
- cmd_vel_bridge node
2.  simple_mobile_robot.urdf
- ultrasonic link
3. Created empty.sdf
