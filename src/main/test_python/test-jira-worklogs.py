import argparse
import datetime
import logging
from atlassian_tools.jira.common import Jira

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-u", dest="username", help="LGE AD Username", required=True)
    arg_parser.add_argument("-p", dest="password", help="LGE AD Password", required=True)
    arg_parser.add_argument("-j", dest="jira_url", help="JIRA Url", required=True)
    args = arg_parser.parse_args()

    user_name = args.username
    password = args.password

    logging.basicConfig(level=logging.INFO)
    # Set jira url
    jira_url = args.jira_url
    hlm_connector_test = Jira(jira_url, user_name, password)
    work_issues = hlm_connector_test.get_today_work_logs()
    total_time_today = 0
    print("")
    for each_issue in work_issues:
        issue_title = each_issue.replace(":", " : ")
        print(f"== {jira_url}browse/{issue_title} ==")
        for log_entity in work_issues[each_issue]:
            time_spent = log_entity['timeSpentSeconds']
            log_comment = log_entity['comment']
            time_spend_formatted = datetime.timedelta(seconds=time_spent)
            print(time_spend_formatted, log_comment)
            total_time_today = total_time_today + time_spent
        print("")
    print("== Total ===")
    print(datetime.timedelta(seconds=total_time_today))
