# Εξερεύνηση Next-Best-View με Επίγνωση Επιστρεψιμότητας

[![Module](https://img.shields.io/badge/DynNav-Contribution%2007-6f42c1)](.)
[![Topic](https://img.shields.io/badge/Topic-Active%20Exploration-0366d6)](.)
[![Status](https://img.shields.io/badge/Status-Research%20Prototype-2ea44f)](.)

[English](README.md) | **Ελληνικά**

<p align="center">
  <img src="assets/next_best_view_pipeline.svg" alt="Εννοιολογικό διάγραμμα next-best-view εξερεύνησης με επίγνωση επιστρεψιμότητας" width="100%" />
</p>

<p align="center"><em>Εννοιολογική απεικόνιση. Η εικόνα δεν αποτελεί πειραματική απόδειξη, αποτέλεσμα τυπικής βελτιστότητας εξερεύνησης ή εγγύηση ασφάλειας.</em></p>

Η συνεισφορά αυτή μελετά την **ενεργή εξερεύνηση** σε άγνωστα περιβάλλοντα. Επεκτείνει την κλασική επιλογή next-best-view πέρα από το information gain και το travel cost, ενσωματώνοντας ρητά τον κίνδυνο διαδρομής, την επιστρεψιμότητα και τη συνδεσιμότητα.

Η βασική θέση είναι ότι ένα πληροφοριακά χρήσιμο viewpoint δεν είναι κατ’ ανάγκη και επιχειρησιακά αποδεκτό.

---

## Ερευνητικό ερώτημα

> **Πώς μπορεί ένα ρομπότ να επιλέγει πληροφοριακά χρήσιμα viewpoints διατηρώντας ελευθερία ανάκαμψης, περιορίζοντας την έκθεση σε κίνδυνο και διατηρώντας την ποιότητα επικοινωνίας;**

Η συνεισφορά αξιολογεί τους υποψηφίους βάσει:

1. αναμενόμενου information gain,
2. κόστους μετάβασης,
3. κινδύνου διαδρομής,
4. επιστρεψιμότητας και
5. ποιότητας επικοινωνίας.

---

## Μαθηματική διατύπωση

Για υποψήφιο viewpoint \(v\), το κλασικό score είναι

\[
S_{\mathrm{classic}}(v)=\frac{I(v)}{\max(C(v),\epsilon)},
\]

όπου \(I(v)\) είναι το information gain και \(C(v)\) το travel cost.

Το υλοποιημένο safety-aware score είναι

\[
S_{\mathrm{safe}}(v)=
\frac{I(v)\left(1+w_R R(v)\right)\left(1+w_Q Q(v)\right)}
{\max(C(v),\epsilon)\left(1+w_P P(v)\right)},
\]

όπου:

- \(R(v)\in[0,1]\) είναι η επιστρεψιμότητα,
- \(Q(v)\in[0,1]\) η συνδεσιμότητα,
- \(P(v)\geq0\) ο κίνδυνος διαδρομής,
- \(w_R,w_Q,w_P\) είναι ρυθμιζόμενα βάρη.

Η υλοποίηση αναφέρει και τα δύο scores και καταγράφει ποιος υποψήφιος επιλέγεται από την κλασική και ποιος από τη safety-aware πολιτική.

---

## Ερμηνεία του scoring

Το safety-aware score επιβραβεύει:

- υψηλό αναμενόμενο information gain,
- ισχυρή επιστρεψιμότητα και
- διατήρηση της συνδεσιμότητας.

Παράλληλα penalizes:

- μεγάλο travel cost και
- υψηλό path risk.

Πρόκειται για διαφανή scalarization ανταγωνιστικών στόχων και όχι για απόδειξη παγκόσμιας βελτιστότητας ή τυπικής ασφάλειας.

---

## Δομή φακέλου

```text
07_next_best_view/
├── README.md
├── README_GR.md
├── assets/
│   └── next_best_view_pipeline.svg
├── code/
│   └── nbv_scoring.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_returnability_aware_nbv.py
└── results/
    └── c07_returnability_aware_nbv.csv
```

---

## Αναπαραγωγιμότητα

Η εκτέλεση γίνεται από τη ρίζα του repository:

```bash
python contributions/07_next_best_view/experiments/eval_returnability_aware_nbv.py
```

Η εντολή παράγει:

```text
contributions/07_next_best_view/results/c07_returnability_aware_nbv.csv
```

Για επιστημονικά αναφέρσιμη εκτέλεση πρέπει να διατηρούνται το ακριβές commit, οι ορισμοί των υποψηφίων, τα βάρη scoring, οι παραδοχές χάρτη και ο random seed όπου εφαρμόζεται.

---

## Πρωτόκολλο αξιολόγησης

Το benchmark συγκρίνει συνθετικά viewpoints που αναπαριστούν διαφορετικά trade-offs:

- κοντινό viewpoint με χαμηλό information gain,
- μακρινό viewpoint με υψηλό information gain,
- frontier σε bottleneck,
- ισορροπημένο χαμηλού κινδύνου και υψηλής επιστρεψιμότητας frontier,
- frontier με relay support.

Για κάθε υποψήφιο καταγράφονται information gain, travel cost, path risk, returnability, connectivity, classic score, safety-aware score και οι επιλογές των δύο πολιτικών.

Το benchmark ελέγχει τη λογική scoring. Δεν ισοδυναμεί με closed-loop εξερεύνηση με πραγματικές αισθητηριακές παρατηρήσεις.

---

## Επιστημονική συνεισφορά

Το C07 επαναδιατυπώνει την επιλογή next-best-view ως πρόβλημα **trade-off πληροφορίας, κινδύνου και ανακτησιμότητας**, αντί για αμιγώς entropy-driven objective.

Η συνεισφορά είναι ισχυρότερη από την απλή μεγιστοποίηση του information-gain-to-cost ratio, επειδή εξετάζει κατά πόσο το ρομπότ μπορεί να αξιοποιήσει με ασφάλεια τη νέα πληροφορία και να διατηρήσει μελλοντική ελευθερία αποφάσεων.

---

## Περιορισμοί

1. Τα viewpoints και τα γνωρίσματά τους είναι συνθετικά στο τρέχον benchmark.
2. Το information gain δεν υπολογίζεται από πλήρες πιθανοτικό μοντέλο αισθητήρα και occlusion.
3. Τα βάρη επιλέγονται χειροκίνητα.
4. Returnability και path risk εξαρτώνται από upstream προσεγγίσεις.
5. Η συνδεσιμότητα αναπαρίσταται ως scalar γνώρισμα.
6. Δεν υλοποιούνται επαναλαμβανόμενη sensing, map update, frontier regeneration και closed-loop replanning.
7. Υψηλό safety-aware score δεν αποτελεί τυπική εγγύηση ασφάλειας.

---

## Ερευνητικές κατευθύνσεις

Σχετικές επεκτάσεις είναι:

- παραγωγή frontiers από τον πραγματικό χάρτη,
- entropy reduction από ρεαλιστικά sensor models,
- occlusion και field-of-view reasoning,
- adaptive ή learned scoring weights,
- επιλογή viewpoints μέσω Pareto front,
- uncertainty-aware εκτίμηση επιστρεψιμότητας,
- πρόβλεψη συνδεσιμότητας σε όλη τη διαδρομή,
- closed-loop exploration με δυναμικά εμπόδια και distribution shift.

Ένα μελλοντικό σύστημα πρέπει να προσαρμόζει την επιθετικότητα εξερεύνησης στη φάση αποστολής, στα resource margins, στην αβεβαιότητα και στην κατάσταση safe mode.

---

## Επιστημονικοί ισχυρισμοί

Η υλοποίηση υποστηρίζει ότι:

- υπολογίζονται ρητά classical και returnability-aware NBV scores,
- risk, returnability και connectivity μπορούν να αλλάξουν την κατάταξη σε σχέση με την κλασική πολιτική,
- οι επιλογές είναι ελέγξιμες μέσω μετρικών ανά υποψήφιο,
- το benchmark αποκαλύπτει τα trade-offs που κωδικοποιούνται από τα βάρη.

Δεν αποδεικνύει παγκόσμια βέλτιστη εξερεύνηση, εγγυημένη αποδοτικότητα ολοκλήρωσης χάρτη, ρεαλιστική αισθητηριακή απόδοση ή πιστοποιημένη ασφάλεια.

---

## Ρόλος στο DynNav

Το C07 χρησιμοποιεί uncertainty και map information, route risk από το C03, recoverability από το C04 και connectivity από το C06. Μπορεί επίσης να ενεργοποιήσει το C05 όταν όλα τα πληροφοριακά χρήσιμα viewpoints έχουν ασθενή επιχειρησιακά περιθώρια.

---

## Αναφορά και αναπαραγωγιμότητα

Σε ακαδημαϊκή χρήση πρέπει να αναφέρονται το ακριβές commit, το σύνολο υποψηφίων, τα scoring weights, οι ορισμοί information gain, risk, returnability και connectivity, η εντολή benchmark και ο random seed.