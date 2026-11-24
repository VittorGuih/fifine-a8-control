# Observed A8 USB behavior

These observations come from one FIFINE AmpliGame A8, VID `3142`, PID `00a8`, on Windows 11. They are not a vendor specification or a compatibility guarantee for other firmware.

## Incoming physical-button notification

- Interface 3, HID consumer collection, usage page `0x000c`, usage `0x0001`.
- Interrupt IN endpoint `0x87`, report ID `1`.
- Observed report (16 bytes):

```text
01 80 00 00 00 ff 00 ff 42 31 a8 00 40 00 20 21
```

The input descriptor assigns the high bit of byte 1 to a relative vendor usage on page `0xff01`. The ordinary Consumer Mute bit (`0x40`) was not set in this report.

Manual button presses produced separate reports with **identical contents**. Comparing only changes in the byte payload misses these events. The first USB capture contained two matching reports during a manual mute/unmute sequence. A subsequent direct HID test received eight reports; the tester confirmed making additional manual presses during that sequence.

This maps an action notification, not absolute LED state. The same report must not be interpreted as “red” or “green”, and it does not identify what caused an unsolicited activation.

## Outgoing mute control

The capture descriptors expose a microphone Feature Unit (unit 10) with a master-channel mute control. During a controlled Windows mute/unmute test, traces showed:

| Field | Value |
| --- | --- |
| `bmRequestType` | `0x21` — host to device, class, interface |
| `bRequest` | `0x01` — `SET_CUR` |
| `wValue` | `0x0100` — master-channel `MUTE_CONTROL` |
| `wIndex` | `0x0a00` — Feature Unit 10, Audio Control interface 0 |
| Data | `01` to mute; `00` to unmute |

The tester visually confirmed that the LED became red and then green. No AM8 ACP, firmware-update, or vendor HID output commands were needed.

The application sends these requests through the existing Windows audio driver via Core Audio; it does not claim the USB interface with libusb or require a replacement driver.

## Reapplying the same state

The physical button can leave the Windows cached mute unchanged. Repeating `SetMute` with the cached value may not send another hardware request. The bridge therefore saves the input level, temporarily sets it to zero, applies the opposite and then desired mute value, and restores the input level in a `finally` block. On failure it attempts to restore the original mute as well.

This is a recovery mechanism, not a device-state query or a hard realtime/privacy guarantee. Other applications can still alter audio settings, and repeated hardware actions can briefly interrupt the signal.

## Discovery and isolation

The bridge enumerates active capture endpoints and follows `IDeviceTopology.GetConnector(0)` / `IConnector.GetDeviceIdConnectedTo()` to the connected adapter. The hardware identifier must contain `vid_3142&pid_00a8`. Missing or multiple matches are errors, never reasons to select the system default input.

The HID listener separately requires exactly one matching A8 consumer collection. Its matcher is intentionally strict about the observed report. Unknown reports are ignored rather than interpreted as a mute action.

## References

- [Microsoft: IConnector.GetDeviceIdConnectedTo](https://learn.microsoft.com/en-us/windows/win32/api/devicetopology/nf-devicetopology-iconnector-getdeviceidconnectedto)
- [Microsoft: IAudioEndpointVolume.SetMute](https://learn.microsoft.com/en-us/windows/win32/api/endpointvolume/nf-endpointvolume-iaudioendpointvolume-setmute)
- [USB Audio Device Class 1.0 specification](https://www.usb.org/sites/default/files/audio10.pdf)
- [USBPcap capture documentation](https://desowin.org/usbpcap/tour.html)
- [AM8 protocol research](https://github.com/Austrum-lab/fifine-am8): useful research context, but a different device and protocol. That implementation is not included or executed here.

The public repository includes the protocol description, not the original diagnostic logs or packet captures.
