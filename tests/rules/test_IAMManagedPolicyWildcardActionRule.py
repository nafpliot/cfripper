"""
Copyright 2018-2019 Skyscanner Ltd

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
import pytest

from cfripper.config.config import Config
from cfripper.model.result import Result
from cfripper.rules.IAMManagedPolicyWildcardActionRule import IAMManagedPolicyWildcardActionRule
from tests.utils import get_cfmodel_from


@pytest.fixture()
def bad_template():
    return get_cfmodel_from(
        "rules/IAMManagedPolicyWildcardActionRule/iam_managed_policy_with_wildcard_action.json"
    ).resolve()


def test_failures_are_raised(bad_template):
    result = Result()
    rule = IAMManagedPolicyWildcardActionRule(Config(aws_account_id="123456789"), result)

    rule.invoke(bad_template)

    assert not result.valid
    assert len(result.failed_rules) == 1
    assert len(result.failed_monitored_rules) == 0
    assert result.failed_rules[0].rule == "IAMManagedPolicyWildcardActionRule"
    assert result.failed_rules[0].reason == "IAM managed policy CreateTestDBPolicy3 should not allow * action"
