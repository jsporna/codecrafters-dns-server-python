import dataclasses
from dataclasses import dataclass
import asyncio
import struct


@dataclass
class DNSHeader:
    id: int
    flags: int
    qdcount: int = 0
    ancount: int = 0
    nscount: int = 0
    arcount: int = 0

    def to_bytes(self):
        return struct.pack("!HHHHHH",
                           self.id, self.flags,
                           self.qdcount, self.ancount, self.nscount, self.arcount)


@dataclass
class DNSQuestion:
    name: bytes
    type_: int
    class_: int

    def __init__(self, name: str, type_: int, class_: int):
        self.name = self.encode_dns_name(name)
        self.type_ = type_
        self.class_ = class_

    def to_bytes(self):
        return self.name + struct.pack("!HH", self.type_, self.class_)

    @staticmethod
    def encode_dns_name(name):
        encoded = b""
        for part in name.encode("ascii").split(b"."):
            encoded += bytes([len(part)]) + part
        return encoded + b"\x00"


class DNSServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        # message = data.decode()
        print(f'Received {data} from {addr}')
        header = DNSHeader(1234, 0x8000, 1, 0, 0, 0)
        question = DNSQuestion("codecrafters.io", 1, 1)
        response = header.to_bytes() + question.to_bytes()
        print(f'Sending {response} to {addr}')
        self.transport.sendto(response, addr)


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
