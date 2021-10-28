/// <reference types="node" />
import { Socket } from 'dgram';
export declare function reservePorts({ count, type, attemptNumber, }?: {
    count?: number;
    type?: 'udp' | 'tcp';
    attemptNumber?: number;
}): Promise<number[]>;
export declare function bindToPort(socket: Socket): Promise<number>;
