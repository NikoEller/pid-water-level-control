# Theorie

## Tankmodell

Der Wasserstand \(h(t)\) wird als ein Zustandsmodell erster Ordnung beschrieben.
Die effektive Beckenflaeche \(A\) verbindet Volumenstrom und Aenderung des
Wasserstands:

\[
\frac{dh}{dt} = \frac{q_{in}(t) + q_{rain}(t) - q_{out}(h) - q_{pump}(u)}{A}
\]

Der freie Ablauf wird als einfache Wurzelkennlinie modelliert:

\[
q_{out}(h) = c \sqrt{h}
\]

Die Pumpe wird ueber eine normierte Stellgroesse \(u \in [0, 1]\) beschrieben:

\[
q_{pump}(u) = u \cdot q_{pump,max}
\]

Das Modell ist bewusst kompakt gehalten. Es ist kein CFD- oder
Hydraulik-Spezialmodell, sondern ein gut nachvollziehbarer Regelungsversuch mit
realistischen Einheiten und Grenzen.

## Diskrete Simulation

Die Simulation nutzt ein explizites Euler-Verfahren mit fester Schrittweite
\(\Delta t\):

\[
h_{k+1} = h_k + \Delta t \cdot \frac{dh}{dt}
\]

Nach jedem Schritt wird der Wasserstand auf den physikalischen Bereich zwischen
0 m und maximaler Beckenhoehe begrenzt.

## Reglerkonvention

Im Projekt ist der Fehler als

\[
e_k = h_k - h_{set}
\]

definiert. Ein positiver Fehler bedeutet also: Der Wasserstand liegt zu hoch und
die Pumpe soll staerker laufen.

Der diskrete PID-Regler berechnet:

\[
u_k = K_P e_k + K_I \sum e_k \Delta t + K_D \frac{e_k - e_{k-1}}{\Delta t}
\]

Danach wird die Stellgroesse auf den Bereich von 0 bis 100 % begrenzt.

## Anti-Windup

Der I-Anteil wird auf einen konfigurierbaren Bereich begrenzt. Zusaetzlich wird
die Integration angehalten, wenn die Pumpe bereits an einer Stellgrenze liegt
und der aktuelle Fehler die Saettigung weiter verstaerken wuerde. Dadurch kann
der Integrator nach einem Starkregenereignis schneller wieder in einen sinnvollen
Bereich zurueckkehren.
