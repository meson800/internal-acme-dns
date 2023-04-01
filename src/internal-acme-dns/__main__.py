"""Starts both an HTTP and a DNS server to serve validation requests."""

import base64
import fnmatch
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Optional

import dnslib
import dnslib.server
import toml

if "LOCAL_ACME_DNS_CONFIG_FILE" in os.environ:
    config_file = Path(os.environ["LOCAL_ACME_DNS_CONFIG_FILE"])
else:
    config_file = Path("/etc/acme/config.toml")


class ValidationResolver(dnslib.server.BaseResolver):
    """Stores an internal dict of TXT DNS entries.

    Emits TXT responses as requested.
    """

    validations: Dict[str, str] = {}

    def resolve(self, request, handler):
        """Reply to DNS entries with NXDOMAIN or proper TXT records."""
        reply = request.reply()
        qname = request.q.qname

        if str(qname) in self.validations:
            reply.add_answer(
                dnslib.RR(
                    qname,
                    dnslib.QTYPE.TXT,
                    rdata=dnslib.TXT(self.validations[str(qname)]),
                    ttl=1,
                )
            )
        else:
            reply.header.rcode = dnslib.RCODE.NXDOMAIN
        return reply


class VerificationEndpoints(BaseHTTPRequestHandler):
    """Handle incoming requests to the /present and /cleanup endpoints."""

    resolver: Optional[ValidationResolver] = None

    def do_POST(self):
        """Check API key credentials and update DNS validator as needed."""
        if self.server.resolver is None:
            self.send_error(500, explain="DNS validator not attached.")
            self.end_headers()
            return
        if "Authorization" not in self.headers:
            self.send_error(401, explain="No Authorization header passed")
            self.end_headers()
            return

        auth_header_tokens = self.headers["Authorization"].split(" ")
        if len(auth_header_tokens) != 2:
            self.send_error(401, explain="Invalid Authorization header")
            self.end_headers()
            return
        if auth_header_tokens[0] != "Basic":
            self.send_error(401, expain="Non-basic auth authorization attempted")
            self.end_headers()
            return

        basic_auth_tokens = base64.b64decode(auth_header_tokens[1]).decode().split(":")
        if len(basic_auth_tokens) != 2:
            self.send_error(401, explain="Invalid basic auth credentials")
            self.end_headers()
            return

        api_key_name = basic_auth_tokens[0]
        api_key = basic_auth_tokens[1]

        # Finally, load the toml file so we can see if this is valid
        credentials = toml.load(config_file)
        if "api_keys" not in credentials or api_key_name not in credentials["api_keys"]:
            self.send_error(401, explain="Invalid basic auth credentials")
            self.end_headers()
            return

        key_config = credentials["api_keys"][api_key_name]
        if "key" not in key_config or api_key != key_config["key"]:
            self.send_error(401, explain="Invalid basic auth credentials")
            self.end_headers()
            return

        # Valid credentials! Let's JSON decode the request
        try:
            content_len = int(self.headers["content-length"])
            request_json = json.loads(self.rfile.read(content_len))
            requested_domain = request_json["fqdn"]
            txt_value = request_json["value"]
        except json.JSONDecodeError:
            self.send_error(400, explain="Could not decode JSON")
            self.end_headers()
            return
        except KeyError:
            self.send_error(400, explain="Missing at least one of the fqdn/value keyvals")
            self.end_headers()
            return

        # If we are here, check that the domain requested is in the list of allowed domains.
        domains = key_config["domains"] if "domains" in key_config else []

        if not any([fnmatch.fnmatch(requested_domain, domain) for domain in domains]):
            self.send_error(401, explain="This API key is not allowed to request that domain")
            self.end_headers()
            return

        # Finally...process the type of command
        if self.path == "/present":
            self.server.resolver.validations[requested_domain] = txt_value
        elif self.path == "/cleanup":
            if requested_domain in self.server.resolver.validations:
                del self.server.resolver.validations[requested_domain]
        else:
            self.send_error(404)
            self.end_headers()
        self.send_response(200)
        self.end_headers()


validations = ValidationResolver()


dns_server = dnslib.server.DNSServer(resolver=validations)
dns_server.server.timeout = 0.05

http_server = HTTPServer(("0.0.0.0", 8080), VerificationEndpoints)
http_server.resolver = validations
http_server.timeout = 0.05

while True:
    http_server.handle_request()
    dns_server.server.handle_request()
