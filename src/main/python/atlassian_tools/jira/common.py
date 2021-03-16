import requests
import json
import types
import logging
from urllib.parse import quote
import pytz
from datetime import date, datetime, timedelta

class Jira:
    def __init__(self, url, username, password):
        self._url = url
        self._api_root = f"{self._url}rest/api/2/"
        self._search_root = f"{self._api_root}search"
        self._username = username
        self._password = password
        self._auth = (self._username, self._password)
        self._jira_datetime_format = "%Y-%m-%dT%X.%f%z"

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value
        self._api_root = f"{self._url}rest/api/2/"

    @property
    def api_root(self):
        return self._api_root

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = value

    def get_work_logs(self, user_name=None, work_log_date='startOfDay()'):
        if user_name is None:
            queried_user = self._username
        else:
            queried_user = user_name
        query_string = f"worklogDate = {work_log_date} and worklogAuthor = '{queried_user}'"
        query_str_converted = quote(query_string)
        api_path = "search?jql=" + query_str_converted
        query_url = f"{self._api_root}{api_path}"
        logging.info("Get a list of issues that has worklogs today")
        r = requests.get(query_url, auth=(self._username, self._password))
        issues = json.loads(r.text)['issues']
        date_time_format_with_tz = "%Y-%m-%dT%H:%M:%S.%f%z"
        date_time_format_wo_tz = "%Y-%m-%d %H:%M:%S"
        current_tz = pytz.timezone("Asia/Seoul")

        today_start_str = f"{str(date.today())} 00:00:00"
        today_start_obj = datetime.strptime(today_start_str, date_time_format_wo_tz)
        today_start_obj_with_tz = current_tz.localize(today_start_obj)

        work_logs_returned = {}
        for each_issue in issues:
            issue_key = each_issue['key']
            issue_summary = each_issue['fields']['summary']
            work_log_key = f"{issue_key}:{issue_summary}"
            logging.warning(f"Get work logs for an issue = {each_issue['key']}")
            get_issue_worklog_url = f"{self._api_root}issue/{each_issue['key']}/worklog"
            r = requests.get(get_issue_worklog_url, auth=(self._username, self._password))
            r_body = json.loads(r.text)
            work_logs = r_body['worklogs']
            for work_log in work_logs:
                started_date = work_log['started']
                start_date_obj = datetime.strptime(started_date, date_time_format_with_tz)
                if start_date_obj > today_start_obj_with_tz:
                    if work_log_key not in work_logs_returned:
                        work_logs_returned[work_log_key] = []
                    work_logs_returned[work_log_key].append(work_log)
        return work_logs_returned

    def get_today_work_logs(self, user_name=None):
        return self.get_work_logs(user_name=user_name)

    def run_jql_query(self, query_statement):
        jql_query = {"jql": query_statement}
        query_req = requests.post(self._search_root, auth=self._auth, json=jql_query)
        query_res = json.loads(query_req.text)
        return query_res

    def get_issue_info(self, key):
        get_issue_info_url = f"{self._api_root}issue/{key}"
        r = requests.get(get_issue_info_url, auth=self._auth)
        issue_info = json.loads(r.text)
        return issue_info

    def get_issue_work_logs_within_two_weeks(self, issue_key):
        output = []
        today = datetime.now().astimezone()
        pre_week_start = today - timedelta(weeks=1, days=today.weekday())
        worklog_url = f"{self._api_root}issue/{issue_key}/worklog"
        r = requests.get(worklog_url, auth=self._auth)
        work_logs = json.loads(r.text)['worklogs']
        time_spent_seconds = 0
        for each_work_log in work_logs:
            worklog_start = each_work_log['started']
            worklog_start_obj = datetime.strptime(worklog_start, self._jira_datetime_format)
            if worklog_start_obj > pre_week_start:
                time_spent_seconds = time_spent_seconds + each_work_log['timeSpentSeconds']
                output.append(each_work_log)
        total_time_spent = timedelta(seconds=time_spent_seconds)
        return {"workLogs": output, "timeSpent": total_time_spent}

