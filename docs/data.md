# Financial data and numerical conventions

Use consistent identifiers, units, currencies, and horizons before constructing a model. Finance aligns labeled inputs by identifier; unlabeled arrays follow the model's declared order. Calculations use binary64 floating point.

## Identifiers and alignment

Model identifiers are nonempty strings or integers. Boolean identifiers, blank strings, empty identifier collections, and duplicate identifiers are rejected. Labeled vectors accept pandas Series or mappings; matrices accept DataFrames, supported column mappings, arrays, or SciPy sparse matrices where the operation supports them. Each API specifies its axis order.

A labeled input must contain exactly the expected identifiers. Finance reorders matching labels to the model's order and rejects missing or unexpected labels. An unlabeled vector must contain one value per identifier. Scalar broadcasting is available only for parameters that document it. Financial input tables require the documented columns and reject unknown columns.

Dense numeric arrays must have a real integer, unsigned integer, or floating dtype. Complex, object, string, and boolean arrays are rejected. Lists and tuples containing booleans are also rejected. Values must be finite. Numeric scalar parameters accept Python or NumPy real numbers, excluding booleans. `Decimal` is not a supported numeric scalar. Quantities, rates, costs, and coefficients are converted to binary64; use compatible units when values exceed its range or precision.

## Financial units

Returns are fractions: `0.05` means 5%. One basis point is `0.0001`. Variance has squared-return units; volatility has return units. A portfolio's expected arithmetic returns, covariance, scenario returns, and financial constraints must use compatible horizons. The `horizon` description records that convention; it does not rescale inputs.

Currency fields describe the amounts supplied. Finance does not infer exchange rates, convert currencies from their names, load market data, adjust prices for distributions, fill missing observations, or infer a market calendar. Models with explicit account transfers or FX inputs apply those supplied conversions. Supply adjusted prices when calculating total returns.

Floating-point feasibility tolerances describe numerical acceptance. For operational use, reconcile proposed decisions with the institution's accounting and transaction systems.

## Covariance validation

Covariance inputs must be square, finite, and exactly symmetric in their supplied numeric representation. Finance does not silently symmetrize or repair them. Singular positive semidefinite covariance is accepted. For a nonzero matrix, validation scales it by its largest absolute entry and rejects a minimum eigenvalue below `-1e-12` times the scaled infinity norm. Sparse inputs retain a CSR representation after duplicate entries are combined and zeros removed.

An accepted roundoff-sized negative eigenvalue is a numerical tolerance, not a request for covariance projection. Apply any intended correction explicitly before passing the matrix. [Risk analytics](risk.md) provides explicit shrinkage and factor representations.

## Dates and information availability

Use the date or instant convention required by the operation. Calendar dates accept ISO `YYYY-MM-DD` strings, `datetime.date`, or midnight `datetime.datetime`, `pandas.Timestamp`, and `numpy.datetime64` values without a timezone. They compare whole dates. Instants accept strings with an explicit timezone/UTC offset, timezone-aware `datetime.datetime`, or timezone-aware `pandas.Timestamp` values; they compare instants after conversion to UTC. A naive timestamp cannot substitute for an operation that requires an aware instant.

As-of filtering checks both when an observation occurred and when it became available. It does not recover historical revisions or data vintages. Supply the values that were actually available at the decision time.

## Data API

Import these functions from `qpiai_finance.data`. They require no authentication and perform no optimization or network requests.

### `history_as_of`

```python
history_as_of(observations, *, as_of, observed_at=None, available_at=None)
```

Select rows whose observation and availability times are both no later than `as_of`.

| Parameter | Type and meaning |
| --- | --- |
| `observations` | One-dimensional observations or a two-dimensional observation × asset array; pandas Series/DataFrame or an array-like input. |
| `as_of` | Decision date or timezone-aware instant. Use the same convention for the row times. |
| `observed_at` | One date/instant per row. Required for arrays; omitted for a pandas input with a DatetimeIndex. A Series of times aligns by input row labels. |
| `available_at` | One publication/availability date or instant per row; defaults to `observed_at`. Each availability must be at or after its observation. |

Returns a selected Series, DataFrame, or ndarray, preserving pandas labels and row order. Pandas and ndarray inputs retain their data dtypes; lists and tuples produce an object-dtype ndarray. An empty selection is possible. Observation times must be unique and strictly increasing. The function does not sort, fill, or validate the observation values; it filters rows by their times. Invalid dimensions, mismatched timestamp labels or lengths, and incompatible time conventions raise `TypeError` or `ValueError`.

### `returns_from_prices`

```python
returns_from_prices(prices, *, kind="simple")
```

`prices` is a one-dimensional price series or a time × asset matrix with at least two rows, at least one asset, and finite strictly positive prices. `kind` is `"simple"` or `"log"`.

For consecutive prices $P_{t-1}$ and $P_t$, simple return is $P_t/P_{t-1}-1$ and log return is $\log(P_t/P_{t-1})$. The output has one fewer row. A Series or DataFrame retains its type, later observation labels, and name or asset columns; other inputs return an ndarray. Pandas time labels must be unique and increasing; DataFrame asset columns must be valid identifiers.

The function performs no corporate-action adjustment, imputation, or annualization. Unsupported kinds, nonpositive prices, nonfinite values, incompatible dimensions or labels, and unrepresentable returns raise `ValueError`.

### `compound_returns`

```python
compound_returns(returns, *, kind="simple")
```

`returns` is a nonempty one-dimensional return series or time × asset matrix. `kind="simple"` calculates $\prod_t(1+r_t)-1$; values must be at least `-1`. `kind="log"` sums log returns and returns the aggregate log return, without converting it to a simple return.

Returns a float for a one-dimensional input, a Series indexed by asset columns for a DataFrame, or an ndarray for other two-dimensional inputs. A DataFrame result is named `simple_return` or `log_return`. Missing or nonfinite data, unsupported dimensions or kinds, and output overflow raise `ValueError`.

### `rescale_moments`

```python
rescale_moments(expected_returns, covariance, *, periods, assumption)
```

Multiply the supplied mean vector and covariance by the positive scalar `periods`. `assumption` must explicitly equal `"iid_additive"`. This scaling applies to independent additive period P&L or log-return moments. It is not exact compounding of simple-return moments.

`expected_returns` accepts a Series, mapping, or one-dimensional array. `covariance` accepts a matching DataFrame, column mapping, dense array, or sparse matrix and must satisfy the covariance validation above. A labeled mean defines asset order; otherwise the order is positional. Returns `(mean, covariance)`, where `mean` is a Series and covariance is a labeled DataFrame for dense inputs or a sparse matrix for sparse inputs. Invalid labels, nonpositive `periods`, unsupported assumptions, and overflow raise `TypeError` or `ValueError`.
