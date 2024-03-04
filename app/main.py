import socket
import asyncio


class DNSServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        # message = data.decode()
        print(f'Received {data} from {addr}')
        # print(f'Send {message} to {addr}')
        self.transport.sendto(data, addr)


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
