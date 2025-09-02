/**
 * Type definitions for Helix SDK
 */

/**
 * Supported Solana networks
 */
export type HelixNetwork = 'mainnet-beta' | 'devnet' | 'testnet';

/**
 * Client configuration
 */
export interface HelixConfig {
    network: HelixNetwork;
    rpcEndpoint: string;
    apiBaseUrl: string;
}

/**
 * Upload options
 */
export interface UploadOptions {
    /** Original filename */
    name: string;
    /** MIME type of the file */
    mimeType: string;
    /** Whether to encrypt the file (default: true) */
    encrypt?: boolean;
    /** Optional callback for upload progress */
    onProgress?: (progress: UploadProgress) => void;
}

/**
 * Upload progress information
 */
export interface UploadProgress {
    /** Current phase of upload */
    phase: 'encrypting' | 'uploading' | 'registering' | 'complete';
    /** Progress percentage (0-100) */
    percent: number;
    /** Bytes uploaded (during upload phase) */
    bytesUploaded?: number;
    /** Total bytes to upload */
    totalBytes?: number;
}

/**
 * Upload result
 */
export interface UploadResult {
    /** Arweave transaction ID */
    transactionId: string;
    /** Base64 encryption key (if encrypted) */
    encryptionKey?: string;
    /** Direct Arweave URL */
    arweaveUrl: string;
    /** File record in Helix database */
    fileId: string;
}

/**
 * Download options
 */
export interface DownloadOptions {
    /** Encryption key for decryption */
    encryptionKey?: string;
    /** Optional callback for download progress */
    onProgress?: (progress: DownloadProgress) => void;
}

/**
 * Download progress information
 */
export interface DownloadProgress {
    /** Current phase */
    phase: 'downloading' | 'decrypting' | 'complete';
    /** Progress percentage (0-100) */
    percent: number;
    /** Bytes downloaded */
    bytesDownloaded?: number;
    /** Total bytes */
    totalBytes?: number;
}

/**
 * Share options
 */
export interface ShareOptions {
    /** Specific wallet that can access (optional, public if not set) */
    recipient?: string;
    /** Expiration date */
    expiresAt?: Date;
    /** Maximum number of downloads */
    maxDownloads?: number;
}

/**
 * File metadata
 */
export interface FileMetadata {
    /** Original filename (decrypted) */
    name: string;
    /** MIME type */
    mimeType: string;
    /** File size in bytes */
    size: number;
    /** Whether the content is encrypted */
    isEncrypted: boolean;
    /** Upload timestamp */
    createdAt: Date;
    /** Last update timestamp */
    updatedAt?: Date;
}

/**
 * Storage statistics
 */
export interface StorageStats {
    /** Total number of files */
    totalFiles: number;
    /** Total storage used in bytes */
    totalBytes: number;
    /** Number of encrypted files */
    encryptedFiles: number;
    /** Number of active share links */
    activeShares: number;
}

/**
 * API error response
 */
export interface ApiError {
    /** Error code */
    code: string;
    /** Human-readable message */
    message: string;
    /** Additional details */
    details?: Record<string, unknown>;
}

/**
 * Rate limit information from response headers
 */
export interface RateLimitInfo {
    /** Maximum requests allowed */
    limit: number;
    /** Remaining requests in window */
    remaining: number;
    /** Unix timestamp when limit resets */
    reset: number;
}

/**
 * Irys receipt from upload
 */
export interface IrysReceipt {
    /** Transaction ID */
    id: string;
    /** Timestamp */
    timestamp: number;
    /** Data size */
    size: number;
    /** Signature */
    signature: string;
}

/**
 * Arweave transaction status
 */
export interface ArweaveStatus {
    /** Number of confirmations */
    confirmations: number;
    /** Block height */
    blockHeight?: number;
    /** Block hash */
    blockHash?: string;
}

/**
 * Key storage options
 */
export interface KeyStorageOptions {
    /** Storage key prefix */
    prefix?: string;
    /** Whether to use sessionStorage instead of localStorage */
    useSession?: boolean;
}

/**
 * Stored key data
 */
export interface StoredKey {
    /** Base64 encoded key */
    key: string;
    /** Wallet address that owns this key */
    walletAddress: string;
    /** Transaction ID this key is for */
    transactionId: string;
    /** Timestamp when stored */
    createdAt: number;
}

/**
 * Wallet connection status
 */
export type WalletStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

/**
 * SDK event types
 */
export type HelixEventType =
    | 'connect'
    | 'disconnect'
    | 'authenticate'
    | 'upload:start'
    | 'upload:progress'
    | 'upload:complete'
    | 'upload:error'
    | 'download:start'
    | 'download:progress'
    | 'download:complete'
    | 'download:error';

/**
 * SDK event payload
 */
export interface HelixEvent<T = unknown> {
    type: HelixEventType;
    timestamp: number;
    data?: T;
}

/**
 * Event listener callback
 */
export type HelixEventListener<T = unknown> = (event: HelixEvent<T>) => void;
