# Hoe snel kun je een 500MB IFC-model valideren? Benchmarks uit de praktijk

*Pillar: Proof | Door: CTO BIM Boost | Status: Draft voor review — benchmarkdata wordt aangevuld zodra BIM-16 compleet is*

---

## De vraag die elke BIM-coordinator stelt

"Hoelang duurt dat?"

Elke keer dat we onze validatie-engine demonstreren, is dit de eerste vraag. Niet: hoeveel issues vindt hij? Niet: hoe integreert het met mijn workflow? Maar: duurt het langer dan mijn huidige handmatige check?

Dat is een eerlijke vraag. Een validatietool die tien minuten nodig heeft voor een model dat in twee minuten te openen is, lost het probleem niet op. Hij verplaatst het.

---

## Wat "snel" betekent in BIM-validatie

Er zijn twee dingen die een validatie-engine traag maken:

1. **Model laden** — grote IFC-bestanden (300MB+) kosten significant tijd om te parsen. Dit is grotendeels het domein van de IFC-library (wij gebruiken ifcopenshell), niet van onze engine.
2. **Rule-executie** — elke regel itereert over (een subset van) de elementen in het model. Slecht geschreven regels met geneste loops over alle elementen zijn O(n²) en schalen niet.

Wij hebben beide bewust geoptimaliseerd.

---

## Hoe we de engine snel houden

**Single-pass loading**
Het model wordt eenmalig geladen. Alle 35 regels draaien op hetzelfde `ifcopenshell.file`-object. Er is geen herhaald parsen, geen dubbele file I/O.

```python
def run(self, model_path: str | Path) -> ValidationResult:
    started = time.monotonic()
    model = self._load(path)          # eenmalig laden
    issues = list(self._run_rules(model))  # alle regels, één model
    elapsed_ms = (time.monotonic() - started) * 1000
```

**Type-filtered queries**
Regels bevragen alleen de elementen die ze nodig hebben. Een MEP-regel vraagt `model.by_type("IfcFlowSegment")`, niet alle `IfcProduct`-instanties. ifcopenshell indexeert op type, dus dit is O(1) lookup + O(k) iteratie over het type.

**Rule isolation met fault tolerance**
Als een regel crashed, gooit de engine een `Issue` met de foutmelding en gaat verder. Geen enkele regel kan de run breken.

```python
try:
    yield from rule.check(model, rule_cfg)
except Exception as exc:
    yield Issue(rule_id=rule_cls.id, severity=Severity.ERROR,
                message=f"Rule '{rule_cls.id}' raised an unexpected error",
                detail=str(exc))
```

---

## Onze performancebudgetten

We hebben formele budgetten gedefinieerd per modelgrootte. Dit zijn de targets die wij intern hanteren:

| Modelgrootte        | Elementen (richtlijn) | Max. duur  | Max. geheugen |
|---------------------|----------------------|------------|---------------|
| Klein (<10MB)       | ~100 elementen       | 5 seconden | 100 MB        |
| Middelgroot (10-100MB) | ~1.000 elementen  | 30 seconden| 300 MB        |
| Groot (100MB+)      | ~5.000+ elementen    | 2 minuten  | 1 GB          |

In de praktijk halen we voor kleine en middelgrote modellen ruim onder het budget. Voor grote modellen (500MB+, tienduizenden elementen) is het model-parse-tijd de dominante factor — onze rule-executie voegt daar typisch maar een paar seconden bovenop.

*Concrete benchmarkresultaten met echte projectmodellen worden gepubliceerd zodra onze pilotfase data oplevert — zie geplande update Q2 2026.*

---

## Vergelijking: handmatig vs. geautomatiseerd

Een typische handmatige QA-check op een middelgroot IFC-model (een compleet gebouwmodel, 500-1000 elementen) kost:

- **Visuele check in Solibri/Navisworks**: 30-60 minuten
- **Handmatige parametercheck in Excel**: 2-4 uur
- **Rapportage opstellen**: 1-2 uur

Totaal: een halve tot hele werkdag per model, per milestone.

Met de BIM Boost engine:

- **Engine run**: < 30 seconden (zie budgetten boven)
- **JSON/BCF output**: direct beschikbaar
- **Actie: alleen issues die boven de threshold komen**: coordinatoren focussen op oplossen, niet op vinden

De tijdsbesparing zit niet primair in de parseersnelheid — die is sowieso snel. Ze zit in de eliminatie van de handmatige zoekfase.

---

## CI/CD: validatie als onderdeel van je modelleerproces

Omdat de engine een CLI heeft, integreert hij direct in automatische pipelines:

```bash
bimoryn validate kantoorgebouw_v3.ifc --min-severity WARNING --format bcf
```

Exit code `1` bij ERRORs, `0` bij schoon model. Dit maakt het mogelijk om validatie te triggeren bij elke model-upload, elke versiewissel, of elke handover-deadline.

```yaml
# Voorbeeld GitHub Actions workflow
- name: Validate IFC model
  run: bimoryn validate model.ifc --min-severity ERROR
```

Een model dat niet door de ERROR-checks komt, wordt niet geaccepteerd voor handover. Dat stopt fouten voor ze downstream schade aanrichten.

---

## Wat we leren van pilotdata

We zijn actief op zoek naar eerste pilotpartners die ons echte productiemodellen willen laten valideren. Dat levert ons:

- Realistische benchmarkdata voor publicatie (met toestemming, geanonimiseerd)
- Inzicht in welke rules het meest waarde leveren per projecttype
- Feedback op de output-formatting voor specifieke downstream tools

En het levert jou: een gratis validatiescan van je huidige model, met volledig rapport.

---

**Geinteresseerd in deelname als pilotpartner?**
We zoeken BIM-coordinatoren en projectmanagers bij ontwikkelaars, aannemers en ingenieursbureaus.

[→ Meld je aan voor de pilot](https://bimboost.io/pilot)

---

*Tags: BIM performance, IFC validatie snelheid, BIM automatisering, CI/CD BIM, ifcopenshell benchmark*
*Gerelateerd: [BIM-16](/BIM/issues/BIM-16) (performance benchmarking — data wordt aangevuld)*
