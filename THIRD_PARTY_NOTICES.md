# Third-party notices

The application source is MIT licensed. This does not relicense its dependencies.

| Component | License / upstream |
| --- | --- |
| PySide6 Essentials / Qt for Python | LGPLv3 / GPL / commercial alternatives, depending on the component and selected terms. [Qt for Python licenses](https://doc.qt.io/qtforpython-6/licenses.html), [Qt licensing](https://www.qt.io/licensing/open-source-lgpl-obligations). |
| Shiboken6 | LGPLv3 / GPL / commercial alternatives. Distributed by the Qt for Python project. |
| Python `hidapi` bindings | BSD / GPLv3 / original-license alternatives. [Upstream license files](https://github.com/trezor/cython-hidapi). |
| HIDAPI native library | BSD-style / GPLv3 / original HIDAPI alternatives. [Upstream licenses](https://github.com/libusb/hidapi). |

The source installation uses separately installed Python packages and their dynamically loaded libraries. This repository does not vendor their binaries or source. Their upstream distributions include their license notices. If you distribute a bundled executable, review the licenses of the exact libraries included and provide the notices, corresponding source access, and replacement/relinking mechanisms required by the applicable terms. The MIT license for this app does not remove those obligations.

The app's icons are drawn in code. No Apple artwork, SF fonts, FIFINE logos, USB capture-tool binaries, or code from the referenced AM8 project are shipped. Installed system fonts are used only when available, with a Windows font fallback.

Native Acrylic uses Win32 composition APIs. Microsoft documentation and the PyQt-Frameless-Window project's discussion of those APIs were consulted during development; that project is not a runtime dependency and its source is not included.
