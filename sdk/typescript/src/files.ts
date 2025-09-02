import { WalletAdapter } from '@solana/wallet-adapter-base';

/**
 * File record as returned by the API
 */
export interface FileRecord {
    id: string;
    transactionId: string;
    encryptedName?: string;
    mimeType: string;
    size: number;
    isEncrypted: boolean;
    createdAt: string;
    updatedAt?: string;
}

/**
 * Response from file listing
 */
export interface FileListResponse {
    files: FileRecord[];
    total: number;
    page: number;
    pageSize: number;
}

/**
 * Parameters for creating a file record
 */
export interface CreateFileParams {
    transactionId: string;
    encryptedName?: string;
    mimeType: string;
    size: number;
    isEncrypted: boolean;
}

/**
 * Parameters for creating a share link
 */
export interface ShareLinkParams {
    fileId: string;
    expiresAt?: string;
    maxDownloads?: number;
    encryptedKey?: string;
}

/**
 * Share link details
 */
export interface ShareLink {
    id: string;
    url: string;
    expiresAt?: string;
    maxDownloads?: number;
    downloadCount: number;
    createdAt: string;
}

/**
 * File operations for Helix API
 */
export class HelixFiles {
    private apiBaseUrl: string;
    private timeout: number;
    private getToken: () => string | null;

    constructor(
        apiBaseUrl: string,
        timeout: number,
        getToken: () => string | null
    ) {
        this.apiBaseUrl = apiBaseUrl;
        this.timeout = timeout;
        this.getToken = getToken;
    }

    /**
     * Build authorization headers
     */
    private getHeaders(): Record<string, string> {
        const token = this.getToken();
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    /**
     * List all files for the authenticated wallet
     * @param page - Page number (1-indexed)
     * @param pageSize - Number of items per page
     * @returns Paginated file list
     */
    async list(page: number = 1, pageSize: number = 20): Promise<FileListResponse> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const url = new URL(`${this.apiBaseUrl}/api/files`);
            url.searchParams.set('page', page.toString());
            url.searchParams.set('pageSize', pageSize.toString());

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: this.getHeaders(),
                signal: controller.signal,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `Failed to list files: ${response.status}`);
            }

            return response.json();
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * Get a single file record by ID
     * @param id - File record ID
     * @returns File record
     */
    async get(id: string): Promise<FileRecord> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/files/${id}`, {
                method: 'GET',
                headers: this.getHeaders(),
                signal: controller.signal,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `Failed to get file: ${response.status}`);
            }

            return response.json();
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * Create a new file record after Arweave upload
     * @param params - File creation parameters
     * @returns Created file record
     */
    async create(params: CreateFileParams): Promise<FileRecord> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/files`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(params),
                signal: controller.signal,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `Failed to create file: ${response.status}`);
            }

            return response.json();
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * Delete a file record (does not delete from Arweave)
     * @param id - File record ID
     */
    async delete(id: string): Promise<void> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/files/${id}`, {
                method: 'DELETE',
                headers: this.getHeaders(),
                signal: controller.signal,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `Failed to delete file: ${response.status}`);
            }
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * Create a share link for a file
     * @param params - Share link parameters
     * @returns Share link details
     */
    async createShareLink(params: ShareLinkParams): Promise<{ shareLink: ShareLink }> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/share`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(params),
                signal: controller.signal,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `Failed to create share link: ${response.status}`);
            }

            return response.json();
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * Get share link details
     * @param id - Share link ID
     * @returns Share link details
     */
    async getShareLink(id: string): Promise<ShareLink> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/share/${id}`, {
                method: 'GET',
                headers: this.getHeaders(),
                signal: controller.signal,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `Failed to get share link: ${response.status}`);
            }

            return response.json();
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * Upload file data to Arweave via Irys
     * 
     * @param data - File data to upload
     * @param mimeType - MIME type of the file
     * @param wallet - Wallet adapter for payment
     * @returns Arweave transaction ID
     */
    async uploadToArweave(
        data: ArrayBuffer,
        mimeType: string,
        wallet: WalletAdapter
    ): Promise<string> {
        const { WebIrys } = await import('@irys/sdk');

        const irys = new WebIrys({
            network: 'mainnet',
            token: 'solana',
            wallet: { provider: wallet },
        });

        await irys.ready();

        const tags = [
            { name: 'Content-Type', value: mimeType },
            { name: 'App-Name', value: 'Helix' },
            { name: 'App-Version', value: '1.0.0' },
        ];

        const receipt = await irys.upload(Buffer.from(data), { tags });

        return receipt.id;
    }

    /**
     * Get the cost to upload a file
     * 
     * @param size - File size in bytes
     * @param wallet - Wallet adapter
     * @returns Cost in SOL
     */
    async getUploadCost(size: number, wallet: WalletAdapter): Promise<string> {
        const { WebIrys } = await import('@irys/sdk');

        const irys = new WebIrys({
            network: 'mainnet',
            token: 'solana',
            wallet: { provider: wallet },
        });

        await irys.ready();

        const price = await irys.getPrice(size);
        return irys.utils.fromAtomic(price).toString();
    }

    /**
     * Download file from Arweave
     * 
     * @param transactionId - Arweave transaction ID
     * @returns File data
     */
    async downloadFromArweave(transactionId: string): Promise<ArrayBuffer> {
        const url = `https://arweave.net/${transactionId}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Failed to download from Arweave: ${response.statusText}`);
        }

        return response.arrayBuffer();
    }
}
