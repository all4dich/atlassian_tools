import urllib.parse
import requests
from requests.auth import HTTPBasicAuth
import json
import types
import logging
from urllib.parse import quote


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
        page_info_url = f"{self._api_root}/content?expand=ancestors,body.storage&spaceKey={space_key}&title=" + urllib.parse.quote(
            title)
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
    _rest_api_path: str

    def __init__(self, url, username, password):
        self._url = url
        self._rest_api_path = f"{self._url}/rest/api"
        self._username = username
        self._password = password
        self._auth = (username, password)
        self.rpc_root = "/rpc/json-rpc/confluenceservice-v2/"
        self.rpc_path = f"{self._url}{self.rpc_root}"
        self.permissions = ["VIEWSPACE", "EDITSPACE", "EXPORTPAGE", "SETPAGEPERMISSIONS", "REMOVEPAGE", "EDITBLOG",
                            "REMOVEBLOG", "COMMENT", "REMOVECOMMENT", "CREATEATTACHMENT", "REMOVEATTACHMENT",
                            "REMOVEMAIL",
                            "EXPORTSPACE", "SETSPACEPERMISSIONS"]
        self.read_permissions = ["VIEWSPACE", "COMMENT"]
        self._rest_api_content = f"{self._rest_api_path}/content/"
        logging.warning(f"{self.__class__.__name__}'s instance has been initialized with url = {self.url}")

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value
        self._rest_api_path = f"{self._url}/rest/api"

    @property
    def api_root(self):
        return self._rest_api_path

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

    def test(self):
        print(self.username)
        print(self.password)
        print(self.rpc_path)
        print(self._rest_api_path)

    def get_space_permissions(self, spaceKey):
        api_url = self.rpc_path + "getSpacePermissionSets"
        res = requests.post(url=api_url, auth=(self.username, self.password), json=[spaceKey])
        if res.status_code == 200:
            return json.loads(res.text)

    def get_assigned_entities_from_space(self, spaceKey):
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

    def give_read_permissions_to_entity(self, userName, spaceKey):
        """

        :param userName: User account name
        :param spaceKey: Confluence Space's Key value
        :return:
        """
        logging.warning(f"{__name__} is called for {userName}, Space = {spaceKey}")
        input_data = [self.read_permissions, userName, spaceKey]
        api_url = "{}addPermissionsToSpace".format(self.rpc_path)
        action_request = requests.post(url=api_url, auth=HTTPBasicAuth(self.username, self.password), json=input_data)
        action_request.close()
        if action_request.status_code == 200:
            logging.info(f"Ok: {userName} is added to {spaceKey}")
        else:
            logging.warning(f"Fail: {userName}")

    def get_confluence_user_info(self, target_user=None):
        # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-users/#api-rest-api-3-user-get
        # https://developer.atlassian.com/cloud/confluence/rest/api-group-users/#api-api-user-current-get
        #   --url 'https://your-domain.atlassian.net/wiki/rest/api/user?accountId={accountId}'\
        if target_user:
            get_user_info_url = f"{self.api_root}/user?accountId={target_user}"
        else:
            get_user_info_url = f"{self.api_root}/user/current"
        r = requests.get(get_user_info_url, auth=self._auth)
        return json.loads(r.text)

    def find_page(self, space_key, page_title):
        find_page_url = f"{self._rest_api_content}?type=page&spaceKey={space_key}&title={quote(page_title)}&expand=version"
        find_page = requests.get(find_page_url, auth=self._auth)
        find_page_result = json.loads(find_page.text)
        return find_page_result

    def create_page(self, space_key, parent_page, page_title, page_content, page_repr="storage"):
        page_data = {
            "type": "page",
            "title": page_title,
            "ancestors": [{"id": parent_page}],
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": page_content,
                    "representation": page_repr
                }
            }
        }
        create_page_req = requests.post(self._rest_api_content, auth=self._auth, json=page_data)
        return json.loads(create_page_req.text)

    def update_page(self, page_title, page_id,  page_content, current_page_version, page_repr="storage"):
        page_version = int(current_page_version) + 1
        page_data = {
             "version": {
                "number": page_version
            },
            "type": "page",
            "title": page_title,
            "body": {
                "storage": {
                    "value": page_content,
                    "representation": page_repr
                }
            }
        }
        update_page_req = requests.put(f"{self._rest_api_content}{page_id}", auth=self._auth, json=page_data)
        return json.loads(update_page_req.text)
    
