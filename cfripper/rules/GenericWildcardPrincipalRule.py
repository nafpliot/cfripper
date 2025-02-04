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
import logging
import re

from pycfmodel.model.resources.iam_managed_policy import IAMManagedPolicy
from pycfmodel.model.resources.iam_policy import IAMPolicy
from pycfmodel.model.resources.iam_role import IAMRole
from pycfmodel.model.resources.iam_user import IAMUser
from pycfmodel.model.resources.kms_key import KMSKey
from pycfmodel.model.resources.properties.policy_document import PolicyDocument
from pycfmodel.model.resources.s3_bucket_policy import S3BucketPolicy
from pycfmodel.model.resources.sns_topic_policy import SNSTopicPolicy
from pycfmodel.model.resources.sqs_queue_policy import SQSQueuePolicy

from ..model.enums import RuleMode
from ..model.rule import Rule

logger = logging.getLogger(__file__)


class GenericWildcardPrincipalRule(Rule):

    REASON_WILCARD_PRINCIPAL = "{} should not allow wildcard in principals or account-wide principals (principal: '{}')"
    REASON_NOT_ALLOWED_PRINCIPAL = "{} contains an unknown principal: {}"
    RULE_MODE = RuleMode.MONITOR

    IAM_PATTERN = re.compile(r"arn:aws:iam::(\d*|\*):.*")
    FULL_REGEX = re.compile(r"^((\w*:){0,1}\*|arn:aws:iam::(\d*|\*):.*)$")

    def invoke(self, cfmodel):
        for logical_id, resource in cfmodel.Resources.items():
            if isinstance(resource, KMSKey):
                self.check_for_wildcards(logical_id, resource.Properties.KeyPolicy)
            elif isinstance(resource, (IAMManagedPolicy, IAMPolicy, S3BucketPolicy, SNSTopicPolicy, SQSQueuePolicy)):
                self.check_for_wildcards(logical_id, resource.Properties.PolicyDocument)
            elif isinstance(resource, (IAMRole, IAMUser)):
                if isinstance(resource, IAMRole):
                    self.check_for_wildcards(logical_id, resource.Properties.AssumeRolePolicyDocument)
                if resource.Properties and resource.Properties.Policies:
                    for policy in resource.Properties.Policies:
                        self.check_for_wildcards(logical_id, policy.PolicyDocument)

    def check_for_wildcards(self, logical_id: str, resource: PolicyDocument):
        for statement in resource._statement_as_list():
            if statement.Effect == "Allow" and statement.principals_with(self.FULL_REGEX):
                for principal in statement.get_principal_list():
                    # Check if account ID is allowed
                    account_id_match = self.IAM_PATTERN.match(principal)
                    if account_id_match:
                        self.validate_account_id(logical_id, account_id_match.group(1))

                    if statement.Condition and statement.Condition.dict():
                        logger.warning(
                            f"Not adding {type(self).__name__} failure in {logical_id} because there are conditions: {statement.Condition}"
                        )
                    elif not self.resource_is_whitelisted(logical_id):
                        self.add_failure(
                            type(self).__name__, self.REASON_WILCARD_PRINCIPAL.format(logical_id, principal)
                        )

    def resource_is_whitelisted(self, logical_id):
        return logical_id in self._config.get_whitelisted_resources(type(self).__name__)

    def validate_account_id(self, logical_id, account_id):
        if self.should_add_failure(logical_id, account_id):
            self.add_failure(type(self).__name__, self.REASON_NOT_ALLOWED_PRINCIPAL.format(logical_id, account_id))

    def should_add_failure(self, logical_id, account_id) -> bool:
        if not self._config.aws_principals:
            return False
        elif account_id in self._config.aws_principals:
            return False
        return not self.resource_is_whitelisted(logical_id)
