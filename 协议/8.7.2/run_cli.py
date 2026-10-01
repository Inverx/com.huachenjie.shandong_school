import argparse
import json
import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cur_dir)

from client import ShanDongClient


def main():
    print("闪动校园 / 室外跑步打卡")
    print()

    parser = argparse.ArgumentParser(description="室外长跑自动化打卡 CLI")
    parser.add_argument("-t", "--type", choices=["free", "sun"], default="free",
                        help="跑步类型: free (自由跑, 默认), sun (阳光跑)")
    parser.add_argument("-d", "--distance", type=int, help="跑步距离 (米，默认 3000)")
    parser.add_argument("-p", "--pace", type=int, default=350, help="平均配速 (秒/公里，默认 350 即 5分50秒/km)")
    parser.add_argument("-m", "--mode", choices=["second_fresh", "heartbeat"], default="second_fresh",
                        help="运行模式: second_fresh (秒级极速即时结算, 默认), heartbeat (真实心跳挂机速率)")
    parser.add_argument("--aim-distance", type=int, help="自由跑设定目标距离 (米)")
    parser.add_argument("--fence-index", type=int, default=0, help="选择打卡围栏索引 (默认 0)")
    parser.add_argument("--token", help="登录 Token")
    parser.add_argument("--satoken", help="SaToken")
    parser.add_argument("--transport", default="direct", choices=["direct", "adb", "proxy"], help="传输模式")
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--adb-path", help="自定义 adb 可执行文件路径")
    args = parser.parse_args()

    distance = args.distance
    if distance is None:
        try:
            d_str = input("跑步距离 (米，默认 3000): ").strip()
            distance = int(d_str) if d_str else 3000
        except (KeyboardInterrupt, EOFError):
            print()
            print("操作已取消")
            return

    if distance <= 0:
        print("错误: 跑步距离必须大于 0")
        return

    client = ShanDongClient(
        token=args.token,
        satoken=args.satoken,
        transport_mode=args.transport,
        proxy=args.proxy,
        adb_path=args.adb_path
    )

    if not client.transport.token:
        print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
        return

    print("正在查询校园电子围栏与打卡规则...")
    print(f"正在生成高拟真轨迹 (目标里程: {distance} 米, 配速: {args.pace//60}分{args.pace%60}秒/km)...")
    print("正在向服务端申请跑步会话...")

    if args.type == "sun":
        if args.mode == "heartbeat":
            print("正在以真实时间心跳模式挂机跑步...")
        else:
            print("正在分批上报 GPS 轨迹切片...")
            print("正在上报打卡桩状态...")
            print("正在计算防篡改校验码并提交打卡结算...")

        res = client.submit_sun_run(
            distance_m=distance,
            avg_pace_sec=args.pace,
            fence_index=args.fence_index,
            mode=args.mode,
            callback=lambda msg: print(f"  -> {msg}")
        )
    else:
        print("正在分批上报 GPS 轨迹切片...")
        print("正在提交自由跑结算...")
        res = client.submit_free_run(
            distance_m=distance,
            avg_pace_sec=args.pace,
            aim_distance=args.aim_distance,
            fence_index=args.fence_index
        )

    if res.get("code") == 0:
        d = res.get("data", {})
        print()
        print("提交成功")
        print(f"跑步记录编号: {d.get('runRecordCode', '-')}")
        print(f"实际打卡里程: {d.get('distance', distance)} 米 ({float(d.get('distance', distance))/1000.0:.2f} km)")
        dur_s = int(d.get("duration", 0))
        print(f"运动总耗时: {dur_s} 秒 ({dur_s//60}分{dur_s%60}秒)")
        print(f"记录总步数: {d.get('steps', 0)} 步")
        print(f"落盘完整轨迹点数: {d.get('poisCount', 0)} 个")
        print()
    else:
        print()
        print("提交失败")
        print(f"错误码: {res.get('code')}")
        print(f"原因: {res.get('message')}")
        if "raw" in res:
            print(f"响应: {json.dumps(res['raw'], ensure_ascii=False)}")
        print()


if __name__ == "__main__":
    main()
