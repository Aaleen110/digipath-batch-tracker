# Task 2 — Debug Report

## Bug 1: Incorrect channel slicing includes baseline in total calculation

**Issue:**

The code uses `raw_counts[:-1]`, which removes only the control channel but still includes the baseline channel in the total. Since the baseline is also used as the denominator, it gets counted twice and causes the calculated ratio to be higher than expected.

**Fix:**

```python
total = sum(raw_counts[1:-1])
baseline = raw_counts[0]
ratio = total / baseline
```

## Bug 2: Mutable default argument causes shared state

**Issue:**

results_store={} is created once when the function is defined, not each time the function is called. This causes different batch executions to share the same dictionary, which can lead to unrelated batch results being returned.

**Fix:**

```python
def process_batch_results(batch_id, raw_counts, results_store=None):
    if results_store is None:
        results_store = {}
```


## Bug 3: Missing validation for zero baseline

**Issue:**

If raw_counts[0] is 0, the division operation fails with a ZeroDivisionError. The function should validate the baseline value before performing the calculation.

**Fix:**

```python
if baseline == 0:
    raise ValueError("Baseline cannot be zero")
```

## Bug 4: Missing input length validation

**Issue:**

The function assumes raw_counts always contains valid data. An empty or incomplete list can cause an index error or generate an invalid ratio without any warning.

**Fix:**

```python
if len(raw_counts) < 3:
    raise ValueError("Insufficient channel readings")
```


## Bug 5: Duplicate batch processing silently overwrites results

**Issue:**

Assigning results_store[batch_id] = ratio overwrites existing results for the same batch ID without warning. This can hide duplicate processing issues and lead to unexpected data changes.

**Fix:**

```python
if batch_id in results_store:
    raise ValueError("Batch already processed")
```