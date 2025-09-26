//+------------------------------------------------------------------+
//|                                            BinaryProtocol.mqh |
//|                     Custom binary protocol for ultra-low latency |
//+------------------------------------------------------------------+
#ifndef BINARYPROTOCOL_MQH
#define BINARYPROTOCOL_MQH

//+------------------------------------------------------------------+
//| Symbol ID enumeration for binary protocol                      |
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
//| Message type enumeration                                        |
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
//| Trading Header Structure (16 bytes)                            |
//+------------------------------------------------------------------+
struct TradingHeader
{
    uint   magic;        // 4 bytes - 0x53554854 ("SUHO")
    ushort version;      // 2 bytes - Protocol version
    uchar  msg_type;     // 1 byte  - Message type
    uchar  pair_count;   // 1 byte  - Number of pairs
    ulong  timestamp;    // 8 bytes - Batch timestamp
};

//+------------------------------------------------------------------+
//| Price Data Structure (16 bytes per pair)                       |
//+------------------------------------------------------------------+
struct PriceData
{
    uint symbol_id;      // 4 bytes - Symbol enum
    uint bid;            // 4 bytes - Bid price (fixed point * 100000)
    uint ask;            // 4 bytes - Ask price (fixed point * 100000)
    uint flags;          // 4 bytes - Spread + server_id + status flags
};

//+------------------------------------------------------------------+
//| Account Profile Structure (64 bytes)                           |
//+------------------------------------------------------------------+
struct AccountProfile
{
    char   user_id[16];     // 16 bytes - User identifier
    char   broker[16];      // 16 bytes - Broker name
    uint   account_number;  // 4 bytes  - Account number
    uint   balance;         // 4 bytes  - Balance * 100 (fixed point)
    uint   equity;          // 4 bytes  - Equity * 100
    uint   margin;          // 4 bytes  - Margin * 100
    uint   free_margin;     // 4 bytes  - Free margin * 100
    ushort leverage;        // 2 bytes  - Leverage
    uchar  currency[3];     // 3 bytes  - Currency code (USD, EUR, etc)
    uchar  reserved;        // 1 byte   - Padding for alignment
    ulong  timestamp;       // 8 bytes  - Profile timestamp
};

//+------------------------------------------------------------------+
//| Trading Command Structure (32 bytes)                           |
//+------------------------------------------------------------------+
struct TradingCommand
{
    uint   command_id;      // 4 bytes - Unique command ID
    uchar  action;          // 1 byte  - BUY=1, SELL=2, CLOSE=3, MODIFY=4
    uchar  symbol_id;       // 1 byte  - Symbol enum
    ushort lots_fp;         // 2 bytes - Lots * 100 (0.01 = 1)
    uint   price;           // 4 bytes - Entry price (fixed point)
    uint   stop_loss;       // 4 bytes - Stop loss (fixed point)
    uint   take_profit;     // 4 bytes - Take profit (fixed point)
    ulong  ticket;          // 8 bytes - Position ticket (for modify/close)
    uint   magic_number;    // 4 bytes - EA magic number
};

//+------------------------------------------------------------------+
//| Custom Binary Protocol Class                                   |
//+------------------------------------------------------------------+
class CBinaryProtocol
{
private:
    static const uint PROTOCOL_MAGIC = 0x53554854; // "SUHO"
    static const ushort PROTOCOL_VERSION = 0x0001;

public:
    //+------------------------------------------------------------------+
    //| Convert symbol string to enum ID                               |
    //+------------------------------------------------------------------+
    static ENUM_SYMBOL_ID GetSymbolID(string symbol)
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
    static string GetSymbolString(ENUM_SYMBOL_ID id)
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
    //| Convert double price to fixed point                            |
    //+------------------------------------------------------------------+
    static uint PriceToFixedPoint(double price)
    {
        return (uint)(price * 100000.0 + 0.5); // Round to nearest
    }

    //+------------------------------------------------------------------+
    //| Convert fixed point to double price                            |
    //+------------------------------------------------------------------+
    static double FixedPointToPrice(uint fixed_point)
    {
        return (double)fixed_point / 100000.0;
    }

    //+------------------------------------------------------------------+
    //| Calculate checksum for data validation                         |
    //+------------------------------------------------------------------+
    static ushort CalculateChecksum(const char &data[], int size)
    {
        uint checksum = 0;
        for(int i = 0; i < size; i++)
        {
            checksum += (uchar)data[i];
        }
        return (ushort)(checksum & 0xFFFF);
    }

    //+------------------------------------------------------------------+
    //| Create binary price stream packet                              |
    //+------------------------------------------------------------------+
    static int CreatePriceStreamPacket(const string user_id, string &symbols[], MqlTick &ticks[], char &buffer[])
    {
        int pairs = ArraySize(symbols);
        if(pairs > 255) pairs = 255; // Max pairs per packet

        // Calculate total size: header(16) + pairs * pricedata(16)
        int total_size = 16 + (pairs * 16);
        ArrayResize(buffer, total_size);
        ArrayInitialize(buffer, 0);

        int pos = 0;

        // Create header
        TradingHeader header;
        header.magic = PROTOCOL_MAGIC;
        header.version = PROTOCOL_VERSION;
        header.msg_type = MSG_PRICE_STREAM;
        header.pair_count = (uchar)pairs;
        header.timestamp = (ulong)GetTickCount();

        // Copy header to buffer
        ArrayCopy(buffer, header, pos, 0, sizeof(TradingHeader));
        pos += sizeof(TradingHeader);

        // Add price data
        for(int i = 0; i < pairs; i++)
        {
            PriceData price;
            price.symbol_id = GetSymbolID(symbols[i]);
            price.bid = PriceToFixedPoint(ticks[i].bid);
            price.ask = PriceToFixedPoint(ticks[i].ask);

            // Pack spread (points), server_id, and flags
            int spread_points = (int)((ticks[i].ask - ticks[i].bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT));
            price.flags = (spread_points & 0xFFFF) | (1 << 16); // Server ID = 1

            // Copy price data to buffer
            ArrayCopy(buffer, price, pos, 0, sizeof(PriceData));
            pos += sizeof(PriceData);
        }

        return total_size;
    }

    //+------------------------------------------------------------------+
    //| Create binary account profile packet                           |
    //+------------------------------------------------------------------+
    static int CreateAccountProfilePacket(const string user_id, char &buffer[])
    {
        int total_size = 16 + 64; // header + profile
        ArrayResize(buffer, total_size);
        ArrayInitialize(buffer, 0);

        int pos = 0;

        // Create header
        TradingHeader header;
        header.magic = PROTOCOL_MAGIC;
        header.version = PROTOCOL_VERSION;
        header.msg_type = MSG_ACCOUNT_PROFILE;
        header.pair_count = 1; // One profile
        header.timestamp = (ulong)GetTickCount();

        // Copy header to buffer
        ArrayCopy(buffer, header, pos, 0, sizeof(TradingHeader));
        pos += sizeof(TradingHeader);

        // Create account profile
        AccountProfile profile;
        ArrayInitialize(profile, 0);

        // Copy user ID (max 15 chars + null terminator)
        string safe_user_id = StringSubstr(user_id, 0, 15);
        StringToCharArray(safe_user_id, profile.user_id, 0, StringLen(safe_user_id));

        // Copy broker name
        string broker = AccountInfoString(ACCOUNT_COMPANY);
        broker = StringSubstr(broker, 0, 15);
        StringToCharArray(broker, profile.broker, 0, StringLen(broker));

        profile.account_number = (uint)AccountInfoInteger(ACCOUNT_LOGIN);
        profile.balance = (uint)(AccountInfoDouble(ACCOUNT_BALANCE) * 100);
        profile.equity = (uint)(AccountInfoDouble(ACCOUNT_EQUITY) * 100);
        profile.margin = (uint)(AccountInfoDouble(ACCOUNT_MARGIN) * 100);
        profile.free_margin = (uint)(AccountInfoDouble(ACCOUNT_MARGIN_FREE) * 100);
        profile.leverage = (ushort)AccountInfoInteger(ACCOUNT_LEVERAGE);
        profile.timestamp = (ulong)GetTickCount();

        // Copy currency
        string currency = AccountInfoString(ACCOUNT_CURRENCY);
        currency = StringSubstr(currency, 0, 3);
        StringToCharArray(currency, profile.currency, 0, StringLen(currency));

        // Copy profile to buffer
        ArrayCopy(buffer, profile, pos, 0, sizeof(AccountProfile));

        return total_size;
    }

    //+------------------------------------------------------------------+
    //| Parse binary trading command from buffer                       |
    //+------------------------------------------------------------------+
    static bool ParseTradingCommand(const char &buffer[], int size, TradingCommand &command)
    {
        if(size < 16) return false; // Minimum header size

        // Extract header
        TradingHeader header;
        ArrayCopy(header, buffer, 0, 0, sizeof(TradingHeader));

        // Validate magic and version
        if(header.magic != PROTOCOL_MAGIC)
        {
            Print("[ERROR] Invalid binary protocol magic: ", IntegerToString(header.magic, 16));
            return false;
        }

        if(header.version != PROTOCOL_VERSION)
        {
            Print("[WARNING] Protocol version mismatch: ", header.version);
        }

        if(header.msg_type != MSG_TRADE_COMMAND)
        {
            Print("[ERROR] Expected trading command, got type: ", header.msg_type);
            return false;
        }

        if(size < 16 + 32) // header + command
        {
            Print("[ERROR] Buffer too small for trading command");
            return false;
        }

        // Extract trading command
        ArrayCopy(command, buffer, 0, 16, sizeof(TradingCommand));

        Print("[SUCCESS] Binary trading command parsed - Action: ", command.action,
              " Symbol: ", GetSymbolString((ENUM_SYMBOL_ID)command.symbol_id));

        return true;
    }

    //+------------------------------------------------------------------+
    //| Validate binary packet integrity                               |
    //+------------------------------------------------------------------+
    static bool ValidatePacket(const char &buffer[], int size)
    {
        if(size < 16) return false;

        // Extract header
        TradingHeader header;
        ArrayCopy(header, buffer, 0, 0, sizeof(TradingHeader));

        // Check magic number
        if(header.magic != PROTOCOL_MAGIC)
        {
            Print("[VALIDATION] Invalid magic number: ", IntegerToString(header.magic, 16));
            return false;
        }

        // Check size consistency
        int expected_size = 16; // Header
        switch(header.msg_type)
        {
            case MSG_PRICE_STREAM:
                expected_size += header.pair_count * 16;
                break;
            case MSG_ACCOUNT_PROFILE:
                expected_size += 64;
                break;
            case MSG_TRADE_COMMAND:
                expected_size += 32;
                break;
        }

        if(size != expected_size)
        {
            Print("[VALIDATION] Size mismatch - Expected: ", expected_size, " Got: ", size);
            return false;
        }

        return true;
    }

    //+------------------------------------------------------------------+
    //| Get packet info for debugging                                  |
    //+------------------------------------------------------------------+
    static string GetPacketInfo(const char &buffer[], int size)
    {
        if(size < 16) return "Invalid packet - too small";

        TradingHeader header;
        ArrayCopy(header, buffer, 0, 0, sizeof(TradingHeader));

        string info = "Binary Packet Info:\n";
        info += "Magic: " + IntegerToString(header.magic, 16) + "\n";
        info += "Version: " + IntegerToString(header.version) + "\n";
        info += "Type: " + IntegerToString(header.msg_type) + "\n";
        info += "Count: " + IntegerToString(header.pair_count) + "\n";
        info += "Timestamp: " + IntegerToString(header.timestamp) + "\n";
        info += "Size: " + IntegerToString(size) + " bytes";

        return info;
    }
};

#endif // BINARYPROTOCOL_MQH