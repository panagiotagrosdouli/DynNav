# Contribution 02 — Εκτίμηση και Βαθμονόμηση Αβεβαιότητας

Το `02_uncertainty_calibration` είναι ο επίσημος φάκελος της Contribution 02.

Η ενότητα καλύπτει:

- εκτίμηση αβεβαιότητας,
- έλεγχο της σχέσης αβεβαιότητας και πραγματικού σφάλματος,
- βαθμονόμηση πιθανοτικών εκτιμήσεων,
- αξιολόγηση coverage και calibration error,
- διασύνδεση με risk-aware και belief-space planners.

Η παλαιότερη θέση `02_uncertainty_estimation` ήταν placeholder χωρίς υλοποίηση και παρέπεμπε σε ανύπαρκτο script. Για αυτό ενοποιήθηκε στην παρούσα contribution.

## Εκτέλεση benchmark

```bash
python contributions/02_uncertainty_calibration/experiments/eval_uncertainty_calibration.py
```

## Επιστημονικός περιορισμός

Μια τιμή αβεβαιότητας δεν πρέπει να ερμηνεύεται αυτομάτως ως αξιόπιστο διάστημα εμπιστοσύνης. Απαιτείται έλεγχος βαθμονόμησης και επαναξιολόγηση σε περίπτωση distribution shift.
