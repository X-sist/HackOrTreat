#define IR_SEND_PIN 2
#define NO_LED_SEND_FEEDBACK_CODE
#include <IRremote.hpp>
#include "shared/generated/protocol.h"

static char inputLine[HackOrTreat::MAX_HOST_LINE_BYTES + 1];
static uint8_t inputLength = 0;
static bool inputOverflow = false;
static uint8_t packet[HackOrTreat::MAX_PACKET_BYTES];

enum ParseResult : uint8_t {
    PARSE_OK,
    PARSE_MALFORMED,
    PARSE_INVALID_TEXT
};

static int8_t hexNibble(char value) {
    if (value >= '0' && value <= '9') {
        return value - '0';
    }
    if (value >= 'A' && value <= 'F') {
        return value - 'A' + 10;
    }
    return -1;
}

static bool parseHexByte(const char* text, uint8_t* value) {
    const int8_t high = hexNibble(text[0]);
    const int8_t low = hexNibble(text[1]);
    if (high < 0 || low < 0) {
        return false;
    }
    *value = static_cast<uint8_t>((high << 4) | low);
    return true;
}

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

static ParseResult parseSend(char* line, char* session, uint16_t* sequence, uint8_t* packetLength) {
    const size_t lineLength = strlen(line);
    if (lineLength < 21 || lineLength > 115 || memcmp(line, "SEND\t", 5) != 0 ||
        line[13] != '\t' || line[18] != '\t') {
        return PARSE_MALFORMED;
    }

    for (uint8_t index = 0; index < 8; ++index) {
        if (hexNibble(line[5 + index]) < 0) {
            return PARSE_MALFORMED;
        }
        session[index] = line[5 + index];
    }
    session[8] = '\0';

    uint16_t parsedSequence = 0;
    for (uint8_t index = 0; index < 4; ++index) {
        const int8_t nibble = hexNibble(line[14 + index]);
        if (nibble < 0) {
            return PARSE_MALFORMED;
        }
        parsedSequence = static_cast<uint16_t>((parsedSequence << 4) | nibble);
    }

    const size_t hexLength = lineLength - 19;
    if (hexLength < 2 || hexLength > HackOrTreat::MAX_TEXT_BYTES * 2 || (hexLength & 1U) != 0) {
        return PARSE_MALFORMED;
    }
    const uint8_t payloadLength = static_cast<uint8_t>(hexLength / 2);
    bool hasNonSpace = false;
    for (size_t index = 19; index < lineLength; ++index) {
        if (line[index] == '\t') {
            return PARSE_MALFORMED;
        }
    }

    packet[0] = static_cast<uint8_t>(HackOrTreat::PROTOCOL_VERSION);
    packet[1] = static_cast<uint8_t>(HackOrTreat::TEXT_PACKET_TYPE);
    for (uint8_t index = 0; index < 4; ++index) {
        uint8_t value = 0;
        if (!parseHexByte(&line[5 + index * 2], &value)) {
            return PARSE_MALFORMED;
        }
        packet[2 + index] = value;
    }
    packet[6] = static_cast<uint8_t>(parsedSequence >> 8);
    packet[7] = static_cast<uint8_t>(parsedSequence);
    packet[8] = payloadLength;

    for (uint8_t index = 0; index < payloadLength; ++index) {
        uint8_t value = 0;
        if (!parseHexByte(&line[19 + index * 2], &value)) {
            return PARSE_MALFORMED;
        }
        if (value < 0x20 || value > 0x7E) {
            return PARSE_INVALID_TEXT;
        }
        if (value != ' ') {
            hasNonSpace = true;
        }
        packet[9 + index] = value;
    }
    if (!hasNonSpace) {
        return PARSE_INVALID_TEXT;
    }

    const uint16_t crc = crc16CcittFalse(packet, static_cast<uint8_t>(9 + payloadLength));
    packet[9 + payloadLength] = static_cast<uint8_t>(crc >> 8);
    packet[10 + payloadLength] = static_cast<uint8_t>(crc);
    *sequence = parsedSequence;
    *packetLength = static_cast<uint8_t>(HackOrTreat::PACKET_OVERHEAD_BYTES + payloadLength);
    return PARSE_OK;
}

static void emitHello() {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(HACKORTREAT_EVENT_HELLO);
    Serial.print(F("\",\"role\":\"tx\",\"max_text_bytes\":"));
    Serial.print(HackOrTreat::MAX_TEXT_BYTES);
    Serial.println('}');
}

static void emitReady() {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(HACKORTREAT_EVENT_READY);
    Serial.println(F("\"}"));
}

static void emitError(const char* code) {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(HACKORTREAT_EVENT_ERROR);
    Serial.print(F("\",\"code\":\""));
    Serial.print(code);
    Serial.println(F("\"}"));
}

static void emitIdentityEvent(const char* event, const char* session, uint16_t sequence) {
    Serial.print(F("{\"v\":1,\"event\":\""));
    Serial.print(event);
    Serial.print(F("\",\"session\":\""));
    Serial.print(session);
    Serial.print(F("\",\"seq\":"));
    Serial.print(sequence);
    Serial.println(F("}"));
}

static void serviceSerial(bool busy);

static void waitUntil(uint32_t target) {
    while (static_cast<int32_t>(target - millis()) > 0) {
        serviceSerial(true);
        delay(1);
    }
}

static void waitGuard(uint32_t lastAttemptStart) {
    while (static_cast<uint32_t>(millis() - lastAttemptStart) < HackOrTreat::PACKET_GUARD_MS) {
        serviceSerial(true);
        delay(1);
    }
}

static void transmitPacket(uint8_t packetLength, const char* session, uint16_t sequence) {
    emitIdentityEvent(HACKORTREAT_EVENT_ACCEPTED, session, sequence);
    Serial.flush();

    uint32_t firstStart = 0;
    uint32_t lastAttemptStart = millis();
    bool failed = false;
    for (uint8_t index = 0; index < packetLength; ++index) {
        if (index == 0) {
            firstStart = millis();
        } else {
            const uint32_t target = firstStart + static_cast<uint32_t>(index) * HackOrTreat::SYMBOL_PERIOD_MS;
            waitUntil(target);
            if (static_cast<uint32_t>(millis() - target) > HackOrTreat::SYMBOL_MAX_LATE_MS) {
                failed = true;
                break;
            }
        }
        lastAttemptStart = millis();
        IrSender.sendNEC(static_cast<uint16_t>(HackOrTreat::IR_ADDRESS_PREFIX | index), packet[index], 0);
    }

    if (failed) {
        emitError(HACKORTREAT_CODE_TX_FAILED);
    } else {
        emitIdentityEvent(HACKORTREAT_EVENT_SENT, session, sequence);
    }
    waitGuard(lastAttemptStart);
    emitReady();
}

static void handleLine(bool busy) {
    if (inputOverflow) {
        emitError(HACKORTREAT_CODE_LINE_TOO_LONG);
        if (!busy) {
            emitReady();
        }
    } else {
        if (inputLength > 0 && inputLine[inputLength - 1] == '\r') {
            --inputLength;
        }
        inputLine[inputLength] = '\0';
        if (inputLength > 0) {
            if (busy) {
                emitError(HACKORTREAT_CODE_BUSY);
            } else if (strcmp(inputLine, "HELLO") == 0) {
                emitHello();
                emitReady();
            } else if (strncmp(inputLine, "SEND", 4) == 0) {
                char session[9];
                uint16_t sequence = 0;
                uint8_t packetLength = 0;
                const ParseResult result = parseSend(inputLine, session, &sequence, &packetLength);
                if (result == PARSE_MALFORMED) {
                    emitError(HACKORTREAT_CODE_MALFORMED_COMMAND);
                    emitReady();
                } else if (result == PARSE_INVALID_TEXT) {
                    emitError(HACKORTREAT_CODE_INVALID_TEXT);
                    emitReady();
                } else {
                    transmitPacket(packetLength, session, sequence);
                }
            } else {
                emitError(HACKORTREAT_CODE_UNKNOWN_COMMAND);
                emitReady();
            }
        }
    }
    inputLength = 0;
    inputOverflow = false;
}

static void serviceSerial(bool busy) {
    while (Serial.available() > 0) {
        const char value = static_cast<char>(Serial.read());
        if (value == '\n') {
            handleLine(busy);
        } else if (!inputOverflow) {
            if (inputLength < HackOrTreat::MAX_HOST_LINE_BYTES) {
                inputLine[inputLength++] = value;
            } else {
                inputOverflow = true;
            }
        }
    }
}

void setup() {
    Serial.begin(HackOrTreat::SERIAL_BAUD);
    IrSender.begin(IR_SEND_PIN);
    emitHello();
    emitReady();
}

void loop() {
    serviceSerial(false);
}