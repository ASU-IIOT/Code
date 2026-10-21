"""Local teaching server. Run: python cnc_server.py"""
import asyncio
from asyncua import Server, ua, uamethod

ENDPOINT = "opc.tcp://127.0.0.1:4840/cnc/"
NAMESPACE = "urn:iiot-course:cnc"

async def main():
    server = Server()
    await server.init()
    server.set_endpoint(ENDPOINT)
    server.set_server_name("CNC Information Model Lab")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
    ns = await server.register_namespace(NAMESPACE)

    def nid(name):
        return ua.NodeId(name, ns)

    cnc = await server.nodes.objects.add_object(nid("CNC_01"), ua.QualifiedName("CNC_01", ns))
    spindle = await cnc.add_object(nid("CNC_01.Spindle"), ua.QualifiedName("Spindle", ns))
    production = await cnc.add_object(nid("CNC_01.Production"), ua.QualifiedName("Production", ns))
    speed = await spindle.add_variable(nid("CNC_01.Spindle.Speed"), ua.QualifiedName("Speed", ns), 1750.0)
    await spindle.add_variable(nid("CNC_01.Spindle.Temperature"), ua.QualifiedName("Temperature", ns), 42.0)
    count = await production.add_variable(nid("CNC_01.Production.PartCount"), ua.QualifiedName("PartCount", ns), 1250, ua.VariantType.Int32)
    running = await production.add_variable(nid("CNC_01.Production.Running"), ua.QualifiedName("Running", ns), True)
    await running.set_writable()

    # Standard EUInformation structure; UN/CEFACT RPM unit code is RPM.
    units = ua.EUInformation()
    units.NamespaceUri = "http://www.opcfoundation.org/UA/units/un/cefact"
    units.UnitId = int.from_bytes(b"RPM", "big")
    units.DisplayName = ua.LocalizedText("rpm")
    units.Description = ua.LocalizedText("revolutions per minute")
    await speed.add_property(nid("CNC_01.Spindle.Speed.EngineeringUnits"), ua.QualifiedName("EngineeringUnits", 0), units)

    @uamethod
    async def reset_count(parent):
        await count.write_value(0, ua.VariantType.Int32)
        return "Part count reset to zero"

    await cnc.add_method(nid("CNC_01.ResetPartCount"), ua.QualifiedName("ResetPartCount", ns), reset_count, [], [ua.VariantType.String])
    async with server:
        print(f"Server ready: {ENDPOINT}", flush=True)
        print(f"Namespace {ns}: {NAMESPACE}", flush=True)
        print("Values stay fixed for inspection. Running is writable. Ctrl+C stops the server.", flush=True)
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped.")
