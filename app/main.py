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


class DNSServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        # message = data.decode()
        print(f'Received {data} from {addr}')
        header = DNSHeader(1234, 0x8000, 0, 0, 0, 0)
        response = struct.pack("!HHHHHH", *dataclasses.astuple(header))
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
