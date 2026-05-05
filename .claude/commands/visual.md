Implement a visual or UI change with iterative verification.
Usage: /visual [description]

## 1. Plan
Read the relevant rendering/UI files. Describe exactly what will change visually and how you'll implement it. Wait for go-ahead.

## 2. Code
Make the change. Keep it targeted — visual work is easier to verify in small steps than in one large diff.

## 3. Verify
Run `uv run python main.py` and describe exactly what you observe in the relevant area:
- What changed from before?
- Does it match the intended outcome?
- Any artifacts, misalignments, off-by-one issues, or frame-rate concerns?

## 4. Iterate
If the result doesn't match the intent, diagnose and fix. Repeat the run → observe → fix loop until it looks right.

## 5. Commit
Show the diff and proposed message. Wait for go-ahead before committing.
