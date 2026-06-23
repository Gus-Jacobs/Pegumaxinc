# Desktop Apps with Electron & Modern UI

*A principal developer's course on turning web skills into real, installable desktop software. Build cross-platform apps once with HTML, CSS, and JavaScript—then ship native executables for Windows and Mac.*

---

## Module 1: Electron Fundamentals & First App
**Understand what Electron is and get a working desktop window on screen so the rest of the course has a foundation.**

- How Electron bundles Chromium and Node.js into a single cross-platform runtime
- Project setup: `package.json`, the entry point, and launching your first window
- When Electron is the right tool—and its tradeoffs in size and memory

---

## Module 2: Main vs. Renderer Process Architecture
**Master Electron's two-process model so you structure every app correctly and securely from the start.**

- The Main process: app lifecycle, native APIs, and managing windows
- Renderer processes: the web page UI and its sandboxed browser context
- Why the separation exists and which responsibilities belong in each process

---

## Module 3: Window & Application Lifecycle Management
**Control how your app opens, behaves, and closes so it feels like polished native software.**

- Creating and configuring `BrowserWindow` instances and their options
- Lifecycle events: ready, activate, window-all-closed, and platform differences
- Multiple windows, modals, and managing window state across a session

---

## Module 4: Building the UI with HTML, CSS & JavaScript
**Apply web design skills to craft the interface so your existing front-end knowledge transfers directly.**

- Structuring the renderer UI with semantic HTML and modern CSS layout
- Styling for desktop: responsive panels, theming, and native-feeling design
- Adding interactivity with JavaScript and optionally a framework (React/Vue)

---

## Module 5: Secure Inter-Process Communication (IPC)
**Connect the UI and backend safely so your app gains native power without opening security holes.**

- IPC fundamentals: `ipcMain`, `ipcRenderer`, and request/response messaging
- Context isolation and `contextBridge` to expose only safe, explicit APIs
- Disabling Node integration in the renderer and validating all IPC inputs

---

## Module 6: Native OS Integration
**Tap into operating-system features so your app does what a browser tab never could.**

- Native menus, system tray icons, and global keyboard shortcuts
- Desktop notifications, dialogs, and clipboard access
- File system access and respecting per-platform conventions

---

## Module 7: Data Persistence & Local Storage
**Store user data reliably so your app remembers state between sessions.**

- Choosing storage: config files, local databases, and user data directories
- Reading and writing app data safely from the Main process
- Managing settings, preferences, and migrating stored data across versions

---

## Module 8: Security Hardening & Best Practices
**Lock down your app so a web-based UI doesn't become a desktop attack surface.**

- The Electron security checklist: context isolation, sandboxing, and CSP
- Safely handling remote content, external links, and untrusted input
- Keeping Electron and dependencies patched against known vulnerabilities

---

## Module 9: Packaging Executables for Windows & Mac
**Bundle your app into native installers so users can download and run it like any other program.**

- Packaging with Electron Builder: targets, icons, and app metadata
- Producing Windows installers (`.exe`/NSIS) and macOS bundles (`.dmg`)
- Code signing and notarization so installs aren't blocked by the OS

---

## Module 10: Auto-Updates, Distribution & Release
**Get your app to users and keep it current so shipping isn't a one-time event.**

- Implementing auto-updates with an update server or release host
- Versioning, release channels, and distributing builds to users
- Crash reporting, basic analytics, and a sustainable release workflow

---
