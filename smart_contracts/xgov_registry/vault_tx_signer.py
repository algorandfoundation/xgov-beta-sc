import base64
import os
from abc import ABC, abstractmethod

import hvac
from algosdk import constants, encoding
from algosdk.atomic_transaction_composer import (
    TransactionSigner,
)
from algosdk.transaction import (
    GenericSignedTransaction,
    LogicSigTransaction,
    Multisig,
    MultisigTransaction,
    SignedTransaction,
    Transaction,
)

## TODO:
# Add more auth methods as needed (AWS, GCP, etc.)


class VaultAuth(ABC):
    """Abstract base class for Vault authentication methods"""

    @abstractmethod
    def authenticate(self, vault_client: hvac.Client) -> None:
        """Authenticate the vault client"""
        pass


class TokenAuth(VaultAuth):
    """Token-based authentication"""

    def __init__(self, token: str):
        self.token = token

    def authenticate(self, vault_client: hvac.Client) -> None:
        vault_client.token = self.token
        if not vault_client.is_authenticated():
            raise ValueError("Failed to authenticate with HashiCorp Vault using token")


class AppRoleAuth(VaultAuth):
    """AppRole-based authentication"""

    def __init__(self, role_id: str, secret_id: str, mount_point: str = "approle"):
        self.role_id = role_id
        self.secret_id = secret_id
        self.mount_point = mount_point

    def authenticate(self, vault_client: hvac.Client) -> None:
        try:
            auth_response = vault_client.auth.approle.login(  # type: ignore
                role_id=self.role_id,
                secret_id=self.secret_id,
                mount_point=self.mount_point,
            )
            vault_client.token = auth_response["auth"]["client_token"]  # type: ignore

            if not vault_client.is_authenticated():
                raise ValueError(
                    "Failed to authenticate with HashiCorp Vault using AppRole"
                )
        except Exception as e:
            raise ValueError(f"AppRole authentication failed: {e!s}") from e


class OIDCAuth(VaultAuth):
    """OIDC-based authentication"""

    def __init__(self, role: str, mount_point: str = "oidc"):
        self.role = role
        self.mount_point = mount_point

    def authenticate(self, vault_client: hvac.Client) -> None:
        try:
            # Get the OIDC auth URL
            auth_url_response = vault_client.auth.oidc.oidc_authorization_url_request(  # type: ignore
                role=self.role, mount_point=self.mount_point
            )
            auth_url = auth_url_response["data"]["auth_url"]  # type: ignore

            print("Please open the following URL in your browser to authenticate:")
            print(f"{auth_url}")  # type: ignore
            print("\nAfter authentication, you will be redirected to a callback URL.")
            print(
                "Please copy the 'code' parameter from the callback URL and paste it below:"
            )

            # Get the authorization code from user input
            auth_code = input("Authorization code: ").strip()

            if not auth_code:
                raise ValueError(
                    "Authorization code is required for OIDC authentication"
                )

            # Exchange the authorization code for a Vault token
            callback_response = vault_client.auth.oidc.oidc_callback(  # type: ignore
                code=auth_code, mount_point=self.mount_point
            )

            vault_client.token = callback_response["auth"]["client_token"]  # type: ignore

            if not vault_client.is_authenticated():
                raise ValueError(
                    "Failed to authenticate with HashiCorp Vault using OIDC"
                )

        except Exception as exc:
            raise ValueError(f"OIDC authentication failed: {exc}") from exc


class OIDCCallbackAuth(VaultAuth):
    """OIDC-based authentication using pre-obtained callback data"""

    def __init__(self, role: str, auth_code: str, mount_point: str = "oidc"):
        self.role = role
        self.auth_code = auth_code
        self.mount_point = mount_point

    def authenticate(self, vault_client: hvac.Client) -> None:
        try:
            # Exchange the authorization code for a Vault token
            callback_response = vault_client.auth.oidc.oidc_callback(  # type: ignore
                code=self.auth_code, mount_point=self.mount_point
            )

            vault_client.token = callback_response["auth"]["client_token"]  # type: ignore

            if not vault_client.is_authenticated():
                raise ValueError(
                    "Failed to authenticate with HashiCorp Vault using OIDC"
                )

        except Exception as exc:
            raise ValueError(f"OIDC callback authentication failed: {exc}") from exc


class OIDCJWTAuth(VaultAuth):
    """OIDC JWT-based authentication (for service accounts)"""

    def __init__(self, role: str, jwt: str, mount_point: str = "oidc"):
        self.role = role
        self.jwt = jwt
        self.mount_point = mount_point

    def authenticate(self, vault_client: hvac.Client) -> None:
        try:
            # Authenticate using JWT
            auth_response = vault_client.auth.oidc.login(  # type: ignore
                role=self.role, jwt=self.jwt, mount_point=self.mount_point
            )

            vault_client.token = auth_response["auth"]["client_token"]  # type: ignore

            if not vault_client.is_authenticated():
                raise ValueError(
                    "Failed to authenticate with HashiCorp Vault using OIDC JWT"
                )

        except Exception as exc:
            raise ValueError(f"OIDC JWT authentication failed: {exc}") from exc


class GitHubActionsAuth(VaultAuth):
    """GitHub Actions OIDC authentication - automatically gets the OIDC token"""

    def __init__(self, role: str, mount_point: str = "oidc", audience: str = "vault"):
        self.role = role
        self.mount_point = mount_point
        self.audience = audience

    def authenticate(self, vault_client: hvac.Client) -> None:
        try:
            import json
            import urllib.parse
            import urllib.request

            # Get the OIDC token from GitHub Actions
            req_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
            req_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")

            if not req_token or not req_url:
                raise ValueError(
                    "GitHub Actions OIDC token request environment variables not found. "
                    "Make sure 'id-token: write' permission is set in your workflow."
                )

            # Request the OIDC token from GitHub
            token_url = f"{req_url}&audience={urllib.parse.quote(self.audience)}"
            request = urllib.request.Request(token_url)
            request.add_header("Authorization", f"bearer {req_token}")
            request.add_header("Accept", "application/json; api-version=2.0")
            request.add_header("Content-Type", "application/json")

            response = urllib.request.urlopen(request)
            response_data = json.loads(response.read().decode())  # type: ignore
            jwt_token = response_data.get("value")  # type: ignore

            if not jwt_token:  # type: ignore
                raise ValueError("Failed to obtain OIDC token from GitHub Actions")

            # Authenticate with Vault using the JWT token
            auth_response = vault_client.auth.oidc.login(  # type: ignore
                role=self.role, jwt=jwt_token, mount_point=self.mount_point  # type: ignore
            )

            vault_client.token = auth_response["auth"]["client_token"]  # type: ignore

            if not vault_client.is_authenticated():
                raise ValueError(
                    "Failed to authenticate with HashiCorp Vault using GitHub Actions OIDC"
                )

        except Exception as exc:
            raise ValueError(
                f"GitHub Actions OIDC authentication failed: {exc}"
            ) from exc


class VaultSecretEngine(ABC):
    """Abstract base class for Vault secret engines"""

    @abstractmethod
    def setup_and_derive_public_key(self, key_name: str) -> bytes:
        """Setup the secret engine and derive the public key bytes"""
        pass

    @abstractmethod
    def sign_data(self, data_b64: str, key_name: str) -> str:
        """Sign data and return the signature"""
        pass


class TransitSecretEngine(VaultSecretEngine):
    """Transit secret engine implementation"""

    def __init__(
        self, vault_url: str, vault_auth: VaultAuth, mount_path: str = "transit"
    ):
        self.vault_url = vault_url
        self.vault_auth = vault_auth
        self.mount_path = mount_path

        # Initialize the Vault client
        self.vault_client = hvac.Client(url=self.vault_url)

        # Authenticate using the provided auth method
        self.vault_auth.authenticate(self.vault_client)

    def setup_and_derive_public_key(self, key_name: str) -> bytes:
        """Setup transit engine and derive the public key bytes from the Vault key"""
        try:
            # Check if transit engine is enabled
            mounts = self.vault_client.sys.list_mounted_secrets_engines()  # type: ignore
            if f"{self.mount_path}/" not in mounts["data"]:  # type: ignore
                raise ValueError(
                    f"Transit secrets engine not mounted at '{self.mount_path}'"
                )

            # Get the public key from Vault (this also verifies the key exists)
            try:
                key_info = self.vault_client.secrets.transit.read_key(  # type: ignore
                    name=key_name, mount_point=self.mount_path
                )
            except Exception as e:
                raise ValueError(f"Key '{key_name}' not found in transit engine") from e

            # Extract public key bytes
            public_key_b64 = key_info["data"]["keys"]["1"]["public_key"]  # type: ignore
            public_key_bytes = base64.b64decode(public_key_b64)  # type: ignore

            return public_key_bytes

        except Exception as exc:
            raise ValueError(
                f"Failed to setup Vault transit engine or derive public key: {exc}"
            ) from exc

    def sign_data(self, data_b64: str, key_name: str) -> str:
        """Sign data using Vault transit engine"""
        try:
            # Sign with Vault transit engine
            # For Ed25519 keys, we use the data directly without pre-hashing
            sign_response = self.vault_client.secrets.transit.sign_data(  # type: ignore
                name=key_name,
                hash_input=data_b64,
                prehashed=False,  # Ed25519 handles hashing internally
                mount_point=self.mount_path,
            )

            # Extract signature from Vault response
            vault_signature = sign_response["data"]["signature"]  # type: ignore
            # Vault returns signature in format "vault:v1:base64signature"
            signature_b64 = vault_signature.split(":")[-1]  # type: ignore

            # Add padding if needed for proper base64 decoding
            missing_padding = len(signature_b64) % 4  # type: ignore
            if missing_padding:
                signature_b64 += "=" * (4 - missing_padding)  # type: ignore

            # Verify the signature is valid base64 and correct length
            try:
                signature_bytes = base64.b64decode(signature_b64)  # type: ignore
                if len(signature_bytes) != 64:  # Ed25519 signatures are 64 bytes
                    raise ValueError(
                        f"Invalid signature length: {len(signature_bytes)}"
                    )
            except Exception as e:
                raise ValueError(f"Invalid signature from Vault: {e}") from e

            return signature_b64  # type: ignore

        except Exception as exc:
            raise ValueError(f"Failed to sign data with transit engine: {exc}") from exc


class HashicorpVaultTransactionSigner(TransactionSigner):
    def __init__(self, secret_engine: VaultSecretEngine, key_name: str):
        """
        Initialize HashiCorp Vault Transaction Signer

        Args:
            secret_engine: The secret engine implementation to use (already configured with Vault connection)
            key_name: Name of the key to use for signing
        """
        self.secret_engine = secret_engine
        self.key_name = key_name

        # Setup secret engine and derive public key from Vault
        self._public_key_bytes = self.secret_engine.setup_and_derive_public_key(
            self.key_name
        )

        # Derive address from public key
        self._address = encoding.encode_address(self._public_key_bytes)  # type: ignore

    def sign_transactions(
        self, txn_group: list[Transaction], indexes: list[int]
    ) -> list[SignedTransaction | LogicSigTransaction | MultisigTransaction]:
        """
        Sign transactions using the configured secret engine

        Args:
            txn_group: list of transactions to sign
            indexes: Indexes of transactions in the group that this signer should sign

        Returns:
            list of signed transaction bytes
        """
        try:
            signed_txns: list[SignedTransaction] = []

            for i in indexes:
                if i >= len(txn_group):
                    raise ValueError(f"Transaction index {i} out of range")

                # Get the transaction to sign
                txn = txn_group[i]

                # Ensure we have a Transaction object
                if not hasattr(txn, "dictify"):
                    raise ValueError(
                        f"Expected Transaction object, got {type(txn)}. Value: {txn}"
                    )

                encoded_txn = encoding.msgpack_encode(txn)  # type: ignore
                to_sign = constants.txid_prefix + base64.b64decode(encoded_txn)  # type: ignore

                # Convert to base64 for Vault API
                to_sign_b64 = base64.b64encode(to_sign).decode("utf-8")

                # Sign using the secret engine
                signature_b64 = self.secret_engine.sign_data(to_sign_b64, self.key_name)

                # Create signed transaction with the base64 signature
                signed_txn = SignedTransaction(transaction=txn, signature=signature_b64)

                signed_txns.append(signed_txn)

            return signed_txns  # type: ignore

        except Exception as exc:
            raise RuntimeError(
                f"Failed to sign transactions with Vault: {exc}"
            ) from exc

    @property
    def address(self) -> str:
        """Get the Algorand address associated with this signer"""
        if not self._address:  # type: ignore
            raise ValueError(
                "Address not available. Failed to derive from Vault or not provided."
            )
        return self._address  # type: ignore

    @property
    def public_key_bytes(self) -> bytes:
        """Get the public key bytes associated with this signer"""
        if not self._public_key_bytes:
            raise ValueError("Public key not available. Failed to derive from Vault.")
        return self._public_key_bytes

    def __repr__(self) -> str:
        return (
            f"HashicorpVaultTransactionSigner("
            f"secret_engine={self.secret_engine.__class__.__name__}, "
            f"key_name='{self.key_name}'"
            f")"
        )


class HashicorpVaultMultisigTransactionSigner(TransactionSigner):
    """
    Represents a Transaction Signer for a Multisig using HashiCorp Vault.

    Args:
        msig (Multisig): Multisig account
        vault_url: URL of the HashiCorp Vault instance
        vault_token: Authentication token for Vault
        secret_engine: The secret engine implementation to use
    """

    def __init__(
        self, msig: Multisig, secret_engine: VaultSecretEngine, key_names: list[str]
    ) -> None:
        super().__init__()
        self.msig = msig
        self.vault_transaction_signers = [
            HashicorpVaultTransactionSigner(
                secret_engine=secret_engine, key_name=key_name
            )
            for key_name in key_names
        ]
        self._address = msig.address()  # type: ignore

    def sign_transactions(
        self, txn_group: list[Transaction], indexes: list[int]
    ) -> list[GenericSignedTransaction]:
        """
        Sign transactions in a transaction group given the indexes.

        Returns an array of encoded signed transactions. The length of the
        array will be the same as the length of indexesToSign, and each index i in the array
        corresponds to the signed transaction from txnGroup[indexesToSign[i]].

        Args:
            txn_group (list[Transaction]): atomic group of transactions
            indexes (list[int]): array of indexes in the atomic transaction group that should be signed
        """
        self.msig.validate()  # type: ignore

        pk_to_signed_txs: dict[bytes, SignedTransaction] = {}
        for signer in self.vault_transaction_signers:
            signed_txns = signer.sign_transactions(txn_group, indexes)
            pk = signer.public_key_bytes
            pk_to_signed_txs[pk] = signed_txns  # type: ignore

        stxns: list[GenericSignedTransaction] = []
        for i in indexes:
            mtxn = MultisigTransaction(txn_group[i], self.msig)
            for subsig in mtxn.multisig.subsigs:
                pk = subsig.public_key
                if pk in pk_to_signed_txs:  # type: ignore
                    stxns_part = pk_to_signed_txs[pk]  # type: ignore
                    subsig.signature = base64.b64decode(stxns_part[i].signature)  # type: ignore
            stxns.append(mtxn)
        return stxns

    @property
    def address(self) -> str:
        """Get the Algorand address associated with this signer"""
        if not self._address:  # type: ignore
            raise ValueError(
                "Address not available. Failed to derive from Vault or not provided."
            )
        return self._address  # type: ignore


# Factory function to create signer from environment variables (backwards compatible)
def create_vault_signer_from_env() -> HashicorpVaultTransactionSigner:
    """
    Create a HashiCorp Vault signer using environment variables with Transit engine

    Supports Token, AppRole, and OIDC authentication methods.

    Expected environment variables:
    - VAULT_URL: HashiCorp Vault URL
    - VAULT_TRANSIT_MOUNT_PATH: Transit engine mount path (optional, defaults to "transit")
    - VAULT_KEY_NAME: Name of the key in transit engine

    For Token authentication:
    - VAULT_TOKEN: Authentication token

    For AppRole authentication:
    - VAULT_ROLE_ID: AppRole role ID
    - VAULT_SECRET_ID: AppRole secret ID
    - VAULT_APPROLE_MOUNT_PATH: AppRole mount path (optional, defaults to "approle")

    For OIDC authentication:
    - VAULT_OIDC_ROLE: OIDC role name
    - VAULT_OIDC_MOUNT_PATH: OIDC mount path (optional, defaults to "oidc")

    For OIDC with auth code:
    - VAULT_OIDC_ROLE: OIDC role name
    - VAULT_OIDC_AUTH_CODE: Pre-obtained authorization code
    - VAULT_OIDC_MOUNT_PATH: OIDC mount path (optional, defaults to "oidc")

    For OIDC JWT (service account):
    - VAULT_OIDC_ROLE: OIDC role name
    - VAULT_OIDC_JWT: JWT token
    - VAULT_OIDC_MOUNT_PATH: OIDC mount path (optional, defaults to "oidc")

    For GitHub Actions OIDC (automatic):
    - VAULT_OIDC_ROLE: OIDC role name configured for GitHub Actions
    - VAULT_OIDC_MOUNT_PATH: OIDC mount path (optional, defaults to "oidc")
    - VAULT_GITHUB_AUDIENCE: Audience for GitHub OIDC token (optional, defaults to "vault")
    Note: Requires 'id-token: write' permission in GitHub Actions workflow
    """
    vault_url = os.environ.get("VAULT_URL")
    transit_mount_path = os.environ.get("VAULT_TRANSIT_MOUNT_PATH", "transit")
    key_name = os.environ.get("VAULT_KEY_NAME")

    if not vault_url:
        raise ValueError("VAULT_URL environment variable is required")
    if not key_name:
        raise ValueError("VAULT_KEY_NAME environment variable is required")

    # Check authentication methods in order of preference

    # 1. Check for GitHub Actions OIDC (automatic detection)
    if (
        os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
        and os.environ.get("VAULT_OIDC_ROLE")
    ):
        oidc_role = os.environ.get("VAULT_OIDC_ROLE", "")
        oidc_mount_path = os.environ.get("VAULT_OIDC_MOUNT_PATH", "oidc")
        github_audience = os.environ.get("VAULT_GITHUB_AUDIENCE", "vault")
        vault_auth: VaultAuth = GitHubActionsAuth(
            role=oidc_role, mount_point=oidc_mount_path, audience=github_audience
        )

    # 2. Check for OIDC JWT authentication (service account)
    elif os.environ.get("VAULT_OIDC_ROLE") and os.environ.get("VAULT_OIDC_JWT"):
        oidc_role = os.environ.get("VAULT_OIDC_ROLE", "")
        oidc_jwt = os.environ.get("VAULT_OIDC_JWT", "")
        oidc_mount_path = os.environ.get("VAULT_OIDC_MOUNT_PATH", "oidc")
        vault_auth = OIDCJWTAuth(
            role=oidc_role, jwt=oidc_jwt, mount_point=oidc_mount_path
        )

    # 3. Check for OIDC with auth code
    elif os.environ.get("VAULT_OIDC_ROLE") and os.environ.get("VAULT_OIDC_AUTH_CODE"):
        oidc_role = os.environ.get("VAULT_OIDC_ROLE", "")
        oidc_auth_code = os.environ.get("VAULT_OIDC_AUTH_CODE", "")
        oidc_mount_path = os.environ.get("VAULT_OIDC_MOUNT_PATH", "oidc")
        vault_auth = OIDCCallbackAuth(
            role=oidc_role, auth_code=oidc_auth_code, mount_point=oidc_mount_path
        )

    # 4. Check for interactive OIDC
    elif os.environ.get("VAULT_OIDC_ROLE"):
        oidc_role = os.environ.get("VAULT_OIDC_ROLE", "")
        oidc_mount_path = os.environ.get("VAULT_OIDC_MOUNT_PATH", "oidc")
        vault_auth = OIDCAuth(role=oidc_role, mount_point=oidc_mount_path)

    # 5. Check for AppRole authentication
    elif os.environ.get("VAULT_ROLE_ID") and os.environ.get("VAULT_SECRET_ID"):
        role_id = os.environ.get("VAULT_ROLE_ID", "")
        secret_id = os.environ.get("VAULT_SECRET_ID", "")
        approle_mount_path = os.environ.get("VAULT_APPROLE_MOUNT_PATH", "approle")
        vault_auth = AppRoleAuth(
            role_id=role_id, secret_id=secret_id, mount_point=approle_mount_path
        )

    # 6. Fall back to token authentication
    elif os.environ.get("VAULT_TOKEN"):
        vault_token = os.environ.get("VAULT_TOKEN", "")
        vault_auth = TokenAuth(token=vault_token)

    else:
        raise ValueError(
            "Authentication required. Please set one of:\n"
            "- VAULT_TOKEN (for token auth)\n"
            "- VAULT_ROLE_ID + VAULT_SECRET_ID (for AppRole auth)\n"
            "- VAULT_OIDC_ROLE (for OIDC auth)\n"
            "- VAULT_OIDC_ROLE + VAULT_OIDC_JWT (for OIDC JWT auth)\n"
            "- VAULT_OIDC_ROLE + VAULT_OIDC_AUTH_CODE (for OIDC callback auth)"
        )

    # Create transit engine with the specified parameters
    transit_engine = TransitSecretEngine(
        vault_url=vault_url, vault_auth=vault_auth, mount_path=transit_mount_path
    )

    return HashicorpVaultTransactionSigner(
        secret_engine=transit_engine,
        key_name=key_name,
    )


# Backwards-compatible constructor for transit engine with token auth
def create_transit_signer(
    vault_url: str,
    vault_token: str,
    transit_mount_path: str = "transit",
    key_name: str = "algorand-key",
) -> HashicorpVaultTransactionSigner:
    """
    Create a HashiCorp Vault signer with Transit engine using token authentication (backwards compatible)

    Args:
        vault_url: URL of the HashiCorp Vault instance
        vault_token: Authentication token for Vault
        transit_mount_path: Mount path for the transit secrets engine (default: "transit")
        key_name: Name of the key in Vault's transit engine
    """
    vault_auth = TokenAuth(token=vault_token)
    transit_engine = TransitSecretEngine(
        vault_url=vault_url, vault_auth=vault_auth, mount_path=transit_mount_path
    )

    return HashicorpVaultTransactionSigner(
        secret_engine=transit_engine,
        key_name=key_name,
    )


# New constructor for transit engine with AppRole auth
def create_transit_signer_approle(
    vault_url: str,
    role_id: str,
    secret_id: str,
    transit_mount_path: str = "transit",
    key_name: str = "algorand-key",
    approle_mount_path: str = "approle",
) -> HashicorpVaultTransactionSigner:
    """
    Create a HashiCorp Vault signer with Transit engine using AppRole authentication

    Args:
        vault_url: URL of the HashiCorp Vault instance
        role_id: AppRole role ID
        secret_id: AppRole secret ID
        transit_mount_path: Mount path for the transit secrets engine (default: "transit")
        key_name: Name of the key in Vault's transit engine
        approle_mount_path: Mount path for AppRole auth method (default: "approle")
    """
    vault_auth = AppRoleAuth(
        role_id=role_id, secret_id=secret_id, mount_point=approle_mount_path
    )
    transit_engine = TransitSecretEngine(
        vault_url=vault_url, vault_auth=vault_auth, mount_path=transit_mount_path
    )

    return HashicorpVaultTransactionSigner(
        secret_engine=transit_engine,
        key_name=key_name,
    )


# New constructor for transit engine with OIDC auth (interactive)
def create_transit_signer_oidc(
    vault_url: str,
    role: str,
    transit_mount_path: str = "transit",
    key_name: str = "algorand-key",
    oidc_mount_path: str = "oidc",
) -> HashicorpVaultTransactionSigner:
    """
    Create a HashiCorp Vault signer with Transit engine using OIDC authentication (interactive)

    Args:
        vault_url: URL of the HashiCorp Vault instance
        role: OIDC role name
        transit_mount_path: Mount path for the transit secrets engine (default: "transit")
        key_name: Name of the key in Vault's transit engine
        oidc_mount_path: Mount path for OIDC auth method (default: "oidc")
    """
    vault_auth = OIDCAuth(role=role, mount_point=oidc_mount_path)
    transit_engine = TransitSecretEngine(
        vault_url=vault_url, vault_auth=vault_auth, mount_path=transit_mount_path
    )

    return HashicorpVaultTransactionSigner(
        secret_engine=transit_engine,
        key_name=key_name,
    )


# New constructor for transit engine with OIDC callback auth
def create_transit_signer_oidc_callback(
    vault_url: str,
    role: str,
    auth_code: str,
    transit_mount_path: str = "transit",
    key_name: str = "algorand-key",
    oidc_mount_path: str = "oidc",
) -> HashicorpVaultTransactionSigner:
    """
    Create a HashiCorp Vault signer with Transit engine using OIDC callback authentication

    Args:
        vault_url: URL of the HashiCorp Vault instance
        role: OIDC role name
        auth_code: Authorization code from OIDC callback
        transit_mount_path: Mount path for the transit secrets engine (default: "transit")
        key_name: Name of the key in Vault's transit engine
        oidc_mount_path: Mount path for OIDC auth method (default: "oidc")
    """
    vault_auth = OIDCCallbackAuth(
        role=role, auth_code=auth_code, mount_point=oidc_mount_path
    )
    transit_engine = TransitSecretEngine(
        vault_url=vault_url, vault_auth=vault_auth, mount_path=transit_mount_path
    )

    return HashicorpVaultTransactionSigner(
        secret_engine=transit_engine,
        key_name=key_name,
    )


# New constructor for transit engine with OIDC JWT auth (service account)
def create_transit_signer_oidc_jwt(
    vault_url: str,
    role: str,
    jwt: str,
    transit_mount_path: str = "transit",
    key_name: str = "algorand-key",
    oidc_mount_path: str = "oidc",
) -> HashicorpVaultTransactionSigner:
    """
    Create a HashiCorp Vault signer with Transit engine using OIDC JWT authentication (service account)

    Args:
        vault_url: URL of the HashiCorp Vault instance
        role: OIDC role name
        jwt: JWT token for service account authentication
        transit_mount_path: Mount path for the transit secrets engine (default: "transit")
        key_name: Name of the key in Vault's transit engine
        oidc_mount_path: Mount path for OIDC auth method (default: "oidc")
    """
    vault_auth = OIDCJWTAuth(role=role, jwt=jwt, mount_point=oidc_mount_path)
    transit_engine = TransitSecretEngine(
        vault_url=vault_url, vault_auth=vault_auth, mount_path=transit_mount_path
    )

    return HashicorpVaultTransactionSigner(
        secret_engine=transit_engine,
        key_name=key_name,
    )


# New constructor for transit engine with GitHub Actions OIDC auth
def create_transit_signer_github_actions(
    vault_url: str,
    role: str,
    transit_mount_path: str = "transit",
    key_name: str = "algorand-key",
    oidc_mount_path: str = "oidc",
    audience: str = "vault",
) -> HashicorpVaultTransactionSigner:
    """
    Create a HashiCorp Vault signer with Transit engine using GitHub Actions OIDC authentication

    Args:
        vault_url: URL of the HashiCorp Vault instance
        role: OIDC role name configured for GitHub Actions
        transit_mount_path: Mount path for the transit secrets engine (default: "transit")
        key_name: Name of the key in Vault's transit engine
        oidc_mount_path: Mount path for OIDC auth method (default: "oidc")
        audience: Audience for GitHub OIDC token (default: "vault")

    Note: This function should only be called from within GitHub Actions with 'id-token: write' permission
    """
    vault_auth = GitHubActionsAuth(
        role=role, mount_point=oidc_mount_path, audience=audience
    )
    transit_engine = TransitSecretEngine(
        vault_url=vault_url, vault_auth=vault_auth, mount_path=transit_mount_path
    )

    return HashicorpVaultTransactionSigner(
        secret_engine=transit_engine,
        key_name=key_name,
    )


def create_transit_multisig_signer(
    vault_url: str,
    vault_token: str,
    msig: Multisig,
    key_names: list[str],
    transit_mount_path: str = "transit",
) -> HashicorpVaultMultisigTransactionSigner:
    """
    Create a HashiCorp Vault signer with Transit engine for multisig (backwards compatible)

    Args:
        vault_url: URL of the HashiCorp Vault instance
        vault_token: Authentication token for Vault
        transit_mount_path: Mount path for the transit secrets engine (default: "transit")
        msig: Multisig configuration
        key_names: list of key names in Vault's transit engine
    """
    vault_auth = TokenAuth(token=vault_token)
    transit_engine = TransitSecretEngine(
        vault_url=vault_url, vault_auth=vault_auth, mount_path=transit_mount_path
    )

    return HashicorpVaultMultisigTransactionSigner(
        secret_engine=transit_engine, key_names=key_names, msig=msig
    )


# Utility function to create a new key in Vault transit engine with token auth
def create_vault_key(
    vault_url: str, vault_token: str, key_name: str, transit_mount_path: str = "transit"
) -> str:
    """
    Create a new Ed25519 key in Vault transit engine using token authentication

    Args:
        vault_url: URL of the HashiCorp Vault instance
        vault_token: Authentication token for Vault
        key_name: Name for the new key
        transit_mount_path: Mount path for transit engine

    Returns:
        The Algorand address corresponding to the created key
    """
    vault_auth = TokenAuth(token=vault_token)
    return _create_vault_key_with_auth(
        vault_url, vault_auth, key_name, transit_mount_path
    )


# Utility function to create a new key in Vault transit engine with AppRole auth
def create_vault_key_approle(
    vault_url: str,
    role_id: str,
    secret_id: str,
    key_name: str,
    transit_mount_path: str = "transit",
    approle_mount_path: str = "approle",
) -> str:
    """
    Create a new Ed25519 key in Vault transit engine using AppRole authentication

    Args:
        vault_url: URL of the HashiCorp Vault instance
        role_id: AppRole role ID
        secret_id: AppRole secret ID
        key_name: Name for the new key
        transit_mount_path: Mount path for transit engine
        approle_mount_path: Mount path for AppRole auth method

    Returns:
        The Algorand address corresponding to the created key
    """
    vault_auth = AppRoleAuth(
        role_id=role_id, secret_id=secret_id, mount_point=approle_mount_path
    )
    return _create_vault_key_with_auth(
        vault_url, vault_auth, key_name, transit_mount_path
    )


# Internal helper function for key creation
def _create_vault_key_with_auth(
    vault_url: str, vault_auth: VaultAuth, key_name: str, transit_mount_path: str
) -> str:
    """
    Internal function to create a new Ed25519 key in Vault transit engine with any auth method

    Args:
        vault_url: URL of the HashiCorp Vault instance
        vault_auth: Vault authentication method
        key_name: Name for the new key
        transit_mount_path: Mount path for transit engine

    Returns:
        The Algorand address corresponding to the created key
    """
    client = hvac.Client(url=vault_url)
    vault_auth.authenticate(client)

    # Create the key
    client.secrets.transit.create_key(  # type: ignore
        name=key_name, key_type="ed25519", mount_point=transit_mount_path
    )

    # Get the public key
    key_info = client.secrets.transit.read_key(  # type: ignore
        name=key_name, mount_point=transit_mount_path
    )

    # Extract public key and convert to Algorand address
    public_key_b64 = key_info["data"]["keys"]["1"]["public_key"]  # type: ignore
    public_key_bytes = base64.b64decode(public_key_b64)  # type: ignore

    # Convert Ed25519 public key to Algorand address
    address = encoding.encode_address(public_key_bytes)  # type: ignore

    return address  # type: ignore
