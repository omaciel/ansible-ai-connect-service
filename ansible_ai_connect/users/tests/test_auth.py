#  Copyright Red Hat
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIRequestFactory
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy

from ansible_ai_connect.test_utils import WisdomServiceLogAwareTestCase
from ansible_ai_connect.users.auth import AAPOAuth2, RHSSOAuthentication
from ansible_ai_connect.users.constants import RHSSO_LIGHTSPEED_SCOPE


class DummyRHBackend(OpenIdConnectAuth):
    name = "oidc"

    def __init__(self):
        self.rsa_private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        algo = jwt.algorithms.RSAAlgorithm(jwt.algorithms.RSAAlgorithm.SHA256)
        self.jwk_public_key = algo.to_jwk(self.rsa_private_key.public_key(), as_dict=True)
        self.jwk_public_key["alg"] = "RS256"
        self.issuer = "https://myauth.com/auth/realms/my-realm"

    def find_valid_key(self, id_token):
        return self.jwk_public_key

    def id_token_issuer(self):
        return self.issuer


def build_access_token(private_key, issuer, payload, scope=None):
    payload["aud"] = RHSSO_LIGHTSPEED_SCOPE
    payload["scope"] = scope if scope else RHSSO_LIGHTSPEED_SCOPE
    payload["iss"] = issuer
    return jwt.encode(payload, key=private_key, algorithm="RS256")


class TestAAPOAuth2(WisdomServiceLogAwareTestCase):

    @patch.multiple(
        "social_core.backends.oauth.BaseOAuth2",
        extra_data=MagicMock(return_value={"test": "data"}),
        get_json=MagicMock(
            return_value={
                "license_info": {"date_expired": False},
            }
        ),
    )
    @patch("django.conf.settings.AAP_API_URL")
    def test_date_expired_checked_and_is_true_during_auth(self, AAP_API_URL):
        self.authentication = AAPOAuth2()
        user = MagicMock()
        response = {"is_system_auditor": True, "is_superuser": True}
        data = self.authentication.extra_data(user, "UUID", response)

        self.assertTrue(data["aap_licensed"])
        self.assertTrue(data["aap_system_auditor"])
        self.assertTrue(data["aap_superuser"])

    @patch.multiple(
        "social_core.backends.oauth.BaseOAuth2",
        extra_data=MagicMock(return_value={"test": "data"}),
        get_json=MagicMock(
            return_value={
                "license_info": {"date_expired": True},
            }
        ),
    )
    @patch("django.conf.settings.AAP_API_URL")
    def test_date_expired_checked_and_is_false_during_auth(self, AAP_API_URL):
        self.authentication = AAPOAuth2()
        user = MagicMock()
        response = {"is_system_auditor": False, "is_superuser": False}
        data = self.authentication.extra_data(user, "UUID", response)

        self.assertFalse(data["aap_licensed"])
        self.assertFalse(data["aap_system_auditor"])
        self.assertFalse(data["aap_superuser"])

    @patch.multiple(
        "social_core.backends.oauth.BaseOAuth2",
        extra_data=MagicMock(return_value={"test": "data"}),
        get_json=MagicMock(return_value={}),
    )
    @patch("django.conf.settings.AAP_API_URL")
    def test_missing_values(self, AAP_API_URL):
        self.authentication = AAPOAuth2()
        user = MagicMock()
        response = {}
        data = self.authentication.extra_data(user, "UUID", response)

        self.assertFalse(data["aap_licensed"])
        self.assertFalse(data["aap_system_auditor"])
        self.assertFalse(data["aap_superuser"])

    def test_get_me_endpoint_controller(self):
        authentication = AAPOAuth2()
        api_url = "http://controller.test/api"
        self.assertEqual(
            "http://controller.test/api/v2/me/", authentication.get_me_endpoint(api_url)
        )

    def test_get_me_endpoint_controller_ended(self):
        authentication = AAPOAuth2()
        api_url = "http://controller.test/api/"
        self.assertEqual(
            "http://controller.test/api/v2/me/", authentication.get_me_endpoint(api_url)
        )

    def test_get_me_endpoint_gateway(self):
        authentication = AAPOAuth2()
        api_url = "http://controller.test"
        self.assertEqual(
            "http://controller.test/api/gateway/v1/me/", authentication.get_me_endpoint(api_url)
        )

    def test_get_config_endpoint_controller(self):
        authentication = AAPOAuth2()
        api_url = "http://controller.test/api"
        self.assertEqual(
            "http://controller.test/api/v2/config/", authentication.get_config_endpoint(api_url)
        )

    def test_get_config_endpoint_gateway(self):
        authentication = AAPOAuth2()
        api_url = "http://controller.test"
        self.assertEqual(
            "http://controller.test/api/controller/v2/config/",
            authentication.get_config_endpoint(api_url),
        )

    def test_get_config_endpoint_gateway_ended(self):
        authentication = AAPOAuth2()
        api_url = "http://controller.test/"
        self.assertEqual(
            "http://controller.test/api/controller/v2/config/",
            authentication.get_config_endpoint(api_url),
        )

    @patch("django.conf.settings.AAP_API_URL")
    def test_local_aap_setup(self, AAP_API_URL):
        authentication = AAPOAuth2()

        with patch.object(
            authentication,
            "get_json",
            return_value={
                "license_info": {
                    "license_type": "open",
                    "valid_key": True,
                    "subscription_name": "OPEN",
                    "product_name": "AWX",
                }
            },
        ):
            access_token = "dummy_token"
            self.assertTrue(authentication.user_has_valid_license(access_token))

    @patch("django.conf.settings.AAP_API_URL")
    def test_no_license_info(self, AAP_API_URL):
        authentication = AAPOAuth2()

        with patch.object(authentication, "get_json", return_value={}):
            access_token = "dummy_token"
            self.assertFalse(authentication.user_has_valid_license(access_token))

    @patch("django.conf.settings.AAP_API_URL")
    def test_license_expired(self, AAP_API_URL):
        authentication = AAPOAuth2()

        with patch.object(
            authentication,
            "get_json",
            return_value={
                "license_info": {
                    "license_type": "whatever",
                    "valid_key": True,
                    "subscription_name": "Whatever",
                    "product_name": "AWX",
                    "date_expired": True,
                }
            },
        ):
            access_token = "dummy_token"
            self.assertFalse(authentication.user_has_valid_license(access_token))


class TestRHSSOAuthentication(WisdomServiceLogAwareTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.authentication = RHSSOAuthentication()
        self.rh_user = get_user_model().objects.create_user(
            username="rh-user",
            email="sso@user.nowhere",
            password="bar",
        )
        self.rh_usa = UserSocialAuth.objects.create(
            user=self.rh_user, provider="oidc", uid=str(uuid4())
        )

    @patch("ansible_ai_connect.users.auth.load_backend")
    def test_authenticate_returns_existing_user(self, mock_load_backend):
        backend = DummyRHBackend()
        mock_load_backend.return_value = backend
        access_token = build_access_token(
            private_key=backend.rsa_private_key,
            issuer=backend.issuer,
            payload={"sub": self.rh_usa.uid},
        )

        request = Mock(headers={"Authorization": f"Bearer {access_token}"})
        user, _ = self.authentication.authenticate(request)

        self.assertEqual(user.id, self.rh_user.id)

    @patch("ansible_ai_connect.users.auth.load_backend")
    def test_authenticate_succeeds_with_extra_scopes(self, mock_load_backend):
        backend = DummyRHBackend()
        mock_load_backend.return_value = backend
        access_token = build_access_token(
            private_key=backend.rsa_private_key,
            issuer=backend.issuer,
            payload={"sub": self.rh_usa.uid},
            scope="openid api.lightspeed",
        )

        request = Mock(headers={"Authorization": f"Bearer {access_token}"})
        user, _ = self.authentication.authenticate(request)

        self.assertEqual(user.id, self.rh_user.id)

    @patch("ansible_ai_connect.users.auth.load_backend")
    def test_authenticate_returns_none_on_invalid_scope(self, mock_load_backend):
        backend = DummyRHBackend()
        mock_load_backend.return_value = backend
        access_token = build_access_token(
            private_key=backend.rsa_private_key,
            issuer=backend.issuer,
            payload={"sub": self.rh_usa.uid},
            scope="bogus-scope",
        )

        request = Mock(headers={"Authorization": f"Bearer {access_token}"})
        self.assertIsNone(self.authentication.authenticate(request))

    def test_authenticate_returns_none_on_invalid_auth_header(self):
        backend = DummyRHBackend()
        access_token = build_access_token(
            private_key=backend.rsa_private_key,
            issuer=backend.issuer,
            payload={"sub": self.rh_usa.uid},
        )

        request = Mock(headers={"Authorization": f"bogus {access_token}"})
        self.assertIsNone(self.authentication.authenticate(request))

        request = Mock(headers={"Authorization": f"{access_token}"})
        self.assertIsNone(self.authentication.authenticate(request))

        request = Mock(headers={})
        self.assertIsNone(self.authentication.authenticate(request))

    @override_settings(ANSIBLE_AI_ENABLE_TECH_PREVIEW=False)
    @patch("ansible_ai_connect.users.auth.load_backend")
    def test_authenticate_creates_new_user(self, mock_load_backend):
        backend = DummyRHBackend()
        backend.strategy = load_strategy()
        mock_load_backend.return_value = backend
        access_token = build_access_token(
            private_key=backend.rsa_private_key,
            issuer=backend.issuer,
            payload={
                "sub": "some_unknown_sub",
                "organization": {"id": "999"},
                "preferred_username": "joe-new-user",
            },
        )

        request = Mock(headers={"Authorization": f"Bearer {access_token}"})
        user, _ = self.authentication.authenticate(request)

        self.assertEqual(user.external_username, "joe-new-user")

    @override_settings(ANSIBLE_AI_ENABLE_TECH_PREVIEW=False)
    @patch("ansible_ai_connect.users.auth.load_backend")
    def test_authenticate_outdated_payload(self, mock_load_backend):
        backend = DummyRHBackend()
        backend.strategy = load_strategy()
        mock_load_backend.return_value = backend
        access_token = build_access_token(
            private_key=backend.rsa_private_key,
            issuer=backend.issuer,
            payload={
                "sub": "some_unknown_sub",
                "organization": {"id": "999"},
                "preferred_username": "joe-new-user",
                "exp": int(datetime.now().timestamp()) - 600,
            },
        )

        request = Mock(headers={"Authorization": f"Bearer {access_token}"})
        self.assertEqual(self.authentication.authenticate(request), None)
