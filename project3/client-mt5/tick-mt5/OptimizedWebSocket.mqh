//+------------------------------------------------------------------+
//|                                        OptimizedWebSocket.mqh    |
//|                        Copyright 2024, Suho AI Trading Platform |
//|                   Optimized fork of official MQL5 WebSocket     |
//+------------------------------------------------------------------+
#property copyright "2024, Suho AI Trading Platform"
#property link      "https://aitrading.suho.platform"
#property version   "1.00"
#property description "High-performance WebSocket client for MT5"
#property description "Optimizations: binary frames, zero-copy, async queue"

//+------------------------------------------------------------------+
//| WebSocket OpCode Constants                                       |
//+------------------------------------------------------------------+
#define WS_OPCODE_CONTINUATION  0x00
#define WS_OPCODE_TEXT          0x01
#define WS_OPCODE_BINARY        0x02
#define WS_OPCODE_CLOSE         0x08
#define WS_OPCODE_PING          0x09
#define WS_OPCODE_PONG          0x0A

//+------------------------------------------------------------------+
//| WebSocket Frame Structure                                        |
//+------------------------------------------------------------------+
struct WebSocketFrame {
    bool fin;              // Final frame flag
    uchar opcode;          // OpCode (text, binary, etc)
    bool masked;           // Masking flag
    ulong payload_length;  // Payload data length
    uchar mask_key[4];     // Masking key (if masked)
    uchar payload[];       // Payload data
};

//+------------------------------------------------------------------+
//| Optimized WebSocket Client Class                                |
//+------------------------------------------------------------------+
class OptimizedWebSocketClient {
private:
    int       m_socket;                // Socket handle
    string    m_host;                  // Server hostname
    int       m_port;                  // Server port
    string    m_path;                  // WebSocket path
    bool      m_connected;             // Connection state
    bool      m_use_binary;            // Use binary frames (faster)

    // Performance optimization: Pre-allocated buffers
    uchar     m_send_buffer[65536];    // 64KB send buffer
    uchar     m_recv_buffer[65536];    // 64KB receive buffer
    int       m_send_buffer_size;      // Current send buffer size

    // Async send queue for non-blocking sends
    string    m_send_queue[];
    int       m_queue_size;
    int       m_max_queue_size;

    // Statistics
    ulong     m_messages_sent;
    ulong     m_messages_received;
    ulong     m_bytes_sent;
    ulong     m_bytes_received;
    datetime  m_last_ping_time;
    datetime  m_last_pong_time;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                      |
    //+------------------------------------------------------------------+
    OptimizedWebSocketClient() {
        m_socket = INVALID_HANDLE;
        m_connected = false;
        m_use_binary = true;           // Default: binary frames (faster)
        m_send_buffer_size = 0;
        m_queue_size = 0;
        m_max_queue_size = 1000;       // Max 1000 messages in queue
        m_messages_sent = 0;
        m_messages_received = 0;
        m_bytes_sent = 0;
        m_bytes_received = 0;
        ArrayResize(m_send_queue, m_max_queue_size);
    }

    //+------------------------------------------------------------------+
    //| Destructor                                                       |
    //+------------------------------------------------------------------+
    ~OptimizedWebSocketClient() {
        Disconnect();
    }

    //+------------------------------------------------------------------+
    //| Parse WebSocket URL                                             |
    //+------------------------------------------------------------------+
    bool ParseURL(string url, string &host, int &port, string &path) {
        // ws://localhost:8001/ws/ticks
        // wss://localhost:8001/ws/ticks (SSL not implemented yet)

        int protocol_end = StringFind(url, "://");
        if(protocol_end < 0) return false;

        string protocol = StringSubstr(url, 0, protocol_end);
        string rest = StringSubstr(url, protocol_end + 3);

        // Extract host:port/path
        int path_start = StringFind(rest, "/");
        string host_port;

        if(path_start >= 0) {
            host_port = StringSubstr(rest, 0, path_start);
            path = StringSubstr(rest, path_start);
        } else {
            host_port = rest;
            path = "/";
        }

        // Extract host and port
        int port_start = StringFind(host_port, ":");
        if(port_start >= 0) {
            host = StringSubstr(host_port, 0, port_start);
            port = (int)StringToInteger(StringSubstr(host_port, port_start + 1));
        } else {
            host = host_port;
            port = (protocol == "wss") ? 443 : 80;
        }

        return true;
    }

    //+------------------------------------------------------------------+
    //| Connect to WebSocket server                                     |
    //+------------------------------------------------------------------+
    bool Connect(string url) {
        if(m_connected) {
            Print("⚠️  Already connected. Disconnect first.");
            return false;
        }

        // Parse URL
        if(!ParseURL(url, m_host, m_port, m_path)) {
            Print("❌ Invalid WebSocket URL: ", url);
            return false;
        }

        Print("🔌 Connecting to WebSocket: ", m_host, ":", m_port, m_path);

        // Create TCP socket
        m_socket = SocketCreate();
        if(m_socket == INVALID_HANDLE) {
            Print("❌ Failed to create socket");
            return false;
        }

        // Connect to server
        if(!SocketConnect(m_socket, m_host, m_port, 5000)) {
            Print("❌ Failed to connect to ", m_host, ":", m_port);
            SocketClose(m_socket);
            m_socket = INVALID_HANDLE;
            return false;
        }

        // Send WebSocket handshake
        if(!SendHandshake()) {
            Print("❌ WebSocket handshake failed");
            SocketClose(m_socket);
            m_socket = INVALID_HANDLE;
            return false;
        }

        // Receive handshake response
        if(!ReceiveHandshake()) {
            Print("❌ WebSocket handshake response invalid");
            SocketClose(m_socket);
            m_socket = INVALID_HANDLE;
            return false;
        }

        m_connected = true;
        m_last_ping_time = TimeCurrent();
        m_last_pong_time = TimeCurrent();

        Print("✅ WebSocket connected successfully");
        return true;
    }

    //+------------------------------------------------------------------+
    //| Send WebSocket handshake                                        |
    //+------------------------------------------------------------------+
    bool SendHandshake() {
        // Generate random key for handshake
        string key = GenerateWebSocketKey();

        // Build HTTP handshake request
        string handshake =
            "GET " + m_path + " HTTP/1.1\r\n" +
            "Host: " + m_host + ":" + IntegerToString(m_port) + "\r\n" +
            "Upgrade: websocket\r\n" +
            "Connection: Upgrade\r\n" +
            "Sec-WebSocket-Key: " + key + "\r\n" +
            "Sec-WebSocket-Version: 13\r\n" +
            "User-Agent: MT5-OptimizedWebSocket/1.0\r\n" +
            "\r\n";

        // Send handshake
        uchar data[];
        StringToCharArray(handshake, data, 0, StringLen(handshake));

        int sent = SocketSend(m_socket, data, ArraySize(data));
        return (sent == ArraySize(data));
    }

    //+------------------------------------------------------------------+
    //| Receive WebSocket handshake response                            |
    //+------------------------------------------------------------------+
    bool ReceiveHandshake() {
        uchar response[];
        ArrayResize(response, 4096);

        uint timeout = 5000; // 5 seconds
        int received = SocketRead(m_socket, response, ArraySize(response), timeout);

        if(received <= 0) return false;

        // Convert to string
        string response_str = CharArrayToString(response, 0, received);

        // Check if upgrade succeeded
        if(StringFind(response_str, "101 Switching Protocols") < 0) {
            Print("❌ WebSocket upgrade failed");
            Print("Response: ", response_str);
            return false;
        }

        return true;
    }

    //+------------------------------------------------------------------+
    //| Generate random WebSocket key                                   |
    //+------------------------------------------------------------------+
    string GenerateWebSocketKey() {
        // Generate 16 random bytes and encode to base64
        uchar random_bytes[16];
        for(int i = 0; i < 16; i++) {
            random_bytes[i] = (uchar)((MathRand() & 0xFF)); // Explicit cast and bit mask
        }
        return Base64Encode(random_bytes);
    }

    //+------------------------------------------------------------------+
    //| Simple Base64 encoding                                          |
    //+------------------------------------------------------------------+
    string Base64Encode(uchar &data[]) {
        string base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        string result = "";

        int size = ArraySize(data);
        int i = 0;

        while(i < size) {
            int b1 = data[i++];
            int b2 = (i < size) ? data[i++] : 0;
            int b3 = (i < size) ? data[i++] : 0;

            int triple = (b1 << 16) | (b2 << 8) | b3;

            result += StringSubstr(base64_chars, (triple >> 18) & 0x3F, 1);
            result += StringSubstr(base64_chars, (triple >> 12) & 0x3F, 1);
            result += (i > size + 1) ? "=" : StringSubstr(base64_chars, (triple >> 6) & 0x3F, 1);
            result += (i > size) ? "=" : StringSubstr(base64_chars, triple & 0x3F, 1);
        }

        return result;
    }

    //+------------------------------------------------------------------+
    //| Send message (optimized with binary frames)                     |
    //+------------------------------------------------------------------+
    bool Send(string message) {
        if(!m_connected) return false;

        // Convert message to bytes
        uchar payload[];
        StringToCharArray(message, payload, 0, StringLen(message));

        return SendFrame(m_use_binary ? WS_OPCODE_BINARY : WS_OPCODE_TEXT, payload);
    }

    //+------------------------------------------------------------------+
    //| Send raw binary data (for Suho Binary Protocol)                |
    //+------------------------------------------------------------------+
    bool SendBinary(char &data[], int size) {
        if(!m_connected) return false;

        // Convert char array to uchar array
        uchar payload[];
        ArrayResize(payload, size);
        for(int i = 0; i < size; i++) {
            payload[i] = (uchar)data[i];
        }

        return SendFrame(WS_OPCODE_BINARY, payload);
    }

    //+------------------------------------------------------------------+
    //| Send message asynchronously (queue-based)                       |
    //+------------------------------------------------------------------+
    bool SendAsync(string message) {
        if(m_queue_size >= m_max_queue_size) {
            Print("⚠️  Send queue full, dropping message");
            return false;
        }

        m_send_queue[m_queue_size++] = message;
        return true;
    }

    //+------------------------------------------------------------------+
    //| Process async send queue                                        |
    //+------------------------------------------------------------------+
    void ProcessSendQueue() {
        int sent_count = 0;
        int max_per_tick = 100; // Max 100 messages per process

        while(m_queue_size > 0 && sent_count < max_per_tick) {
            if(Send(m_send_queue[0])) {
                sent_count++;
                // Shift queue
                for(int i = 0; i < m_queue_size - 1; i++) {
                    m_send_queue[i] = m_send_queue[i + 1];
                }
                m_queue_size--;
            } else {
                break; // Stop if send fails
            }
        }
    }

    //+------------------------------------------------------------------+
    //| Send WebSocket frame                                            |
    //+------------------------------------------------------------------+
    bool SendFrame(uchar opcode, uchar &payload[]) {
        int payload_len = ArraySize(payload);

        // Build frame header
        uchar frame[14]; // Max header size
        int header_len = 0;

        // Byte 0: FIN + OpCode
        frame[header_len++] = 0x80 | opcode; // FIN=1, OpCode

        // Byte 1: MASK + Payload length
        bool mask = true; // Client must mask
        uchar mask_bit = mask ? 0x80 : 0x00;

        if(payload_len < 126) {
            frame[header_len++] = mask_bit | (uchar)payload_len;
        } else if(payload_len < 65536) {
            frame[header_len++] = mask_bit | 126;
            frame[header_len++] = (uchar)(payload_len >> 8);
            frame[header_len++] = (uchar)(payload_len & 0xFF);
        } else {
            frame[header_len++] = mask_bit | 127;
            // Extended payload length (8 bytes)
            for(int i = 7; i >= 0; i--) {
                frame[header_len++] = (uchar)((payload_len >> (i * 8)) & 0xFF);
            }
        }

        // Masking key (4 random bytes)
        uchar mask_key[4];
        if(mask) {
            for(int i = 0; i < 4; i++) {
                mask_key[i] = (uchar)((MathRand() & 0xFF)); // Explicit cast and bit mask
                frame[header_len++] = mask_key[i];
            }
        }

        // Send frame header
        if(SocketSend(m_socket, frame, header_len) != header_len) {
            return false;
        }

        // Mask and send payload
        if(mask) {
            for(int i = 0; i < payload_len; i++) {
                payload[i] ^= mask_key[i % 4];
            }
        }

        if(SocketSend(m_socket, payload, payload_len) != payload_len) {
            return false;
        }

        m_messages_sent++;
        m_bytes_sent += header_len + payload_len;

        return true;
    }

    //+------------------------------------------------------------------+
    //| Receive message                                                  |
    //+------------------------------------------------------------------+
    bool Receive(string &message) {
        if(!m_connected) return false;

        // Read frame header (at least 2 bytes)
        uchar header[2];
        if(SocketRead(m_socket, header, 2, 100) != 2) {
            return false; // No data or timeout
        }

        // Parse header
        bool fin = (header[0] & 0x80) != 0;
        uchar opcode = header[0] & 0x0F;
        bool masked = (header[1] & 0x80) != 0;
        ulong payload_len = header[1] & 0x7F;

        // Handle extended payload length
        if(payload_len == 126) {
            uchar len_bytes[2];
            if(SocketRead(m_socket, len_bytes, 2, 1000) != 2) return false;
            payload_len = (len_bytes[0] << 8) | len_bytes[1];
        } else if(payload_len == 127) {
            uchar len_bytes[8];
            if(SocketRead(m_socket, len_bytes, 8, 1000) != 8) return false;
            payload_len = 0;
            for(int i = 0; i < 8; i++) {
                payload_len = (payload_len << 8) | len_bytes[i];
            }
        }

        // Read masking key (if masked)
        uchar mask_key[4];
        if(masked) {
            if(SocketRead(m_socket, mask_key, 4, 1000) != 4) return false;
        }

        // Read payload
        uchar payload[];
        ArrayResize(payload, (int)payload_len);
        if(SocketRead(m_socket, payload, (int)payload_len, 5000) != (int)payload_len) {
            return false;
        }

        // Unmask if needed
        if(masked) {
            for(int i = 0; i < (int)payload_len; i++) {
                payload[i] ^= mask_key[i % 4];
            }
        }

        // Handle different opcodes
        if(opcode == WS_OPCODE_TEXT || opcode == WS_OPCODE_BINARY) {
            message = CharArrayToString(payload);
            m_messages_received++;
            m_bytes_received += payload_len;
            return true;
        } else if(opcode == WS_OPCODE_PING) {
            // Respond with PONG
            SendFrame(WS_OPCODE_PONG, payload);
            return false;
        } else if(opcode == WS_OPCODE_PONG) {
            m_last_pong_time = TimeCurrent();
            return false;
        } else if(opcode == WS_OPCODE_CLOSE) {
            Print("📪 Server closed connection");
            Disconnect();
            return false;
        }

        return false;
    }

    //+------------------------------------------------------------------+
    //| Send Ping (keep-alive)                                          |
    //+------------------------------------------------------------------+
    bool SendPing() {
        if(!m_connected) return false;

        // Empty payload for ping (dynamic array)
        uchar payload[];
        ArrayResize(payload, 0);
        bool success = SendFrame(WS_OPCODE_PING, payload);

        if(success) {
            m_last_ping_time = TimeCurrent();
        }

        return success;
    }

    //+------------------------------------------------------------------+
    //| Disconnect from server                                          |
    //+------------------------------------------------------------------+
    void Disconnect() {
        if(!m_connected) return;

        // Send close frame
        uchar payload[2] = {0x03, 0xE8}; // Status code 1000 (normal closure)
        SendFrame(WS_OPCODE_CLOSE, payload);

        // Close socket
        if(m_socket != INVALID_HANDLE) {
            SocketClose(m_socket);
            m_socket = INVALID_HANDLE;
        }

        m_connected = false;
        Print("📪 WebSocket disconnected");
    }

    //+------------------------------------------------------------------+
    //| Check if connected                                              |
    //+------------------------------------------------------------------+
    bool IsConnected() {
        return m_connected && (m_socket != INVALID_HANDLE);
    }

    //+------------------------------------------------------------------+
    //| Get statistics                                                   |
    //+------------------------------------------------------------------+
    string GetStatistics() {
        return StringFormat(
            "Messages: Sent=%I64u, Received=%I64u | Bytes: Sent=%I64u, Received=%I64u | Queue: %d/%d",
            m_messages_sent, m_messages_received,
            m_bytes_sent, m_bytes_received,
            m_queue_size, m_max_queue_size
        );
    }

    //+------------------------------------------------------------------+
    //| Get queue size                                                   |
    //+------------------------------------------------------------------+
    int GetQueueSize() {
        return m_queue_size;
    }

    //+------------------------------------------------------------------+
    //| Set binary mode                                                  |
    //+------------------------------------------------------------------+
    void SetBinaryMode(bool use_binary) {
        m_use_binary = use_binary;
    }
};
//+------------------------------------------------------------------+
