import { Connection, PublicKey } from '@solana/web3.js';
import { WalletAdapter } from '@solana/wallet-adapter-base';
import { HelixAuth } from './auth';
import { HelixEncryption } from './encryption';
import { HelixFiles } from './files';
import { HelixNetwork, HelixConfig } from './types';

/**
 * Configuration options for HelixClient
 */
export interface HelixClientConfig {
    /** Solana network to connect to */
    network?: HelixNetwork;
    /** Custom RPC endpoint URL */
    rpcEndpoint?: string;
    /** Helix API base URL */
    apiBaseUrl?: string;
    /** Request timeout in milliseconds */
    timeout?: number;
    /** Enable debug logging */
    debug?: boolean;
}

/**
 * Default configuration values
 */
const DEFAULT_CONFIG: Required<HelixClientConfig> = {
    network: 'mainnet-beta',
    rpcEndpoint: 'https://api.mainnet-beta.solana.com',
    apiBaseUrl: 'https://heyx-production.up.railway.app',
    timeout: 30000,
    debug: false,
};

/**
 * Main client for interacting with Helix storage
 * 
 * @example
 * ```typescript
 * const client = new HelixClient({
 *   network: 'mainnet-beta',
 *   apiBaseUrl: 'https://helix.storage'
 * });
 * 
 * await client.connect(walletAdapter);
 * const files = await client.files.list();
 * ```
 */
export class HelixClient {
    private config: Required<HelixClientConfig>;
    private connection: Connection;
    private wallet: WalletAdapter | null = null;
    private authToken: string | null = null;

    /** Authentication module */
    public readonly auth: HelixAuth;

    /** Encryption utilities */
    public readonly encryption: HelixEncryption;

    /** File operations */
    public readonly files: HelixFiles;

    /**
     * Create a new HelixClient instance
     * @param config - Client configuration options
     */
    constructor(config: HelixClientConfig = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };

        if (this.config.network === 'devnet') {
            this.config.rpcEndpoint = 'https://api.devnet.solana.com';
        }

        this.connection = new Connection(this.config.rpcEndpoint, 'confirmed');

        this.auth = new HelixAuth(this.config.apiBaseUrl, this.config.timeout);
        this.encryption = new HelixEncryption();
        this.files = new HelixFiles(
            this.config.apiBaseUrl,
            this.config.timeout,
            () => this.authToken
        );
    }

    /**
     * Connect a wallet adapter
     * @param wallet - Solana wallet adapter instance
     */
    async connect(wallet: WalletAdapter): Promise<void> {
        if (!wallet.publicKey) {
            throw new Error('Wallet not connected');
        }

        this.wallet = wallet;
        this.log(`Wallet connected: ${wallet.publicKey.toBase58()}`);
    }

    /**
     * Authenticate with the Helix API using wallet signature
     * @returns JWT token for authenticated requests
     */
    async authenticate(): Promise<string> {
        if (!this.wallet || !this.wallet.publicKey) {
            throw new Error('Wallet not connected');
        }

        const walletAddress = this.wallet.publicKey.toBase58();

        const { nonce } = await this.auth.getNonce(walletAddress);
        this.log(`Got nonce: ${nonce}`);

        const message = `Sign in to Helix: ${nonce}`;
        const messageBytes = new TextEncoder().encode(message);

        if (!this.wallet.signMessage) {
            throw new Error('Wallet does not support message signing');
        }

        const signatureBytes = await this.wallet.signMessage(messageBytes);
        const signature = Buffer.from(signatureBytes).toString('base64');

        this.log('Message signed');

        const { token } = await this.auth.verify(walletAddress, signature, nonce);
        this.authToken = token;

        this.log('Authentication successful');
        return token;
    }

    /**
     * Check if the client has a valid auth token
     */
    isAuthenticated(): boolean {
        return this.authToken !== null;
    }

    /**
     * Get the connected wallet's public key
     */
    getWalletPublicKey(): PublicKey | null {
        return this.wallet?.publicKey ?? null;
    }

    /**
     * Get the Solana connection instance
     */
    getConnection(): Connection {
        return this.connection;
    }

    /**
     * Get current configuration
     */
    getConfig(): Readonly<HelixConfig> {
        return {
            network: this.config.network,
            rpcEndpoint: this.config.rpcEndpoint,
            apiBaseUrl: this.config.apiBaseUrl,
        };
    }

    /**
     * Upload a file with optional encryption
     * 
     * @param file - File data as ArrayBuffer
     * @param options - Upload options
     * @returns Transaction ID and file record
     */
    async uploadFile(
        file: ArrayBuffer,
        options: {
            name: string;
            mimeType: string;
            encrypt?: boolean;
        }
    ): Promise<{
        transactionId: string;
        encryptionKey?: string;
        arweaveUrl: string;
    }> {
        if (!this.isAuthenticated()) {
            throw new Error('Not authenticated');
        }

        let dataToUpload = file;
        let encryptionKey: string | undefined;

        if (options.encrypt !== false) {
            const key = await this.encryption.generateKey();
            const encrypted = await this.encryption.encrypt(file, key);
            dataToUpload = encrypted.data;
            encryptionKey = await this.encryption.exportKey(key);
            this.log('File encrypted');
        }

        const transactionId = await this.files.uploadToArweave(
            dataToUpload,
            options.mimeType,
            this.wallet!
        );

        this.log(`Uploaded to Arweave: ${transactionId}`);

        let encryptedName: string | undefined;
        if (encryptionKey) {
            const nameKey = await this.encryption.importKey(encryptionKey);
            const nameBytes = new TextEncoder().encode(options.name);
            const encryptedNameData = await this.encryption.encrypt(nameBytes, nameKey);
            encryptedName = Buffer.from(encryptedNameData.data).toString('base64');
        }

        await this.files.create({
            transactionId,
            encryptedName,
            mimeType: options.mimeType,
            size: file.byteLength,
            isEncrypted: options.encrypt !== false,
        });

        this.log('File record created');

        return {
            transactionId,
            encryptionKey,
            arweaveUrl: `https://arweave.net/${transactionId}`,
        };
    }

    /**
     * Download and optionally decrypt a file
     * 
     * @param transactionId - Arweave transaction ID
     * @param encryptionKey - Key for decryption (if encrypted)
     * @returns Decrypted file data
     */
    async downloadFile(
        transactionId: string,
        encryptionKey?: string
    ): Promise<ArrayBuffer> {
        const url = `https://arweave.net/${transactionId}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Failed to download file: ${response.statusText}`);
        }

        let data = await response.arrayBuffer();

        if (encryptionKey) {
            const key = await this.encryption.importKey(encryptionKey);
            data = await this.encryption.decrypt(data, key);
            this.log('File decrypted');
        }

        return data;
    }

    /**
     * Create a share link for a file
     * 
     * @param fileId - File record ID
     * @param options - Share options
     * @returns Share link details
     */
    async createShareLink(
        fileId: string,
        options: {
            expiresAt?: Date;
            maxDownloads?: number;
            encryptedKey?: string;
        } = {}
    ) {
        if (!this.isAuthenticated()) {
            throw new Error('Not authenticated');
        }

        return this.files.createShareLink({
            fileId,
            expiresAt: options.expiresAt?.toISOString(),
            maxDownloads: options.maxDownloads,
            encryptedKey: options.encryptedKey,
        });
    }

    /**
     * Disconnect and clear state
     */
    disconnect(): void {
        this.wallet = null;
        this.authToken = null;
        this.log('Disconnected');
    }

    private log(message: string): void {
        if (this.config.debug) {
            console.log(`[Helix] ${message}`);
        }
    }
}

// v0.1.0
