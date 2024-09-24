import rospy
import subprocess
import time
import os
import multiprocessing
from flask import Flask, jsonify, request

app = Flask(__name__)

# 定义设备信息
devices = {
    "d455": {
        "topics": [
            "/d455/infra1/image_rect_raw",
            "/d455/infra2/image_rect_raw",
            "/d455/depth/image_rect_raw"
        ],
        "launch_command": "roslaunch realsense2_camera rs_camera.launch camera:=d455 serial_no:=318122301402 enable_color:=true enable_depth:=true enable_infra1:=true enable_infra2:=true"
    },
    "t265": {
        "topics": [
            "/t265/fisheye1/image_raw",
            "/t265/fisheye2/image_raw"
        ],
        "launch_command": "roslaunch realsense2_camera rs_t265.launch camera:=t265 serial_no:=952322110920 enable_fisheye1:=true enable_fisheye2:=true enable_odom:=true enable_pose:=true"
    },
    "ouster": {
        "topics": [
            "/ouster/points"
        ],
        "launch_command": "roslaunch ouster_ros sensor.launch sensor_hostname:=os-122101000009.local use_ros_time:=true"
    },
    "device4": {
        "topics": [
            "/fisheye/bleft/image_raw/compressed",
            "/fisheye/bright/image_raw/compressed",
            "/fisheye/left/image_raw/compressed",
            "/fisheye/right/image_raw/compressed"
        ],
        "launch_command": """adb shell 'bash -c "source /opt/ros/noetic/setup.bash && export ROS_IP=10.42.0.2 && roslaunch seeker_cam_bridge test_4cam.launch"'""",
        "ros_master_uri": "http://10.42.0.2:11311"  # 设备4的ROS Master URI
    }
}

# 检查话题是否存在
def topic_exists(topic, ros_master_uri=None):
    try:
        if ros_master_uri:
            # 使用指定的ROS_MASTER_URI和rostopic list | grep来检查话题
            env = os.environ.copy()
            env['ROS_MASTER_URI'] = ros_master_uri
            result = subprocess.run(
                f"rostopic list | grep {topic}",
                shell=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                return True
            else:
                return False
        else:
            # 使用默认的ROS_MASTER_URI来检查话题
            topic_list = rospy.get_published_topics()
            for t in topic_list:
                if t[0] == topic:
                    return True
            return False
    except Exception as e:
        rospy.logwarn(f"Error checking topic {topic}: {str(e)}")
        return False

# 重新启动设备
def restart_device(device_name):
    command = devices[device_name]['launch_command']
    rospy.logwarn(f"Restarting {device_name} with command: {command}")
    subprocess.Popen(command, shell=True)
    time.sleep(10)  # 等待设备重新启动稳定

# 检查所有设备的状态
def check_devices():
    rospy.init_node('device_monitor', anonymous=True)
    rospy.loginfo("Starting to check devices...")
    while not rospy.is_shutdown():
        for device_name, device_info in devices.items():
            for topic in device_info['topics']:
                ros_master_uri = device_info.get('ros_master_uri', None)
                if not topic_exists(topic, ros_master_uri):
                    rospy.logwarn(f"Topic {topic} for device {device_name} not found. Attempting to restart device.")
                    restart_device(device_name)
        time.sleep(30)  # 每隔30秒检查一次

# 启动Flask服务的函数
def start_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # 启动设备监控进程
    monitor_process = multiprocessing.Process(target=check_devices)
    monitor_process.start()

    # 启动Flask服务
    start_flask()
