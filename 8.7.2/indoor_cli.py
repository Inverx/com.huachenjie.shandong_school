import argparse
import json
import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cur_dir)

from client import ShanDongClient

SPORTS_MAPPING = {
    1: "深蹲",
    2: "开合跳",
    3: "跳绳",
    4: "高抬腿",
    5: "俯卧撑",
    6: "平板支撑",
    7: "下蹲开合跳",
    8: "水平开合跳",
    9: "深蹲跳",
    10: "仰卧起坐",
    11: "波比跳",
    12: "卷腹",
    13: "坐位体前屈"
}


def main():
    print("闪动校园 / 室内 AI 运动")
    print()

    parser = argparse.ArgumentParser(description="室内 AI 运动项目打卡 CLI")
    parser.add_argument("-s", "--sport-type", type=int, default=1, help="运动动作类型编号 (默认 1 为深蹲)")
    parser.add_argument("-c", "--count", type=int, default=30, help="完成动作次数 (默认 30)")
    parser.add_argument("-d", "--duration", type=int, default=60, help="锻炼时长 (秒，默认 60)")
    parser.add_argument("--list-types", action="store_true", help="列出所有支持的运动项目编号")
    parser.add_argument("--token", help="登录 Token")
    parser.add_argument("--satoken", help="SaToken")
    parser.add_argument("--transport", default="direct", choices=["direct", "adb", "proxy"], help="传输模式")
    parser.add_argument("--proxy", help="代理地址")
    args = parser.parse_args()

    if args.list_types:
        print("支持的 AI 室内运动项目编号:")
        for k, v in SPORTS_MAPPING.items():
            print(f"  [{k:02d}] {v}")
        print()
        return

    client = ShanDongClient(
        token=args.token,
        satoken=args.satoken,
        transport_mode=args.transport,
        proxy=args.proxy
    )

    if not client.transport.token:
        print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
        return

    sport_name = SPORTS_MAPPING.get(args.sport_type, f"动作{args.sport_type}")
    print(f"正在准备【{sport_name}】打卡 (目标次数: {args.count} 次, 用时: {args.duration} 秒)...")
    print("正在获取运动项目配置...")
    print("正在提交运动打卡结算...")

    res = client.submit_indoor_exercise(
        sport_type=args.sport_type,
        total_count=args.count,
        duration=args.duration
    )

    if res.get("code") == 0:
        d = res.get("data", {})
        print()
        print("提交成功")
        print(f"运动记录编号: {d.get('sportsRecordCode', '-')}")
        print(f"运动项目: {sport_name}")
        print(f"完成次数: {d.get('total', args.count)} 次")
        print(f"锻炼耗时: {d.get('duration', args.duration)} 秒")
        print(f"获得能量值: {d.get('energy', 0)} 点")
        print(f"消耗卡路里: {d.get('calorie', 0)} 卡")
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
