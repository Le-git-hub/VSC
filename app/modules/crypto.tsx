


export interface EncryptedMessage {
  ciphertext: string;
  iv: string;
}

export async function generateIdentityKey(): Promise<CryptoKeyPair> {
  return crypto.subtle.generateKey(
    {
      name: "ECDH",
      namedCurve: "P-256",
    },
    true,
    ["deriveKey"]
  );
}

export async function exportKey(key: CryptoKey, format: 'spki' | 'pkcs8' | 'raw'): Promise<string> {
  const exported = await crypto.subtle.exportKey(format, key);
  return btoa(String.fromCharCode(...new Uint8Array(exported)));
}

export async function importKey(base64Key: string, keyType: 'spki' | 'pkcs8' | 'raw'): Promise<CryptoKey> {
  const binary = Uint8Array.from(atob(base64Key), (c) => c.charCodeAt(0));
  
  switch (keyType) {
    case 'spki':
      return crypto.subtle.importKey(
        "spki",
        binary,
        { name: "ECDH", namedCurve: "P-256" },
        true,
        []
      );
    case 'pkcs8':
      return crypto.subtle.importKey(
        "pkcs8",
        binary,
        { name: "ECDH", namedCurve: "P-256" },
        true,
        ["deriveKey"]
      );
    case 'raw':
      return crypto.subtle.importKey(
        "raw",
        binary,
        { name: "AES-GCM" },
        true,
        ["encrypt", "decrypt"]
      );
  }
}

export async function deriveSharedSecret(
  privateKey: CryptoKey,
  peerPublicKey: CryptoKey
): Promise<CryptoKey> {
  return crypto.subtle.deriveKey(
    { name: "ECDH", public: peerPublicKey },
    privateKey,
    { name: "AES-GCM", length: 256 },
    true,
    ["encrypt", "decrypt"]
  );
}

export async function encryptMessage(
  sharedKey: CryptoKey,
  plaintext: string
): Promise<EncryptedMessage> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(plaintext);

  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    sharedKey,
    encoded
  );

  return {
    ciphertext: btoa(String.fromCharCode(...new Uint8Array(ciphertext))),
    iv: btoa(String.fromCharCode(...iv)),
  };
}

export async function decryptMessage(
  sharedKey: CryptoKey,
  data: EncryptedMessage
): Promise<string> {
  const ciphertext = Uint8Array.from(atob(data.ciphertext), (c) => c.charCodeAt(0));
  const iv = Uint8Array.from(atob(data.iv), (c) => c.charCodeAt(0));

  const decrypted = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    sharedKey,
    ciphertext
  );

  return new TextDecoder().decode(decrypted);
}
export function getChatId(user1: number, user2: number): string {
    const sortedIds = [user1, user2].sort();
    return `${sortedIds[0]}:${sortedIds[1]}`;
}
