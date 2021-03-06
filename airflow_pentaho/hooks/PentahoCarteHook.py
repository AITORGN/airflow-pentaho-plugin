# -*- coding: utf-8 -*-
# Copyright 2020 Aneior Studio, SL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import requests
import xmltodict
from urllib.parse import urlencode

from airflow import AirflowException
from airflow.hooks.base_hook import BaseHook
from requests.auth import HTTPBasicAuth


class PentahoCarteHook(BaseHook):

    class PentahoCarteClient:

        RUN_JOB = "/kettle/executeJob/"
        JOB_STATUS = "/kettle/jobStatus/"
        RUN_TRANS = "/kettle/executeTrans/"
        TRANS_STATUS = "/kettle/transStatus/"

        def __init__(
                self,
                host,
                port,
                rep,
                username,
                password,
                carte_username,
                carte_password,
                level='Basic'):
            self.host = host
            self.port = port
            self.rep = rep
            self.username = username
            self.password = password
            self.carte_username = carte_username
            self.carte_password = carte_password
            self.level = level

        def __get_url(self, method):
            return "http://{}:{}{}".format(self.host, self.port, method)

        def __get_auth(self):
            return HTTPBasicAuth(self.carte_username, self.carte_password)

        def job_status(self, job_name, job_id, previous_response=None):
            url = self.__get_url(self.JOB_STATUS)
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            from_line = previous_response["jobstatus"]["last_log_line_nr"] \
                if previous_response \
                else 0

            payload = {
                "name": job_name,
                "id": job_id,
                "xml": "Y",
                "from": from_line
            }

            rs = requests.post(url=url, headers=headers,
                               data=urlencode(payload), auth=self.__get_auth())
            if rs.status_code >= 400:
                result = xmltodict.parse(rs.content)
                raise AirflowException("{}: {}".format(
                    result["webresult"]["result"],
                    result["webresult"]["message"])
                )
            else:
                return xmltodict.parse(rs.content)

        def run_job(self, job_path, params=None):
            url = self.__get_url(self.RUN_JOB)
            args = {
                "user": self.username,
                "pass": self.password,
                "rep": self.rep,
                "job": job_path,
                "level": "Debug"
            }

            if params:
                args.update(params)

            rs = requests.get(url=url, params=args, auth=self.__get_auth())
            if rs.status_code >= 400:
                result = xmltodict.parse(rs.content)
                raise AirflowException("{}: {}".format(
                    result["webresult"]["result"],
                    result["webresult"]["message"])
                )
            else:
                return xmltodict.parse(rs.content)

        def trans_status(self, trans_name, previous_response=None):
            url = self.__get_url(self.TRANS_STATUS)
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            from_line = previous_response["transstatus"]["last_log_line_nr"] \
                if previous_response \
                else 0

            payload = {
                "name": trans_name,
                "xml": "Y",
                "from": from_line
            }

            rs = requests.post(url=url, headers=headers,
                               data=urlencode(payload), auth=self.__get_auth())
            if rs.status_code >= 400:
                result = xmltodict.parse(rs.content)
                raise AirflowException("{}: {}".format(
                    result["webresult"]["result"],
                    result["webresult"]["message"])
                )
            else:
                return xmltodict.parse(rs.content)

        def run_trans(self, trans_path, params=None):
            url = self.__get_url(self.RUN_TRANS)
            args = {
                "user": self.username,
                "pass": self.password,
                "rep": self.rep,
                "trans": trans_path,
                "level": "Debug"
            }

            if params:
                args.update(params)

            rs = requests.get(url=url, params=args, auth=self.__get_auth())
            if rs.status_code >= 400:
                raise AirflowException(rs.content)

    def __init__(self, conn_id="pdi_default", level='Basic'):
        self.conn_id = conn_id
        self.level = level
        self.connection = self.get_connection(conn_id)
        self.extras = self.connection.extra_dejson
        self.pentaho_cli = None

    def get_conn(self):
        """
        Provide required object to run jobs on Carte
        :return:
        """
        if self.pentaho_cli:
            return self.pentaho_cli

        self.pentaho_cli = self.PentahoCarteClient(
            self.connection.host,
            self.connection.port,
            self.extras.get('rep'),
            self.connection.login,
            self.connection.password,
            self.extras.get('carte_username'),
            self.extras.get('carte_password'),
            self.level)

        return self.pentaho_cli
