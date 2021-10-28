export declare const defaultFfmpegPath: string;
export declare function doesFfmpegSupportCodec(codec: string, ffmpegPath?: string): Promise<boolean>;
export declare function isFfmpegInstalled(ffmpegPath?: string): Promise<boolean>;
