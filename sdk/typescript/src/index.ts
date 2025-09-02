/**
 * Helix SDK - TypeScript client for permanent encrypted storage
 * 
 * @packageDocumentation
 */

export { HelixClient, HelixClientConfig } from './client';
export { HelixAuth, AuthToken, NonceResponse } from './auth';
export { 
  HelixEncryption, 
  EncryptedData, 
  EncryptionKey,
  exportKey,
  importKey 
} from './encryption';
export { 
  HelixFiles, 
  FileRecord, 
  FileListResponse, 
  CreateFileParams,
  ShareLinkParams,
  ShareLink 
} from './files';
export * from './types';

import { HelixClient } from './client';

export default HelixClient;
