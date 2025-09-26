"""
Shared Protocol Definitions for Suho AI Trading System

This module provides Protocol Buffer definitions and utilities
for Python-based backend services (ML Processing, Analytics, etc.)
"""

from typing import Dict, Any, Union, Optional
import struct
from enum import IntEnum

# Import generated Protocol Buffer classes
# from . import trading_pb2

__version__ = "1.0.0"

# Protocol version constants
PROTOCOL_VERSION = {
    "major": 2,
    "minor": 0,
    "patch": 0
}

# Suho Binary Protocol constants
class SuhoBinary:
    MAGIC_NUMBER = 0x53554854  # "SUHO"
    VERSION = 0x0001
    PACKET_SIZE = 144
    HEADER_SIZE = 16
    DATA_SIZE = 128
    MAX_SYMBOLS_PER_PACKET = 7

class SuhoMessageType(IntEnum):
    """Message types for Suho Binary Protocol"""
    PRICE_STREAM = 0x01
    TRADING_COMMAND = 0x02
    ACCOUNT_PROFILE = 0x03
    EXECUTION_RESP = 0x04
    HEARTBEAT = 0x05
    ERROR_RESPONSE = 0x06
    SYSTEM_STATUS = 0x07

class SuhoSymbol(IntEnum):
    """Symbol enumeration matching binary protocol"""
    SYMBOL_UNKNOWN = 0
    EURUSD = 1
    GBPUSD = 2
    USDJPY = 3
    AUDUSD = 4
    USDCAD = 5
    USDCHF = 6
    NZDUSD = 7
    EURGBP = 8
    EURJPY = 9
    GBPJPY = 10
    AUDJPY = 11
    EURAUD = 12
    EURCHF = 13
    GBPCHF = 14
    AUDCAD = 15
    AUDCHF = 16
    CADCHF = 17
    CADJPY = 18
    CHFJPY = 19
    XAUUSD = 36
    XAGUSD = 37
    USOIL = 38
    BRENT = 39

class ProtocolUtils:
    """Utility functions for protocol conversion"""

    @staticmethod
    def binary_to_protobuf_symbol(binary_symbol: int) -> int:
        """Convert binary symbol enum to Protocol Buffer Symbol"""
        return binary_symbol  # Direct mapping for now

    @staticmethod
    def binary_to_protobuf_price(binary_price: int) -> float:
        """Convert binary price (integer) to Protocol Buffer price (float)"""
        return binary_price / 100000.0

    @staticmethod
    def protobuf_to_binary_price(price: float) -> int:
        """Convert Protocol Buffer price (float) to binary price (integer)"""
        return round(price * 100000)

    @staticmethod
    def binary_to_protobuf_timestamp(microseconds: int) -> Dict[str, int]:
        """Convert binary timestamp (microseconds) to Protocol Buffer Timestamp"""
        return {
            "seconds": microseconds // 1000000,
            "nanos": (microseconds % 1000000) * 1000
        }

    @staticmethod
    def protobuf_to_binary_timestamp(timestamp: Dict[str, int]) -> int:
        """Convert Protocol Buffer Timestamp to binary timestamp (microseconds)"""
        return timestamp["seconds"] * 1000000 + timestamp["nanos"] // 1000

    @staticmethod
    def validate_binary_header(header_bytes: bytes) -> bool:
        """Validate Suho Binary packet header"""
        if len(header_bytes) < 16:
            return False

        magic, version, msg_type = struct.unpack('<IHB', header_bytes[:7])

        return (magic == SuhoBinary.MAGIC_NUMBER and
                version == SuhoBinary.VERSION and
                1 <= msg_type <= 7)

    @staticmethod
    def get_symbol_name(symbol: SuhoSymbol) -> str:
        """Get symbol name from enum value"""
        return symbol.name if isinstance(symbol, SuhoSymbol) else 'UNKNOWN'

    @staticmethod
    def get_symbol_enum(symbol_name: str) -> SuhoSymbol:
        """Get symbol enum from name"""
        try:
            return SuhoSymbol[symbol_name.upper()]
        except KeyError:
            return SuhoSymbol.SYMBOL_UNKNOWN

# Type checking functions
def is_price_stream(message: Dict[str, Any]) -> bool:
    """Check if message is a price stream"""
    return 'prices' in message and isinstance(message['prices'], list)

def is_trading_command(message: Dict[str, Any]) -> bool:
    """Check if message is a trading command"""
    return 'command_id' in message and 'action' in message

def is_account_profile(message: Dict[str, Any]) -> bool:
    """Check if message is an account profile"""
    return 'account_number' in message and 'balance' in message

def is_trading_engine_output(message: Dict[str, Any]) -> bool:
    """Check if message is trading engine output"""
    return ('signals' in message and isinstance(message['signals'], list)) or \
           ('responses' in message and isinstance(message['responses'], list))

def is_analytics_output(message: Dict[str, Any]) -> bool:
    """Check if message is analytics output"""
    return 'performance_metrics' in message

def is_ml_output(message: Dict[str, Any]) -> bool:
    """Check if message is ML output"""
    return 'predictions' in message and isinstance(message['predictions'], list)

def is_notification_output(message: Dict[str, Any]) -> bool:
    """Check if message is notification output"""
    return 'channels' in message and isinstance(message['channels'], list)

# Custom exceptions
class ProtocolError(Exception):
    """Base class for protocol-related errors"""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code

class BinaryParseError(ProtocolError):
    """Error parsing binary protocol data"""
    def __init__(self, message: str):
        super().__init__(message, 'BINARY_PARSE_ERROR')

class ProtobufSerializeError(ProtocolError):
    """Error serializing Protocol Buffer data"""
    def __init__(self, message: str):
        super().__init__(message, 'PROTOBUF_SERIALIZE_ERROR')

class InvalidMessageTypeError(ProtocolError):
    """Invalid message type error"""
    def __init__(self, message_type: str):
        super().__init__(f"Invalid message type: {message_type}", 'INVALID_MESSAGE_TYPE')

# Binary protocol parser for Python services
class SuhoBinaryParser:
    """Parser for Suho Binary Protocol packets"""

    @staticmethod
    def parse_header(packet_bytes: bytes) -> Dict[str, Any]:
        """Parse binary packet header"""
        if len(packet_bytes) < SuhoBinary.HEADER_SIZE:
            raise BinaryParseError("Packet too short for header")

        header_data = struct.unpack('<IHBBQ', packet_bytes[:16])

        return {
            'magic': header_data[0],
            'version': header_data[1],
            'msg_type': header_data[2],
            'data_count': header_data[3],
            'timestamp': header_data[4]
        }

    @staticmethod
    def parse_price_stream(packet_bytes: bytes) -> Dict[str, Any]:
        """Parse price stream data from binary packet"""
        header = SuhoBinaryParser.parse_header(packet_bytes)

        if header['msg_type'] != SuhoMessageType.PRICE_STREAM:
            raise InvalidMessageTypeError(f"Expected PRICE_STREAM, got {header['msg_type']}")

        prices = []
        data_offset = SuhoBinary.HEADER_SIZE

        for i in range(header['data_count']):
            if data_offset + 18 > len(packet_bytes):
                break

            price_data = struct.unpack('<BIIHBB', packet_bytes[data_offset:data_offset + 18])

            prices.append({
                'symbol': price_data[0],
                'bid': ProtocolUtils.binary_to_protobuf_price(price_data[1]),
                'ask': ProtocolUtils.binary_to_protobuf_price(price_data[2]),
                'spread_pts': price_data[3],
                'volume': price_data[4]
            })

            data_offset += 18

        return {
            'type': 'price_stream',
            'timestamp': ProtocolUtils.binary_to_protobuf_timestamp(header['timestamp']),
            'prices': prices
        }

# Export all public APIs
__all__ = [
    'PROTOCOL_VERSION',
    'SuhoBinary',
    'SuhoMessageType',
    'SuhoSymbol',
    'ProtocolUtils',
    'SuhoBinaryParser',
    'ProtocolError',
    'BinaryParseError',
    'ProtobufSerializeError',
    'InvalidMessageTypeError',
    'is_price_stream',
    'is_trading_command',
    'is_account_profile',
    'is_trading_engine_output',
    'is_analytics_output',
    'is_ml_output',
    'is_notification_output'
]