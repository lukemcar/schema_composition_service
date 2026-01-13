# app/utils/jwt_util.py

import time
from typing import Iterable, Optional, Set, Dict, Any

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from app.core.config import Config
import logging


# Hard-coded testing password
TEST_PASSWORD = "changeme123"

security = HTTPBearer()


def generate_test_jwt(
    username: str,
    claims: Dict,
    password: str,
    expires_in: int = 3600
) -> str:
    """
    Generate a valid JWT for testing only.

    Args:
        username (str): The username to embed in the token (sub claim if not overridden).
        claims (dict): Arbitrary claims to include in the payload.
        password (str): Password provided by the caller. Must match TEST_PASSWORD.
        expires_in (int): Token lifetime in seconds (default: 1 hour).

    Returns:
        str: A signed JWT token.

    Raises:
        ValueError: If the provided password is incorrect.
    """
    if password != TEST_PASSWORD:
        raise ValueError("Invalid test password")

    now = int(time.time())
    payload = {
        "iss": Config.auth0_domain(),
        "iat": now,
        "exp": now + expires_in,
    }

    # Add subject
    payload["sub"] = claims.get("sub", username)

    # Merge arbitrary claims from user
    payload.update(claims)

    token = jwt.encode(
        payload,
        Config.jwt_secret(),
        algorithm=Config.jwt_algorithm()
    )

    return token



def auth_jwt(
    required_claims: Optional[Dict[str, Any]] = None
):
    """
    Dependency factory for JWT auth.

    Args:
        required_claims:
            Dict of required claims with expected values.
            Example: {"admin": True}
    """

    required = required_claims or {}

    async def _auth_jwt(
        token: HTTPAuthorizationCredentials = Security(security),
        tenant_id: Optional[str] = None,  # injected from path if present
        user_id: Optional[str] = None,    # injected from path if present
    ) -> Dict[str, Any]:
        try:
            logging.info("Received JWT token for validation")

            payload = jwt.decode(
                token.credentials,
                key=Config.jwt_secret(),
                algorithms=[Config.jwt_algorithm()],
            )

            logging.info(
                "JWT validation successful for subject: %s", payload.get("sub")
            )

            # ---------- static required claims ----------
            if required:
                missing = []
                mismatched = []

                for claim, expected_value in required.items():
                    if claim not in payload:
                        missing.append(claim)
                        continue

                    claim_value = payload.get(claim)

                    # Exact match required for tenant_id
                    if claim == "tenant_id":
                        if claim_value != tenant_id:
                            mismatched.append(
                                f"{claim} (expected {tenant_id}, got {claim_value})"
                            )
                        continue

                    # Exact match required for user_id
                    if claim == "user_id":
                        if claim_value != user_id:
                            mismatched.append(
                                f"{claim} (expected {user_id}, got {claim_value})"
                            )
                        continue

                    # Case-insensitive match for all other claims
                    if expected_value is not None:
                        norm_expected = str(expected_value).lower()
                        norm_actual = str(claim_value).lower()

                        if norm_expected != norm_actual:
                            mismatched.append(
                                f"{claim} (expected {expected_value}, got {claim_value})"
                            )

                if missing or mismatched:
                    logging.warning(
                        "JWT claim validation failed. Missing: %s, Mismatched: %s",
                        missing,
                        mismatched,
                    )

                    details = []
                    if missing:
                        details.append(f"Missing: {', '.join(missing)}")
                    if mismatched:
                        details.append(f"Mismatched: {', '.join(mismatched)}")

                    raise HTTPException(
                        status_code=403,
                        detail=f"Access denied: {', '.join(details)}",
                    )

            # ---------- build response ----------
            top_level_and_standard_keys = {
                "sub",
                "email",
                "nickname",
                "iss",
                "iat",
                "exp",
                "nbf",
                "aud",
                "jti",
            }

            top_level: Dict[str, Any] = {
                key: payload.get(key)
                for key in top_level_and_standard_keys
                if key in payload
            }

            extra_claims = {
                key: value
                for key, value in payload.items()
                if key not in top_level_and_standard_keys
            }

            top_level["claims"] = extra_claims
            top_level["jwt"] = token.credentials

            return top_level

        except jwt.ExpiredSignatureError as e:
            logging.error("JWT validation failed: Token has expired - %s", e)
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError as e:
            logging.error("JWT validation failed: Invalid token - %s", e)
            raise HTTPException(status_code=401, detail="Invalid token")
        except HTTPException:
            raise
        except Exception as e:
            logging.error("JWT validation failed: Unexpected error - %s", e)
            raise HTTPException(
                status_code=500,
                detail="Unexpected error during token validation",
            )

    return _auth_jwt
