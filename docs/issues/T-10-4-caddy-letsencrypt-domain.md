# Task

- user story: [US-10](US-10-demo-preparation.md)

/label ~UserStory_US-10
/label ~Task
/label ~ToDo

# Description

**HTTPS mit registrierter Domain & Let's Encrypt (Cloudflare DNS-Challenge)**

Für den Betrieb auf einem öffentlich erreichbaren Server mit registrierter Domain soll eine
zweite Caddy-Variante bereitgestellt werden, die ein gültiges Let's Encrypt-Zertifikat per
Cloudflare DNS-Challenge ausstellt. Damit entfällt das manuelle Zertifikat-Trust auf dem
iPad — Safari akzeptiert das Zertifikat ohne Warnung.

## Motivation

| Aspekt | `tls internal` (T-10-1) | Let's Encrypt + Cloudflare (T-10-4) |
|--------|-------------------------|--------------------------------------|
| Zertifikat | Selbstsigniert (Caddy CA) | Öffentlich vertrauenswürdig |
| iPad-Setup | Manuelles Trust-Profil nötig | Kein Setup am iPad nötig |
| Voraussetzung | Nur lokales Netz | Registrierte Domain + Cloudflare |
| Portfreigabe | Beliebige Ports | Port 443 (HTTPS) |

## Technischer Ansatz

### Caddy-Image mit Cloudflare-Plugin

Das offizielle `caddy:2-alpine`-Image enthält keinen DNS-Provider. Stattdessen wird ein
Community-Build mit integriertem Cloudflare-Modul verwendet:

```
image: ghcr.io/caddybuilds/caddy-cloudflare:v2.11.2
```

### DNS-Challenge-Ablauf

1. Caddy stellt bei Let's Encrypt eine Zertifikatsanfrage
2. Let's Encrypt fordert einen DNS-TXT-Record als Challenge
3. Caddy legt den Record automatisch über die Cloudflare API an
4. Let's Encrypt verifiziert den Record und stellt das Zertifikat aus
5. Caddy entfernt den Challenge-Record wieder

Vorteil gegenüber HTTP-Challenge: Port 80 muss **nicht** öffentlich erreichbar sein.

### Caddyfile

Neues `Caddyfile.cloudflare` (`compose/admin/caddy/Caddyfile.cloudflare`):

```
{
    auto_https off
}

{$SOOFI_DOMAIN} {
    tls {
        dns cloudflare {$CLOUDFLARE_API_TOKEN}
    }
    reverse_proxy landingpage:80
}

{$SOOFI_DOMAIN}:3443 {
    tls {
        dns cloudflare {$CLOUDFLARE_API_TOKEN}
    }
    reverse_proxy soofi-ui:80
}
```

### Docker Compose Profiles

Beide Caddy-Varianten bleiben im Stack. Per `--profile` wird eine davon aktiviert:

| Profile | Dienst | Zweck |
|---------|--------|-------|
| `local` | `caddy` | Selbstsigniertes Zertifikat (Standardfall, iPad-Demo im LAN) |
| `domain` | `caddy-cloudflare` | Let's Encrypt via Cloudflare (öffentlicher Server mit Domain) |

Starten mit:

```bash
./up.sh --profile local    # oder kein --profile → default
./up.sh --profile domain   # Let's Encrypt-Variante
```

### Neue `.env`-Variablen

```
# Für Let's Encrypt / Cloudflare (nur bei profile=domain nötig)
SOOFI_DOMAIN=soofi.example.com
```

Secrets (in `~/.env.secrets`):

```
CLOUDFLARE_API_TOKEN=<token mit Zone:DNS:Edit-Berechtigung>
```

## Betroffene Dateien

| Datei | Änderung |
|-------|---------|
| `compose/admin/caddy/Caddyfile.cloudflare` | Neu — Caddy-Konfig für Domain + Let's Encrypt |
| `compose/admin.yml` | Profile für `caddy` (local) und `caddy-cloudflare` (domain) |
| `.env` | Neue Variable `SOOFI_DOMAIN` |
| `~/.env.secrets` | Neue Variable `CLOUDFLARE_API_TOKEN` |

## Acceptance Criteria

- [ ] `Caddyfile.cloudflare` erstellt und korrekt konfiguriert (DNS-Challenge via Cloudflare)
- [ ] `caddy-cloudflare`-Dienst in `compose/admin.yml` mit Profile `domain` eingetragen
- [ ] Bestehender `caddy`-Dienst mit Profile `local` versehen — kein Einfluss auf bisheriges Verhalten
- [ ] `SOOFI_DOMAIN` in `.env` dokumentiert (als leerer Platzhalter)
- [ ] `CLOUDFLARE_API_TOKEN` in `~/.env.secrets`-Vorlage dokumentiert
- [ ] Let's Encrypt-Zertifikat wird automatisch ausgestellt (kein manuelles Trust auf dem iPad)
- [ ] Safari auf iPad akzeptiert das Zertifikat ohne Warnung
- [ ] Mikrofon-Zugriff (`getUserMedia`) funktioniert auf der Domain

# Branches

- feature/T-10-4-caddy-letsencrypt-domain
