/**
 * AES-256-GCM encryption utilities for Helix
 * Uses Web Crypto API for browser-native encryption
 */

/**
 * Encryption key wrapper
 */
export type EncryptionKey = CryptoKey;

/**
 * Encrypted data with IV
 */
export interface EncryptedData {
    /** Combined IV + ciphertext + auth tag */
    data: ArrayBuffer;
    /** IV used for encryption (first 12 bytes of data) */
    iv: Uint8Array;
}

/** IV length in bytes (96 bits) */
const IV_LENGTH = 12;

/** Algorithm configuration */
const ALGORITHM = {
    name: 'AES-GCM',
    length: 256,
};

/**
 * Encryption utilities for AES-256-GCM
 */
export class HelixEncryption {
    /**
     * Generate a new random encryption key
     * @returns CryptoKey for AES-256-GCM
     */
    async generateKey(): Promise<EncryptionKey> {
        return crypto.subtle.generateKey(
            { name: ALGORITHM.name, length: ALGORITHM.length },
            true,
            ['encrypt', 'decrypt']
        );
    }

    /**
     * Encrypt data with AES-256-GCM
     * 
     * @param data - Data to encrypt
     * @param key - Encryption key
     * @returns Encrypted data with IV prepended
     * 
     * @example
     * ```typescript
     * const key = await encryption.generateKey();
     * const encrypted = await encryption.encrypt(fileData, key);
     * // Format: [IV (12 bytes)][Ciphertext][Auth Tag (16 bytes)]
     * ```
     */
    async encrypt(data: ArrayBuffer, key: EncryptionKey): Promise<EncryptedData> {
        const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));

        const ciphertext = await crypto.subtle.encrypt(
            { name: ALGORITHM.name, iv },
            key,
            data
        );

        const combined = new Uint8Array(iv.length + ciphertext.byteLength);
        combined.set(iv);
        combined.set(new Uint8Array(ciphertext), iv.length);

        return {
            data: combined.buffer,
            iv,
        };
    }

    /**
     * Decrypt data encrypted with AES-256-GCM
     * 
     * @param encryptedData - Data with IV prepended
     * @param key - Decryption key
     * @returns Decrypted data
     */
    async decrypt(encryptedData: ArrayBuffer, key: EncryptionKey): Promise<ArrayBuffer> {
        const dataArray = new Uint8Array(encryptedData);

        if (dataArray.length < IV_LENGTH + 16) {
            throw new Error('Invalid encrypted data: too short');
        }

        const iv = dataArray.slice(0, IV_LENGTH);
        const ciphertext = dataArray.slice(IV_LENGTH);

        return crypto.subtle.decrypt(
            { name: ALGORITHM.name, iv },
            key,
            ciphertext
        );
    }

    /**
     * Export key to base64 string for storage
     * @param key - CryptoKey to export
     * @returns Base64 encoded key
     */
    async exportKey(key: EncryptionKey): Promise<string> {
        const raw = await crypto.subtle.exportKey('raw', key);
        return Buffer.from(raw).toString('base64');
    }

    /**
     * Import key from base64 string
     * @param keyString - Base64 encoded key
     * @returns CryptoKey for decryption
     */
    async importKey(keyString: string): Promise<EncryptionKey> {
        const raw = Buffer.from(keyString, 'base64');

        if (raw.length !== 32) {
            throw new Error('Invalid key length: expected 32 bytes');
        }

        return crypto.subtle.importKey(
            'raw',
            raw,
            { name: ALGORITHM.name },
            true,
            ['encrypt', 'decrypt']
        );
    }

    /**
     * Generate a key derivation from password (for backup)
     * 
     * @param password - User password
     * @param salt - Salt for derivation
     * @returns Derived key
     */
    async deriveKey(password: string, salt: Uint8Array): Promise<EncryptionKey> {
        const passwordKey = await crypto.subtle.importKey(
            'raw',
            new TextEncoder().encode(password),
            'PBKDF2',
            false,
            ['deriveBits', 'deriveKey']
        );

        return crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt,
                iterations: 100000,
                hash: 'SHA-256',
            },
            passwordKey,
            { name: ALGORITHM.name, length: ALGORITHM.length },
            true,
            ['encrypt', 'decrypt']
        );
    }

    /**
     * Generate a random salt for key derivation
     * @returns 16-byte salt
     */
    generateSalt(): Uint8Array {
        return crypto.getRandomValues(new Uint8Array(16));
    }

    /**
     * Encrypt a string (helper for filenames, etc.)
     * @param text - String to encrypt
     * @param key - Encryption key
     * @returns Base64 encoded encrypted data
     */
    async encryptString(text: string, key: EncryptionKey): Promise<string> {
        const data = new TextEncoder().encode(text);
        const encrypted = await this.encrypt(data.buffer, key);
        return Buffer.from(encrypted.data).toString('base64');
    }

    /**
     * Decrypt a string
     * @param encryptedBase64 - Base64 encoded encrypted data
     * @param key - Decryption key
     * @returns Decrypted string
     */
    async decryptString(encryptedBase64: string, key: EncryptionKey): Promise<string> {
        const data = Buffer.from(encryptedBase64, 'base64');
        const decrypted = await this.decrypt(data.buffer, key);
        return new TextDecoder().decode(decrypted);
    }
}

/**
 * Export a key to base64 string (standalone function)
 */
export async function exportKey(key: EncryptionKey): Promise<string> {
    const raw = await crypto.subtle.exportKey('raw', key);
    return Buffer.from(raw).toString('base64');
}

/**
 * Import a key from base64 string (standalone function)
 */
export async function importKey(keyString: string): Promise<EncryptionKey> {
    const raw = Buffer.from(keyString, 'base64');
    return crypto.subtle.importKey(
        'raw',
        raw,
        { name: ALGORITHM.name },
        true,
        ['encrypt', 'decrypt']
    );
}

/**
 * Encrypt data with a base64 key string
 */
export async function encryptWithKeyString(
    data: ArrayBuffer,
    keyString: string
): Promise<ArrayBuffer> {
    const key = await importKey(keyString);
    const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));
    const ciphertext = await crypto.subtle.encrypt(
        { name: ALGORITHM.name, iv },
        key,
        data
    );
    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv);
    combined.set(new Uint8Array(ciphertext), iv.length);
    return combined.buffer;
}

/**
 * Decrypt data with a base64 key string
 */
export async function decryptWithKeyString(
    encryptedData: ArrayBuffer,
    keyString: string
): Promise<ArrayBuffer> {
    const key = await importKey(keyString);
    const dataArray = new Uint8Array(encryptedData);
    const iv = dataArray.slice(0, IV_LENGTH);
    const ciphertext = dataArray.slice(IV_LENGTH);
    return crypto.subtle.decrypt(
        { name: ALGORITHM.name, iv },
        key,
        ciphertext
    );
}

// AES-256-GCM
