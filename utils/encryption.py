"""
Brambler encryption system for expedition name anonymization.
Provides secure AES encryption for name mappings with proper key derivation.
Enhanced with Fernet encryption and multiple anonymization levels.
"""

import os
import base64
import hashlib
import secrets
import logging
from typing import Dict, Optional, Tuple, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from dataclasses import dataclass
import json


logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Custom exception for encryption-related errors."""
    pass


@dataclass
class EncryptionResult:
    """Result of encryption operation."""
    encrypted_data: str
    salt: str
    key_id: str


@dataclass
class DecryptionResult:
    """Result of decryption operation."""
    decrypted_data: Dict[str, str]
    success: bool
    error_message: Optional[str] = None


class ExpeditionEncryption:
    """
    Secure encryption service for expedition name mapping.
    Uses AES-256-GCM for authenticated encryption.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._backend = default_backend()

    def generate_user_master_key(self, owner_chat_id: int) -> str:
        """
        Generate a SINGLE master key for a user (based on chat_id).
        This key will be used for ALL expeditions owned by this user.

        Args:
            owner_chat_id: Owner's Telegram chat ID

        Returns:
            Base64-encoded master key (consistent for this user)
        """
        try:
            # Create a deterministic seed from the user's chat_id
            # Using a fixed secret to ensure the same chat_id always produces the same key
            seed_data = f"user_master_key_v1_{owner_chat_id}"
            seed_bytes = seed_data.encode('utf-8')

            # Generate a fixed salt based on chat_id (deterministic)
            # This ensures the same chat_id always produces the same master key
            salt_seed = f"salt_for_user_{owner_chat_id}_v1"
            salt = hashlib.sha256(salt_seed.encode('utf-8')).digest()  # 256-bit deterministic salt

            # Generate a strong key using PBKDF2 with deterministic inputs
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256-bit key
                salt=salt,
                iterations=100000,  # Strong iteration count
                backend=self._backend
            )

            key = kdf.derive(seed_bytes)

            # Combine salt and key for storage
            key_data = salt + key
            encoded_key = base64.urlsafe_b64encode(key_data).decode('utf-8')

            self.logger.info(f"Generated user master key for chat_id {owner_chat_id}")
            return encoded_key

        except Exception as e:
            self.logger.error(f"Failed to generate user master key: {e}", exc_info=True)
            raise EncryptionError(f"User master key generation failed: {str(e)}")

    def generate_owner_key(self, expedition_id: int, owner_user_id: int, use_master_key: bool = True) -> str:
        """
        Generate a secure owner key for expedition encryption.

        By default, uses the user's master key (consistent across all expeditions).
        Can optionally generate per-expedition keys for backward compatibility.

        Args:
            expedition_id: Expedition identifier
            owner_user_id: Owner's user ID (chat_id)
            use_master_key: If True, returns the user's master key (default)

        Returns:
            Base64-encoded owner key
        """
        try:
            if use_master_key:
                # Use the user's master key (consistent for all their expeditions)
                return self.generate_user_master_key(owner_user_id)

            # Legacy mode: Generate per-expedition key (with randomness)
            # Create a unique seed from expedition and owner data
            seed_data = f"expedition_{expedition_id}_owner_{owner_user_id}_{secrets.token_hex(16)}"
            seed_bytes = seed_data.encode('utf-8')

            # Generate a strong random key using PBKDF2
            salt = os.urandom(32)  # 256-bit salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256-bit key
                salt=salt,
                iterations=100000,  # Strong iteration count
                backend=self._backend
            )

            key = kdf.derive(seed_bytes)

            # Combine salt and key for storage
            key_data = salt + key
            encoded_key = base64.urlsafe_b64encode(key_data).decode('utf-8')

            self.logger.info(f"Generated owner key for expedition {expedition_id}")
            return encoded_key

        except Exception as e:
            self.logger.error(f"Failed to generate owner key: {e}", exc_info=True)
            raise EncryptionError(f"Key generation failed: {str(e)}")

    def _derive_key_from_owner_key(self, owner_key: str) -> Tuple[bytes, bytes]:
        """
        Derive encryption key and salt from owner key.

        Args:
            owner_key: Base64-encoded owner key

        Returns:
            Tuple of (key, salt)
        """
        try:
            key_data = base64.urlsafe_b64decode(owner_key.encode('utf-8'))

            if len(key_data) < 64:  # 32 bytes salt + 32 bytes key
                raise EncryptionError("Invalid owner key format")

            salt = key_data[:32]
            key = key_data[32:64]

            return key, salt

        except Exception as e:
            raise EncryptionError(f"Invalid owner key: {str(e)}")

    def encrypt_name_mapping(self, expedition_id: int, name_mapping: Dict[str, str], owner_key: str) -> str:
        """
        Encrypt name mapping dictionary with owner key.

        Args:
            expedition_id: Expedition identifier
            name_mapping: Dictionary mapping original names to pirate names
            owner_key: Owner's encryption key

        Returns:
            Base64-encoded encrypted mapping
        """
        try:
            # Derive encryption key
            key, salt = self._derive_key_from_owner_key(owner_key)

            # Prepare data for encryption
            mapping_data = {
                'expedition_id': expedition_id,
                'mapping': name_mapping,
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }

            plaintext = json.dumps(mapping_data, sort_keys=True).encode('utf-8')

            # Generate random nonce for GCM
            nonce = os.urandom(12)  # 96-bit nonce for GCM

            # Create cipher with AES-GCM mode
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=self._backend)
            encryptor = cipher.encryptor()

            # Encrypt data
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()

            # Combine nonce, tag, and ciphertext
            encrypted_data = nonce + encryptor.tag + ciphertext

            # Encode for storage
            encoded_data = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

            self.logger.info(f"Encrypted name mapping for expedition {expedition_id}")
            return encoded_data

        except Exception as e:
            self.logger.error(f"Encryption failed: {e}", exc_info=True)
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt_name_mapping(self, encrypted_mapping: str, owner_key: str) -> Optional[Dict[str, str]]:
        """
        Decrypt name mapping with owner key.

        Args:
            encrypted_mapping: Base64-encoded encrypted mapping
            owner_key: Owner's encryption key

        Returns:
            Decrypted name mapping dictionary or None if decryption fails
        """
        try:
            # Derive decryption key
            key, salt = self._derive_key_from_owner_key(owner_key)

            # Decode encrypted data
            encrypted_data = base64.urlsafe_b64decode(encrypted_mapping.encode('utf-8'))

            if len(encrypted_data) < 28:  # 12 bytes nonce + 16 bytes tag
                raise EncryptionError("Invalid encrypted data format")

            # Extract components
            nonce = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]

            # Create cipher with AES-GCM mode
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=self._backend)
            decryptor = cipher.decryptor()

            # Decrypt data
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Parse JSON data
            mapping_data = json.loads(plaintext.decode('utf-8'))

            # Validate data structure
            if 'mapping' not in mapping_data or 'expedition_id' not in mapping_data:
                raise EncryptionError("Invalid decrypted data structure")

            self.logger.info(f"Decrypted name mapping for expedition {mapping_data['expedition_id']}")
            return mapping_data  # Return full mapping_data, not just the mapping

        except Exception as e:
            self.logger.error(f"Decryption failed: {e}", exc_info=True)
            return None

    def verify_owner_key(self, expedition_id: int, owner_key: str, test_mapping: Dict[str, str]) -> bool:
        """
        Verify owner key by testing encryption/decryption roundtrip.

        Args:
            expedition_id: Expedition identifier
            owner_key: Owner's encryption key
            test_mapping: Test mapping to verify with

        Returns:
            True if key is valid, False otherwise
        """
        try:
            # Test encryption
            encrypted = self.encrypt_name_mapping(expedition_id, test_mapping, owner_key)

            # Test decryption
            decrypted = self.decrypt_name_mapping(encrypted, owner_key)

            # Verify roundtrip
            return decrypted == test_mapping

        except Exception as e:
            self.logger.warning(f"Owner key verification failed: {e}")
            return False

    def create_secure_hash(self, data: str) -> str:
        """
        Create a secure hash of data for integrity checking.

        Args:
            data: Data to hash

        Returns:
            Hex-encoded hash
        """
        try:
            hash_obj = hashlib.sha256()
            hash_obj.update(data.encode('utf-8'))
            return hash_obj.hexdigest()

        except Exception as e:
            self.logger.error(f"Hash creation failed: {e}")
            raise EncryptionError(f"Hash creation failed: {str(e)}")

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a secure random token.

        Args:
            length: Token length in bytes

        Returns:
            Hex-encoded secure token
        """
        try:
            return secrets.token_hex(length)
        except Exception as e:
            self.logger.error(f"Token generation failed: {e}")
            raise EncryptionError(f"Token generation failed: {str(e)}")

    def constant_time_compare(self, a: str, b: str) -> bool:
        """
        Perform constant-time string comparison to prevent timing attacks.

        Args:
            a: First string
            b: Second string

        Returns:
            True if strings are equal, False otherwise
        """
        try:
            return secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8'))
        except Exception:
            return False


# Global encryption instance
_encryption_instance = None


def get_encryption_service() -> ExpeditionEncryption:
    """Get the global encryption service instance."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = ExpeditionEncryption()
    return _encryption_instance


# Convenience functions
def generate_owner_key(expedition_id: int, owner_user_id: int) -> str:
    """Generate owner key for expedition."""
    return get_encryption_service().generate_owner_key(expedition_id, owner_user_id)


def encrypt_mapping(expedition_id: int, name_mapping: Dict[str, str], owner_key: str) -> str:
    """Encrypt name mapping with owner key."""
    return get_encryption_service().encrypt_name_mapping(expedition_id, name_mapping, owner_key)


def decrypt_mapping(encrypted_mapping: str, owner_key: str) -> Optional[Dict[str, str]]:
    """Decrypt name mapping with owner key."""
    return get_encryption_service().decrypt_name_mapping(encrypted_mapping, owner_key)


def verify_key(expedition_id: int, owner_key: str, test_mapping: Dict[str, str]) -> bool:
    """Verify owner key validity."""
    return get_encryption_service().verify_owner_key(expedition_id, owner_key, test_mapping)


class SecureKeyManager:
    """Manages encryption keys with proper security practices."""

    @staticmethod
    def generate_salt() -> bytes:
        """Generate a random salt for key derivation."""
        return os.urandom(16)

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # 100k iterations for security
        )
        return kdf.derive(password.encode('utf-8'))

    @staticmethod
    def generate_fernet_key(derived_key: bytes) -> Fernet:
        """Create Fernet cipher from derived key."""
        # Encode the derived key to base64 for Fernet
        fernet_key = base64.urlsafe_b64encode(derived_key)
        return Fernet(fernet_key)

    @staticmethod
    def generate_admin_key() -> str:
        """Generate secure admin key for expeditions."""
        return base64.b64encode(secrets.token_bytes(32)).decode()

    @staticmethod
    def validate_key(key: str) -> bool:
        """Validate if key format is correct."""
        try:
            decoded = base64.b64decode(key.encode())
            return len(decoded) >= 16  # Minimum key length
        except Exception:
            return False


class BramblerEncryption:
    """
    Main encryption service for Brambler name anonymization.
    Provides AES encryption with PBKDF2 key derivation using Fernet.
    """

    def __init__(self):
        self.key_manager = SecureKeyManager()

    def encrypt_name_mapping(
        self,
        name_mappings: Dict[str, str],
        password: str,
        salt: Optional[bytes] = None
    ) -> EncryptionResult:
        """
        Encrypt name mappings using AES encryption.

        Args:
            name_mappings: Dictionary of original_name -> pirate_name
            password: Password for encryption (expedition key)
            salt: Optional salt (generated if not provided)

        Returns:
            EncryptionResult with encrypted data and metadata
        """
        try:
            # Generate salt if not provided
            if salt is None:
                salt = self.key_manager.generate_salt()

            # Derive key from password
            derived_key = self.key_manager.derive_key_from_password(password, salt)

            # Create Fernet cipher
            fernet = self.key_manager.generate_fernet_key(derived_key)

            # Serialize name mappings to JSON
            json_data = json.dumps(name_mappings, ensure_ascii=False)

            # Encrypt the data
            encrypted_data = fernet.encrypt(json_data.encode('utf-8'))

            # Encode for storage
            encrypted_b64 = base64.b64encode(encrypted_data).decode()
            salt_b64 = base64.b64encode(salt).decode()

            # Generate key ID for tracking
            key_id = secrets.token_hex(8)

            logger.info(f"Successfully encrypted name mappings with key ID: {key_id}")

            return EncryptionResult(
                encrypted_data=encrypted_b64,
                salt=salt_b64,
                key_id=key_id
            )

        except Exception as e:
            logger.error(f"Failed to encrypt name mappings: {e}")
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt_name_mapping(
        self,
        encrypted_data: str,
        salt: str,
        password: str
    ) -> DecryptionResult:
        """
        Decrypt name mappings.

        Args:
            encrypted_data: Base64 encoded encrypted data
            salt: Base64 encoded salt
            password: Password for decryption

        Returns:
            DecryptionResult with decrypted mappings
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            salt_bytes = base64.b64decode(salt.encode())

            # Derive key from password
            derived_key = self.key_manager.derive_key_from_password(password, salt_bytes)

            # Create Fernet cipher
            fernet = self.key_manager.generate_fernet_key(derived_key)

            # Decrypt the data
            decrypted_bytes = fernet.decrypt(encrypted_bytes)

            # Parse JSON
            json_data = decrypted_bytes.decode('utf-8')
            name_mappings = json.loads(json_data)

            logger.info("Successfully decrypted name mappings")

            return DecryptionResult(
                decrypted_data=name_mappings,
                success=True
            )

        except Exception as e:
            logger.error(f"Failed to decrypt name mappings: {e}")
            return DecryptionResult(
                decrypted_data={},
                success=False,
                error_message=str(e)
            )

    def encrypt_single_value(self, value: str, password: str) -> Tuple[str, str]:
        """
        Encrypt a single string value.

        Args:
            value: String to encrypt
            password: Encryption password

        Returns:
            Tuple of (encrypted_data, salt) both base64 encoded
        """
        try:
            salt = self.key_manager.generate_salt()
            derived_key = self.key_manager.derive_key_from_password(password, salt)
            fernet = self.key_manager.generate_fernet_key(derived_key)

            encrypted_data = fernet.encrypt(value.encode('utf-8'))

            return (
                base64.b64encode(encrypted_data).decode(),
                base64.b64encode(salt).decode()
            )

        except Exception as e:
            logger.error(f"Failed to encrypt single value: {e}")
            raise EncryptionError(f"Single value encryption failed: {str(e)}")

    def decrypt_single_value(self, encrypted_data: str, salt: str, password: str) -> str:
        """
        Decrypt a single string value.

        Args:
            encrypted_data: Base64 encoded encrypted data
            salt: Base64 encoded salt
            password: Decryption password

        Returns:
            Decrypted string value
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            salt_bytes = base64.b64decode(salt.encode())

            derived_key = self.key_manager.derive_key_from_password(password, salt_bytes)
            fernet = self.key_manager.generate_fernet_key(derived_key)

            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')

        except Exception as e:
            logger.error(f"Failed to decrypt single value: {e}")
            raise EncryptionError(f"Single value decryption failed: {str(e)}")


# Utility functions for quick operations
def generate_expedition_keys(expedition_id: int, owner_chat_id: int) -> Tuple[str, str]:
    """Quick function to generate expedition keys."""
    key_manager = SecureKeyManager()
    owner_key = generate_owner_key(expedition_id, owner_chat_id)
    admin_key = key_manager.generate_admin_key()
    return owner_key, admin_key


def encrypt_names(name_mappings: Dict[str, str], key: str) -> EncryptionResult:
    """Quick function to encrypt name mappings."""
    brambler = BramblerEncryption()
    return brambler.encrypt_name_mapping(name_mappings, key)


def decrypt_names(encrypted_data: str, salt: str, key: str) -> DecryptionResult:
    """Quick function to decrypt name mappings."""
    brambler = BramblerEncryption()
    return brambler.decrypt_name_mapping(encrypted_data, salt, key)


def validate_encryption_key(key: str) -> bool:
    """Quick function to validate encryption key format."""
    key_manager = SecureKeyManager()
    return key_manager.validate_key(key)


# Product Name Encryption Functions
import random
import string


def generate_encrypted_product_name(expedition_id: int, product_id: int, item_sequence: int) -> str:
    """
    Generate a unique encrypted product name for expedition items.

    Format: PREFIX-XXXX where:
    - PREFIX: Random from ['ITEM', 'CARGO', 'GOODS', 'SUPPLY']
    - XXXX: 4-character alphanumeric code based on IDs

    Args:
        expedition_id: The expedition ID
        product_id: The product ID
        item_sequence: Sequence number of item in expedition

    Returns:
        Encrypted name like "ITEM-A7B3" or "CARGO-X9Z2"

    Example:
        >>> name = generate_encrypted_product_name(1, 100, 0)
        >>> print(name)  # "CARGO-K7M9"
    """
    prefixes = ['ITEM', 'CARGO', 'GOODS', 'SUPPLY']

    # Use expedition and product IDs to generate deterministic but obscured code
    seed_value = (expedition_id * 1000 + product_id * 100 + item_sequence)
    random.seed(seed_value)

    # Generate 4-character alphanumeric code
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(4))

    # Select prefix based on seed
    prefix = prefixes[seed_value % len(prefixes)]

    # Reset random seed to avoid affecting other operations
    random.seed()

    logger.debug(f"Generated encrypted product name: {prefix}-{code} for expedition {expedition_id}, product {product_id}, sequence {item_sequence}")

    return f"{prefix}-{code}"


def generate_encrypted_product_name_random(expedition_id: int) -> str:
    """
    Generate a completely random encrypted product name.

    Args:
        expedition_id: The expedition ID (for logging purposes)

    Returns:
        Random encrypted name like "CARGO-K7M9"

    Example:
        >>> name = generate_encrypted_product_name_random(1)
        >>> print(name)  # "MERCH-P3Q8" (random each time)
    """
    prefixes = ['ITEM', 'CARGO', 'GOODS', 'SUPPLY', 'MERCH', 'STOCK']
    prefix = random.choice(prefixes)

    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(4))

    encrypted_name = f"{prefix}-{code}"
    logger.debug(f"Generated random encrypted product name: {encrypted_name} for expedition {expedition_id}")

    return encrypted_name