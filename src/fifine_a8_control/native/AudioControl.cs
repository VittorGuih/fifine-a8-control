using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace FifineA8Control
{
    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
    internal class DeviceEnumerator { }

    [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IMMDeviceEnumerator
    {
        [PreserveSig] int EnumAudioEndpoints(int flow, int states, out IMMDeviceCollection devices);
        [PreserveSig] int GetDefaultAudioEndpoint(int flow, int role, out IMMDevice device);
        [PreserveSig] int GetDevice([MarshalAs(UnmanagedType.LPWStr)] string id, out IMMDevice device);
    }

    [ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IMMDeviceCollection
    {
        [PreserveSig] int GetCount(out uint count);
        [PreserveSig] int Item(uint index, out IMMDevice device);
    }

    [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IMMDevice
    {
        [PreserveSig] int Activate(ref Guid iid, int context, IntPtr parameters, [MarshalAs(UnmanagedType.IUnknown)] out object instance);
        [PreserveSig] int OpenPropertyStore(int access, out IntPtr store);
        [PreserveSig] int GetId([MarshalAs(UnmanagedType.LPWStr)] out string id);
        [PreserveSig] int GetState(out int state);
    }

    [ComImport, Guid("2A07407E-6497-4A18-9787-32F79BD0D98F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IDeviceTopology
    {
        [PreserveSig] int GetConnectorCount(out uint count);
        [PreserveSig] int GetConnector(uint index, out IConnector connector);
    }

    [ComImport, Guid("9C2C4058-23F5-41DE-877A-DF3AF236A09E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IConnector
    {
        [PreserveSig] int GetType(out int type);
        [PreserveSig] int GetDataFlow(out int flow);
        [PreserveSig] int ConnectTo(IConnector other);
        [PreserveSig] int Disconnect();
        [PreserveSig] int IsConnected([MarshalAs(UnmanagedType.Bool)] out bool connected);
        [PreserveSig] int GetConnectedTo(out IConnector other);
        [PreserveSig] int GetConnectorIdConnectedTo([MarshalAs(UnmanagedType.LPWStr)] out string id);
        [PreserveSig] int GetDeviceIdConnectedTo([MarshalAs(UnmanagedType.LPWStr)] out string id);
    }

    [ComImport, Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IAudioEndpointVolume
    {
        [PreserveSig] int RegisterControlChangeNotify(IntPtr callback);
        [PreserveSig] int UnregisterControlChangeNotify(IntPtr callback);
        [PreserveSig] int GetChannelCount(out uint count);
        [PreserveSig] int SetMasterVolumeLevel(float value, IntPtr context);
        [PreserveSig] int SetMasterVolumeLevelScalar(float value, IntPtr context);
        [PreserveSig] int GetMasterVolumeLevel(out float value);
        [PreserveSig] int GetMasterVolumeLevelScalar(out float value);
        [PreserveSig] int SetChannelVolumeLevel(uint channel, float value, IntPtr context);
        [PreserveSig] int SetChannelVolumeLevelScalar(uint channel, float value, IntPtr context);
        [PreserveSig] int GetChannelVolumeLevel(uint channel, out float value);
        [PreserveSig] int GetChannelVolumeLevelScalar(uint channel, out float value);
        [PreserveSig] int SetMute([MarshalAs(UnmanagedType.Bool)] bool value, IntPtr context);
        [PreserveSig] int GetMute([MarshalAs(UnmanagedType.Bool)] out bool value);
    }

    public sealed class CaptureDevice
    {
        public string EndpointId { get; set; }
        public string HardwareId { get; set; }
    }

    public sealed class AudioStatus
    {
        public bool Muted { get; set; }
        public float Level { get; set; }
    }

    public static class AudioControl
    {
        private const string HardwareMarker = "vid_3142&pid_00a8";
        private static readonly Guid TopologyId = new Guid("2A07407E-6497-4A18-9787-32F79BD0D98F");
        private static readonly Guid VolumeId = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");

        private static void Release(object value)
        {
            if (value != null && Marshal.IsComObject(value)) Marshal.ReleaseComObject(value);
        }

        // Match the capture endpoint to its physical adapter, never by its display name
        // and never by the current default input. Only active A8 endpoints are returned.
        public static CaptureDevice[] Discover()
        {
            IMMDeviceEnumerator enumerator = (IMMDeviceEnumerator)new DeviceEnumerator();
            IMMDeviceCollection devices = null;
            List<CaptureDevice> result = new List<CaptureDevice>();
            try
            {
                Marshal.ThrowExceptionForHR(enumerator.EnumAudioEndpoints(1, 1, out devices));
                uint count;
                Marshal.ThrowExceptionForHR(devices.GetCount(out count));
                for (uint index = 0; index < count; index++)
                {
                    IMMDevice device = null;
                    object topologyObject = null;
                    IConnector connector = null;
                    try
                    {
                        Marshal.ThrowExceptionForHR(devices.Item(index, out device));
                        Guid iid = TopologyId;
                        Marshal.ThrowExceptionForHR(device.Activate(ref iid, 23, IntPtr.Zero, out topologyObject));
                        IDeviceTopology topology = (IDeviceTopology)topologyObject;
                        Marshal.ThrowExceptionForHR(topology.GetConnector(0, out connector));
                        string hardwareId;
                        Marshal.ThrowExceptionForHR(connector.GetDeviceIdConnectedTo(out hardwareId));
                        if (hardwareId.IndexOf(HardwareMarker, StringComparison.OrdinalIgnoreCase) < 0) continue;
                        string endpointId;
                        Marshal.ThrowExceptionForHR(device.GetId(out endpointId));
                        result.Add(new CaptureDevice { EndpointId = endpointId, HardwareId = hardwareId });
                    }
                    catch (COMException) { /* Unrelated virtual/disconnected topology. */ }
                    finally { Release(connector); Release(topologyObject); Release(device); }
                }
                return result.ToArray();
            }
            finally { Release(devices); Release(enumerator); }
        }

        private sealed class Handle : IDisposable
        {
            private IMMDeviceEnumerator enumerator;
            private IMMDevice device;
            public IAudioEndpointVolume Volume;
            public Handle()
            {
                CaptureDevice[] matches = Discover();
                if (matches.Length == 0) throw new InvalidOperationException("No active FIFINE A8 (3142:00a8) capture endpoint was found.");
                if (matches.Length != 1) throw new InvalidOperationException("Multiple FIFINE A8 microphones found. Connect only one A8 to use this version.");
                try
                {
                    enumerator = (IMMDeviceEnumerator)new DeviceEnumerator();
                    Marshal.ThrowExceptionForHR(enumerator.GetDevice(matches[0].EndpointId, out device));
                    Guid iid = VolumeId;
                    object instance;
                    Marshal.ThrowExceptionForHR(device.Activate(ref iid, 23, IntPtr.Zero, out instance));
                    Volume = (IAudioEndpointVolume)instance;
                }
                catch { Dispose(); throw; }
            }
            public void Dispose() { Release(Volume); Release(device); Release(enumerator); Volume = null; device = null; enumerator = null; }
        }

        public static AudioStatus Status()
        {
            using (Handle handle = new Handle())
            {
                bool muted; float level;
                Marshal.ThrowExceptionForHR(handle.Volume.GetMute(out muted));
                Marshal.ThrowExceptionForHR(handle.Volume.GetMasterVolumeLevelScalar(out level));
                return new AudioStatus { Muted = muted, Level = level };
            }
        }

        // A physical press can leave Windows' cached mute unchanged. Reapply both
        // values so the desired command reaches the hardware. Temporarily zero
        // the input level while crossing the opposite state, then restore it.
        public static AudioStatus Apply(bool target)
        {
            using (Handle handle = new Handle())
            {
                IAudioEndpointVolume volume = handle.Volume;
                bool initial; float level;
                Marshal.ThrowExceptionForHR(volume.GetMute(out initial));
                Marshal.ThrowExceptionForHR(volume.GetMasterVolumeLevelScalar(out level));
                bool completed = false;
                try
                {
                    Marshal.ThrowExceptionForHR(volume.SetMasterVolumeLevelScalar(0, IntPtr.Zero));
                    Marshal.ThrowExceptionForHR(volume.SetMute(!target, IntPtr.Zero));
                    Marshal.ThrowExceptionForHR(volume.SetMute(target, IntPtr.Zero));
                    completed = true;
                }
                finally
                {
                    try
                    {
                        if (!completed) Marshal.ThrowExceptionForHR(volume.SetMute(initial, IntPtr.Zero));
                    }
                    finally { Marshal.ThrowExceptionForHR(volume.SetMasterVolumeLevelScalar(level, IntPtr.Zero)); }
                }
                bool muted; float readback;
                Marshal.ThrowExceptionForHR(volume.GetMute(out muted));
                Marshal.ThrowExceptionForHR(volume.GetMasterVolumeLevelScalar(out readback));
                return new AudioStatus { Muted = muted, Level = readback };
            }
        }
    }
}
