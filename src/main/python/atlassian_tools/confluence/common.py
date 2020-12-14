import urllib.parse
import requests
import json
import types
import logging


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

    def get_attachments(self, space_key="", title="", page_id=0, expand_list="expand=version,container",
                        media_type="mediaType=text/plain"):
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


class ConfluenceManager:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.rpc_root = "/rpc/json-rpc/confluenceservice-v2/"
        self.rpc_path = f"{self.url}{self.rpc_root}"
        self.permissions = ["VIEWSPACE", "EDITSPACE", "EXPORTPAGE", "SETPAGEPERMISSIONS", "REMOVEPAGE", "EDITBLOG",
                            "REMOVEBLOG", "COMMENT", "REMOVECOMMENT", "CREATEATTACHMENT", "REMOVEATTACHMENT",
                            "REMOVEMAIL",
                            "EXPORTSPACE", "SETSPACEPERMISSIONS"]
        logging.warning(f"{self.__class__.__name__}'s instance has been initialized with url = {self.url}")

    def get_space_permissions(self, spaceKey):
        api_url = self.rpc_path + "getSpacePermissionSets"
        res = requests.post(url=api_url, auth=(self.username, self.password), json=[spaceKey])
        if res.status_code == 200:
            return json.loads(res.text)

    def get_assigned_users_from_space(self, spaceKey):
        logging.warning(f"{__name__} is called")
        space_permissions = self.get_space_permissions(spaceKey)
        users = []
        groups = []
        for each_permission in space_permissions:
            space_permissions = each_permission['spacePermissions']
            for each_entity in space_permissions:
                if each_entity['userName']:
                    users.append(each_entity['userName'])
                else:
                    groups.append(each_entity['groupName'])
        users = set(users)
        groups = set(groups)
        return users, groups

    def get_permissions_for_user(self, spaceKey, userName):
        api_url = self.rpc_path + "getPermissionsForUser"
        res = requests.post(url=api_url, auth=(self.username, self.password), json=[spaceKey, userName])
        if res.status_code == 200:
            return json.loads(res.text)

    def remove_entity_from_space(self, entity_name, spaceKey):
        logging.warning(f"{__name__} is called")
        # Permissions https://developer.atlassian.com/server/confluence/remote-confluence-methods/#permissions-1
        # boolean removePermissionFromSpace(String token, String permission, String remoteEntityName, String spaceKey)
        api_url = self.rpc_path + "removePermissionFromSpace"
        logging.warning(f"Remove a entity {entity_name} from space {spaceKey}")
        for permission_name in self.permissions:
            res = requests.post(url=api_url, auth=(self.username, self.password),
                                json=[permission_name, entity_name, spaceKey])
            logging.warning(
                f"Remove a permission {permission_name} for entity {entity_name} from {spaceKey}, with response code "
                f"{res.status_code}")
