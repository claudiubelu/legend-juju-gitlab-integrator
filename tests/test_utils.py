# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import base64
import unittest
from unittest import mock

import utils


class TestUtils(unittest.TestCase):
    @mock.patch.object(utils, "_HTTPResponse__init__")
    def test_httpresponse_init(self, mock_orig_constructor):
        mock_self = mock.Mock()
        mock_sock = mock_self.connection.sock
        fake_cert = "fake-cert"
        mock_sock.getpeercert.return_value = fake_cert

        utils._new_httpresponse__init__(mock_self, mock.sentinel.arg, key=mock.sentinel.kwarg)

        self.assertEqual(fake_cert, mock_self.peer_cert)
        mock_orig_constructor.assert_called_once_with(
            mock_self, mock.sentinel.arg, key=mock.sentinel.kwarg
        )
        mock_sock.getpeercert.assert_called_once_with(True)

    @mock.patch.object(utils, "_HTTPResponse__init__")
    def test_httpresponse_init_err(self, mock_original_httpresponse_init):
        mock_self = mock.Mock()
        mock_sock = mock_self.connection.sock
        mock_sock.getpeercert.side_effect = AttributeError

        utils._new_httpresponse__init__(mock_self, mock.sentinel.arg, key=mock.sentinel.kwarg)

        self.assertIsNone(mock_self.peer_cert)
        mock_sock.getpeercert.assert_called_once_with(True)

    @mock.patch.object(utils, "_build_response")
    def test_new_build_response(self, mock_original_build):
        mock_resp = mock.Mock()

        response = utils._new_build_response(mock.sentinel.self, mock.sentinel.request, mock_resp)

        self.assertEqual(mock_resp.peer_cert, response.peer_cert)
        mock_original_build.assert_called_once_with(
            mock.sentinel.self, mock.sentinel.request, mock_resp
        )

    @mock.patch.object(utils, "_build_response")
    def test_new_build_response_err(self, mock_original_build):
        mock_resp = mock.Mock(spec=[])
        mock_original_build.return_value.peer_cert = None

        response = utils._new_build_response(mock.sentinel.self, mock.sentinel.request, mock_resp)

        self.assertIsNone(response.peer_cert)
        mock_original_build.assert_called_once_with(
            mock.sentinel.self, mock.sentinel.request, mock_resp
        )

    @mock.patch("ssl.PEM_cert_to_DER_cert")
    @mock.patch("ssl.get_server_certificate")
    def test_get_gitlab_host_cert(self, mock_get_cert, mock_pem_to_der):
        cert = b"some_cert"
        mock_pem_to_der.return_value = cert

        result = utils.get_gitlab_host_cert_b64(mock.sentinel.host, mock.sentinel.port)

        self.assertEqual(base64.b64encode(cert).decode(), result)
        mock_get_cert.assert_called_once_with((mock.sentinel.host, mock.sentinel.port))
        mock_pem_to_der.assert_called_once_with(mock_get_cert.return_value)

    @mock.patch("requests.get")
    @mock.patch("ssl.get_server_certificate")
    def test_get_gitlab_host_cert_gitlab(self, mock_get_cert, mock_get):
        mock_get_cert.side_effect = Exception("Just as expected.")
        cert = b"some_cert"
        mock_get.return_value.peer_cert = cert
        gitlab_name = "gitlab.com"

        result = utils.get_gitlab_host_cert_b64(gitlab_name, 443)

        self.assertEqual(base64.b64encode(cert).decode(), result)
        expected_url = "https://%s:%s/explore" % (gitlab_name, 443)
        mock_get.assert_called_once_with(expected_url)

    @mock.patch("requests.get")
    @mock.patch("ssl.get_server_certificate")
    def test_get_gitlab_host_cert_gitlab_err(self, mock_get_cert, mock_get):
        mock_get_cert.side_effect = Exception("Just as expected.")
        mock_get.return_value.peer_cert = None
        gitlab_name = "gitlab.com"

        self.assertRaises(Exception, utils.get_gitlab_host_cert_b64, gitlab_name, 443)
        expected_url = "https://%s:%s/explore" % (gitlab_name, 443)
        mock_get.assert_called_once_with(expected_url)
