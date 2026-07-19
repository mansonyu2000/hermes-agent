#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU使用率监控脚本
通过SSH连接到远程服务器，定期获取nvidia-smi输出并记录GPU使用率变化
"""

import subprocess
import time
import re
import sys
import argparse
from datetime import datetime


def get_gpu_usage_via_ssh(hostname, username=None, interval=1, duration=60):
    """
    通过SSH获取远程服务器的GPU使用率
    
    Args:
        hostname: 远程服务器地址（如 wuserver）
        username: 用户名（可选，如果需要指定用户名）
        interval: 采样间隔（秒）
        duration: 监控总时长（秒）
    """
    # 构建SSH命令
    if username:
        ssh_target = f"{username}@{hostname}"
    else:
        ssh_target = hostname
    
    ssh_cmd = ["ssh", ssh_target, "nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"]
    
    print(f"开始监控 {hostname} 的GPU使用率...")
    print(f"采样间隔: {interval}秒, 总时长: {duration}秒")
    print("-" * 50)
    print("时间戳\t\t\tGPU使用率(%)")
    print("-" * 50)
    
    start_time = time.time()
    usage_data = []
    
    try:
        while time.time() - start_time < duration:
            try:
                # 执行SSH命令获取GPU使用率
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # 解析输出，提取GPU使用率
                    output = result.stdout.strip()
                    if output:
                        # 可能有多个GPU，取第一个或处理所有
                        gpu_usages = [int(x.strip()) for x in output.split('\n') if x.strip().isdigit()]
                        if gpu_usages:
                            current_usage = gpu_usages[0]  # 取第一个GPU的使用率
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print(f"{timestamp}\t{current_usage}%")
                            usage_data.append((timestamp, current_usage))
                        else:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print(f"{timestamp}\t无法解析GPU使用率")
                            usage_data.append((timestamp, None))
                    else:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"{timestamp}\t无输出")
                        usage_data.append((timestamp, None))
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{timestamp}\tSSH命令执行失败: {result.stderr}")
                    usage_data.append((timestamp, None))
                    
            except subprocess.TimeoutExpired:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{timestamp}\tSSH命令超时")
                usage_data.append((timestamp, None))
            except Exception as e:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{timestamp}\t错误: {str(e)}")
                usage_data.append((timestamp, None))
            
            # 等待下一个采样周期
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n用户中断监控...")
    
    return usage_data


def plot_usage_data(usage_data):
    """
    简单的文本形式显示使用率趋势（可选的可视化）
    """
    if not usage_data:
        return
        
    print("\n" + "="*60)
    print("GPU使用率变化趋势摘要:")
    print("="*60)
    
    valid_usages = [usage for _, usage in usage_data if usage is not None]
    if valid_usages:
        avg_usage = sum(valid_usages) / len(valid_usages)
        max_usage = max(valid_usages)
        min_usage = min(valid_usages)
        
        print(f"平均使用率: {avg_usage:.1f}%")
        print(f"最高使用率: {max_usage}%")
        print(f"最低使用率: {min_usage}%")
        print(f"有效采样点: {len(valid_usages)}/{len(usage_data)}")
    else:
        print("没有有效的使用率数据")


def main():
    parser = argparse.ArgumentParser(description='监控远程服务器GPU使用率')
    parser.add_argument('hostname', help='远程服务器主机名或IP地址')
    parser.add_argument('-u', '--username', help='SSH用户名（可选）')
    parser.add_argument('-i', '--interval', type=int, default=1, help='采样间隔（秒），默认1秒')
    parser.add_argument('-d', '--duration', type=int, default=60, help='监控时长（秒），默认60秒')
    
    args = parser.parse_args()
    
    # 执行监控
    usage_data = get_gpu_usage_via_ssh(
        hostname=args.hostname,
        username=args.username,
        interval=args.interval,
        duration=args.duration
    )
    
    # 显示统计信息
    plot_usage_data(usage_data)


if __name__ == "__main__":
    main()