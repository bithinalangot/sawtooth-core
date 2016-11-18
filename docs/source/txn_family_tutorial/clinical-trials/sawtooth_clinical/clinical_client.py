# Copyright 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

from sawtooth.client import SawtoothClient


class ClinicalClient(SawtoothClient):
    def __init__(self,
                 base_url,
                 keyfile,
                 disable_client_validation=False):
        super(ClinicalClient, self).__init__(
            base_url=base_url,
            store_name='ClinicalTransaction',
            name='ClinicalClient',
            txntype_name='/ClinicalTransaction',
            msgtype_name='/Clinical/Transaction',
            keyfile=keyfile,
            disable_client_validation=disable_client_validation)

    def send_clinical_txn(self, update):
        """
        This sets up the same defaults as the Transaction so when
        signing happens in sendtxn, the same payload is signed.
        Args:
            update: dict The data associated with the Clinical data model
        Returns:
            txnid: str The txnid associated with the transaction

        """
        if 'StudyNumber' in update and 'CrfId' not in update:
            if 'StudyDetails' not in update:
                update['StudyDetails'] = None

        if 'CrfId' in update and 'ProdId' not in update:
            if 'CrfDetails' not in update:
                update['CrfDetails'] = None
            if 'StudyNumber' not in update:
                update['StudyNumber'] = None

        if 'ProdId' in update:
            if 'CrfId' not in update:
                update['CrfId'] = None
            if 'CrfData' not in update:
                update['CrfData'] = None

        if 'Action' not in update:
            update['Action'] = None

        return self.sendtxn('/ClinicalTransaction',
                            '/Clinical/Transaction',
                            update)

    def create_study(self, study_number, study_details):
        """
        To create a new study
        """
        update = {
            'Action':'CREATE_STUDY',
            'StudyNumber':study_number,
            'StudyDetails':study_details
        }

        return self.send_clinical_txn(update)

    def create_crf(self, crf_id, crf_details, study_number):
        """
        To create a new CRF within a study.
        """
        update = {
            'Action':'CREATE_CRF',
            'CrfId':crf_id,
            'StudyNumber':study_number,
            'CrfDetails':crf_details
        }

        return self.send_clinical_txn(update)

    def add_crf_entry(self, crf_id, prod_id, crf_data):
        """
        A single CRF entry.
        """
        update = {
            'Action':'ADD',
            'CrfId':crf_id,
            'ProdId':prod_id,
            'CrfData':crf_data
        }

        return self.send_clinical_txn(update)
