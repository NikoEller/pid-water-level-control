# Theorie

## Tankmodell

Der Wasserstand `h(t)` wird als ein Zustandsmodell erster Ordnung beschrieben.
Die effektive Beckenflaeche `A` verbindet Volumenstrom und Aenderung des
Wasserstands:

```math
\frac{dh}{dt} =
\frac{q_{\mathrm{in}}(t) + q_{\mathrm{rain}}(t)
      - q_{\mathrm{out}}(h) - q_{\mathrm{pump}}(u)}{A}
```

Der freie Ablauf wird als einfache Wurzelkennlinie modelliert:

```math
q_{\mathrm{out}}(h) = c \sqrt{h}
```

Die Pumpe wird ueber eine normierte Stellgroesse `u` zwischen 0 und 1 beschrieben:

```math
q_{\mathrm{pump}}(u) = u \cdot q_{\mathrm{pump,max}}
```

Das Modell ist bewusst kompakt gehalten. Es ist kein CFD- oder
Hydraulik-Spezialmodell, sondern ein gut nachvollziehbarer Regelungsversuch mit
realistischen Einheiten und Grenzen.

## Diskrete Simulation

Die Simulation nutzt ein explizites Euler-Verfahren mit fester Schrittweite
`Delta t`:

```math
h_{k+1} = h_k + \Delta t \cdot \frac{dh}{dt}
```

Nach jedem Schritt wird der Wasserstand auf den physikalischen Bereich zwischen
0 m und maximaler Beckenhoehe begrenzt.

## Reglerkonvention

Im Projekt ist der Fehler als

```math
e_k = h_k - h_{\mathrm{set}}
```

definiert. Ein positiver Fehler bedeutet also: Der Wasserstand liegt zu hoch und
die Pumpe soll staerker laufen.

Der diskrete PID-Regler berechnet:

```math
u_k = K_P e_k + K_I \sum_{i=0}^{k} e_i \Delta t
      + K_D \frac{e_k - e_{k-1}}{\Delta t}
```

Danach wird die Stellgroesse auf den Bereich von 0 bis 100 % begrenzt.

## Anti-Windup

Der I-Anteil wird auf einen konfigurierbaren Bereich begrenzt. Zusaetzlich wird
die Integration angehalten, wenn die Pumpe bereits an einer Stellgrenze liegt
und der aktuelle Fehler die Saettigung weiter verstaerken wuerde. Dadurch kann
der Integrator nach einem Starkregenereignis schneller wieder in einen sinnvollen
Bereich zurueckkehren.
