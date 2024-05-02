import pandas as pd
from github import Github
from datetime import datetime, timezone


class CommitReportGenerator:
    def __init__(self, token, base_url, repo_name, main_branch='develop'):
        self.github = Github(base_url=base_url, login_or_token=token)
        self.repo = self.github.get_repo(repo_name)
        self.main_branch = main_branch

    def _fetch_commit_data(self, start_date, end_date, target_users_email=None, title_keywords=None):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)

        pulls = self.repo.get_pulls(state='closed', sort='created', base=self.main_branch)
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

    def generate_commit_report(self, start_date, end_date, target_users_email=None, title_keywords=None,
                               output_file='commit_report.csv'):
        commits_info = self._fetch_commit_data(start_date, end_date, target_users_email, title_keywords)
        df = pd.DataFrame(commits_info, columns=['date', 'contributor'])
        report = df.pivot_table(index='date', columns='contributor', aggfunc='size', fill_value=0)

        total_commits = report.sum(numeric_only=True)
        total_commits['date'] = 'Total commits'
        total_worked_days = (report.iloc[:, :] > 0).sum()
        total_worked_days['date'] = 'Total worked days'
        totals_df = pd.DataFrame([total_commits, total_worked_days])

        final_df = pd.concat([report.reset_index(), totals_df], ignore_index=True)
        final_df.to_csv(output_file, index=False)



if __name__ == '__main__':
    generator = CommitReportGenerator(
        token='TOKEN',
        base_url='IF GIT ENTERPRISE PUT HOST HERE',
        repo_name='TARGET REPO'
    )
    generator.generate_commit_report(
        start_date='2024-01-01',
        end_date='2024-05-01',
        target_users_email=['some_user@mail.com'],
        title_keywords=['some keywords to filter PR titles'],
        output_file='output.csv'
    )
