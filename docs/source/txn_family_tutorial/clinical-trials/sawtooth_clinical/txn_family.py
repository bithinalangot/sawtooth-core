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
# -----------------------------------------------------------------------------

import logging

from journal import transaction, global_store_manager
from journal.messages import transaction_message

from sawtooth.exceptions import InvalidTransactionError

LOGGER = logging.getLogger(__name__)


def _register_transaction_types(journal):
    """Registers the Clinical transaction types on the ledger.

    Args:
        ledger (journal.journal_core.Journal): The ledger to register
            the transaction type against.
    """
    journal.dispatcher.register_message_handler(
        ClinicalTransactionMessage,
        transaction_message.transaction_message_handler)
    journal.add_transaction_store(ClinicalTransaction)


class ClinicalTransactionMessage(transaction_message.TransactionMessage):
    """Clinical transaction message represent Clinical transactions.

    Attributes:
        MessageType (str): The class name of the message.
        Transaction (ClinicalTransaction): The transaction the
            message is associated with.
    """
    MessageType = "/Clinical/Transaction"

    def __init__(self, minfo=None):
        if minfo is None:
            minfo = {}

        super(ClinicalTransactionMessage, self).__init__(minfo)

        tinfo = minfo.get('Transaction', {})
        self.Transaction = ClinicalTransaction(tinfo)


class ClinicalTransaction(transaction.Transaction):
    """A Transaction is a set of updates to be applied atomically
    to a ledger.

    It has a unique identifier and a signature to validate the source.

    Attributes:
        TransactionTypeName (str): The name of the Clinical
            transaction type.
        TransactionTypeStore (type): The type of transaction store.
        MessageType (type): The object type of the message associated
            with this transaction.
    """
    TransactionTypeName = '/ClinicalTransaction'
    TransactionStoreType = global_store_manager.KeyValueStore
    MessageType = ClinicalTransactionMessage

    def __init__(self, minfo=None):
        """Constructor for the ClinicalTransaction class.

        Args:
            minfo: Dictionary of values for transaction fields.
        """

        if minfo is None:
            minfo = {}

        super(ClinicalTransaction, self).__init__(minfo)

        LOGGER.debug("minfo: %s", repr(minfo))
        self._study_number = minfo['StudyNumber'] if 'StudyNumber' in minfo else None
        self._study_details = minfo['StudyDetails'] if 'StudyDetails' in minfo else None
        """
        self._crf_id = minfo['CrfId'] if 'CrfId' in minfo else None
        self._crf_details = minfo['CrfDetails'] if 'CrfDetails' in minfo else None
        self._prod_id = minfo['ProdId'] if 'ProdId' in minfo else None
        self._crf_data = minfo['CrfData'] if 'CrfData' in minfo else None
        """
        self._action = minfo['Action'] if 'Action' in minfo else None

    def __str__(self):
        try:
            oid = self.OriginatorID
        except AssertionError:
            oid = "unknown"
        return "({0} {1} {2})".format(oid,
                                      self._study_number,
                                      self._study_details)

    def check_valid(self, store):
        """Determines if the transaction is valid.

        Args:
            store (dict): Transaction store mapping.
        """

        super(ClinicalTransaction, self).check_valid(store)
        LOGGER.info('checking %s', str(self))

        if self._action is None or self._action == '':
            raise InvalidTransactionError('action not set')

        if self._action == 'CREATE_STUDY':
            if self._study_number is None or self._study_number == '':
                raise InvalidTransactionError('study number is not set')
            if self._study_details is None or self._study_details == '':
                raise InvalidTransactionError('study details are not set')
        elif self._action == 'CREATE_CRF':
            if self._crf_id is None or self._crf_id == '':
                raise InvalidTransactionError('CRF identifier is not set')
        elif self._action == 'ADD':
            if self._crf_id is None or self._crf_id == '':
                raise InvalidTransactionError('Need to specify CRF identifier')
            if self._prod_id is None or self._prod_id == '':
                raise InvalidTransactionError('Procedure identifier not set')
        else:
            raise InvalidTransactionError('invalid action')


    def apply(self, store):
        """Applies all the updates in the transaction to the transaction
        store.

        Args:
            store (dict): Transaction store mapping.
        """
        LOGGER.debug('apply %s', str(self))

        if self._action  == 'CREATE_STUDY':
            store[self._study_number] = self._study_number
            store[self._study_details] = 'test'   # self._study_details

        elif self._action == 'CREATE_CRF':
            store[self._crf_id] = self._crf_id
            store[self._crf_details] = self._crf_details

        elif self._action == 'ADD':
            store[self._crf_id] = self._crf_id
            store[self._prod_id] = self._prod_id
            store[self._crf_data] = self._crf_data

    def dump(self):
        """Returns a dict with attributes from the transaction object.

        Returns:
            dict: The updates from the transaction object.
        """
        result = super(ClinicalTransaction, self).dump()

        result['Action'] = self._action
        if self._study_number is not None and self._study_details is not None:
            result['StudyNumber'] = self._study_number
            result['StudyDetails'] = 'test' #self._study_details
        """
        if self._crf_id is not None and self._crf_data is not None:
            result['CrfId'] = self._crf_id
            result['CrfDetails'] = self._crf_details

        if self._prod_id is not None:
            result['CrfId'] = self._crf_id
            result['ProdId'] = self._prod_id
            result['CrfData'] = self._crf_data
        """
        return result
