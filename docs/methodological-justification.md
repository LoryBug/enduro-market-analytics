# Giustificazione Delle Scelte Metodologiche

Questo documento raccoglie le motivazioni principali dietro le scelte fatte nel progetto. L'obiettivo ? avere una traccia chiara per rispondere alle domande del docente durante la presentazione o la discussione finale.

## Idea Guida Del Progetto

Il progetto non nasce per stimare il prezzo esatto di una singola moto, ma per analizzare l'andamento del mercato delle enduro usate e trasformare il forecast in indicazioni operative di acquisto.

La logica complessiva ?:

```text
annunci grezzi -> pulizia -> aggregazione temporale -> segmentazione -> forecasting -> raccomandazione di acquisto
```

La scelta più importante e stata privilegiare robustezza, interpretabilita e coerenza con i dati disponibili, invece di usare modelli complessi non pienamente adatti al contesto.

Risposta sintetica da presentazione:

> Le scelte metodologiche sono state guidate dalla natura del dataset. Il mercato delle moto usate ? molto eterogeneo, quindi abbiamo evitato di modellare direttamente il prezzo del singolo annuncio. Abbiamo costruito serie temporali aggregate sul prezzo mediano, segmentando poi per età e chilometraggio. In questo modo il forecast diventa più stabile e può essere trasformato in una raccomandazione operativa su quando e in quale cluster conviene comprare.

## Obiettivo: Forecasting, Non Regressione Sul Singolo Annuncio

Una prima scelta importante ? stata distinguere tra regressione e forecasting.

Stimare il prezzo di una singola moto usando caratteristiche come anno, km, cilindrata e marca sarebbe un problema di regressione. Invece, il progetto richiedeva una logica di Operational Analytics basata su una serie temporale: osservare come cambia il mercato nel tempo e prevedere il comportamento futuro.

Per questo il target principale ? diventato il prezzo mediano aggregato per periodo, non il prezzo del singolo annuncio.

Giustificazione:

> Abbiamo scelto il forecasting perché l'obiettivo non era valutare una singola moto, ma capire l'evoluzione temporale del mercato e individuare finestre di acquisto convenienti. La regressione sul singolo annuncio sarebbe stata utile per una valutazione puntuale, ma meno coerente con l'obiettivo del progetto.

## Perché Aggregare Gli Annunci In Serie Temporali

Gli annunci singoli sono molto rumorosi. Due moto possono avere prezzi diversi per motivi difficili da osservare nel dataset: stato reale del mezzo, manutenzione, preparazioni, urgenza del venditore, trattabilità del prezzo, accessori inclusi o localizzazione.

Aggregare gli annunci per periodo riduce parte di questo rumore e permette di osservare un fenomeno più stabile: il prezzo tipico del mercato in un certo mese.

Giustificazione:

> Il singolo annuncio contiene molto rumore e fattori non osservabili. Aggregare per mese consente di ottenere una misura più stabile del mercato e di costruire una vera serie temporale su cui applicare modelli di forecasting.

## Perché Usare La Mediana Invece Della Media

Nel mercato dell'usato la distribuzione dei prezzi può essere sbilanciata. Ci possono essere moto quasi nuove con prezzi molto alti, moto vecchie o incomplete con prezzi molto bassi, annunci sovraprezzati, moto d'epoca o modelli particolari.

La media ? sensibile a questi valori estremi. La mediana, invece, descrive meglio il prezzo centrale del mercato perché non viene spostata eccessivamente dagli outlier.

Giustificazione:

> Abbiamo usato la mediana perché nel mercato dell'usato sono presenti outlier e annunci molto eterogenei. La media rischierebbe di essere distorta da pochi prezzi estremi, mentre la mediana rappresenta meglio il prezzo tipico di mercato.

Esempio semplice:

```text
Prezzi: 4000, 4500, 4700, 5000, 15000
Media: 6640
Mediana: 4700
```

In questo caso la media risulta poco rappresentativa, mentre la mediana descrive meglio il valore centrale del mercato.

## Perché Usare Una Frequenza Mensile

Una frequenza giornaliera o settimanale avrebbe prodotto molte osservazioni instabili, con pochi annunci per periodo. Questo avrebbe reso difficile distinguere un vero trend da semplici oscillazioni casuali dovute alla disponibilità degli annunci.

La frequenza mensile ? un compromesso tra dettaglio temporale e stabilità statistica.

Giustificazione:

> Abbiamo scelto una frequenza mensile perché i dati settimanali sarebbero stati troppo sparsi e rumorosi. Il mese consente di avere abbastanza annunci per calcolare una mediana più stabile, mantenendo comunque una dinamica temporale utile per il forecasting.

## Perché Selezionare Il Segmento Core

Il mercato completo delle enduro usate contiene mezzi molto diversi tra loro: moto moderne, moto vintage, cilindrate diverse, prezzi molto bassi o molto alti. Usare tutto il mercato insieme avrebbe prodotto una serie aggregata poco interpretabile.

Per questo ? stato definito un segmento principale:

```text
modern enduro 250-500cc
1000 <= price <= 20000
```

Questa scelta rende il mercato analizzato più omogeneo e più coerente con una decisione reale di acquisto.

Giustificazione:

> Il segmento core serve a evitare di confrontare moto non comparabili. Una enduro moderna 250-500cc appartiene a un mercato diverso rispetto a una moto d'epoca, una cilindrata molto alta o un annuncio anomalo. Restringere il perimetro migliora l'interpretabilita del forecast.

## Perché Usare Cluster Età/Km

Età e chilometraggio sono due delle variabili più importanti nel mercato dell'usato. Una moto di 2 anni con pochi km e una moto di 15 anni con molti km non dovrebbero essere trattate come parte dello stesso mercato decisionale.

Le fasce usate nel progetto sono:

```text
età: 0-2, 3-5, 6-10, 11-20, 20+ anni
km: 0-5k, 5-10k, 10-15k, 15k+
```

La segmentazione permette di costruire gruppi più omogenei e raccomandazioni più realistiche.

Giustificazione:

> Abbiamo segmentato per età e chilometraggio perché sono variabili direttamente legate al valore di una moto usata. Il forecast generale descrive il mercato nel suo complesso, ma le decisioni operative diventano più utili se riferite a cluster omogenei.

## Perché Il Forecast Generale E Solo Una Baseline

Il forecast sul mercato generale e utile per avere un riferimento complessivo, ma non ? la parte più forte del progetto. Il problema ? che la composizione degli annunci cambia nel tempo: in un mese possono esserci più moto nuove, in un altro più moto vecchie, oppure più annunci con pochi km.

Quindi una variazione del prezzo mediano generale non indica necessariamente che tutto il mercato stia cambiando prezzo. Potrebbe indicare che ? cambiato il mix degli annunci disponibili.

Giustificazione:

> Il forecast generale ? utile come benchmark, ma non basta per una raccomandazione operativa. Se cambia la composizione degli annunci, cambia anche il prezzo mediano aggregato. Per questo abbiamo dato più importanza ai cluster età/km, che sono più omogenei e interpretabili.

## Perché Non Abbiamo Usato ARIMA O SARIMA

ARIMA e SARIMA sono modelli classici per serie temporali, ma non erano la scelta più coerente con questo dataset e con l'obiettivo del progetto.

Le ragioni principali sono:

| Motivo | Spiegazione |
|---|---|
| Serie relativamente corte | Il dataset copre pochi anni a frequenza mensile. Nei cluster le osservazioni disponibili sono ancora meno. |
| Cluster piccoli | Alcuni cluster hanno circa 20-45 mesi utili, pochi per stimare modelli stagionali robusti. |
| Stagionalità non sempre stabile | SARIMA richiede pattern stagionali abbastanza regolari, ad esempio più cicli annuali osservabili. |
| Mercato non puramente temporale | Il prezzo dipende anche da età, km, numerosità degli annunci e composizione del mercato. |
| Rischio di overfitting | Con pochi dati, ARIMA/SARIMA possono adattarsi al passato ma generalizzare male. |
| Obiettivo operativo | Il progetto deve produrre raccomandazioni per cluster, non solo un forecast univariato. |

Risposta breve:

> Non abbiamo usato ARIMA o SARIMA perché sono modelli più adatti a serie lunghe, regolari e prevalentemente univariate. Nel nostro caso le serie sono corte, soprattutto per cluster, e il prezzo dipende anche dalla composizione degli annunci. Per questo abbiamo preferito modelli più robusti e coerenti con i dati disponibili.

Risposta tecnica:

> SARIMA avrebbe richiesto una stagionalità ben osservabile, idealmente più cicli annuali completi. Con serie mensili relativamente corte e cluster con poche osservazioni, la stima dei parametri sarebbe stata fragile. Inoltre ARIMA/SARIMA modellano principalmente la dinamica passata della variabile target, mentre nel nostro caso sono importanti anche feature come età media, km medi e numero di annunci.

Frase forte:

> Non usare ARIMA/SARIMA non ? una mancanza, ma una scelta metodologica. Abbiamo preferito modelli proporzionati alla quantità e qualità dei dati.

## Perché Usare Seasonal Naive

Il modello seasonal naive ? una baseline semplice: usa valori passati recenti o stagionali come previsione futura. ? importante perché permette di verificare se modelli più complessi aggiungono davvero valore.

Giustificazione:

> Seasonal naive ? stato usato come baseline. In un progetto di forecasting ? fondamentale confrontare i modelli complessi con una regola semplice. Se un modello avanzato non batte la baseline, allora non sta aggiungendo valore reale.

## Perché Usare Holt-Winters

Holt-Winters ? un metodo statistico di exponential smoothing che può catturare livello, trend e stagionalità con una complessità inferiore rispetto a SARIMA.

? adatto come modello intermedio: più sofisticato della baseline, ma ancora interpretabile e relativamente robusto su serie non molto lunghe.

Giustificazione:

> Holt-Winters ? stato scelto per avere un modello statistico interpretabile, capace di gestire trend e stagionalità senza richiedere una stima parametrica complessa come SARIMA. E una scelta più prudente su serie corte.

## Perché Usare Random Forest

Random Forest permette di costruire un modello supervisionato usando non solo i valori passati del prezzo, ma anche variabili esplicative.

Nel progetto il modello può usare feature come:

```text
lag del prezzo mediano
rolling mean
rolling std
listings_count
avg_km
avg_age
month
week_number
```

Questo ? coerente con il problema, perché il prezzo del mercato non dipende solo dal tempo, ma anche dalla composizione degli annunci.

Giustificazione:

> Random Forest ? stato scelto perché consente di combinare informazione temporale e variabili descrittive del mercato. A differenza di un modello puramente univariato, può tenere conto di età media, km medi e numero di annunci, che sono fattori rilevanti per il prezzo.

Limite da dichiarare:

> Random Forest ? meno interpretabile di una baseline statistica semplice e può soffrire se i dati sono pochi. Per questo non ? stato usato da solo, ma confrontato con modelli più semplici tramite metriche di errore.

## Perché Usare MLP Solo Come Confronto Generale

Un modello neurale come MLP può apprendere relazioni non lineari, ma richiede più dati per essere stabile. Nel contesto del progetto, soprattutto sui cluster, i dati disponibili non sono sufficienti per giustificare un uso forte del modello neurale.

Giustificazione:

> L'MLP ? stato considerato come confronto sul forecast generale, ma non ? la scelta centrale del progetto. Con dataset piccoli, i modelli neurali rischiano di essere instabili e meno interpretabili. Per la parte operativa abbiamo quindi privilegiato modelli più robusti.

## Perché Usare Uno Split Cronologico

Nel forecasting non ? corretto mischiare casualmente osservazioni passate e future. Un train-test split casuale creerebbe leakage temporale: il modello potrebbe imparare informazioni provenienti dal futuro.

Per questo la valutazione ? stata fatta rispettando l'ordine temporale: addestramento sul passato, test sui periodi successivi.

Giustificazione:

> Abbiamo usato uno split cronologico per simulare il vero scenario predittivo. In produzione il modello avrebbe solo dati passati per prevedere il futuro, quindi anche la valutazione deve rispettare questa logica.

## Perché Usare Più Metriche

Una sola metrica non basta per valutare un forecast. Ogni metrica evidenzia un aspetto diverso dell'errore.

| Metrica | Cosa misura | Perché e utile |
|---|---|---|
| MAE | Errore medio assoluto | Facile da interpretare in euro. |
| RMSE | Errore quadratico medio | Penalizza di più gli errori grandi. |
| MAPE | Errore percentuale medio | Permette di leggere l'errore in termini relativi. |
| R2 | Capacità esplicativa rispetto alla variabilita | Utile come indicatore generale, ma non sufficiente da solo. |

Giustificazione:

> Abbiamo usato più metriche per evitare una valutazione parziale. MAE e RMSE mostrano l'errore in euro, MAPE rende l'errore confrontabile in percentuale e R2 aiuta a capire quanto il modello spiega la variabilita della serie.

Nota importante:

> Nel nostro contesto MAE, RMSE e MAPE sono più direttamente interpretabili di R2, perché l'obiettivo operativo ? capire quanto può essere grande l'errore del prezzo previsto.

## Perché Trasformare Il Forecast In Raccomandazione

Il valore del progetto non sta solo nella previsione numerica, ma nella trasformazione della previsione in una decisione. Questo ? il passaggio dalla predictive analytics alla prescriptive analytics.

La raccomandazione confronta il prezzo previsto con la mediana storica del cluster. Se il prezzo previsto ? significativamente più basso, il periodo viene considerato potenzialmente conveniente.

Giustificazione:

> Il progetto non si ferma al forecast, ma usa la previsione per supportare una decisione operativa. Questo rende l'analisi più vicina a un problema reale: non solo quanto costera il mercato, ma quando conviene comprare.

## Perché Usare Soglie Di Raccomandazione

Le soglie servono a trasformare una differenza numerica in una classe leggibile, ad esempio `good_buy`, `neutral` o `avoid_expensive`.

Senza soglie, il risultato sarebbe solo una tabella di prezzi previsti. Con le soglie, invece, il risultato diventa un'indicazione pratica.

Giustificazione:

> Le soglie non vogliono essere regole assolute, ma criteri operativi per leggere il forecast. Servono a distinguere variazioni piccole, probabilmente poco significative, da differenze abbastanza grandi da suggerire una possibile opportunità di acquisto.

## Perché Trattare Il Dataset In Modo Uniforme

Tutte le osservazioni del dataset vengono trattate nello stesso modo nella pipeline. La distinzione rilevante per il progetto non ? l'origine della singola riga, ma la trasformazione degli annunci in serie temporali aggregate e cluster omogenei.

Questa scelta rende la presentazione più semplice e coerente: il modello lavora sul dataset di mercato disponibile, usando regole uguali per pulizia, aggregazione, forecasting e raccomandazione.

Giustificazione:

> Abbiamo scelto di trattare tutte le osservazioni con la stessa pipeline. L'affidabilità non viene basata sulla provenienza della singola riga, ma su aggregazione mensile, mediana, segmentazione e soglie minime di copertura dei cluster.

## Limiti Del Progetto

I principali limiti da dichiarare sono:

| Limite | Impatto | Come lo gestiamo |
|---|---|---|
| Dataset non enorme | Alcuni modelli complessi non sono giustificati | Usiamo modelli robusti e baseline. |
| Cluster con poche osservazioni | Forecast meno stabile | Usiamo soglie minime di eleggibilita. |
| Prezzi richiesti, non prezzi finali | Il prezzo reale di vendita può essere diverso | Interpretiamo il risultato come andamento degli annunci. |
| Variabili non osservate | Stato reale, manutenzione e trattabilità non sono pienamente catturati | Aggregazione e mediana riducono parte del rumore. |
| Mercato locale e fonti specifiche | Generalizzazione limitata | Presentiamo il progetto come analisi del dataset raccolto. |

Risposta da esame:

> Il limite principale ? la disponibilità dei dati. Alcuni mesi e cluster hanno pochi annunci, e inoltre osserviamo prezzi richiesti, non prezzi effettivi di vendita. Per questo il forecast va interpretato come supporto decisionale e non come previsione certa. Abbiamo gestito il problema usando mediana, aggregazione mensile, cluster minimi e confronto tra modelli.

## Punti Di Forza Del Progetto

I punti di forza da sottolineare sono:

| Punto di forza | Spiegazione |
|---|---|
| Coerenza con l'obiettivo | Il progetto passa da dati grezzi a raccomandazioni operative. |
| Robustezza | Mediana, aggregazione e cluster riducono rumore e outlier. |
| Interpretàbilita | Le scelte sono spiegabili e difendibili. |
| Confronto tra modelli | Non viene usato un solo modello senza benchmark. |
| Valutazione temporale corretta | Lo split cronologico evita leakage. |
| Segmentazione utile | I cluster età/km sono comprensibili anche per un utente non tecnico. |

Risposta da presentazione:

> Il punto forte del progetto ? che non si limita a costruire un modello predittivo, ma collega descriptive, predictive e prescriptive analytics. Prima descriviamo il mercato, poi prevediamo l'andamento dei cluster, infine trasformiamo il risultato in una raccomandazione di acquisto.

## Tabella Riassuntiva Delle Scelte

| Scelta | Motivazione | Frase pronta |
|---|---|---|
| Forecast invece di regressione | L'obiettivo ? prevedere l'andamento del mercato | "Volevamo prevedere una serie temporale, non valutare un singolo annuncio." |
| Mediana invece di media | Maggiore robustezza agli outlier | "La mediana descrive meglio il prezzo tipico." |
| Frequenza mensile | Compromesso tra granularità e stabilità | "Il mese riduce il rumore dei dati troppo sparsi." |
| Segmento core | Evita di mischiare moto non comparabili | "Abbiamo analizzato un mercato più omogeneo." |
| Cluster età/km | Rendono le raccomandazioni più realistiche | "Età e km sono determinanti fondamentali del prezzo." |
| Forecast generale come baseline | Il mix degli annunci cambia nel tempo | "Il mercato aggregato serve come contesto, non come unica decisione." |
| Seasonal naive | Baseline semplice | "Serve a verificare se modelli complessi aggiungono valore." |
| Holt-Winters | Modello statistico interpretabile | "Cattura trend e stagionalità con complessità contenuta." |
| Random Forest | Usa feature temporali ed esplicative | "Il prezzo dipende anche dalla composizione degli annunci." |
| No ARIMA/SARIMA | Serie corte e non puramente univariate | "Sarebbero stati meno robusti su questi dati." |
| Split cronologico | Evita leakage temporale | "Si addestra sul passato e si testa sul futuro." |
| Più metriche | Valutazione più completa | "Ogni metrica evidenzia un aspetto diverso dell'errore." |
| Raccomandazione finale | Passaggio a prescriptive analytics | "Il forecast viene trasformato in una decisione operativa." |

## Domande Probabili Del Docente

### Perché non avete previsto il prezzo di ogni singola moto?

Perché quello sarebbe stato un problema di regressione, non di forecasting. Il progetto voleva analizzare l'andamento temporale del mercato, quindi abbiamo costruito serie aggregate per periodo.

### Perché la mediana e non la media?

Perché il mercato dell'usato contiene outlier e prezzi molto eterogenei. La mediana e più robusta e rappresenta meglio il prezzo tipico.

### Perché non ARIMA/SARIMA?

Perché le serie sono relativamente corte, i cluster hanno poche osservazioni e il prezzo dipende anche da variabili esplicative come età, km e numerosità degli annunci. ARIMA/SARIMA sarebbero stati meno coerenti con questo contesto.

### Perché Random Forest?

Perché permette di usare sia i valori passati del prezzo sia le caratteristiche del mercato, come età media, km medi e numero di annunci. Questo ? coerente con la natura del problema.

### Perché avete segmentato per età e km?

Perché sono due variabili fondamentali nel valore di una moto usata. Segmentare permette di confrontare moto simili e produrre consigli più realistici.

### Perché il forecast generale non basta?

Perché il prezzo mediano generale può cambiare anche solo per effetto del mix degli annunci. I cluster riducono questo problema perché sono più omogenei.

### Qual ? il limite principale?

La disponibilità dei dati e la numerosità di alcuni cluster. Per questo abbiamo usato modelli semplici, metriche di errore e soglie minime di eleggibilita.

### Qual ? il contributo operativo del progetto?

Il progetto trasforma dati di annunci in indicazioni pratiche: quali cluster sembrano più convenienti e in quali periodi futuri potrebbe convenire acquistare.

## Risposta Finale Completà

Questa ? una risposta lunga ma completa da usare se il docente chiede di giustificare l'impostazione generale:

> Abbiamo impostato il progetto partendo dall'obiettivo operativo: non stimare il prezzo esatto di una singola moto, ma capire l'evoluzione del mercato e individuare finestre di acquisto convenienti. Per questo abbiamo trasformato gli annunci in serie temporali aggregate, usando la mediana per ridurre l'effetto degli outlier. Abbiamo scelto la frequenza mensile per avere osservazioni più stabili e abbiamo ristretto l'analisi al segmento core delle enduro moderne 250-500cc, evitando di mischiare moto troppo diverse. Successivamente abbiamo segmentato per età e chilometraggio, perché sono variabili fondamentali nel mercato dell'usato. Per il forecasting abbiamo confrontato baseline semplici, Holt-Winters e Random Forest. Non abbiamo usato ARIMA/SARIMA perché le serie sono corte, i cluster hanno poche osservazioni e il prezzo dipende anche da variabili esplicative, non solo dal tempo. Infine abbiamo trasformato il forecast in raccomandazioni operative, collegando descriptive, predictive e prescriptive analytics.

## Frase Conclusiva Forte

> La scelta principale del progetto ? stata privilegiare robustezza e interpretabilita rispetto alla complessità. In un contesto con dati limitati e mercato eterogeneo, un modello più semplice ma coerente e difendibile ? preferibile a un modello avanzato ma fragile.
