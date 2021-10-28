/// <reference types="node" />
export declare function getPayloadType(message: Buffer): number;
export declare function isRtpMessagePayloadType(payloadType: number): boolean;
export declare function getSsrc(message: Buffer): number | null;
