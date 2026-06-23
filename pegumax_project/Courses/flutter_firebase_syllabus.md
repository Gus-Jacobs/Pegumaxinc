# Flutter & Firebase for Solo Founders

*A practical, ship-first course for indie builders. No dry CS theory—just the skills to get a secure, real-time app into users' hands.*

---

## Module 1: Project Scaffolding & The Founder's Mindset
**Set up a production-grade Flutter project structure that scales from MVP to launch without a rewrite.**

- Folder architecture by feature vs. by layer, and why solo founders should pick one early
- Flavors and environment configs for `dev`, `staging`, and `prod`
- Wiring Firebase into Flutter with FlutterFire CLI and per-environment options files

---

## Module 2: UI That Ships—Widgets & Responsive Layout
**Build clean, adaptive interfaces fast using composition patterns that keep your codebase maintainable solo.**

- Composition over inheritance: extracting reusable widgets without over-engineering
- Responsive layouts with `LayoutBuilder`, `MediaQuery`, and breakpoint helpers
- Theming, design tokens, and dark mode from a single source of truth

---

## Module 3: State Management Foundations with Riverpod
**Master a single, scalable state solution so your app's logic stays predictable as features pile up.**

- Providers, `Notifier`, and `AsyncNotifier`—choosing the right tool per use case
- Separating UI, business logic, and data layers with provider scoping
- Avoiding rebuild storms: `select`, `ref.watch` vs. `ref.read`, and lifecycle gotchas

---

## Module 4: Asynchronous Data & Reactive Streams
**Tame async code and real-time data so your UI reacts instantly to server and device changes.**

- `Future` vs. `Stream`: when to use each and how to expose them through providers
- `StreamProvider` and `AsyncValue` for loading, error, and data states without boilerplate
- Combining and transforming streams (`StreamController`, `map`, `where`, debouncing input)

---

## Module 5: Cloud Firestore—Real-Time Data Modeling
**Design Firestore schemas that stay cheap, fast, and queryable as your user base grows.**

- Collection vs. subcollection modeling and denormalization tradeoffs for read-heavy apps
- Real-time listeners with snapshot streams piped directly into Riverpod
- Pagination, compound queries, and indexing to keep read costs and latency low

---

## Module 6: Firebase Authentication End-to-End
**Implement secure, multi-provider sign-in flows that users trust and you can maintain alone.**

- Email/password, Google, and Apple Sign-In with proper account linking
- Auth state as a reactive stream driving app-wide navigation and gating
- Token refresh, session persistence, and handling re-authentication for sensitive actions

---

## Module 7: Local Security States & Sensitive Data
**Protect credentials and on-device data so a lost phone never becomes a breach.**

- Secure storage with `flutter_secure_storage` (Keychain/Keystore) vs. plaintext `SharedPreferences`
- Biometric and PIN gating with `local_auth` for app-lock and re-auth flows
- Managing "locked / unlocked / unauthenticated" as explicit security states in your provider tree

---

## Module 8: Routing, Navigation & Auth-Aware Flows
**Build a navigation system that reacts to auth and security state without spaghetti redirects.**

- Declarative routing with `go_router` and redirect logic tied to auth streams
- Guarding protected routes and deep links behind authentication and security gates
- Passing typed parameters and handling nested/tab navigation cleanly

---

## Module 9: Cloud Functions, Storage & Backend Glue
**Add server-side logic and file handling so your app does more than a client ever could.**

- Cloud Functions for privileged operations, triggers, and keeping secrets off the client
- Firebase Storage for image and file uploads with progress streams and security rules
- Firestore & Storage security rules as your real backend defense layer

---

## Module 10: Hardening, Release & Going Live Solo
**Polish, test, and ship to both stores while setting yourself up to monitor and iterate.**

- Error handling, Crashlytics, and analytics for a one-person ops team
- Build signing, store assets, and the iOS/Android submission checklist
- Post-launch: feature flags, Remote Config, and a lightweight update loop
