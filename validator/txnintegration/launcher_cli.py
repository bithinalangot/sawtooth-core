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

import os
import sys
import argparse
import pprint
import traceback
import tempfile
import logging
import tarfile

from txnintegration.exceptions import ExitError
from txnintegration.utils import find_executable
from txnintegration.utils import load_log_config
from txnintegration.utils import parse_configuration_file
from txnintegration.validator_network_manager import get_default_vnm

from sawtooth.cli.stats_client import run_stats

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)


def parse_args(args):
    parser = argparse.ArgumentParser()

    # use system or dev paths...
    parser.add_argument('--validator',
                        help='Fully qualified path to the txnvalidator to run',
                        default=None)
    parser.add_argument('--config',
                        help='Base validator config file',
                        default=None)
    parser.add_argument('--count',
                        help='Number of validators to launch',
                        default=1,
                        type=int)
    parser.add_argument('--save-blockchain',
                        help='Save the blockchain to a file when the '
                             'network is shutdown. This is the name of the '
                             'tar.gz file that the blockchain will be saved '
                             'in. ',
                        default=None)
    parser.add_argument('--load-blockchain',
                        help='load an existing blockchain from file. This '
                             'is a file name that points to a tar.gz that '
                             'was generated from a previous run using the '
                             '--save-blockchain option.',
                        default=None)
    parser.add_argument('--data-dir',
                        help='Where to store the logs, data, etc for the '
                             'network',
                        default=None)
    parser.add_argument('--log-config',
                        help='The python logging config file to be passed '
                             'to the validators.',
                        default=None)
    parser.add_argument('--port',
                        help='The base gossip UDP port to use',
                        default=5500)
    parser.add_argument('--http-port',
                        help='The base HTTP port to use',
                        default=8800)
    parser.add_argument('--host',
                        help='host/ip to bind the ports to defaults to '
                             'localhost, use 0.0.0.0 for all adapters',
                        default='localhost')
    parser.add_argument('--endpoint',
                        help='Name of host/ip to register in the endpoint '
                             'default None, if binding adapters to 0.0.0.0'
                             ' "localhost" is a good value for this.',
                        default=None)

    return parser.parse_args(args)


def get_archive_config(data_dir, archive_name):
    tar = tarfile.open(archive_name, "r|gz")
    for f in tar:
        if os.path.basename(f.name) == 'validator-0.json':
            config = os.path.join(data_dir, "config.json")
            if os.path.exists(config):
                os.remove(config)
            tar.extract(f, data_dir)
            os.rename(os.path.join(data_dir, f.name), config)
            os.rmdir(os.path.join(data_dir, os.path.dirname(f.name)))
            break
    tar.close()
    return config


def configure(args):
    opts = parse_args(args)

    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Find the validator to use
    if opts.validator is None:
        opts.validator = find_executable('txnvalidator')
        if not os.path.isfile(opts.validator):
            print "txnvalidator: {}".format(opts.validator)
            raise ExitError("Could not find txnvalidator.")
    else:
        if not os.path.isfile(opts.validator):
            print "txnvalidator: {}".format(opts.validator)
            raise ExitError("txnvalidator script does not exist.")

    # Create directory -- after the params have been validated
    if opts.data_dir is None:
        opts.data_dir_is_tmp = True  # did we make up a directory
        opts.data_dir = tempfile.mkdtemp()
    else:
        opts.data_dir = os.path.abspath(opts.data_dir)
        if not os.path.exists(opts.data_dir):
            os.makedirs(opts.data_dir)

    if opts.load_blockchain is not None:
        if not os.path.isfile(opts.load_blockchain):
            raise ExitError("Blockchain archive to load {} does not "
                            "exist.".format(opts.load_blockchain))
        else:
            opts.config = get_archive_config(opts.data_dir,
                                             opts.load_blockchain)
            if opts.config is None:
                raise ExitError("Could not read config from Blockchain "
                                "archive: {}".format(opts.load_blockchain))

    if opts.config is not None:
        if os.path.exists(opts.config):
            validator_config = parse_configuration_file(opts.config)
        else:
            raise ExitError("Config file does not exist: {}".format(
                opts.config))
    else:
        opts.config = os.path.realpath(os.path.join(script_dir, "..", "etc",
                                                    "txnvalidator.js"))
        print "No config file specified, loading  {}".format(opts.config)
        if os.path.exists(opts.config):
            validator_config = parse_configuration_file(opts.config)
        else:
            raise ExitError(
                "Default config file does not exist: {}".format(opts.config))

    opts.log_config_dict = None
    if opts.log_config is not None:
        if not os.path.exists(opts.log_config):
            raise ExitError("log-config file does not exist: {}"
                            .format(opts.log_config))
        else:
            opts.log_config_dict = load_log_config(opts.log_config)

    keys = [
        'NodeName',
        'Listen',
        'KeyFile',
        'AdministrationNode',
        'DataDirectory',
        'LedgerURL',
    ]
    if any(k in validator_config for k in keys):
        print "Overriding the following keys from validator configuration " \
              "file: {}".format(opts.config)
        for k in keys:
            if k in validator_config:
                print "\t{}".format(k)
                del validator_config[k]
    if opts.log_config:
        print "\tLogConfigFile"

    opts.validator_config = validator_config

    opts.count = max(1, opts.count)

    print "Configuration:"
    pp.pprint(opts.__dict__)

    return vars(opts)


def main():
    vnm = None
    error_occurred = False
    try:
        opts = configure(sys.argv[1:])
    except Exception as e:
        print >> sys.stderr, str(e)
        sys.exit(1)

    try:
        vnm = get_default_vnm(opts['count'],
                              txnvalidator=opts['validator'],
                              overrides=opts['validator_config'],
                              log_config=opts['log_config_dict'],
                              data_dir=opts['data_dir'],
                              block_chain_archive=opts['load_blockchain'],
                              http_port=int(opts['http_port']),
                              udp_port=int(opts['port']),
                              host=opts['host'],
                              endpoint_host=opts['endpoint'])
        vnm.do_genesis()
        vnm.staged_launch()
        run_stats(vnm.urls()[0])
    except KeyboardInterrupt:
        print "\nExiting"
    except ExitError as e:
        # this is an expected error/exit, don't print stack trace -
        # the code raising this exception is expected to have printed the error
        # details
        error_occurred = True
        print "\nFailed!\nExiting: {}".format(e)
    except:
        error_occurred = True
        traceback.print_exc()
        print "\nFailed!\nExiting: {}".format(sys.exc_info()[0])

    finally:
        archive_name = None
        if opts['save_blockchain']:
            archive_name = opts['save_blockchain']
        if vnm is not None:
            vnm.shutdown(archive_name=archive_name)


if __name__ == "__main__":
    main()
