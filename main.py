import argparse
import pandas as pd
import os
from datetime import datetime, timedelta


class RewardEntry:
    def __init__(self, index, date, name):
        self.index = index
        self.date = date
        self.name = name

    def __repr__(self):
        return f"RewardEntry(index={self.index}, date='{self.date}', name='{self.name}')"


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process member information and generate reports.")
    parser.add_argument('-m', '--member_csv', required=True, help='Path to the member.csv file')
    parser.add_argument('-p', '--minimum_score', type=int, required=True, help='Minimum score')
    parser.add_argument('-f', '--fortress_points', type=int, required=True, help='Minimum fortress score')
    parser.add_argument('-o', '--output_dir', required=True, help='Output directory for the generated CSV files')
    parser.add_argument('-n', '--names', nargs='*', required=True, help='List of names separated by spaces')
    return parser.parse_args()


def generate_dates():
    start_date = datetime.now()
    dates = [start_date + timedelta(days=i) for i in range(8)]
    return [date.strftime("%Y-%m-%d ") + date.strftime("%A") for date in dates]


def main():
    args = parse_arguments()
    # 1. 将names按空格拆分，理论上names的数量控制在[1,3]直接
    # 1.1 检查names的长度是否满足，不满足退出
    if len(args.names) < 1 or len(args.names) > 3:
        print("Error: The number of names should be between 1 and 3.")
        return

    # 1.2 设置奖励数组
    reward_entities = []
    dates = generate_dates()
    for index, name in enumerate(args.names):
        for date in dates:
            for _ in range(5):
                reward_entities.append(RewardEntry(index, date, ''))

    reward_entities_index = 0  # 初始化奖励索引

    # 2. 读取成员积分文件
    members = pd.read_csv(args.member_csv)

    # 3. 超过minimum_score的用户，他们这周能获得一份奖励
    eligible_members = members[members['本周考核积分'] >= args.minimum_score]
    if len(eligible_members) == 0:
        print("No members")
        return
    for name in eligible_members['昵称']:
        if reward_entities_index >= len(reward_entities):
            break
        reward_entities[reward_entities_index].name = name
        reward_entities_index += 1

    # 4. 按要塞积分排序
    eligible_members = members[members['要塞积分'] >= args.fortress_points]
    eligible_members = eligible_members.sort_values(by='要塞积分', ascending=False).reset_index(drop=True)

    # 4.1 根据要塞积分排序派发奖励
    eligible_members_index = 0
    while reward_entities_index < len(reward_entities):
        reward_entities[reward_entities_index].name = eligible_members['昵称'][eligible_members_index]
        reward_entities_index += 1
        eligible_members_index = (eligible_members_index + 1) % len(eligible_members)

    # 生成当前日期前缀
    current_date_prefix = datetime.now().strftime("%Y-%m-%d")

    # 生成 member_rewards.csv
    member_rewards = {name: [] for name in members['昵称']}
    for entry in reward_entities:
        member_rewards[entry.name].append(entry.date)

    member_rewards_df = pd.DataFrame.from_dict(member_rewards, orient='index').transpose()
    member_rewards_csv_path = os.path.join(args.output_dir, f"{current_date_prefix}_member_rewards.csv")
    member_rewards_df.to_csv(member_rewards_csv_path, index=False)

    # 生成 rewards_distribution.csv
    rewards_distribution = []
    for date in dates:
        row = [date]
        for name in args.names:
            row.append(','.join([entry.name for entry in reward_entities if entry.date == date and entry.index == args.names.index(name)]))
        rewards_distribution.append(row)

    rewards_distribution_df = pd.DataFrame(rewards_distribution, columns=['日期'] + args.names)
    rewards_distribution_csv_path = os.path.join(args.output_dir, f"{current_date_prefix}_rewards_distribution.csv")
    rewards_distribution_df.to_csv(rewards_distribution_csv_path, index=False)

    print("Reward distribution completed successfully.")


if __name__ == "__main__":
    main()
