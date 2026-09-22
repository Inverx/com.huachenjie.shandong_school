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
    print("闪动校园 / 排行榜")
    print()

    parser = argparse.ArgumentParser(description="查询校园跑步排行榜")
    parser.add_argument("-t", "--type", choices=["distance", "progress"], default="distance",
                        help="排行榜类型: distance(30天全校里程榜), progress(达标进度榜)")
    parser.add_argument("-s", "--sex", type=int, choices=[1, 2], default=2,
                        help="性别筛选: 1 为男生榜, 2 为女生榜 (默认 2)")
    parser.add_argument("--token", help="登录 Token")
    parser.add_argument("--satoken", help="SaToken")
    parser.add_argument("--transport", default="direct", choices=["direct", "adb", "proxy"], help="传输模式")
    parser.add_argument("--proxy", help="代理地址")
    args = parser.parse_args()

    client = ShanDongClient(
        token=args.token,
        satoken=args.satoken,
        transport_mode=args.transport,
        proxy=args.proxy
    )

    if not client.transport.token:
        print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
        return

    gender_str = "男生" if args.sex == 1 else "女生"
    print(f"正在查询排行榜 ({gender_str}榜)...")

    if args.type == "distance":
        res = client.get_distance_rank(rank_cycle=30, sex=args.sex)
    else:
        res = client.get_progress_rank(sex=args.sex)

    if res.get("code") == 0:
        data_field = res.get("data", {})
        rank_list = data_field.get("list", []) if isinstance(data_field, dict) else (data_field if isinstance(data_field, list) else [])
        if not rank_list:
            print()
            print("暂无数据")
            print()
            return

        print()
        print(f"查询结果 (前 {min(len(rank_list), 30)} 名)")
        for idx, r in enumerate(rank_list[:30], 1):
            name = r.get("userName") or r.get("nickName") or "匿名学生"
            dist_val = float(r.get("distance") or r.get("totalDistance") or 0)
            dept = r.get("departmentName") or r.get("className") or "校区"
            print(f"  [{idx:02d}] 姓名: {name} | 里程: {dist_val/1000.0:.2f} km | 学院/班级: {dept}")
        print()
    else:
        print()
        print("查询失败")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    main()
