# BIM basis ILS compliance automatiseren: zo werkt het onder de motorkap

*Pillar: Standaarden | Door: CTO BIMoryn | Status: Draft voor review*

---

## Het ILS-probleem dat niemand graag benoemt

Elke opdrachtgever met een BIM-verplichting heeft een ILS. Een Informatie Leverings Specificatie — het document dat beschrijft welke informatie in het model moet zitten, in welk formaat, op welk moment.

In de meeste projecten wordt het ILS-document gereviewed bij de start. Dan verdwijnt het in een map op de projectschijf. Bij handover haalt iemand het terug tevoorschijn en begint handmatig te checken of het model compliant is.

Dat is geen kwaliteitsproces. Dat is hopen dat niemand iets vergeten is.

---

## Wat ILS-compliance eigenlijk vraagt

Een ILS beschrijft in essentie drie dingen:

1. **Welke elementen** moeten in het model zitten (objecttypen, detailniveaus per LOD)
2. **Welke attributen** die elementen moeten hebben (property sets, classificaties, quantities)
3. **Hoe die attributen ingevuld** moeten zijn (conventies, eenheden, toegestane waarden)

Voor punt 2 en 3 — de attributen — is geautomatiseerde validatie goed te doen. Je weet precies welk veld je zoekt, je kunt controleren of het gevuld is, en je kunt conventies checken.

Dat is precies waar onze parameter-categorie (PM) op focust.

---

## De technische aanpak: property set validatie op IFC-niveau

IFC slaat attributen op in `IfcPropertySet`-instanties, gekoppeld aan elementen via `IfcRelDefinesByProperties`. Een typische compliance-check werkt zo:

```python
def _get_pset_value(self, element, pset_name: str, prop_name: str):
    """Haal een property op uit een named property set."""
    for rel in getattr(element, "IsDefinedBy", []):
        if rel.is_a("IfcRelDefinesByProperties"):
            pset = rel.RelatingPropertyDefinition
            if pset.is_a("IfcPropertySet") and pset.Name == pset_name:
                for prop in pset.HasProperties:
                    if prop.Name == prop_name:
                        return getattr(prop, "NominalValue", None)
    return None
```

Met deze helper kun je elke ILS-eis vertalen naar een concrete check. Neem PM-001 (wall fire rating):

```python
# PM-001: Wall missing fire rating
class WallFireRatingRule(Rule):
    id = "PM-001"
    name = "Wall has no fire rating"
    severity = Severity.WARNING

    def check(self, model, config):
        for wall in model.by_type("IfcWall"):
            rating = self._get_pset_value(wall, "Pset_WallCommon", "FireRating")
            if not rating or not str(rating).strip():
                yield Issue(
                    rule_id=self.id,
                    element_id=wall.id(),
                    element_type="IfcWall",
                    message="Wall missing fire rating in Pset_WallCommon",
                )
```

Eenvoudig, traceerbaar, en testbaar met een minimale IFC-fixture.

---

## Onze huidige PM-checks als ILS-basis

Onze 8 parameter-regels dekken de meest voorkomende ILS-vereisten:

| Rule   | Check                              | ILS-relevantie |
|--------|------------------------------------|----------------|
| PM-001 | Wand mist brandweerstand           | Brandveiligheid, EPB |
| PM-002 | Ruimte mist oppervlak              | NEN2580, programma van eisen |
| PM-003 | Constructief element mist LoadBearing | Structuurberekening |
| PM-004 | Deur mist hardwareset referentie   | Bestek-koppeling |
| PM-005 | Element niet gekoppeld aan verdieping | Storey-structuur, kostencalculatie |
| PM-006 | Element mist classificatiereferentie | NL-SfB, Stabu, ETIM |
| PM-007 | Plaat mist dikte                   | Constructie, thermische berekening |
| PM-008 | IfcProject mist auteur/organisatie | Documentbeheer, audit trail |

Elke check geeft een element-specifieke foutmelding met de exacte property set en property naam — zodat de BIM-modelleur weet waar in Revit of ArchiCAD hij moet kijken.

---

## Drempels en severities als ILS-vertaling

Niet elke ILS-eis heeft dezelfde urgentie. Wij vertalen dit naar severity-niveaus:

- **ERROR** — het model is niet bruikbaar zonder dit attribuut (bijv. ruimte zonder oppervlak: PvE-compliance is onmogelijk)
- **WARNING** — data ontbreekt die downstream workflows raakt (bijv. wand zonder brandweerstand: EPB-berekening mist input)
- **INFO** — best practice die in de ILS aanbevolen wordt maar niet verplicht is (bijv. deur zonder hardwareset: niet blokkend voor handover)

Deze mapping is configureerbaar per opdrachtgever. Een rijksgebouwendienst-project heeft andere verplichte velden dan een commercial developer.

---

## Wat automatisering niet kan (en wat dat betekent)

Eerlijk zijn over de grenzen is belangrijk.

Automatiseerde ILS-compliance kan checken of velden gevuld zijn, of conventies kloppen, of required property sets aanwezig zijn. Dat dekt de meeste kwantitatieve ILS-eisen.

Wat het niet kan: oordelen over inhoudelijke correctheid. Als de brandwerendheid "REI 60" is maar de werkelijke constructie dat niet haalt — dat valt buiten de scope van data-validatie. Dat is een engineeringsoordeel.

Maar in de praktijk zijn de meeste ILS-fouten niet inhoudelijk fout. Ze zijn simpelweg niet ingevuld. Dat is het probleem dat we oplossen.

---

## Integratie in de handoverworkflow

De typische workflow met BIMoryn voor ILS-compliance:

1. **Upload model** (IFC4 of IFC2x3) via CLI of API
2. **Run engine** met de relevante ruleset (of alle 35 checks)
3. **Review JSON of BCF** — ERRORs blokkeren handover, WARNINGs gaan naar een actielijst
4. **Modelleur lost op** in Revit/ArchiCAD/Archicad
5. **Re-run** voor sign-off

Dit kan dagelijks draaien tijdens de modelleerperiode — niet alleen bij milestone. Zo worden fouten gerepareerd terwijl ze nog goedkoop zijn.

---

## Richting projectspecifieke rule packs

De volgende stap voor ILS-compliance is projectspecifieke configuratie: een opdrachtgever uploadt zijn ILS-template, wij genereren de bijbehorende rules als een rule pack. De engine draait dan tegen de specifieke eisen van dat project.

Dit is waar we naartoe bouwen. De architectuur ondersteunt het al — elke rule accepteert een `RuleConfig` met parameters, zodat drempelwaarden, property set-namen, en vereiste waarden per project te configureren zijn.

---

**Wil je een ILS-compliance check op je eigen model?**
We bouwen pilotpartner-specifieke rulesets voor de eerste deelnemers.

[→ Meld je aan als pilotpartner](https://bimoryn.com/pilot)

---

*Tags: ILS compliance, BIM standaarden, IFC property sets, NEN-normen, BIM automatisering*
*Gerelateerd: [BIM-15](/BIM/issues/BIM-15) (rule library), [BIM-11](/BIM/issues/BIM-11) (pilot funnel)*
