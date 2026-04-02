# User story

- tasks:
  - [T-10-1](T-10-1-mobile-ui-ipad.md)
  - [T-10-2](T-10-2-demo-use-cases.md)
  - [T-10-3](T-10-3-aas-submodels.md)
  - [T-10-4](T-10-4-caddy-letsencrypt-domain.md)

/label ~UserStory_US-10
/label ~UserStory

# Story

*"As a demo presenter at the Hannover Messe, I want a polished, self-contained demonstration
of Soofi Trainer, so that I can showcase AI-driven LLM specialization to an audience without
technical setup or friction."*

# Description

US-10 bundles all preparation tasks for the Hannover Messe demonstration. The goal is a
compelling, reliable demo that runs on consumer hardware (iPad) and covers realistic use cases
from the target domain.

## Tasks

### T-10-1 — Mobile UI iPad
Landing page and Soofi UI should run as a full-screen Progressive Web App (PWA) on an iPad.
No browser chrome, no address bar — pure kiosk-style presentation. Requires responsive layout
adjustments and PWA manifest configuration.

### T-10-2 — Demo Use Cases
Define and validate two or three concrete demo scenarios that walk through the full Soofi
pipeline (use-case analysis → method recommendation → training job). Scripts and sample data
must be prepared and tested end-to-end before the event.

### T-10-3 — AAS Submodels
Generate AI-Dataset submodels (Teilmodelle) conforming to the Asset Administration Shell
(AAS) standard. The training pipeline output should be exportable as AAS submodel descriptors
so that trained models and their datasets can be represented in an industry-standard digital
twin format.

### T-10-4 — HTTPS mit registrierter Domain & Let's Encrypt (Cloudflare)
Zweite Caddy-Variante für den Betrieb auf einem öffentlichen Server mit registrierter Domain.
Nutzt `ghcr.io/caddybuilds/caddy-cloudflare:v2.11.2` und Let's Encrypt per Cloudflare
DNS-Challenge. Beide Caddy-Dienste bleiben im Stack und werden per Docker Compose Profile
(`local` / `domain`) ausgewählt.

## Acceptance Criteria

- [ ] Soofi UI and landing page display correctly in full-screen PWA mode on iPad
- [ ] PWA manifest and service worker configured; app installable from Safari
- [ ] At least two demo use cases defined, scripted, and tested end-to-end
- [ ] Demo data (knowledge documents, sample datasets) prepared and loaded into the stack
- [ ] AAS submodel structure defined for AI-Dataset artifacts
- [ ] Training pipeline can export at least one AAS-compliant submodel descriptor
- [ ] Full demo runs without errors on the target hardware
