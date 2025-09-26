//+------------------------------------------------------------------+
//|                                         BinaryProtocol.mqh |
//|                     Fixed binary protocol for MQL5 compatibility |
//+------------------------------------------------------------------+
#ifndef BINARYPROTOCOL_MQH
#define BINARYPROTOCOL_MQH

//+------------------------------------------------------------------+
//| Protocol constants                                              |
//+------------------------------------------------------------------+
#define BINARY_MAGIC       0x53554854  // "SUHO"
#define BINARY_VERSION     0x0001
#define HEADER_SIZE        16
#define PRICE_DATA_SIZE    16
#define ACCOUNT_DATA_SIZE  64
#define COMMAND_DATA_SIZE  32

//+------------------------------------------------------------------+
//| Message types                                                   |
//+------------------------------------------------------------------+
enum ENUM_MESSAGE_TYPE
{
    MSG_PRICE_STREAM = 1,
    MSG_ACCOUNT_PROFILE = 2,
    MSG_TRADE_COMMAND = 3,
    MSG_TRADE_CONFIRMATION = 4,
    MSG_HEARTBEAT = 5
};

//+------------------------------------------------------------------+
//| Symbol ID enumeration                                           |
//+------------------------------------------------------------------+
enum ENUM_SYMBOL_ID
{
    SYMBOL_EURUSD = 1,
    SYMBOL_GBPUSD = 2,
    SYMBOL_USDJPY = 3,
    SYMBOL_USDCHF = 4,
    SYMBOL_AUDUSD = 5,
    SYMBOL_USDCAD = 6,
    SYMBOL_NZDUSD = 7,
    SYMBOL_XAUUSD = 8,
    SYMBOL_XAGUSD = 9,
    SYMBOL_UNKNOWN = 255
};

//+------------------------------------------------------------------+
//| Fixed Binary Protocol Class                                    |
//+------------------------------------------------------------------+
class CBinaryProtocol
{
public:
    //+------------------------------------------------------------------+
    //| Convert symbol string to enum ID                               |
    //+------------------------------------------------------------------+
    static int GetSymbolID(string symbol)
    {
        if(symbol == "EURUSD") return SYMBOL_EURUSD;
        if(symbol == "GBPUSD") return SYMBOL_GBPUSD;
        if(symbol == "USDJPY") return SYMBOL_USDJPY;
        if(symbol == "USDCHF") return SYMBOL_USDCHF;
        if(symbol == "AUDUSD") return SYMBOL_AUDUSD;
        if(symbol == "USDCAD") return SYMBOL_USDCAD;
        if(symbol == "NZDUSD") return SYMBOL_NZDUSD;
        if(symbol == "XAUUSD") return SYMBOL_XAUUSD;
        if(symbol == "XAGUSD") return SYMBOL_XAGUSD;
        return SYMBOL_UNKNOWN;
    }

    //+------------------------------------------------------------------+
    //| Convert symbol ID to string                                    |
    //+------------------------------------------------------------------+
    static string GetSymbolString(int id)
    {
        switch(id)
        {
            case SYMBOL_EURUSD: return "EURUSD";
            case SYMBOL_GBPUSD: return "GBPUSD";
            case SYMBOL_USDJPY: return "USDJPY";
            case SYMBOL_USDCHF: return "USDCHF";
            case SYMBOL_AUDUSD: return "AUDUSD";
            case SYMBOL_USDCAD: return "USDCAD";
            case SYMBOL_NZDUSD: return "NZDUSD";
            case SYMBOL_XAUUSD: return "XAUUSD";
            case SYMBOL_XAGUSD: return "XAGUSD";
            default: return "UNKNOWN";
        }
    }

    //+------------------------------------------------------------------+
    //| Convert price to fixed point (multiply by 100000)             |
    //+------------------------------------------------------------------+
    static uint PriceToFixedPoint(double price)
    {
        return (uint)(price * 100000.0 + 0.5);
    }

    //+------------------------------------------------------------------+
    //| Convert fixed point to price (divide by 100000)               |
    //+------------------------------------------------------------------+
    static double FixedPointToPrice(uint fixedPoint)
    {
        return (double)fixedPoint / 100000.0;
    }

    //+------------------------------------------------------------------+
    //| Write 32-bit integer to buffer at position                     |
    //+------------------------------------------------------------------+
    static void WriteUInt32(char &buffer[], int pos, uint value)
    {
        buffer[pos + 0] = (char)(value & 0xFF);
        buffer[pos + 1] = (char)((value >> 8) & 0xFF);
        buffer[pos + 2] = (char)((value >> 16) & 0xFF);
        buffer[pos + 3] = (char)((value >> 24) & 0xFF);
    }

    //+------------------------------------------------------------------+
    //| Write 16-bit integer to buffer at position                     |
    //+------------------------------------------------------------------+
    static void WriteUInt16(char &buffer[], int pos, ushort value)
    {
        buffer[pos + 0] = (char)(value & 0xFF);
        buffer[pos + 1] = (char)((value >> 8) & 0xFF);
    }

    //+------------------------------------------------------------------+
    //| Write 64-bit integer to buffer at position                     |
    //+------------------------------------------------------------------+
    static void WriteUInt64(char &buffer[], int pos, ulong value)
    {
        buffer[pos + 0] = (char)(value & 0xFF);
        buffer[pos + 1] = (char)((value >> 8) & 0xFF);
        buffer[pos + 2] = (char)((value >> 16) & 0xFF);
        buffer[pos + 3] = (char)((value >> 24) & 0xFF);
        buffer[pos + 4] = (char)((value >> 32) & 0xFF);
        buffer[pos + 5] = (char)((value >> 40) & 0xFF);
        buffer[pos + 6] = (char)((value >> 48) & 0xFF);
        buffer[pos + 7] = (char)((value >> 56) & 0xFF);
    }

    //+------------------------------------------------------------------+
    //| Read 32-bit integer from buffer at position                    |
    //+------------------------------------------------------------------+
    static uint ReadUInt32(const char &buffer[], int pos)
    {
        return ((uint)(uchar)buffer[pos + 0]) |
               ((uint)(uchar)buffer[pos + 1] << 8) |
               ((uint)(uchar)buffer[pos + 2] << 16) |
               ((uint)(uchar)buffer[pos + 3] << 24);
    }

    //+------------------------------------------------------------------+
    //| Read 16-bit integer from buffer at position                    |
    //+------------------------------------------------------------------+
    static ushort ReadUInt16(const char &buffer[], int pos)
    {
        return ((ushort)(uchar)buffer[pos + 0]) |
               ((ushort)(uchar)buffer[pos + 1] << 8);
    }

    //+------------------------------------------------------------------+
    //| Read 64-bit integer from buffer at position                    |
    //+------------------------------------------------------------------+
    static ulong ReadUInt64(const char &buffer[], int pos)
    {
        return ((ulong)(uchar)buffer[pos + 0]) |
               ((ulong)(uchar)buffer[pos + 1] << 8) |
               ((ulong)(uchar)buffer[pos + 2] << 16) |
               ((ulong)(uchar)buffer[pos + 3] << 24) |
               ((ulong)(uchar)buffer[pos + 4] << 32) |
               ((ulong)(uchar)buffer[pos + 5] << 40) |
               ((ulong)(uchar)buffer[pos + 6] << 48) |
               ((ulong)(uchar)buffer[pos + 7] << 56);
    }

    //+------------------------------------------------------------------+
    //| Create binary price stream packet (MQL5 compatible)            |
    //+------------------------------------------------------------------+
    static int CreatePriceStreamPacket(string userId, string &symbols[], MqlTick &ticks[], char &buffer[])
    {
        int pairs = ArraySize(symbols);
        if(pairs > 255) pairs = 255;

        int totalSize = HEADER_SIZE + (pairs * PRICE_DATA_SIZE);
        ArrayResize(buffer, totalSize);
        ArrayInitialize(buffer, 0);

        int pos = 0;

        // Write header (16 bytes)
        WriteUInt32(buffer, pos, BINARY_MAGIC); pos += 4;          // Magic number
        WriteUInt16(buffer, pos, BINARY_VERSION); pos += 2;       // Version
        buffer[pos++] = (char)MSG_PRICE_STREAM;                   // Message type
        buffer[pos++] = (char)pairs;                              // Pair count
        WriteUInt64(buffer, pos, (ulong)GetTickCount()); pos += 8; // Timestamp

        // Write price data (16 bytes per pair)
        for(int i = 0; i < pairs; i++)
        {
            WriteUInt32(buffer, pos, GetSymbolID(symbols[i])); pos += 4;        // Symbol ID
            WriteUInt32(buffer, pos, PriceToFixedPoint(ticks[i].bid)); pos += 4; // Bid
            WriteUInt32(buffer, pos, PriceToFixedPoint(ticks[i].ask)); pos += 4; // Ask

            // Calculate spread and flags
            int spread = (int)((ticks[i].ask - ticks[i].bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT));
            uint flags = (spread & 0xFFFF) | (1 << 16); // Server ID = 1
            WriteUInt32(buffer, pos, flags); pos += 4;                          // Flags
        }

        Print("[BINARY] Created price stream packet: ", totalSize, " bytes for ", pairs, " symbols");
        return totalSize;
    }

    //+------------------------------------------------------------------+
    //| Create binary account profile packet                           |
    //+------------------------------------------------------------------+
    static int CreateAccountProfilePacket(string userId, char &buffer[])
    {
        int totalSize = HEADER_SIZE + ACCOUNT_DATA_SIZE;
        ArrayResize(buffer, totalSize);
        ArrayInitialize(buffer, 0);

        int pos = 0;

        // Write header (16 bytes)
        WriteUInt32(buffer, pos, BINARY_MAGIC); pos += 4;
        WriteUInt16(buffer, pos, BINARY_VERSION); pos += 2;
        buffer[pos++] = (char)MSG_ACCOUNT_PROFILE;
        buffer[pos++] = (char)1; // One profile
        WriteUInt64(buffer, pos, (ulong)GetTickCount()); pos += 8;

        // Write account profile (64 bytes)
        // User ID (16 bytes)
        string safeUserId = StringSubstr(userId, 0, 15);
        for(int i = 0; i < 16; i++)
        {
            if(i < StringLen(safeUserId))
                buffer[pos + i] = (char)StringGetCharacter(safeUserId, i);
            else
                buffer[pos + i] = 0;
        }
        pos += 16;

        // Broker name (16 bytes)
        string broker = StringSubstr(AccountInfoString(ACCOUNT_COMPANY), 0, 15);
        for(int i = 0; i < 16; i++)
        {
            if(i < StringLen(broker))
                buffer[pos + i] = (char)StringGetCharacter(broker, i);
            else
                buffer[pos + i] = 0;
        }
        pos += 16;

        // Account data (32 bytes)
        WriteUInt32(buffer, pos, (uint)AccountInfoInteger(ACCOUNT_LOGIN)); pos += 4;
        WriteUInt32(buffer, pos, (uint)(AccountInfoDouble(ACCOUNT_BALANCE) * 100)); pos += 4;
        WriteUInt32(buffer, pos, (uint)(AccountInfoDouble(ACCOUNT_EQUITY) * 100)); pos += 4;
        WriteUInt32(buffer, pos, (uint)(AccountInfoDouble(ACCOUNT_MARGIN) * 100)); pos += 4;
        WriteUInt32(buffer, pos, (uint)(AccountInfoDouble(ACCOUNT_MARGIN_FREE) * 100)); pos += 4;
        WriteUInt16(buffer, pos, (ushort)AccountInfoInteger(ACCOUNT_LEVERAGE)); pos += 2;

        // Currency (3 bytes + 1 padding)
        string currency = StringSubstr(AccountInfoString(ACCOUNT_CURRENCY), 0, 3);
        for(int i = 0; i < 3; i++)
        {
            if(i < StringLen(currency))
                buffer[pos + i] = (char)StringGetCharacter(currency, i);
            else
                buffer[pos + i] = 0;
        }
        pos += 4; // Include padding

        // Timestamp (8 bytes)
        WriteUInt64(buffer, pos, (ulong)GetTickCount());

        Print("[BINARY] Created account profile packet: ", totalSize, " bytes");
        return totalSize;
    }

    //+------------------------------------------------------------------+
    //| Validate binary packet                                         |
    //+------------------------------------------------------------------+
    static bool ValidatePacket(const char &buffer[], int size)
    {
        if(size < HEADER_SIZE) return false;

        // Check magic number
        uint magic = ReadUInt32(buffer, 0);
        if(magic != BINARY_MAGIC)
        {
            Print("[VALIDATION] Invalid magic: ", IntegerToString(magic, 16), " expected: ", IntegerToString(BINARY_MAGIC, 16));
            return false;
        }

        // Check version
        ushort version = ReadUInt16(buffer, 4);
        if(version != BINARY_VERSION)
        {
            Print("[VALIDATION] Version mismatch: ", version, " expected: ", BINARY_VERSION);
        }

        return true;
    }

    //+------------------------------------------------------------------+
    //| Get packet info for debugging                                  |
    //+------------------------------------------------------------------+
    static string GetPacketInfo(const char &buffer[], int size)
    {
        if(size < HEADER_SIZE) return "Invalid packet - too small";

        uint magic = ReadUInt32(buffer, 0);
        ushort version = ReadUInt16(buffer, 4);
        uchar msgType = (uchar)buffer[6];
        uchar count = (uchar)buffer[7];
        ulong timestamp = ReadUInt64(buffer, 8);

        string info = "Binary Packet Info:\n";
        info += "Magic: " + IntegerToString(magic, 16) + "\n";
        info += "Version: " + IntegerToString(version) + "\n";
        info += "Type: " + IntegerToString(msgType) + "\n";
        info += "Count: " + IntegerToString(count) + "\n";
        info += "Timestamp: " + IntegerToString(timestamp) + "\n";
        info += "Size: " + IntegerToString(size) + " bytes";

        return info;
    }
};

#endif // BINARYPROTOCOL_MQH