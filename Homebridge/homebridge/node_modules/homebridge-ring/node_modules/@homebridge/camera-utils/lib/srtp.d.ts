/// <reference types="node" />
export interface SrtpOptions {
    srtpKey: Buffer;
    srtpSalt: Buffer;
}
export declare function encodeSrtpOptions({ srtpKey, srtpSalt }: SrtpOptions): string;
export declare function decodeSrtpOptions(encodedOptions: string): SrtpOptions;
export declare function createCryptoLine(srtpOptions: SrtpOptions): string;
export declare function generateSrtpOptions(): SrtpOptions;
