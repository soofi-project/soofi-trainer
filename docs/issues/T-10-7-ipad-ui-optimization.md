# Task

- user story: [US-10](US-10-demo-preparation.md)

/label ~UserStory_US-10
/label ~Task
/label ~ToDo

# Description

**iPad UI Optimization — Touch-freundliche Oberfläche und integrierte Demo-Ansicht**

Landing page und Soofi UI sollen auf dem Demo-iPad optimal bedienbar sein: größere
Touch-Targets, responsives Layout, und optional eine engere Integration beider Oberflächen
über das reveal.js-Framework.

## Teilaufgaben

### 1. Touch-optimiertes Soofi UI

Größere Schaltflächen und Eingabeelemente in `soofi-ui/src/main.ts` für Touch-Bedienung:

- Mindestgröße aller interaktiven Elemente: 48×48 px (Apple HIG)
- Mikrofon- und Senden-Button deutlich größer (aktuell zu klein für Touch)
- Eingabefeld höher / leichter tappbar
- Keine versehentlichen Doppel-Taps (z. B. `touch-action: manipulation`)
- Schriftgrößen auf kleinen Displays lesbar (min. 16px, kein Zoom-Trigger)
- Side-Panel (Dokumente, Training) auf Hochformat-iPad sinnvoll nutzbar

### 2. Responsives Layout Landing page

Landing page (`compose/admin/landingpage/`) auf iPad-Auflösungen anpassen:

- Reveal.js-Folien auf 1024×1366 (Portrait) und 1366×1024 (Landscape) testen
- Schriftgrößen und Abstände für große Touch-Displays anpassen
- Navigation (Pfeile, Progress-Bar) touch-freundlich

### 3. Integration Soofi UI in Landing page (Evaluierung)

**Option A — iframe (aktuell):**  
Soofi UI läuft als `data-background-iframe` in einer reveal.js-Folie. Einfach,
aber iframe-Reload-Verhalten muss mit `data-preload` unterdrückt werden (bereits
umgesetzt in T-10-5).

**Option B — Soofi UI als reveal.js-Plugin / eigene Folie:**  
`<soofi-chat>` als Lit-Komponente direkt in `index.html` der Landing page einbetten,
als dedizierte Folie ohne iframe-Overhead. Erfordert:
- Soofi UI als npm-Paket oder per CDN einbindbar
- AG-UI/SSE-Endpunkt über nginx der Landing page erreichbar
- Kein doppeltes nginx-Routing nötig

**Option C — Getrennte Apps (Status quo beibehalten):**  
Landing page und Soofi UI bleiben separate Dienste, iPad-Nutzer wechseln per
Link/Swipe zwischen ihnen. Geringster Aufwand.

**Empfehlung:** Option A mit `data-preload` (bereits aktiv) für die kurzfristige Demo
evaluieren. Option B als mittelfristige Verbesserung umsetzen, wenn die Demo stabil läuft.

## Betroffene Dateien

| Datei | Änderungen |
|-------|-----------|
| `soofi-ui/src/main.ts` | Touch-Target-Größen, CSS-Anpassungen |
| `compose/admin/landingpage/content/slides/slides.md` | ggf. Soofi-Folie anpassen |
| `compose/admin/landingpage/index.html` | Optional: `<soofi-chat>` einbetten (Option B) |
| `soofi-ui/nginx.conf` | Optional: AG-UI-Proxy für Landing page (Option B) |

## Acceptance Criteria

- [ ] Alle Buttons und interaktiven Elemente im Soofi UI ≥ 48×48 px
- [ ] Kein ungewollter Zoom beim Antippen von Eingabefeldern (font-size ≥ 16px)
- [ ] Soofi UI auf iPad 10. Gen (1080×1488 logical px) ohne Layout-Brüche
- [ ] Landing page auf iPad Portrait und Landscape ohne Scrollbars / Overflow
- [ ] Soofi-Demo-Folie in Landing page: kein Reload beim Navigieren (data-preload aktiv)
- [ ] Entscheidung Option A/B/C dokumentiert und umgesetzt

# Branches

- feature/T-10-7-ipad-ui-optimization
