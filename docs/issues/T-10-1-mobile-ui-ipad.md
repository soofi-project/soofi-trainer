# Task

- user story: [US-10](US-10-demo-preparation.md)

/label ~UserStory_US-10
/label ~Task
/label ~ToDo

# Description

**Mobile UI iPad — Vollbild-PWA für die Hannover Messe**

Landing page und Soofi UI sollen auf einem iPad als Vollbild-Webapp (Progressive Web App)
dargestellt werden — ohne Browserchrome, Adressleiste oder Tab-Leiste. Der Benutzer sieht
nur die Anwendung, kiosk-ähnlich.

## PWA-Konfiguration

### Web App Manifest

Beide Apps (Landing page und Soofi UI) benötigen ein `manifest.json`:

```json
{
  "name": "Soofi Trainer",
  "short_name": "Soofi",
  "display": "standalone",
  "orientation": "portrait",
  "start_url": "/",
  "background_color": "#0d1117",
  "theme_color": "#0d1117",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

In `index.html` einbinden:

```html
<link rel="manifest" href="/manifest.json">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Soofi Trainer">
<link rel="apple-touch-icon" href="/icons/icon-192.png">
```

**Hinweis für iOS/Safari:** `display: standalone` wird von Safari erst nach dem
„Zum Home-Bildschirm hinzufügen"-Dialog aktiviert. Das ist der erwartete Workflow
für die Demo-Vorbereitung.

### Responsive Layout

Das bestehende Soofi UI (`<soofi-chat>`) und die Landing page müssen auf iPad-Auflösungen
(1024×1366 im Hochformat, 1366×1024 im Querformat) korrekt dargestellt werden:

- Keine horizontalen Scrollbars
- Touch-freundliche Tap-Targets (min. 44×44 px)
- Viewport-Meta-Tag korrekt gesetzt: `width=device-width, initial-scale=1`
- Eingabefeld und Senden-Button auch mit Touch-Tastatur nutzbar

### Demo-Ablauf (iPad-Setup)

1. Safari öffnen → URL der Soofi-Instanz eingeben
2. „Teilen" → „Zum Home-Bildschirm" → App-Icon erscheint
3. App-Icon antippen → startet im Vollbildmodus ohne Browserchrome
4. Für die Demo: Guided Access (iOS-Kioskmodus) aktivieren, um versehentliches
   Verlassen der App zu verhindern

## HTTPS mit Caddy (Voraussetzung für Spracheingabe)

Safari auf iOS verweigert den Zugriff auf das Mikrofon (`getUserMedia`) auf unsicheren
Ursprüngen (HTTP). Für die Spracheingabe ist HTTPS zwingend erforderlich.

### Warum Caddy

Caddy wird als TLS-Reverse-Proxy vor Landing page und Soofi UI geschaltet. Es generiert
mit `tls internal` automatisch ein selbstsigniertes Zertifikat — kein externer CA-Dienst
oder manuelles Zertifikatsmanagement nötig.

### Setup (bereits in `compose/admin.yml` implementiert)

```
iPad
  ├─ https://<HOST>:<LANDING_PAGE_HTTPS_PORT>  →  Caddy  →  landingpage:80
  └─ https://<HOST>:<SOOFI_UI_HTTPS_PORT>      →  Caddy  →  soofi-ui:80
```

Caddyfile (`compose/admin/caddy/Caddyfile`):

```
{
    auto_https disable_redirects
}

{$LANDING_PAGE_HOSTNAME}:{$LANDING_PAGE_HTTPS_PORT:443} {
    tls internal
    reverse_proxy landingpage:80
}

{$LANDING_PAGE_HOSTNAME}:{$CADDY_HTTPS_PORT:3443} {
    tls internal
    reverse_proxy soofi-ui:80
}
```

Relevante `.env`-Variablen:

```
LANDING_PAGE_HOSTNAME=<IP oder Hostname des Demo-Rechners>
LANDING_PAGE_HTTPS_PORT=443
SOOFI_UI_HTTPS_PORT=3443
```

### Einmaliges Zertifikat-Trust auf dem iPad

Da `tls internal` ein selbstsigniertes Zertifikat erzeugt, muss es einmalig auf dem
iPad als vertrauenswürdig markiert werden:

1. Caddy CA-Zertifikat exportieren:
   ```bash
   docker cp soofi-caddy:/data/caddy/pki/authorities/local/root.crt ./caddy-root.crt
   ```
2. `caddy-root.crt` per AirDrop oder E-Mail auf das iPad übertragen
3. iPad: Einstellungen → Allgemein → VPN & Geräteverwaltung → Profil installieren
4. iPad: Einstellungen → Allgemein → Info → Zertifikatsvertrauenseinstellungen →
   Caddy Local Authority aktivieren
5. Safari öffnet die HTTPS-URL ohne Warnung; Mikrofon-Zugriff wird gewährt

## Betroffene Dienste

| Dienst | Änderungen |
|--------|-----------|
| `soofi-ui` | `manifest.json`, Apple-Meta-Tags, responsive CSS-Fixes |
| Landing page (admin compose) | `manifest.json`, Apple-Meta-Tags, responsive Layout |
| nginx (`nginx.conf`) | Statische Auslieferung von `manifest.json` und Icon-Assets |
| Caddy (`compose/admin.yml`) | Neuer Dienst: TLS-Terminierung für Landing page und Soofi UI |

## Acceptance Criteria

- [ ] Caddy-Dienst startet und ist über HTTPS erreichbar
- [ ] Selbstsigniertes Caddy-Zertifikat auf dem Demo-iPad installiert und als vertrauenswürdig markiert
- [ ] Safari gewährt Mikrofon-Zugriff auf der HTTPS-URL (kein `getUserMedia`-Fehler)
- [ ] Spracheingabe funktioniert End-to-End auf dem iPad
- [ ] `manifest.json` in Soofi UI eingebunden, App installierbar über Safari
- [ ] `manifest.json` in Landing page eingebunden, App installierbar über Safari
- [ ] Soofi UI läuft im Vollbildmodus auf iPad (kein Browserchrome nach Installation)
- [ ] Landing page läuft im Vollbildmodus auf iPad
- [ ] Keine Layout-Brüche auf iPad-Auflösungen (Portrait und Landscape)
- [ ] Touch-Eingabe funktioniert zuverlässig (Senden, Sprachtaste, Scrollen)
- [ ] App-Icons (192px, 512px) erstellt und eingebunden
- [ ] Guided Access (iOS Kioskmodus) getestet und dokumentiert

# Branches

- feature/T-10-1-mobile-ui-ipad
