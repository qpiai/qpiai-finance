# Trading fee and market-impact functions

Import `transaction_fees` and `market_impact_cost` from `qpiai_finance.trading.costs`. They evaluate or construct the stated cost terms without modifying an existing financial model or executing a solve.

## Quantity and coefficient alignment

Quantities are signed actual traded units, not portfolio weights. Positive and negative entries represent opposing trade directions. A scalar represents one ticket; each array or table entry also represents one ticket.

Numeric inputs must be finite and real. A mapping of quantities becomes a labeled Series. Series/DataFrame quantity axes must be unique. Scalar and array coefficients use NumPy broadcasting to the quantity shape. A coefficient Series or mapping aligns to a quantity Series' index or a quantity DataFrame's columns. A coefficient DataFrame aligns both axes to a quantity DataFrame. Labeled coefficients require compatible labeled quantities and exactly matching axes.

## `transaction_fees`

```python
transaction_fees(quantities, *, per_unit=0.0, fixed=0.0)
```

`quantities` is a finite numeric scalar, array-like input, Series, DataFrame, or mapping. `per_unit` is a nonnegative coefficient in currency per traded unit; `fixed` is a nonnegative amount per execution ticket. Each may be a scalar or a compatible array/labeled coefficient.

Returns `per_unit * abs(quantities) + fixed * (quantities != 0)` per entry. A zero quantity incurs no fixed charge; any nonzero quantity incurs the full charge without a tolerance. A scalar returns a float, an array returns an ndarray, a Series/mapping returns a Series named `transaction_fees`, and a DataFrame returns a DataFrame with matching axes.

To evaluate asymmetric fees, apply the actual buy/sell coefficients separately to the corresponding quantities. Spreads, price movements, taxes, and market impact are separate costs. In an optimization formulation, fixed fees require properly linked activation variables; replacing them with proportional costs changes the financial problem.

## `market_impact_cost`

```python
market_impact_cost(
    quantities, *, quadratic=0.0, power_3_2=0.0, backend="numpy",
)
```

Construct or evaluate temporary impact $a|q|^2+b|q|^{3/2}$ for each trade. `quadratic` is the nonnegative finite coefficient $a$ in currency per quantity-unit squared. `power_3_2` is the nonnegative finite coefficient $b$ in currency per quantity-unit to the power `1.5`. Coefficients use the alignment rules above.

For `backend="numpy"`, quantities have the numeric types accepted by `transaction_fees`. Returns a float, ndarray, Series named `market_impact_cost`, or DataFrame, preserving the corresponding input shape and labels.

For `backend="cvxpy"`, quantities may be a real affine CVXPY expression or an array-like/Series/DataFrame of real affine scalar expressions and finite constants. The returned object is a convex CVXPY expression of the quantity shape; it is not a free cost variable or labeled pandas result. Empty expression inputs, complex or non-affine quantities, and nonfinite expression constants are rejected. Sum costs explicitly when a total objective term is required.

The accepted backends are exactly `"numpy"` and `"cvxpy"`. It does not calibrate coefficients or infer volume, volatility, permanent impact, spread, fixed fees, tax, or a quoted piecewise curve. Financial models with their own `set_market_impact` method define their supported power and curve contracts separately.

An equality between a cash variable and a convex cost expression is generally nonconvex. An epigraph is an exact financial representation only when the surrounding model makes it tight; use a formulation that preserves the intended cash accounting. See [custom models](custom-models.md), [investment planning](trading.md), and [execution scheduling](execution.md).

Invalid shapes, mismatched labels, negative coefficients, and unsupported backends raise `TypeError` or `ValueError`. Overflow in `transaction_fees` raises `ValueError`; NumPy market-impact arithmetic can raise `FloatingPointError`. Neither function changes the caller's inputs or requires authentication.
