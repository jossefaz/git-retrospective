from datetime import timezone
from github import Github
import pandas as pd
from datetime import datetime


def fetch_commit_data(start_date, end_date, repo_name, token, base_url, target_users_email=None, title_keywords=None, main_branch='develop'):
    g = Github(base_url=base_url, login_or_token=token)
    repo = g.get_repo(repo_name)

    start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)

    pulls = repo.get_pulls(state='closed', sort='created', base=main_branch)
    commits_info = []

    for pull in pulls:
        if pull.merged_at and start_date <= pull.merged_at <= end_date:
            if title_keywords and not any(keyword in pull.title for keyword in title_keywords):
                continue
            for commit in pull.get_commits():
                if target_users_email and commit.commit.committer.email not in target_users_email:
                    continue
                commit_date = commit.commit.committer.date.date()
                commits_info.append((commit_date, commit.commit.committer.email))

    return commits_info


def generate_commit_report(start_date, end_date, repo_name, token, base_url, target_users_email=None,
                           title_keywords=None, main_branch='develop'):
    commits_info = fetch_commit_data(start_date, end_date, repo_name, token, base_url, target_users_email,
                                     title_keywords, main_branch)
    df = pd.DataFrame(commits_info, columns=['date', 'contributor'])
    report = df.pivot_table(index='date', columns='contributor', aggfunc='size', fill_value=0)
    report.to_csv('commit_report.csv')


def add_stats(file_path):
    df = pd.read_csv(file_path)
    total_commits = df.sum(numeric_only=True)
    total_commits['date'] = 'Total commits'
    total_worked_days = (df.iloc[:, 1:] > 0).sum()
    total_worked_days['date'] = 'Total worked days'
    totals_df = pd.DataFrame([total_commits, total_worked_days])
    df = pd.concat([df, totals_df], ignore_index=True)
    df.to_csv('commit_report_with_totals.csv', index=False)


if __name__ == '__main__':
    generate_commit_report('2024-01-01', '2024-05-01', 'REPO',
                           'TOKEN',
                           'IF GITHUB.COM NO NEED T SPECIFY THIS IS ONLY FOR ENTERPRISE',
                           target_users_email=['some_user@mail.com'],
                           title_keywords=['SOME TITLE KEY WORD OF THE PR'],
                           main_branch='develop'
                           )
    add_stats('commit_report.csv')
