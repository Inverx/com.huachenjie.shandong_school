import argparse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
from client import ShanDongClient

def main():
    print("闪动校园 / 模拟跑步打卡\n")
    
    parser = argparse.ArgumentParser(description="闪动校园模拟长跑打卡 CLI")
    parser.add_argument("-d", "--distance", type=int, help="跑步距离 (米，默认 2000)")
    parser.add_argument("-p", "--pace", type=int, default=320, help="平均配速 (秒/公里，默认 320 即 5分20秒/km)")
    args = parser.parse_args()
    
    try:
        distance = args.distance
        if distance is None:
            dist_str = input("跑步距离 (米，默认 2000): ").strip()
            distance = int(dist_str) if dist_str else 2000
        if distance <= 0:
            print("错误: 跑步距离必须大于 0")
            return
            
        client = ShanDongClient(use_adb=True)
        if not client.transport.token:
            print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
            return
            
        print("正在获取校园电子围栏并启动运动学生成引擎...")
        print(f"正在生成高拟真轨迹 (目标里程: {distance} 米, 配速: {args.pace//60}分{args.pace%60}秒/km)...")
        print("正在向服务端申请跑步会话...")
        print("正在分段上报 GPS 轨迹切片...")
        print("正在计算防篡改校验码并提交打卡结算...")
        
        res = client.submit_free_run(distance_m=distance, avg_pace_sec=args.pace)
        
        if res.get("error") == 0:
            d = res.get("data", {})
            print("\n提交成功")
            print(f"跑步记录编号: {d.get('runRecordCode')}")
            print(f"实际打卡里程: {d.get('distance')} 米 ({float(d.get('distance'))/1000:.2f} km)")
            print(f"运动总用时: {d.get('duration')} 秒 ({d.get('duration')//60}分{d.get('duration')%60}秒)")
            print(f"运动总步数: {d.get('steps')} 步")
            print(f"打卡奖励状态: {d.get('reward')}")
        else:
            print("\n提交失败")
            print(f"错误码: {res.get('error')}")
            print(f"原因: {res.get('message')}")
            if "raw" in res:
                print(json.dumps(res["raw"], ensure_ascii=False, indent=2))
    except (KeyboardInterrupt, EOFError):
        print("\n操作已取消")

if __name__ == "__main__":
    main()

