# Risk estimates and portfolio analytics

Risk functions prepare financial model inputs, construct risk terms, and explain decisions. They preserve the supplied horizon and units. Import them from `qpiai_finance.risk`; none authenticates or submits a job.

Use [data conventions](data.md) for numeric types, alignment, and covariance validation. A labeled vector accepts a pandas Series or mapping; an unlabeled vector follows the corresponding asset or scenario order. Functions reject incompatible shapes, missing labels, nonfinite values, and invalid parameter domains with `TypeError` or `ValueError`.

Variance calculations also check the evaluated quadratic form. A negative value below `-1e-12 * sum(abs(w_i) * abs((covariance @ w)_i))` raises `ValueError`; a negative value within that tolerance is reported as zero. `FactorRisk.risk_contributions` applies the same check to its factor and specific-risk component exposures and covariance products. Passing covariance validation does not guarantee that every position passes this directional check, because matrix validation permits small negative eigenvalues without repairing them.

## Loss-tail risk

A positive loss denotes a loss; negative values denote gains. Finance does not clip negative VaR or expected shortfall to zero. For weighted losses $L_s$ and confidence $\beta$, expected shortfall is the mean of the upper loss tail of probability $1-\beta$, including fractional probability at the boundary.

$$
\operatorname{ES}_{\beta}(L)=\min_{\eta}\left[\eta+\frac{1}{1-\beta}\sum_s p_s\max(L_s-\eta,0)\right].
$$

Financial expected shortfall describes loss scenarios. The lower-energy-tail aggregation configured in some gate-based algorithms describes optimization samples and uses a different sign and tail convention.

### `value_at_risk` and `expected_shortfall`

```python
value_at_risk(losses, *, confidence=0.95, probabilities=None)
expected_shortfall(losses, *, confidence=0.95, probabilities=None)
```

| Parameter | Type and meaning |
| --- | --- |
| `losses` | Nonempty one-dimensional finite real array, Series, or mapping; all losses use one financial unit. |
| `confidence` | Finite real scalar strictly between `0` and `1`; default `0.95`. |
| `probabilities` | Matching vector, Series, or mapping of nonnegative probabilities summing to one within absolute `1e-12`; omitted means equal probabilities. |

Both return a float in loss units. Zero-probability scenarios are excluded. Supplied probability ratios determine normalized probability masses. VaR uses the left inverse CDF: the smallest loss whose cumulative probability is at least `confidence`, without interpolation. Expected shortfall includes only the required fraction of the probability mass at the VaR boundary. Averaging a rounded number of worst observations generally gives a different result.

### `expected_shortfall_epigraph`

```python
expected_shortfall_epigraph(
    losses, *, probabilities, confidence=0.95, scenario_ids=None,
    name="expected_shortfall", backend="opt",
)
```

Build an expected-shortfall upper bound for a custom model. Returns `(upper_bound, constraints)` without mutating a model or objective.

| Parameter | Type and meaning |
| --- | --- |
| `losses` | One-dimensional sequence, Series, or mapping of finite constants or affine Opt expressions for `backend="opt"`. For `"cvxpy"`, convex scalar expressions or a convex CVXPY vector expression are accepted. |
| `probabilities` | Required probability vector with the same validation as above. Labeled probabilities align to scenario identifiers. |
| `confidence` | Tail confidence in `(0, 1)`. |
| `scenario_ids` | Optional nonempty unique string/integer identifiers; inferred from labeled losses or assigned positional integers otherwise. |
| `name` | Nonempty single-line variable-name prefix, excluding NUL, carriage return, and newline. Use a distinct name for each risk block. |
| `backend` | `"opt"` or `"cvxpy"`; default `"opt"`. |

The construction introduces an unrestricted threshold $\eta$ and nonnegative excess variables $u_s$ with $\eta+u_s\geq L_s$. The upper bound is $\eta+\sum_s p_su_s/(1-\beta)$. Add every returned constraint to the destination model. Minimize the bound, give it a nonnegative weight in a minimization objective, or constrain it from above. Maximizing this epigraph or imposing a lower bound on it does not optimize or bound actual expected shortfall correctly. Zero-probability stress scenarios need separate hard stress limits.

For Opt, returns an Opt expression and list of constraints. For CVXPY, returns a scalar expression and list of constraints. Evaluate actual risk from the recovered financial decision with `expected_shortfall` after solving. Unsupported curvature, dimensions, backend names, and invalid probabilities raise `ValueError`.

## Return estimates

### `sample_moments`

```python
sample_moments(returns)
```

Accepts a finite observation × asset array or DataFrame; a one-dimensional array or Series denotes one asset. At least two observations and one asset are required. A DataFrame must have unique increasing time labels and valid asset columns. A Series is treated as a single-column DataFrame; its name becomes the asset identifier and must be valid. An unnamed Series uses asset identifier `0`.

Returns `(expected_returns, covariance)` as a Series named `expected_return` and a square DataFrame. DataFrame columns define asset identifiers; arrays use positional integer identifiers. The mean is the arithmetic sample mean; covariance uses the `T-1` denominator. The function neither imputes missing observations nor annualizes estimates.

### `exponential_moments`

```python
exponential_moments(returns, *, decay, unbiased=True)
```

Accepts the same observations as `sample_moments`. `decay` is a finite real scalar in `(0, 1]`. For `T` rows, weights are proportional to `decay**(T-1-t)`; the newest row has unnormalized weight one. `decay=1` gives uniform weights.

`unbiased` is a Python boolean. With `True`, weighted covariance divides the weighted centered second moment by $1-\sum_t p_t^2$ under the independent-observation interpretation. This denominator must exceed binary64 machine epsilon (`2**-52`); otherwise effective observations are insufficient and the function raises `ValueError`. With `False`, it returns the population weighted second moment. The function does not substitute another estimator. Return types, labels, and horizon follow `sample_moments`.

### `shrink_covariance`

```python
shrink_covariance(covariance, *, intensity, target=None)
```

Returns $(1-\delta)\Sigma+\delta F$, where `intensity` is the supplied scalar $\delta\in[0,1]`. Both `covariance` and optional `target` must be valid, aligned covariance matrices. With `target=None`, $F$ is the diagonal of the supplied covariance. Intensity is explicit; the function does not estimate a Ledoit–Wolf coefficient.

A DataFrame or column-mapping covariance retains its labels and returns a DataFrame. Otherwise, dense inputs return an ndarray, sparse inputs with a sparse/default target retain a sparse result, and mixing dense and sparse inputs yields a dense result. The operation is shrinkage between valid risk models, not a repair of an invalid covariance matrix.

## Factor covariance

### `FactorRisk`

```python
FactorRisk(
    exposures, factor_covariance, specific_variance, *,
    asset_ids=None, factor_ids=None,
)
```

Represent $\Sigma=BFB^\top+\operatorname{diag}(d)$ without constructing a dense asset covariance matrix.

| Parameter | Type and meaning |
| --- | --- |
| `exposures` | Asset × factor DataFrame, column mapping, dense array, or sparse matrix $B$. |
| `factor_covariance` | Factor × factor covariance $F$; finite, symmetric, and PSD under the covariance validation rules. Supports labeled, dense, or sparse input. |
| `specific_variance` | Nonnegative finite vector $d$ with one value per asset; Series, mapping, or array. |
| `asset_ids` | Optional unique asset identifiers; inferred from exposure rows or assigned positional integers. |
| `factor_ids` | Optional unique factor identifiers; inferred from exposure columns or assigned positional integers. |

The `asset_ids` property returns a detached pandas Index. Matrices and vectors align to these asset and factor orders. Factor covariance and specific variances must use compatible horizon and exposure units.

```python
risk.apply(weights)
risk.factor_exposures(weights)
risk.risk_contributions(weights)
```

All three accept a finite vector, Series, or mapping of weights. No weight normalization is performed. `apply` returns an ndarray equal to $\Sigma w$. `factor_exposures` returns a Series named `exposure`, indexed by factor identifiers, equal to $B^\top w$.

`risk_contributions` returns a DataFrame indexed by `(component, id)`, with `component` equal to `factor` or `specific`, and columns `exposure`, `variance`, and `volatility`. Factor variance contribution is $e_k(Fe)_k$ for $e=B^\top w$; asset-specific contribution is $d_iw_i^2$. Contributions sum to portfolio variance. Volatility contributions divide by portfolio volatility and are NaN at zero volatility. Correlated factors can have negative contributions. These operations preserve the factor representation and reject unrepresentable output values.

## Portfolio metrics

### `risk_contributions`

```python
risk_contributions(weights, covariance)
```

`weights` is a finite asset vector, Series, or mapping. `covariance` is an aligned covariance DataFrame, column mapping, dense/sparse matrix, or `FactorRisk`. Returns a DataFrame indexed by asset identifiers with `variance` and `volatility` columns.

Asset variance contribution is $w_i(\Sigma w)_i$; it sums to $w^\top\Sigma w$. Asset volatility contribution divides this quantity by $\sqrt{w^\top\Sigma w}$ and is NaN when total volatility is zero. Contributions can be negative for hedged positions. Weights are not normalized.

### `portfolio_metrics`

```python
portfolio_metrics(weights, covariance, *, expected_returns=None, benchmark=None)
```

Accepts the same weight and covariance types as `risk_contributions`. Optional `expected_returns` and `benchmark` are aligned finite asset vectors, Series, or mappings. A labeled covariance defines asset order; otherwise labeled weights define it, followed by positional integer order for arrays. `FactorRisk` supplies its own asset order.

Returns a dictionary of floats:

| Key | Meaning |
| --- | --- |
| `variance` | $w^\top\Sigma w$. |
| `volatility` | Square root of variance. |
| `gross_exposure` | $\sum_i\lvert w_i\rvert$. |
| `net_exposure` | $\sum_iw_i$. |
| `expected_return` | $\mu^\top w$; present when returns are supplied. |
| `tracking_error` | $\sqrt{(w-b)^\top\Sigma(w-b)}$; present when a benchmark is supplied. |
| `active_return` | $\mu^\top(w-b)$; present when returns and benchmark are supplied. |
| `beta` | $b^\top\Sigma w/(b^\top\Sigma b)$; present with a benchmark and NaN for a zero-variance benchmark. |

No market proxy, annualization, cash return, transaction costs, or normalization is inferred. All quantities describe the supplied weight basis and horizon.

## Black–Litterman estimates

```python
black_litterman(prior, covariance, views, view_returns, view_covariance, *, tau)
```

Combine Gaussian prior expectations with supplied linear views. This function estimates inputs; it does not select portfolio weights.

| Parameter | Type and meaning |
| --- | --- |
| `prior` | Asset mean vector $\pi$; Series, mapping, or array. |
| `covariance` | Asset return covariance $\Sigma$; aligned DataFrame, column mapping, dense array, or sparse matrix. |
| `views` | View × asset matrix $P$; DataFrame, column mapping, dense array, or sparse matrix. |
| `view_returns` | View mean vector $q$; Series, mapping, or array. |
| `view_covariance` | View-noise covariance $\Omega$; aligned square DataFrame, column mapping, dense array, or sparse matrix. |
| `tau` | Required positive finite scalar; prior mean covariance is $C=\tau\Sigma$. |

A labeled prior defines asset order; otherwise a labeled covariance defines the prior array's order. Labeled view rows define view order; for array views, labeled view returns or view covariance define it, followed by positional order. All inputs must share compatible horizon and units. Covariance inputs must satisfy PSD validation, and $PCP^\top+\Omega$ must be positive definite.

The posterior mean is $\pi+CP^\top(PCP^\top+\Omega)^{-1}(q-P\pi)$. The function uses linear-system calculations and returns:

| Key | Type and meaning |
| --- | --- |
| `expected_returns` | Asset-indexed Series of posterior means. |
| `mean_covariance` | Asset × asset DataFrame of posterior uncertainty in the mean. |
| `predictive_covariance` | Asset × asset DataFrame equal to return covariance plus posterior mean uncertainty. |

`mean_covariance` alone is not the predictive return covariance. Sparse inputs are converted to dense matrices for this calculation. Invalid observation-system definiteness or unrepresentable posterior values raise `ValueError`.
