import argparse
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from client import ShanDongClient

def main():
    print("闪动校园 / 跑步排行榜\n")
    
    parser = argparse.ArgumentParser(description="闪动校园排行榜查询")
    parser.add_argument("-t", "--type", choices=["distance", "progress"], default="distance", help="榜单类型 (distance: 30天里程榜, progress: 达标进度榜)")
    parser.add_argument("-s", "--sex", choices=[1, 2], type=int, default=2, help="性别 (1: 男生榜, 2: 女生榜, 默认 2)")
    args = parser.parse_args()
    
    try:
        client = ShanDongClient(use_adb=True)
        if not client.transport.token:
            print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
            return
            
        if args.type == "distance":
            print(f"正在查询 30 天全校里程排行榜 ({'男生' if args.sex==1 else '女生'}榜)...")
            res = client.get_distance_rank(rank_cycle=30, sex=args.sex)
        else:
            print(f"正在查询全校跑步达标进度排行榜 ({'男生' if args.sex==1 else '女生'}榜)...")
            res = client.get_progress_rank(sex=args.sex)
            
        if res.get("code") == 0:
            rank_list = res.get("data", {}).get("list", []) if isinstance(res.get("data"), dict) else (res.get("data") if isinstance(res.get("data"), list) else [])
            if not rank_list:
                print("\n暂无数据")
                return
            print(f"\n查询结果 (前 {len(rank_list)} 名)")
            for i, r in enumerate(rank_list[:20], 1):
                name = r.get("userName") or r.get("nickName") or "匿名学生"
                dist = r.get("distance") or r.get("totalDistance") or 0
                print(f"{i:02d}. 姓名: {name} | 里程: {float(dist)/1000:.2f} km | 所属学院: {r.get('departmentName', '校区')}")
        else:
            print("\n查询失败")
            print(f"错误码: {res.get('code')}")
            print(f"原因: {res.get('message')}")
    except (KeyboardInterrupt, EOFError):
        print("\n操作已取消")

if __name__ == "__main__":
    main()

