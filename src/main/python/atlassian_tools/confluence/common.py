import urllib.parse
import requests
import json
import types

class Confluence:
    def __init__(self, url, username, password):
        self._url = url
        self._api_root = f"{self._url}/rest/api"
        self._username = username
        self._password = password
        self._auth = (self._username, self._password)

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value
        self._api_root = f"{self._url}/rest/api"

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

    def get_page(self, space_key, title):
        page_info_url = f"{self._api_root}/content?expand=ancestors,body.storage&spaceKey={space_key}&title=" + urllib.parse.quote(title)
        page_info_res = requests.get(page_info_url, auth=self._auth)
        return json.loads(page_info_res.text)['results'][0]

    def get_attachments(self, space_key="", title="", page_id=0, expand_list="expand=version,container", media_type="mediaType=text/plain"):
        parent_id = 0
        if page_id != 0:
            parent_id = page_id
        else:
            page_info = self.get_page(space_key, title)
            parent_id = page_info['id']
        get_attachments_url = f"{self._api_root}/content/{parent_id}/child/attachment?{media_type}&{expand_list}"
        get_attachments_res = requests.get(get_attachments_url, auth=self._auth)
        get_attachments_json = json.loads(get_attachments_res.text)

        def add_download_url(each_file):
            download_uri = each_file['_links']['download']
            download_full_url = f"{self._url}{download_uri}"
            each_file['download_url'] = download_full_url
            def get_content():
                res = requests.get(download_full_url, auth=self._auth)
                return res.text
            each_file['get_content'] = get_content
            return each_file

        attachments = map(lambda each_file: add_download_url(each_file), get_attachments_json['results'])
        return list(attachments)
