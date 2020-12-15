import requests
import json
import types
import logging
from urllib.parse import quote
import pytz
import datetime


class Jira:
    def __init__(self, url, username, password):
        self._url = url
        self._api_root = f"{self._url}rest/api/2/"
        self._username = username
        self._password = password
        self._auth = (self._username, self._password)

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

    def get_today_work_logs(self, user_name=None):
        if user_name is None:
            queried_user = self._username
        else:
            queried_user = user_name
        query_string = f"worklogDate = startOfDay() and worklogAuthor = '{queried_user}'"
        query_str_converted = quote(query_string)
        api_path = "search?jql=" + query_str_converted
        query_url = f"{self._api_root}{api_path}"
        logging.info("Get a list of issues that has worklogs today")
        r = requests.get(query_url, auth=(self._username, self._password))
        issues = json.loads(r.text)['issues']
        date_time_format_with_tz = "%Y-%m-%dT%H:%M:%S.%f%z"
        date_time_format_wo_tz = "%Y-%m-%d %H:%M:%S"
        current_tz = pytz.timezone("Asia/Seoul")

        today_start_str = f"{str(datetime.date.today())} 00:00:00"
        today_start_obj = datetime.datetime.strptime(today_start_str, date_time_format_wo_tz)
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
                start_date_obj = datetime.datetime.strptime(started_date, date_time_format_with_tz)
                if start_date_obj > today_start_obj_with_tz:
                    if work_log_key not in work_logs_returned:
                        work_logs_returned[work_log_key] = []
                    work_logs_returned[work_log_key].append(work_log)
        return work_logs_returned

