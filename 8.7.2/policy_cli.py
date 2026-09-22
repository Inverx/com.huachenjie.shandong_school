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
    print("闪动校园 / 跑步规则与校园围栏")
    print()

    parser = argparse.ArgumentParser(description="查询学期跑步计划、考核要求与校园围栏")
    parser.add_argument("-s", "--school-code", help="学校编号")
    parser.add_argument("-t", "--token", help="登录 Token")
    parser.add_argument("--satoken", help="SaToken")
    parser.add_argument("--transport", default="direct", choices=["direct", "adb", "proxy"], help="传输模式")
    parser.add_argument("--proxy", help="代理地址")
    args = parser.parse_args()

    client = ShanDongClient(
        token=args.token,
        satoken=args.satoken,
        school_code=args.school_code,
        transport_mode=args.transport,
        proxy=args.proxy
    )

    if not client.transport.token:
        print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
        return

    print("正在查询校园电子围栏与考核规则...")
    plans = client.get_run_plans()
    fences = client.get_school_fences(args.school_code)

    plan_code = plans[0].get("runPlanCode", "") if plans else ""
    rules_res = client.query_sunrun_rule(run_plan_code=plan_code)

    print()
    print("查询结果")

    if plans:
        p = plans[0]
        print(f"学期计划: {p.get('runPlanName', '当前跑步计划')} (计划编号: {p.get('runPlanCode', '-')})")
    else:
        print("学期计划: 暂无活跃跑步计划")

    if rules_res.get("code") == 0:
        d = rules_res.get("data", {})
        rule = d.get("schoolDemandRule", {})
        done = d.get("studentDoneRuleInfo", {})
        print()
        print("考核标准")
        print(f"单次里程要求: {rule.get('singleMinDistance', 0)} 米 ~ {rule.get('singleMaxDistance', 0)} 米")
        print(f"有效配速范围: {rule.get('maxPace', 0)} 秒 ~ {rule.get('minPace', 0)} 秒 /公里")
        print(f"单日有效上限: {rule.get('dayMaxDistance', 0)} 米")
        print(f"学期目标总里程: {rule.get('totalDistance', 0)} 米")
        print()
        print("个人完成进度")
        pct = float(done.get("completionRate", 0)) * 100
        print(f"已完成里程: {d.get('doneDistance', 0)} 米 / {rule.get('totalDistance', 0)} 米 (完成率: {pct:.1f}%)")

    if fences:
        print()
        print(f"校区围栏列表 (共 {len(fences)} 处打卡区域)")
        for idx, f in enumerate(fences, 1):
            p_cnt = len(f.get("fenceList", []))
            status_text = "开放中" if f.get("openStatus") else "未开放"
            print(f"  [{idx}] {f.get('fenceName', '校区围栏')} | 必经打卡点: {f.get('requiredPointCounts', 0)} 个 | 边界顶点数: {p_cnt} | 状态: {status_text}")
    else:
        print()
        print("校区围栏: 暂无可用围栏数据")

    print()


if __name__ == "__main__":
    main()
