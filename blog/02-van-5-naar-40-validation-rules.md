# Van 5 naar 40 validation rules: hoe we de BIM Boost engine opschalen

*Pillar: Bouw | Door: CTO BIM Boost | Status: Draft voor review*

---

## Hoe bouw je een rule-engine die meegroeit met de praktijk?

De eerste versie van onze validatie-engine had 5 regels. Ze waren hard-coded, project-specifiek, en onmogelijk te hergebruiken.

Een handoverdocument met de verkeerde GUID-structuur hadden we gevonden — maar alleen in dat project, met die specifieke check. De volgende keer dat hetzelfde probleem opdook, hadden we die check niet meer.

Dat is het centrale probleem van BIM QA: kennis zit in de hoofden van mensen, niet in herhaalbare systemen. Elke coordinator die een patroon herkent, schrijft een ad-hoc check. Die check verdwijnt bij het volgende project.

Wij besloten dat anders te doen.

---

## De architectuur: regels als eerste-klas objecten

De kern van de BIM Boost engine is een `Rule`-basisklasse. Elke validatieregel erft daarvan en implementeert één methode: `check(model, config)`.

```python
class Rule:
    id: str          # bijv. "GE-001"
    name: str        # bijv. "Duplicate GlobalId (GUID)"
    category: RuleCategory
    severity: Severity

    def check(self, model: ifcopenshell.file, config: RuleConfig) -> Iterator[Issue]:
        raise NotImplementedError
```

Dit levert drie grote voordelen op:

1. **Ontkoppeling** — de engine weet niets van specifieke regels. Hij itereert over een registry, roept `check()` aan, verzamelt `Issue`-objecten.
2. **Testbaarheid** — elke regel heeft zijn eigen unittest. Je kunt een minimale IFC aanmaken, er een defect in zetten, en de regel isoleren testen.
3. **Uitbreidbaarheid** — nieuwe regel toevoegen betekent: één Python-bestand, register in de module `__init__`, klaar.

---

## Van 5 naar 35: hoe we het rule-backlog hebben opgebouwd

We zijn niet gaan zitten om een lijst te bedenken. We zijn begonnen met de fouten die we kenden uit projecten, en hebben die gestructureerd.

Dat leverde drie initiële categorieën op: geometrie, naamgeving, en parameters. Daarna kwamen MEP en structuur — disciplines met eigen conventies die BIM-coordinatoren structureel misten in handover-checks.

Onze huidige 35 regels zijn verdeeld over 5 categorieen:

**Geometrie (GE, 7 regels)**
De meest basale maar ook meest destructieve fouten. Een duplicate GUID (GE-001) brengt elk downstream systeem in de war — van cost management tot facility management. Een element op world-origin (0,0,0) geplaatst (GE-007) geeft geometry errors in rendering en export.

```python
# GE-001: Duplicate GlobalId detection
def check(self, model, config):
    seen = set()
    for product in model.by_type("IfcProduct"):
        gid = product.GlobalId
        if gid in seen:
            yield Issue(
                rule_id=self.id,
                severity=Severity.ERROR,
                element_id=product.id(),
                element_type=product.is_a(),
                message=f"Duplicate GlobalId: {gid}",
            )
        seen.add(gid)
```

**MEP (ME, 6 regels)**
MEP-modellen zijn notoir slecht gevuld. We detecteren ongekoppelde ports (ME-002), leidingen zonder nominale maat (ME-003/004), en flow terminals zonder richting (ME-005). In de praktijk zijn dit de issues die installateurs pas op de bouwplaats ontdekken.

**Naamgeving (NM, 8 regels)**
Duplicate marks op deuren (NM-004) zijn een ERROR — ze breken scheduler-exports. Generieke typenamen als "Revit Basic Wall" (NM-006) zijn een WARNING — ze signaleren dat het model nooit goed opgezet is.

**Parameters (PM, 8 regels)**
Fire ratings ontbreken bij wanden (PM-001), areas niet gevuld bij spaces (PM-002), elementen niet gekoppeld aan een verdieping (PM-005). Dit zijn de velden die contractueel verplicht zijn maar nooit geautomatiseerd gecheckt worden.

**Structuur (ST, 6 regels)**
Kolommen zonder `LoadBearing = True` (ST-001), structurele elementen zonder materiaal (ST-002), slabs met `PredefinedType = NOTDEFINED` (ST-003). Fouten die in structuurberekeningen nauwkeurig zijn maar in het BIM-model slordig worden bijgehouden.

---

## De output: gestructureerd, niet een lijst van meldingen

Elke run produceert een `ValidationResult` — een machine-leesbaar JSON-object met:

```json
{
  "run_id": "a3f9c2b1-...",
  "model_path": "kantoorgebouw_v3.ifc",
  "schema": "IFC4",
  "project_name": "Kantoorgebouw Breda",
  "summary": {
    "total_elements": 2847,
    "rules_run": 35,
    "total_issues": 63,
    "errors": 8,
    "warnings": 41,
    "infos": 14,
    "duration_ms": 4230
  },
  "issues": [
    {
      "rule_id": "GE-001",
      "severity": "ERROR",
      "element_id": 1204,
      "element_type": "IfcWall",
      "message": "Duplicate GlobalId: 3kUl9v...",
      "location": {"storey": "Begane Grond"}
    }
  ]
}
```

BCF-export is ook beschikbaar — voor directe integratie met Revit, BIMcollab, en Solibri.

---

## Wat er nog komt

35 regels is een solide basis. Maar we zien in pilotfeedback al waar gaten zitten:

- **ILS-specifieke checks** — per opdrachtgevertype (rijksoverheid, gemeenten, zorginstellingen) zijn er andere verplichte attributen. Die worden parameteriseerbaar.
- **Revit-native checks** — directe integratie via de Revit API voor checks pre-IFC-export, zodat fouten nog eerder worden opgepikt.
- **Custom rule packs** — pilotpartners kunnen hun eigen conventies als rules definieren, zonder onze codebase te forken.

De architectuur maakt dit mogelijk. Dat was de investering die we bewust vroeg hebben gedaan.

---

**Wil je de volledige rule-bibliotheek zien of je eigen conventie-checks toevoegen?**
We bespreken dit graag met de eerste pilotpartners.

[→ Plan een technisch gesprek](https://bimboost.io/pilot)

---

*Tags: BIM validatie engine, IFC rules, BIM automatisering, ifcopenshell, rule-based checking*
*Gerelateerd: [BIM-15](/BIM/issues/BIM-15) (rule library uitbreiding)*
