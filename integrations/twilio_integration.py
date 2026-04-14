"""
Twilio Integration – Agentic Call Center & SMS
Enables Big Homie to make/receive calls, send SMS, and run IVR flows
"""
import base64
import xml.sax.saxutils as _xml
from urllib.parse import urlparse as _urlparse
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger
from config import settings


@dataclass
class TwilioResult:
    """Result of a Twilio operation"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class TwilioIntegration:
    """
    Twilio REST API integration

    Capabilities:
    - Send / receive SMS
    - Initiate outbound voice calls
    - Generate TwiML for IVR (Interactive Voice Response) flows
    - Send WhatsApp messages
    - Manage phone numbers

    NOTE: Inbound calls/messages require a publicly accessible webhook URL
          configured in the Twilio console.
    """

    BASE_URL = "https://api.twilio.com/2010-04-01"

    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = settings.twilio_phone_number

    def _auth(self):
        creds = f"{self.account_sid}:{self.auth_token}"
        return base64.b64encode(creds.encode()).decode()

    def _headers(self) -> Dict:
        return {
            "Authorization": f"Basic {self._auth()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _url(self, path: str) -> str:
        return f"{self.BASE_URL}/Accounts/{self.account_sid}/{path}.json"

    async def health_check(self) -> bool:
        """Verify Twilio credentials"""
        if not settings.twilio_enabled or not self.account_sid or not self.auth_token:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.BASE_URL}/Accounts/{self.account_sid}.json",
                    headers=self._headers(),
                    timeout=10.0,
                )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Twilio health check failed: {e}")
            return False

    async def send_sms(
        self,
        to: str,
        body: str,
        from_number: Optional[str] = None,
    ) -> TwilioResult:
        """
        Send an SMS message.

        Args:
            to:          Destination phone number (E.164 format, e.g. +15551234567)
            body:        Message text (max 1600 chars)
            from_number: Override the default Twilio number
        """
        if not settings.twilio_enabled:
            return TwilioResult(success=False, error="Twilio integration not enabled")
        try:
            data = {
                "To": to,
                "From": from_number or self.from_number,
                "Body": body[:1600],
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._url("Messages"),
                    headers=self._headers(),
                    data=data,
                    timeout=15.0,
                )
            result = resp.json()
            if resp.status_code in (200, 201):
                logger.info(f"Twilio SMS sent to {to}: SID={result.get('sid')}")
                return TwilioResult(success=True, data=result)
            return TwilioResult(success=False, error=result.get("message", resp.text))
        except Exception as e:
            logger.error(f"Twilio send_sms failed: {e}")
            return TwilioResult(success=False, error=str(e))

    async def make_call(
        self,
        to: str,
        twiml_url: str,
        from_number: Optional[str] = None,
        record: bool = False,
    ) -> TwilioResult:
        """
        Initiate an outbound voice call using a TwiML URL for call flow.

        Args:
            to:         Destination phone number (E.164)
            twiml_url:  Publicly accessible URL returning TwiML instructions
            from_number: Override the default Twilio number
            record:     Whether to record the call
        """
        if not settings.twilio_enabled:
            return TwilioResult(success=False, error="Twilio integration not enabled")
        try:
            data: Dict[str, Any] = {
                "To": to,
                "From": from_number or self.from_number,
                "Url": twiml_url,
                "Record": str(record).lower(),
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._url("Calls"),
                    headers=self._headers(),
                    data=data,
                    timeout=15.0,
                )
            result = resp.json()
            if resp.status_code in (200, 201):
                logger.info(f"Twilio call initiated to {to}: SID={result.get('sid')}")
                return TwilioResult(success=True, data=result)
            return TwilioResult(success=False, error=result.get("message", resp.text))
        except Exception as e:
            logger.error(f"Twilio make_call failed: {e}")
            return TwilioResult(success=False, error=str(e))

    async def make_call_with_twiml(
        self,
        to: str,
        twiml: str,
        from_number: Optional[str] = None,
    ) -> TwilioResult:
        """
        Initiate an outbound call with inline TwiML (no external URL needed).

        Args:
            to:      Destination phone number (E.164)
            twiml:   TwiML XML string e.g. '<Response><Say>Hello!</Say></Response>'
            from_number: Override the default Twilio number
        """
        if not settings.twilio_enabled:
            return TwilioResult(success=False, error="Twilio integration not enabled")
        try:
            data: Dict[str, Any] = {
                "To": to,
                "From": from_number or self.from_number,
                "Twiml": twiml,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._url("Calls"),
                    headers=self._headers(),
                    data=data,
                    timeout=15.0,
                )
            result = resp.json()
            if resp.status_code in (200, 201):
                logger.info(f"Twilio call (inline TwiML) to {to}: SID={result.get('sid')}")
                return TwilioResult(success=True, data=result)
            return TwilioResult(success=False, error=result.get("message", resp.text))
        except Exception as e:
            logger.error(f"Twilio make_call_with_twiml failed: {e}")
            return TwilioResult(success=False, error=str(e))

    async def list_messages(self, limit: int = 20) -> TwilioResult:
        """List recent messages"""
        if not settings.twilio_enabled:
            return TwilioResult(success=False, error="Twilio integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self._url("Messages"),
                    headers=self._headers(),
                    params={"PageSize": limit},
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return TwilioResult(success=True, data=resp.json().get("messages", []))
            return TwilioResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Twilio list_messages failed: {e}")
            return TwilioResult(success=False, error=str(e))

    async def list_calls(self, limit: int = 20) -> TwilioResult:
        """List recent calls"""
        if not settings.twilio_enabled:
            return TwilioResult(success=False, error="Twilio integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self._url("Calls"),
                    headers=self._headers(),
                    params={"PageSize": limit},
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return TwilioResult(success=True, data=resp.json().get("calls", []))
            return TwilioResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Twilio list_calls failed: {e}")
            return TwilioResult(success=False, error=str(e))

    def build_ivr_twiml(
        self,
        greeting: str,
        menu_options: Dict[str, str],
        gather_action_url: str,
    ) -> str:
        """
        Build a simple IVR TwiML menu.

        Args:
            greeting:         Text to speak on answer
            menu_options:     Dict of digit -> description e.g. {"1": "Sales", "2": "Support"}
            gather_action_url: URL to POST the caller's digit selection
        Returns:
            TwiML XML string
        """
        # Validate the action URL using proper URL parsing to prevent SSRF / injection.
        # Only allow http/https, a non-empty hostname, and no embedded credentials.
        _parsed = _urlparse(gather_action_url)
        if _parsed.scheme not in ("http", "https") or not _parsed.hostname or _parsed.username or _parsed.password:
            raise ValueError(f"Invalid gather_action_url: {gather_action_url!r}")

        menu_text = ". ".join(
            f"Press {_xml.escape(k)} for {_xml.escape(v)}"
            for k, v in menu_options.items()
        )
        escaped_greeting = _xml.escape(greeting)
        # gather_action_url goes into an XML attribute – use quoteattr for safety
        action_attr = _xml.quoteattr(gather_action_url)
        twiml = (
            "<?xml version='1.0' encoding='UTF-8'?>"
            "<Response>"
            f"<Gather numDigits='1' action={action_attr} method='POST' "
            "input='dtmf' timeout='10' finishOnKey=''>"
            f"<Say>{escaped_greeting}. {menu_text}. Press 0 to repeat.</Say>"
            "</Gather>"
            "<Say>We didn't receive your selection. Goodbye.</Say>"
            "</Response>"
        )
        return twiml


# Global instance
twilio = TwilioIntegration()
