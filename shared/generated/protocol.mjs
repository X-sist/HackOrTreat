// Generated; do not edit.
function freeze(v) { if (v && typeof v === "object") { Object.values(v).forEach(freeze); Object.freeze(v); } return v; }
export const CONTRACT = freeze({
  "revision": "1.0.0",
  "constants": {
    "PROTOCOL_VERSION": 1,
    "TEXT_PACKET_TYPE": 1,
    "MAX_TEXT_BYTES": 48,
    "PACKET_OVERHEAD_BYTES": 11,
    "MAX_PACKET_BYTES": 59,
    "SERIAL_BAUD": 115200,
    "MAX_HOST_LINE_BYTES": 128,
    "MAX_EVENT_LINE_BYTES": 256,
    "IR_ADDRESS_PREFIX": 42752,
    "SYMBOL_PERIOD_MS": 120,
    "SYMBOL_MAX_LATE_MS": 20,
    "INTER_SYMBOL_TIMEOUT_MS": 500,
    "PACKET_TIMEOUT_MS": 9000,
    "PACKET_GUARD_MS": 600,
    "DEDUP_TTL_MS": 60000,
    "HOST_BOOT_TIMEOUT_MS": 5000,
    "HOST_ACCEPT_TIMEOUT_MS": 2000,
    "HOST_SEND_TIMEOUT_MS": 12000,
    "DISTURBANCE_COOLDOWN_MS": 5000,
    "CRC_POLYNOMIAL": 4129,
    "CRC_INITIAL": 65535,
    "CRC_CHECK_VALUE": 10673,
    "HEARTBEATS_ENABLED": false
  },
  "event_fields": {
    "hello": {
      "roles": [
        "tx",
        "rx"
      ],
      "required": [
        "role",
        "max_text_bytes"
      ]
    },
    "ready": {
      "roles": [
        "tx"
      ],
      "required": []
    },
    "accepted": {
      "roles": [
        "tx"
      ],
      "required": [
        "session",
        "seq"
      ]
    },
    "sent": {
      "roles": [
        "tx"
      ],
      "required": [
        "session",
        "seq"
      ]
    },
    "error": {
      "roles": [
        "tx",
        "rx"
      ],
      "required": [
        "code"
      ]
    },
    "message": {
      "roles": [
        "rx"
      ],
      "required": [
        "session",
        "seq",
        "payload_hex"
      ]
    },
    "duplicate": {
      "roles": [
        "rx"
      ],
      "required": [
        "session",
        "seq"
      ]
    },
    "disturbance": {
      "roles": [
        "rx"
      ],
      "required": [
        "code",
        "reason",
        "session",
        "seq"
      ]
    },
    "protocol_error": {
      "roles": [
        "rx"
      ],
      "required": [
        "code"
      ]
    }
  },
  "error_codes": [
    "MALFORMED_COMMAND",
    "LINE_TOO_LONG",
    "INVALID_TEXT",
    "UNKNOWN_COMMAND",
    "BUSY",
    "TX_FAILED"
  ],
  "protocol_error_codes": [
    "UNSUPPORTED_TYPE",
    "INVALID_LENGTH",
    "INVALID_TEXT",
    "ID_CONFLICT"
  ],
  "disturbance_reasons": {
    "CHECKSUM_FAILED": [
      "CRC_MISMATCH"
    ],
    "INCOMPLETE_PACKET": [
      "INDEX_GAP",
      "RESTART",
      "INTER_SYMBOL_TIMEOUT",
      "PACKET_TIMEOUT"
    ]
  }
});
