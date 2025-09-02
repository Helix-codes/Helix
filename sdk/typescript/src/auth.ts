import { PublicKey } from '@solana/web3.js';
import nacl from 'tweetnacl';

/**
 * Response from nonce request
 */
export interface NonceResponse {
    nonce: string;
}

/**
 * Response from authentication verification
 */
export interface AuthToken {
    token: string;
    expiresAt: string;
}

/**
 * Authentication utilities for Helix API
 * Uses wallet signatures for passwordless auth
 */
export class HelixAuth {
    private apiBaseUrl: string;
    private timeout: number;

    constructor(apiBaseUrl: string, timeout: number = 30000) {
        this.apiBaseUrl = apiBaseUrl;
        this.timeout = timeout;
    }

    /**
     * Request a nonce for wallet signature
     * @param walletAddress - Solana wallet address
     * @returns Nonce string to sign
     */
    async getNonce(walletAddress: string): Promise<NonceResponse> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(
                `${this.apiBaseUrl}/api/auth/nonce?wallet=${encodeURIComponent(walletAddress)}`,
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    signal: controller.signal,
                }
            );

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `Failed to get nonce: ${response.status}`);
            }

            return response.json();
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * Verify signature and get auth token
     * @param walletAddress - Solana wallet address
     * @param signature - Base64 encoded signature
     * @param nonce - Original nonce that was signed
     * @returns JWT token for authenticated requests
     */
    async verify(
        walletAddress: string,
        signature: string,
        nonce: string
    ): Promise<AuthToken> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    wallet: walletAddress,
                    signature,
                    nonce,
                }),
                signal: controller.signal,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `Failed to verify signature: ${response.status}`);
            }

            return response.json();
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * Create the message to be signed
     * @param nonce - Nonce from server
     * @returns Message string
     */
    static createSignMessage(nonce: string): string {
        return `Sign in to Helix: ${nonce}`;
    }

    /**
     * Verify a signature locally (server-side utility)
     * @param walletAddress - Solana wallet address
     * @param message - Original message that was signed
     * @param signature - Base64 encoded signature
     * @returns Whether the signature is valid
     */
    static verifySignature(
        walletAddress: string,
        message: string,
        signature: string
    ): boolean {
        try {
            const publicKey = new PublicKey(walletAddress);
            const messageBytes = new TextEncoder().encode(message);
            const signatureBytes = Buffer.from(signature, 'base64');

            return nacl.sign.detached.verify(
                messageBytes,
                signatureBytes,
                publicKey.toBytes()
            );
        } catch {
            return false;
        }
    }

    /**
     * Parse a JWT token to extract claims
     * @param token - JWT token string
     * @returns Decoded token payload
     */
    static parseToken(token: string): {
        wallet: string;
        exp: number;
        iat: number;
    } {
        const parts = token.split('.');
        if (parts.length !== 3) {
            throw new Error('Invalid token format');
        }

        const payload = Buffer.from(parts[1], 'base64url').toString('utf-8');
        return JSON.parse(payload);
    }

    /**
     * Check if a token is expired
     * @param token - JWT token string
     * @returns Whether the token is expired
     */
    static isTokenExpired(token: string): boolean {
        try {
            const { exp } = HelixAuth.parseToken(token);
            return Date.now() >= exp * 1000;
        } catch {
            return true;
        }
    }
}
