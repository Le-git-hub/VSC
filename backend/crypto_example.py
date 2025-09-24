from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import base64
from typing import Tuple

class ECDHEKeyExchange:
    
    def __init__(self):
        """
        Initialize ECDHE with secp256r1 curve
        """

        self.curve = ec.SECP256R1()
        self.private_key = None
        self.public_key = None
    
    def generate_keypair(self) -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
        """Generate a new ECDH keypair"""
        self.private_key = ec.generate_private_key(self.curve)
        self.public_key = self.private_key.public_key()
        return self.private_key, self.public_key
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        if not self.public_key:
            raise ValueError("Must generate keypair first")
        
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def get_public_bytes(self, compressed: bool = True) -> bytes:
        """Get public key in raw bytes format"""
        if not self.public_key:
            raise ValueError("Must generate keypair first")
        
        format_type = (serialization.PublicFormat.CompressedPoint 
                      if compressed else serialization.PublicFormat.UncompressedPoint)
        
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=format_type
        )
    
    def load_public_key_from_pem(self, pem_data: str) -> ec.EllipticCurvePublicKey:
        """Load public key from PEM format"""
        return serialization.load_pem_public_key(pem_data.encode('utf-8'))
    
    def load_public_key_from_bytes(self, key_bytes: bytes) -> ec.EllipticCurvePublicKey:
        """Load public key from raw bytes"""
        return ec.EllipticCurvePublicKey.from_encoded_point(self.curve, key_bytes)
    
    def compute_shared_secret(self, other_public_key: ec.EllipticCurvePublicKey, 
                            key_length: int = 32) -> bytes:
        """
        Compute shared secret using ECDH and derive key using HKDF
        
        Args:
            other_public_key: The other party's public key
            key_length: Length of derived key in bytes (default 32 for AES-256)
        
        Returns:
            Derived shared secret of specified length
        """
        if not self.private_key:
            raise ValueError("Must generate keypair first")
        
        shared_key = self.private_key.exchange(ec.ECDH(), other_public_key)
        
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=None,
            info=b'ECDHE key exchange',
        ).derive(shared_key)
        
        return derived_key
    
    def encrypt_message(self, message: str, shared_secret: bytes) -> dict:
        """
        Encrypt a message using AES-GCM with the shared secret
        
        Returns dict with 'ciphertext', 'nonce', and 'tag' as base64 strings
        """

        nonce = os.urandom(12)

        cipher = Cipher(algorithms.AES(shared_secret), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(message.encode('utf-8')) + encryptor.finalize()
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'nonce': base64.b64encode(nonce).decode('utf-8'),
            'tag': base64.b64encode(encryptor.tag).decode('utf-8')
        }
    
    def decrypt_message(self, encrypted_data: dict, shared_secret: bytes) -> str:
        """
        Decrypt a message using AES-GCM with the shared secret
        
        Args:
            encrypted_data: Dict with 'ciphertext', 'nonce', and 'tag'
            shared_secret: The shared secret key
        
        Returns:
            Decrypted message as string
        """
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        tag = base64.b64decode(encrypted_data['tag'])
        
        cipher = Cipher(algorithms.AES(shared_secret), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext.decode('utf-8')