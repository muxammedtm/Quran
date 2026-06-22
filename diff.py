"""O'qilgan matn bilan to'g'ri oyatni so'z va harf darajasida solishtirish."""
import difflib
from quran_data import normalize


def letter_diff(expected_word: str, recited_word: str):
    """Ikki so'z orasidagi harf farqlarini qaytaradi."""
    sm = difflib.SequenceMatcher(a=list(expected_word), b=list(recited_word))
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        out.append({
            "op": tag,                       # replace / delete / insert
            "expected": expected_word[i1:i2],
            "recited": recited_word[j1:j2],
        })
    return out


def compare(expected_text: str, recited_text: str):
    """So'z darajasidagi xatolar ro'yxatini qaytaradi.
    type: skipped (tashlab ketilgan) / added (ortiqcha) / wrong (noto'g'ri)."""
    exp = normalize(expected_text).split()
    rec = normalize(recited_text).split()
    sm = difflib.SequenceMatcher(a=exp, b=rec, autojunk=False)
    issues = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            for w in exp[i1:i2]:
                issues.append({"type": "skipped", "expected": w})
        elif tag == "insert":
            for w in rec[j1:j2]:
                issues.append({"type": "added", "recited": w})
        elif tag == "replace":
            span = max(i2 - i1, j2 - j1)
            for k in range(span):
                e = exp[i1 + k] if i1 + k < i2 else None
                r = rec[j1 + k] if j1 + k < j2 else None
                if e and r:
                    issues.append({
                        "type": "wrong",
                        "expected": e,
                        "recited": r,
                        "letters": letter_diff(e, r),
                    })
                elif e:
                    issues.append({"type": "skipped", "expected": e})
                elif r:
                    issues.append({"type": "added", "recited": r})
    return exp, rec, issues


def accuracy(exp_words, issues) -> float:
    """Taxminiy aniqlik foizi (so'zlar bo'yicha)."""
    total = max(len(exp_words), 1)
    errs = sum(1 for i in issues if i["type"] in ("skipped", "wrong"))
    return round(100 * (1 - min(errs, total) / total), 1)
