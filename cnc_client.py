"""Interactive terminal OPC UA client. Start cnc_server.py first."""
import asyncio
from asyncua import Client, ua

ENDPOINT = "opc.tcp://127.0.0.1:4840/cnc/"
NAMESPACE = "urn:iiot-course:cnc"

async def browse(node, depth=0):
    name = await node.read_browse_name()
    cls = await node.read_node_class()
    print(f"{'  ' * depth}{name.Name} [{cls.name}] ({node.nodeid.to_string()})")
    for child in await node.get_children():
        await browse(child, depth + 1)

async def inspect(node):
    print("NodeId:", node.nodeid.to_string())
    print("BrowseName:", await node.read_browse_name())
    print("DisplayName:", (await node.read_display_name()).Text)
    cls = await node.read_node_class()
    print("NodeClass:", cls.name)
    if cls == ua.NodeClass.Variable:
        print("DataType:", (await node.read_data_type_as_variant_type()).name)
        print("Value:", await node.read_value())
        print("UserAccessLevel:", await node.get_user_access_level())
    print("Forward references (including type definitions):")
    for ref in await node.get_references(direction=ua.BrowseDirection.Forward):
        # Standard reference IDs are translated to their OPC UA names.
        label = ua.ObjectIdNames.get(ref.ReferenceTypeId.Identifier, ref.ReferenceTypeId.to_string())
        print(f"  {label} -> {ref.BrowseName.Name} ({ref.NodeId.to_string()})")

async def main():
    async with Client(ENDPOINT) as client:
        ns = await client.get_namespace_index(NAMESPACE)
        cnc = client.get_node(ua.NodeId("CNC_01", ns))
        print("Connected to", ENDPOINT)
        print("Namespace table:")
        for index, uri in enumerate(await client.get_namespace_array()):
            print(f"  ns={index}: {uri}")
        await browse(cnc)
        while True:
            print("\n1 Browse model | 2 Inspect node | 3 Toggle Running | 4 Reset count | 5 Quit")
            choice = (await asyncio.to_thread(input, "Choice: ")).strip()
            if choice == "1":
                await browse(cnc)
            elif choice == "2":
                identifier = (await asyncio.to_thread(input, "String identifier (e.g. CNC_01.Spindle.Speed): ")).strip()
                try:
                    await inspect(client.get_node(ua.NodeId(identifier, ns)))
                except ua.UaStatusCodeError as error:
                    print("Cannot inspect that node:", error)
            elif choice == "3":
                node = client.get_node(ua.NodeId("CNC_01.Production.Running", ns))
                await node.write_value(not await node.read_value())
                print("Running:", await node.read_value())
            elif choice == "4":
                result = await cnc.call_method(ua.NodeId("CNC_01.ResetPartCount", ns))
                print(result)
                print("PartCount:", await client.get_node(ua.NodeId("CNC_01.Production.PartCount", ns)).read_value())
            elif choice == "5":
                break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        print("Client stopped.")
    except (OSError, asyncio.TimeoutError) as error:
        print(f"Connection failed: {error}. Start cnc_server.py first.")
