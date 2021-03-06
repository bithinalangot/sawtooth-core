#
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

from sawtooth.client import SawtoothClient


class RPSClient(SawtoothClient):
    def __init__(self, base_url, keyfile):
        super(RPSClient, self).__init__(
            base_url=base_url,
            store_name='RPSTransaction',
            name='RPSClient',
            txntype_name='/RPSTransaction',
            msgtype_name='/RPS/Transaction',
            keyfile=keyfile,
        )

    def create(self, name, players):
        update = {
            'Action': 'CREATE',
            'Name': name,
            'Players': players,
        }

        return self.sendtxn('/RPSTransaction',
                            '/RPS/Transaction', update)

    def shoot(self, name, hand):
        update = {
            'Action': 'SHOOT',
            'Name': name,
            'Hand': hand,
        }

        return self.sendtxn('/RPSTransaction',
                            '/RPS/Transaction', update)
