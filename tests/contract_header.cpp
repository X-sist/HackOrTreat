#include "../shared/generated/protocol.h"
static_assert(HackOrTreat::MAX_PACKET_BYTES == HackOrTreat::MAX_TEXT_BYTES + HackOrTreat::PACKET_OVERHEAD_BYTES, "packet size drift");
static_assert(HackOrTreat::PROTOCOL_VERSION == 1, "fixture version drift");
static_assert(HackOrTreat::PACKET_GUARD_MS > HackOrTreat::INTER_SYMBOL_TIMEOUT_MS, "unsafe guard");
int main() { return HackOrTreat::HEARTBEATS_ENABLED ? 1 : 0; }
