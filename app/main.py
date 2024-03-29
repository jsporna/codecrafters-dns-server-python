from typing import List
from dataclasses import dataclass
from enum import Enum
import asyncio
import struct


def _encode_name(data: str) -> bytes:
    encoded = b""
    for part in data.encode("ascii").split(b"."):
        encoded += bytes([len(part)]) + part
    return encoded + b"\x00"


def _decode_name(data: bytes) -> str:
        parts = []
        start = 1
        length = data[0]
        end = start + length
        while length != 0:
            part = data[start:end].decode('ascii')
            parts.append(part)
            length = data[end]
            start = end+1
            end = start + length
        return ".".join(parts)


class Type_(Enum):
    ALL = 0
    A = 1
    NS = 2
    MD = 3
    MF = 4
    CNAME = 5
    SOA = 6
    MB = 7
    MG = 8
    MR = 9
    NULL = 10
    WKS = 11
    PTR = 12
    HINFO = 13
    MINFO = 14
    MX = 15
    TXT = 16


class Class_(Enum):
    ANY = 0
    IN = 1
    CS = 2
    CH = 3
    HS = 4


@dataclass
class Flags:
    qr: int
    opcode: int
    aa: int
    tc: int
    rd: int
    ra: int
    z: int
    rcode: int

    def __init__(self, flags: int):
        self.qr = (flags >> 15) & 1
        self.opcode = (flags >> 11) & 0b111
        self.aa = (flags >> 10) & 1
        self.tc = (flags >> 9) & 1
        self.rd = (flags >> 8) & 1
        self.ra = (flags >> 7) & 1
        self.z = (flags >> 4) & 0b111
        self.rcode = (flags >> 0) & 0b1111

    def to_int(self):
        return (self.qr * 0x8000 +
                self.opcode * 0x0800 +
                self.aa * 0x0400 +
                self.tc * 0x0200 +
                self.rd * 0x0100 +
                self.ra * 0x0080 +
                self.z * 0x0010 +
                self.rcode)


@dataclass
class DNSHeader:
    id: int
    flags: Flags
    qdcount: int = 0
    ancount: int = 0
    nscount: int = 0
    arcount: int = 0

    def __init__(self, data):
        self.id, flags_, self.qdcount, self.ancount, self.nscount, self.arcount = struct.unpack("!HHHHHH", data)
        self.flags = Flags(flags_)

    def to_bytes(self):
        return struct.pack("!HHHHHH",
                           self.id, self.flags.to_int(),
                           self.qdcount, self.ancount, self.nscount, self.arcount)


@dataclass
class ResourceRecord:
    name: str
    type_: Type_
    class_: Class_
    ttl: int
    data: str = ""

    def to_bytes(self):
        return _encode_name(self.name) + struct.pack("!HHI", self.type_.value,
                                                     self.class_.value, self.ttl)


class RecordA(ResourceRecord):
    data: str

    def _encode_data(self):
        encoded = b""
        for octet in self.data.split("."):
            encoded += int(octet).to_bytes(1, "big")
        return len(encoded).to_bytes(2, 'big') + encoded

    def to_bytes(self):
        return super().to_bytes() + self._encode_data()


@dataclass
class DNSAnswer:
    header: DNSHeader
    rrs: List[ResourceRecord]

    def to_bytes(self):
        answer = self.header.to_bytes()
        for rr in self.rrs:
            answer += rr.to_bytes()
        return answer


@dataclass
class DNSQuestion:
    name: str
    type_: Type_ = 1
    class_: Class_ = 1

    def __init__(self, data: bytes):
        self.name = _decode_name(data[:-4])
        type_, class_ = struct.unpack("!HH", data[-4:])
        self.type_, self.class_ = Type_(type_), Class_(class_)

    def to_bytes(self):
        return (_encode_name(self.name) +
                struct.pack("!HH", self.type_.value, self.class_.value))


@dataclass
class DNSPacket:
    header: DNSHeader
    questions: List[DNSQuestion]
    answers: List[ResourceRecord]
    authorities: List[ResourceRecord]
    additionals: List[ResourceRecord]

    def to_bytes(self):
        self.header.qdcount = len(self.questions)
        self.header.ancount = len(self.answers)
        self.header.nscount = len(self.authorities)
        self.header.arcount = len(self.additionals)
        self.header.flags.qr = 1
        if self.header.flags.opcode == 0:
            self.header.flags.rcode = 0
        else:
            self.header.flags.rcode = 4
        packet = self.header.to_bytes()
        for rr in self.questions:
            packet += rr.to_bytes()
        for rr in self.answers:
            packet += rr.to_bytes()
        for rr in self.authorities:
            packet += rr.to_bytes()
        for rr in self.additionals:
            packet += rr.to_bytes()

        return packet


class DNSServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        print(f'Received {data} from {addr}')
        header = DNSHeader(data[:12])
        question = DNSQuestion(data[12:])
        answer = RecordA(question.name, question.type_, question.class_, ttl=60, data="8.8.8.8")
        packet = DNSPacket(header, [question], [answer], [], [])
        print(packet.header)
        print(packet.header.flags)

        print(f'Sending {packet.to_bytes()} to {addr}')
        self.transport.sendto(packet.to_bytes(), addr)


async def main():
    print("Logs from your program will appear here!")

    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: DNSServerProtocol(),
        local_addr=('127.0.0.1', 2053)
    )

    try:
        await asyncio.sleep(3600)
    finally:
        transport.close()


if __name__ == "__main__":
    asyncio.run(main())
