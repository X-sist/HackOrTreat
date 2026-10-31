#define IR_RECEIVE_PIN 3
#define NO_LED_FEEDBACK_CODE
#include <IRremote.hpp>
#include "shared/generated/protocol.h"

static uint8_t packet[HackOrTreat::MAX_PACKET_BYTES];
static uint8_t packetLength = 0;
static uint8_t expectedLength = 0;
static uint32_t packetStartedAt = 0;
static uint32_t lastSymbolAt = 0;
static bool packetActive = false;

struct RecentMessage {
    uint32_t session;
    uint32_t fingerprint;
    uint16_t sequence;
    uint16_t receivedAt;
    bool valid;
};

static constexpr uint8_t RECENT_MESSAGE_COUNT = 32;
static RecentMessage recentMessages[RECENT_MESSAGE_COUNT];
static uint8_t nextRecentMessage = 0;

static uint16_t crc16CcittFalse(const uint8_t* bytes, uint8_t length) {
    uint16_t crc = static_cast<uint16_t>(HackOrTreat::CRC_INITIAL);
    for (uint8_t index = 0; index < length; ++index) {
        crc ^= static_cast<uint16_t>(bytes[index]) << 8;
        for (uint8_t bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x8000U) != 0
                ? static_cast<uint16_t>((crc << 1) ^ HackOrTreat::CRC_POLYNOMIAL)
                : static_cast<uint16_t>(crc << 1);
        }
    }
    return crc;
}

static uint32_t payloadFingerprint(const uint8_t* bytes, uint8_t length) {
    uint32_t hash = 2166136261UL;
    for (uint8_t index = 0; index < length; ++index) {
        hash ^= bytes[index];
        hash *= 16777619UL;
    }
    return hash;
}

static void emitProtocolError(const char* code) {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(HACKORTREAT_EVENT_PROTOCOL_ERROR);
    Serial.print(F("\",\"code\":\""));
    Serial.print(code);
    Serial.println(F("\"}"));
}

static void emitDisturbance(const char* reason) {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(HACKORTREAT_EVENT_DISTURBANCE);
    Serial.print(F("\",\"code\":\""));
    Serial.print(HACKORTREAT_CODE_INCOMPLETE_PACKET);
    Serial.print(F("\",\"reason\":\""));
    Serial.print(reason);
    Serial.println(F("\",\"session\":null,\"seq\":null}"));
}

static void emitChecksumFailure() {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(HACKORTREAT_EVENT_DISTURBANCE);
    Serial.print(F("\",\"code\":\""));
    Serial.print(HACKORTREAT_CODE_CHECKSUM_FAILED);
    Serial.print(F("\",\"reason\":\""));
    Serial.print(HACKORTREAT_REASON_CRC_MISMATCH);
    Serial.println(F("\",\"session\":null,\"seq\":null}"));
}

static uint32_t readSession() {
    return (static_cast<uint32_t>(packet[2]) << 24) |
        (static_cast<uint32_t>(packet[3]) << 16) |
        (static_cast<uint32_t>(packet[4]) << 8) |
        static_cast<uint32_t>(packet[5]);
}

static uint16_t readSequence() {
    return static_cast<uint16_t>(
        (static_cast<uint16_t>(packet[6]) << 8) | packet[7]);
}

static void printSession(uint32_t session) {
    for (int8_t shift = 28; shift >= 0; shift -= 4) {
        const uint8_t nibble = static_cast<uint8_t>((session >> shift) & 0x0F);
        Serial.write(nibble < 10 ? static_cast<char>('0' + nibble)
                                : static_cast<char>('A' + nibble - 10));
    }
}

static void expireRecentMessages(uint32_t now) {
    const uint16_t recentNow = static_cast<uint16_t>(now);
    for (uint8_t index = 0; index < RECENT_MESSAGE_COUNT; ++index) {
        RecentMessage& message = recentMessages[index];
        if (message.valid &&
            static_cast<uint16_t>(recentNow - message.receivedAt) >= HackOrTreat::DEDUP_TTL_MS) {
            message.valid = false;
        }
    }
}

static void emitIdentityEvent(const char* event, uint32_t session, uint16_t sequence) {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(event);
    Serial.print(F("\",\"session\":\""));
    printSession(session);
    Serial.print(F("\",\"seq\":"));
    Serial.print(sequence);
    Serial.println(F("}"));
}

static bool emitIfDuplicate(uint32_t now, uint32_t session, uint16_t sequence,
                            uint32_t fingerprint) {
    expireRecentMessages(now);
    for (uint8_t index = 0; index < RECENT_MESSAGE_COUNT; ++index) {
        RecentMessage& message = recentMessages[index];
        if (!message.valid ||
            message.session != session || message.sequence != sequence) {
            continue;
        }
        if (message.fingerprint == fingerprint) {
            emitIdentityEvent(HACKORTREAT_EVENT_DUPLICATE, session, sequence);
        } else {
            emitProtocolError(HACKORTREAT_CODE_ID_CONFLICT);
        }
        return true;
    }
    return false;
}

static void rememberMessage(uint32_t now, uint32_t session, uint16_t sequence,
                            uint32_t fingerprint) {
    RecentMessage& message = recentMessages[nextRecentMessage];
    message.session = session;
    message.sequence = sequence;
    message.fingerprint = fingerprint;
    message.receivedAt = static_cast<uint16_t>(now);
    message.valid = true;
    nextRecentMessage = static_cast<uint8_t>((nextRecentMessage + 1) % RECENT_MESSAGE_COUNT);
}

static void emitMessage(uint32_t session, uint16_t sequence, uint8_t textLength) {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(HACKORTREAT_EVENT_MESSAGE);
    Serial.print(F("\",\"session\":\""));
    printSession(session);
    Serial.print(F("\",\"seq\":"));
    Serial.print(sequence);
    Serial.print(F(",\"payload_hex\":\""));
    for (uint8_t index = 0; index < textLength; ++index) {
        const uint8_t value = packet[9 + index];
        const uint8_t high = value >> 4;
        const uint8_t low = value & 0x0F;
        Serial.write(high < 10 ? static_cast<char>('0' + high)
                               : static_cast<char>('A' + high - 10));
        Serial.write(low < 10 ? static_cast<char>('0' + low)
                              : static_cast<char>('A' + low - 10));
    }
    Serial.println(F("\"}"));
}

static void resetPacket() {
    packetActive = false;
    packetLength = 0;
    expectedLength = 0;
}

static void completePacket(uint32_t now) {
    const uint8_t textLength = packet[8];
    const uint16_t expectedCrc = static_cast<uint16_t>(
        (static_cast<uint16_t>(packet[packetLength - 2]) << 8) |
        packet[packetLength - 1]);
    if (crc16CcittFalse(packet, static_cast<uint8_t>(packetLength - 2)) != expectedCrc) {
        emitChecksumFailure();
        resetPacket();
        return;
    }

    bool hasNonSpace = false;
    for (uint8_t index = 0; index < textLength; ++index) {
        const uint8_t value = packet[9 + index];
        if (value < 0x20 || value > 0x7E) {
            emitProtocolError(HACKORTREAT_CODE_INVALID_TEXT);
            resetPacket();
            return;
        }
        if (value != ' ') {
            hasNonSpace = true;
        }
    }
    if (!hasNonSpace) {
        emitProtocolError(HACKORTREAT_CODE_INVALID_TEXT);
        resetPacket();
        return;
    }

    const uint32_t session = readSession();
    const uint16_t sequence = readSequence();
    const uint32_t fingerprint = payloadFingerprint(&packet[9], textLength);
    if (!emitIfDuplicate(now, session, sequence, fingerprint)) {
        emitMessage(session, sequence, textLength);
        rememberMessage(now, session, sequence, fingerprint);
    }
    resetPacket();
}

static void acceptSymbol(uint32_t now, uint8_t index, uint8_t value) {
    if (index == 0) {
        if (packetActive) {
            emitDisturbance(HACKORTREAT_REASON_RESTART);
        }
        packetActive = true;
        packetLength = 0;
        expectedLength = 0;
        packetStartedAt = now;
        lastSymbolAt = now;
    } else if (!packetActive) {
        return;
    } else {
        const uint32_t packetAge = static_cast<uint32_t>(now - packetStartedAt);
        const uint32_t symbolGap = static_cast<uint32_t>(now - lastSymbolAt);
        if (packetAge >= HackOrTreat::PACKET_TIMEOUT_MS) {
            emitDisturbance(HACKORTREAT_REASON_PACKET_TIMEOUT);
            resetPacket();
            return;
        }
        if (symbolGap >= HackOrTreat::INTER_SYMBOL_TIMEOUT_MS) {
            emitDisturbance(HACKORTREAT_REASON_INTER_SYMBOL_TIMEOUT);
            resetPacket();
            return;
        }
        if (index != packetLength || index >= HackOrTreat::MAX_PACKET_BYTES) {
            emitDisturbance(HACKORTREAT_REASON_INDEX_GAP);
            resetPacket();
            return;
        }
        lastSymbolAt = now;
    }

    if (index != packetLength || index >= HackOrTreat::MAX_PACKET_BYTES) {
        resetPacket();
        return;
    }
    packet[packetLength++] = value;

    if (packetLength == 1 && packet[0] != HackOrTreat::PROTOCOL_VERSION) {
        resetPacket();
        return;
    }
    if (packetLength == 2 && packet[1] != HackOrTreat::TEXT_PACKET_TYPE) {
        emitProtocolError(HACKORTREAT_CODE_UNSUPPORTED_TYPE);
        resetPacket();
        return;
    }
    if (packetLength == HackOrTreat::PACKET_OVERHEAD_BYTES - 2) {
        if (value == 0 || value > HackOrTreat::MAX_TEXT_BYTES) {
            emitProtocolError(HACKORTREAT_CODE_INVALID_LENGTH);
            resetPacket();
            return;
        }
        expectedLength = static_cast<uint8_t>(HackOrTreat::PACKET_OVERHEAD_BYTES + value);
    }
    if (expectedLength != 0 && packetLength == expectedLength) {
        completePacket(now);
    }
}

static void checkTimeouts(uint32_t now) {
    if (!packetActive) {
        return;
    }
    if (static_cast<uint32_t>(now - packetStartedAt) >= HackOrTreat::PACKET_TIMEOUT_MS) {
        emitDisturbance(HACKORTREAT_REASON_PACKET_TIMEOUT);
        resetPacket();
    } else if (static_cast<uint32_t>(now - lastSymbolAt) >= HackOrTreat::INTER_SYMBOL_TIMEOUT_MS) {
        emitDisturbance(HACKORTREAT_REASON_INTER_SYMBOL_TIMEOUT);
        resetPacket();
    }
}

static void emitHello() {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(HACKORTREAT_EVENT_HELLO);
    Serial.print(F("\",\"role\":\"rx\",\"max_text_bytes\":"));
    Serial.print(HackOrTreat::MAX_TEXT_BYTES);
    Serial.println('}');
}

static void serviceSerial() {
    static char inputPrefix[7];
    static uint8_t inputLength = 0;
    static bool inputOverflow = false;
    static bool trailingCarriageReturn = false;
    while (Serial.available() > 0) {
        const char value = static_cast<char>(Serial.read());
        if (value == '\n') {
            if (inputOverflow) {
                Serial.print(F("{\"v\":1,\"event\":\""));
                Serial.print(HACKORTREAT_EVENT_ERROR);
                Serial.print(F("\",\"code\":\""));
                Serial.print(HACKORTREAT_CODE_LINE_TOO_LONG);
                Serial.println(F("\"}"));
            } else {
                if (!trailingCarriageReturn && inputLength > 0 &&
                    inputLength <= sizeof(inputPrefix) &&
                    inputPrefix[inputLength - 1] == '\r') {
                    --inputLength;
                }
                if (inputLength > 0) {
                    if (inputLength == 5 && memcmp(inputPrefix, "HELLO", 5) == 0) {
                        emitHello();
                    } else {
                        Serial.print(F("{\"v\":1,\"event\":\""));
                        Serial.print(HACKORTREAT_EVENT_ERROR);
                        Serial.print(F("\",\"code\":\""));
                        Serial.print(HACKORTREAT_CODE_UNKNOWN_COMMAND);
                        Serial.println(F("\"}"));
                    }
                }
            }
            inputLength = 0;
            inputOverflow = false;
            trailingCarriageReturn = false;
        } else if (!inputOverflow) {
            if (trailingCarriageReturn) {
                inputOverflow = true;
            } else if (inputLength < HackOrTreat::MAX_HOST_LINE_BYTES) {
                if (inputLength < sizeof(inputPrefix)) {
                    inputPrefix[inputLength] = value;
                }
                ++inputLength;
            } else if (value == '\r') {
                trailingCarriageReturn = true;
            } else {
                inputOverflow = true;
            }
        }
    }
}

void setup() {
    Serial.begin(HackOrTreat::SERIAL_BAUD);
    IrReceiver.begin(IR_RECEIVE_PIN, DISABLE_LED_FEEDBACK);
    emitHello();
}

void loop() {
    serviceSerial();
    const uint32_t now = millis();
    checkTimeouts(now);
    expireRecentMessages(now);
    if (IrReceiver.decode()) {
        const IRData& received = IrReceiver.decodedIRData;
        const bool fullFrameProtocol = received.protocol == NEC || received.protocol == NEC2;
        const bool shortRepeat = received.protocol == NEC &&
            (received.flags & IRDATA_FLAGS_IS_REPEAT) != 0;
        if (fullFrameProtocol && !shortRepeat &&
            (received.flags & IRDATA_FLAGS_WAS_OVERFLOW) == 0 &&
            (received.address & 0xFF00U) == HackOrTreat::IR_ADDRESS_PREFIX) {
            const uint8_t index = static_cast<uint8_t>(received.address & 0x00FFU);
            acceptSymbol(now, index, static_cast<uint8_t>(received.command));
        }
        IrReceiver.resume();
    }
    checkTimeouts(millis());
}
