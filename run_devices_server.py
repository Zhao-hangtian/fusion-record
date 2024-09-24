import logging
from flask import Flask, jsonify, request
import subprocess
import os
import multiprocessing
from datetime import datetime
from run_devices_monitor import devices

app = Flask(__name__)

# 设置日志配置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("recording.log"),
                        logging.StreamHandler()
                    ])

# 录制函数
def record_bag(device_name, topics, ros_master_uri):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = 'tmp'
    bag_filename = f"{folder}/{device_name}_{timestamp}.bag"  # 以设备名称命名 bag 文件
    topic_string = ' '.join(topics)

    # 设置独立的环境变量
    env = os.environ.copy()
    env['ROS_MASTER_URI'] = ros_master_uri

    # 使用 --duration 参数控制录制时间
    command = f"rosbag record -O {bag_filename} {topic_string} --duration=10"
    logging.info(f"开始录制设备 {device_name} 的 bag 文件: {bag_filename}，ROS_MASTER_URI: {ros_master_uri}，话题: {topic_string}")

    # 启动录制进程
    process = subprocess.Popen(command, shell=True, env=env)
    logging.info(f"录制进程 {process.pid} 已启动，设备: {device_name}，bag 文件: {bag_filename}")
    process.wait()  # 等待录制完成
    logging.info(f"录制完成: {bag_filename}")

# 录制请求处理器
@app.route('/record', methods=['POST'])
def record():
    # 启动多个进程录制 bag 文件
    processes = []
    for device_name, device_info in devices.items():
        p = multiprocessing.Process(target=record_bag, args=(device_name, device_info['topics'], device_info.get('ros_master_uri', 'http://127.0.0.1:11311') ))
        p.start()
        processes.append(p)
        logging.info(f"启动设备 {device_name} 的录制进程，ROS_MASTER_URI: {device_info.get('ros_master_uri', 'http://10.42.0.2:11311')}")

    return jsonify({"status": "recording started"}), 200

# 启动 Flask 服务的函数
def start_flask():
    app.run(host='0.0.0.0', port=6000)

if __name__ == "__main__":
    # 启动 Flask 服务
    start_flask()
