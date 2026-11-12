"""Sparse numeric coefficients translated to public Opt expressions."""

from scipy import sparse


def export_model(model, source, return_variables):
    """Associate a detached native model with its financial expressions."""
    if not isinstance(return_variables, bool):
        raise TypeError("return_variables must be a boolean")
    if not return_variables:
        return model
    variables = {variable.name: variable for variable in model.variables()}
    return model, source._financial_variables(variables)


def linear_model(data):
    """Translate a Finance LP/MILP matrix into a public Opt Model."""
    import numpy as np
    from qpiai_opt.opt_modeller import Continuous, Integer, Model

    model = Model(data["name"])
    variables = model.add_variables(
        [
            (Integer if integer else Continuous)(name, float(low), float(high))
            for name, integer, low, high in zip(
                data["variable_names"],
                data["integrality"],
                data["lower_bounds"],
                data["upper_bounds"],
            )
        ]
    )
    coefficients = data["constraint_matrix"].tocsr()
    for i, (low, high, name) in enumerate(
        zip(data["row_lower"], data["row_upper"], data["constraint_names"])
    ):
        row = coefficients.getrow(i)
        activity = linear([variables[j] for j in row.indices], row.data)
        if low == high:
            model.add_constraint(activity == float(low), label=name)
        else:
            if np.isfinite(low):
                model.add_constraint(
                    activity >= float(low), label=f"{name}_lower"
                )
            if np.isfinite(high):
                model.add_constraint(
                    activity <= float(high), label=f"{name}_upper"
                )
    objective = linear(variables, data["objective"]) + float(
        data["objective_offset"]
    )
    if data["sense"] == "min":
        model.minimize(objective)
    else:
        model.maximize(objective)
    return model


def quadratic(variables, coefficients):
    from qpiai_opt.opt_modeller import Expression, Term

    coo = sparse.triu(sparse.csr_matrix(coefficients), format="coo")
    terms = []
    for row, column, coefficient in zip(coo.row, coo.col, coo.data):
        if coefficient == 0:
            continue
        if row != column:
            coefficient *= 2
        terms.append(
            Term(float(coefficient), [variables[row], variables[column]])
        )
    return Expression(terms=terms)


def linear(variables, coefficients):
    from qpiai_opt.opt_modeller import Expression, Term

    return Expression(
        terms=[
            Term(float(coefficient), [variable])
            for variable, coefficient in zip(variables, coefficients)
            if coefficient != 0
        ]
    )
