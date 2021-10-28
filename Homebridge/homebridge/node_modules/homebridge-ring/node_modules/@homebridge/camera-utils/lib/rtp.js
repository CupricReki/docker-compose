"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getSsrc = exports.isRtpMessagePayloadType = exports.getPayloadType = void 0;
function getPayloadType(message) {
    return message.readUInt8(1) & 0x7f;
}
exports.getPayloadType = getPayloadType;
function isRtpMessagePayloadType(payloadType) {
    return payloadType > 90 || payloadType === 0;
}
exports.isRtpMessagePayloadType = isRtpMessagePayloadType;
function getSsrc(message) {
    try {
        const payloadType = getPayloadType(message), isRtp = isRtpMessagePayloadType(payloadType);
        return message.readUInt32BE(isRtp ? 8 : 4);
    }
    catch (_) {
        return null;
    }
}
exports.getSsrc = getSsrc;
