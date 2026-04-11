# Waarom de meeste BIM clash detection tools 80% van de problemen missen

*Pillar: Probleem | Door: CTO BIMoryn | Status: Draft voor review*

---

## De clash check vinkten we af. En toch ging het mis.

Het was een zorgvuldig gecoordineerd installatieproject. Clash detection: gedaan. Alle harde botsingen tussen buizen en balken opgelost. Het model leek groen.

Drie weken later, tijdens de eerste prefab-levering, bleek dat 14 kanaalstukken niet gemonteerd konden worden. Niet vanwege een clash — maar omdat de nomale maat nooit was ingevuld in het IFC-bestand. Downstream had de installateur aannames gemaakt. Die waren fout.

Clash detection had niets gevonden. Want clash detection zoekt naar geometrische botsingen. De echte fout zat in de data.

---

## Wat clash detection wel — en niet — doet

Vrijwel elke BIM workflow bevat een clash detection stap. Navisworks, Solibri, BIMcollab — ze zijn er allemaal op ingericht om te detecteren wanneer twee objecten fysiek overlappen.

Dat is waardevol. Maar het dekt hooguit 20% van de kwaliteitsproblemen die wij in de praktijk tegenkomen.

De overige 80% zijn data-integriteits problemen:

- **Ontbrekende parameters** — fire ratings niet ingevuld, slabs zonder dikte, elementen zonder storey-koppeling
- **Naamgevingsfouten** — duplicate markeringen op deuren, spaces zonder long name, generieke typenamen die tooling breken
- **MEP systeemfouten** — leidingen niet gekoppeld aan een systeem, onverbonden ports, kanalen zonder nominale afmeting
- **Structurele ontbrekingen** — kolommen niet gemarkeerd als draagconstructie, materialen niet ingevuld
- **Metadata gaps** — project zonder auteur/organisatie, elementen zonder classification reference, IFC2x3 schema waar IFC4 vereist is

Al deze problemen worden door clash detection niet opgepikt. Ze verschijnen pas downstream: bij calculatie, bij uitbesteding, bij as-built documentatie, bij BIM-verplichtingen richting opdrachtgever.

---

## Het echte probleem: validatie stopt bij geometrie

De reden dat tools als Navisworks zo dominant zijn, is historisch. BIM begon bij geometrie. De eerste business case was: "we vinden fouten eerder dan op de bouwplaats." Dat klopte, en het was genoeg.

Maar de BIM-scope is verbreed. We gebruiken modellen nu voor calculatie, onderhoudsplanning, facility management, NEN- en ILS-compliance. Voor elk van die use cases geldt: de data moet kloppen, niet alleen de geometrie.

De tools hebben die shift niet bijgehouden. Ze controleren nog steeds primair op botsingen.

---

## Wat validatie eigenlijk moet zijn

Goede BIM-validatie werkt als een linter voor code. Net zoals een Python-linter niet alleen syntaxfouten pikt maar ook logische inconsistenties, naamgevingsconventies en best practices — zo zou BIM-validatie het model moeten doordoorzoeken op alle lagen waarop het gebruikt wordt.

Concreet betekent dat: regels per discipline, per use case, per leverfase.

Bij BIMoryn hebben we dit opgebouwd als een rule-engine met 35 checks verdeeld over 5 categorieen:

| Categorie   | Aantal regels | Voorbeelden |
|-------------|--------------|-------------|
| Geometrie   | 7            | Duplicate GUIDs, zero-length walls, world-origin placements |
| MEP         | 6            | Unconnected ports, missing system assignments, duct sizing |
| Naamgeving  | 8            | Duplicate marks, space naming conventions, generic type names |
| Parameters  | 8            | Fire ratings, area quantities, storey assignments |
| Structuur   | 6            | Load-bearing flags, material assignments, PredefinedTypes |

Elke check geeft een severity (ERROR, WARNING, INFO), een element-referentie, en een actionable melding. Het resultaat is geen rood/groen vinkje — het is een gestructureerde lijst van wat er moet gebeuren voor handover.

---

## Het resultaat in de praktijk

Met deze aanpak zien we in typische projectmodellen:

- Gemiddeld 40-80 issues per model bij een eerste run
- Vaak 3-5 kritieke ERRORs die downstream workflows zouden hebben gebroken
- Meest voorkomende categorieën: ontbrekende parameters (PM) en MEP-systemen (ME)

Clash detection vindt geometrie. Validatie vindt de rest.

---

## Wat dit betekent voor jouw QA-workflow

Als je nu alleen clash detection doet voor handover, check je de verkeerde laag. Je geeft een model vrij dat geometrisch klopt maar datamatig gaten heeft.

De oplossing is geen extra tool bovenop je huidige stack. Het is een andere categorie check — geautomatiseerd, reproduceerbaar, integrable in je bestaande workflow.

Dat is precies wat we bouwen.

---

**Wil je zien hoeveel issues er in jouw huidige projectmodellen zitten?**
We runnen een gratis validatiescan voor pilotpartners — geen installatie vereist, binnen 24 uur resultaat.

[→ Meld je aan als pilotpartner](https://bimoryn.com/pilot)

---

*Tags: BIM validatie, clash detection, IFC kwaliteit, BIM QA, data-integriteit*
*Gerelateerd: BIM-15 (rule library), BIM-16 (performance benchmarks)*
