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

from cfripper.model.result import Result
from cfripper.rules.PrivilegeEscalationRule import PrivilegeEscalationRule
from tests.utils import get_cfmodel_from


@pytest.fixture()
def valid_role_inline_policy():
    return get_cfmodel_from("rules/PrivilegeEscalationRule/valid_role_inline_policy.json").resolve()


def test_valid_role_inline_policy(valid_role_inline_policy):
    result = Result()
    rule = PrivilegeEscalationRule(None, result)
    rule.invoke(valid_role_inline_policy)

    assert not result.valid
    assert len(result.failed_rules) == 1
    assert len(result.failed_monitored_rules) == 0
    assert result.failed_rules[0].rule == "PrivilegeEscalationRule"
    assert result.failed_rules[0].reason == "PolicyA has blacklisted IAM action iam:createpolicy"
