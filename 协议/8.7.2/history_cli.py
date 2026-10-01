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
    print("闪动校园 / 历史记录")
    print()

    parser = argparse.ArgumentParser(description="查询跑步与运动历史记录")
    parser.add_argument("-t", "--type", choices=["summary", "sun", "free", "indoor"], default="summary",
                        help="查询类型: summary(累计概览), sun(阳光跑记录), free(自由跑记录), indoor(AI运动记录)")
    parser.add_argument("-p", "--page", type=int, default=1, help="分页页码 (默认 1)")
    parser.add_argument("-s", "--page-size", type=int, default=10, help="每页条数 (默认 10)")
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

    print("正在查询历史记录...")

    if args.type == "summary":
        res = client.get_run_summary(sport_type=2, time_type=3)
        if res.get("code") == 0:
            d = res.get("data", {})
            total_dist = float(d.get("totalDistance", 0))
            total_dur = int(d.get("totalDuration", 0))
            print()
            print("查询结果")
            print(f"累计总里程: {total_dist / 1000.0:.2f} 公里 ({int(total_dist)} 米)")
            print(f"累计总运动耗时: {total_dur // 60} 分钟 ({total_dur} 秒)")
            print(f"累计消耗热量: {d.get('totalCalorie', 0)} 卡路里")
            print(f"打卡达标天数: {d.get('checkDays', 0)} 天")
            print(f"个人最佳配速: {d.get('bestPace', 0)} 秒/公里")
            print()
        else:
            print()
            print("查询失败")
            print(json.dumps(res, ensure_ascii=False, indent=2))
            print()

    elif args.type == "sun":
        res = client.get_sun_run_records(page_num=args.page, page_size=args.page_size)
        if res.get("code") == 0:
            d = res.get("data", {})
            records = d.get("list", [])
            total = d.get("total", len(records))
            if not records:
                print()
                print("暂无数据")
                print()
                return

            print()
            print(f"查询结果 (共 {total} 条阳光跑记录，当前第 {args.page} 页)")
            for i, r in enumerate(records, 1):
                dist_m = float(r.get("distance", 0))
                dur_s = int(r.get("duration", 0))
                flag_text = "达标" if r.get("qualifiedFlag") else "未达标"
                print(f"  [{i:02d}] {r.get('createTime', '-')} | 里程: {dist_m/1000.0:.2f} km | 用时: {dur_s//60}分{dur_s%60}秒 | 配速: {r.get('pace', '-')} | 状态: {flag_text}")
            print()
        else:
            print()
            print("查询失败")
            print(json.dumps(res, ensure_ascii=False, indent=2))
            print()

    elif args.type == "free":
        res = client.get_free_run_records(page_num=args.page, page_size=args.page_size)
        if res.get("code") == 0:
            d = res.get("data", {})
            records = d.get("list", [])
            total = d.get("total", len(records))
            if not records:
                print()
                print("暂无数据")
                print()
                return

            print()
            print(f"查询结果 (共 {total} 条自由跑记录，当前第 {args.page} 页)")
            for i, r in enumerate(records, 1):
                dist_m = float(r.get("distance", 0))
                dur_s = int(r.get("duration", 0))
                print(f"  [{i:02d}] {r.get('createTime', '-')} | 里程: {dist_m/1000.0:.2f} km | 用时: {dur_s//60}分{dur_s%60}秒 | 步数: {r.get('totalStep', 0)} 步")
            print()
        else:
            print()
            print("查询失败")
            print(json.dumps(res, ensure_ascii=False, indent=2))
            print()

    elif args.type == "indoor":
        res = client.get_indoor_sports_page(sport_type=1, page_num=args.page, page_size=args.page_size)
        if res.get("code") == 0:
            d = res.get("data", {})
            records = d.get("list", [])
            total = d.get("total", len(records))
            if not records:
                print()
                print("暂无数据")
                print()
                return

            print()
            print(f"查询结果 (共 {total} 条 AI 室内运动记录)")
            for i, r in enumerate(records, 1):
                dur_s = int(r.get("duration", 0))
                print(f"  [{i:02d}] {r.get('createTime', '-')} | 项目: {r.get('sportName', '室内运动')} | 动作数: {r.get('count', 0)} 次 | 耗时: {dur_s} 秒")
            print()
        else:
            print()
            print("查询失败")
            print(json.dumps(res, ensure_ascii=False, indent=2))
            print()


if __name__ == "__main__":
    main()
