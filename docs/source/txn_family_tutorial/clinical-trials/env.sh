#!/bin/sh

# This script sets the PYTHONPATH variable to the correct value for the current step of the
# transaction family tutorial.

export PYTHONPATH=/project/sawtooth-core/core:/project/sawtooth-core/docs/source/txn_family_tutorial/clinical-trials:/project/sawtooth-core/validator:/project/sawtooth-core/validator/build/lib.linux-x86_64-2.7
echo "Changed PYTHONPATH for Clinical Trials"
