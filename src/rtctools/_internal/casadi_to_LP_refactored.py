from typing import Dict, Any, Tuple, List, Union, Callable
import os
import glob
import pickle
import shutil
import casadi as ca
import numpy as np
import textwrap

def load_latest_pickle(pattern: str = "nlp*.pickle") -> Tuple[Dict[str, Any], str]:
    """
    Load the latest pickle file matching the given pattern.

    Args:
        pattern (str): File pattern to match. Defaults to "nlp*.pickle".

    Returns:
        Tuple[Dict[str, Any], str]: The loaded pickle data and the extracted pickle id.
    
    Raises:
        FileNotFoundError: If no matching pickle files are found.
    """
    ps = sorted(glob.glob(pattern))
    if not ps:
        raise FileNotFoundError("No pickle files found.")
    with open(ps[-1], 'rb') as f:
        d = pickle.load(f)
    pickleid = os.path.basename(ps[-1]).split('.')[0].rsplit('_', 1)[1]
    return d, pickleid

def build_objective(expand_f_g: Callable[[ca.SX], Tuple[ca.SX, ca.SX]], var_names: List[str]) -> str:
    """
    Build the LP objective string from the symbolic function and variable names.

    Args:
        expand_f_g (Callable): A callable that takes an SX symbol and returns a tuple (f, g).
        var_names (List[str]): List of variable names.

    Returns:
        str: The formatted objective function string.
    """
    X = ca.SX.sym('X', expand_f_g.nnz_in())
    f, _ = expand_f_g(X)
    Af = ca.Function('Af', [X], [ca.jacobian(f, X)])
    bf = ca.Function('bf', [X], [f])
    
    A = Af(0)
    A = ca.sparsify(A)
    b = bf(0)
    b = ca.sparsify(b)
    
    ind = np.array(A)[0, :]
    objective = []
    for v, c in zip(var_names, ind):
        if c != 0:
            objective.extend(['+' if c > 0 else '-', str(abs(c)), v])
    if objective and objective[0] == "-":
        objective[1] = "-" + objective[1]
    if objective:
        objective.pop(0)
    objective_str = " ".join(objective)
    wrapped_objective = "\n".join(textwrap.wrap("  " + objective_str, width=255))
    return wrapped_objective

def build_constraints(expand_f_g: Callable[[ca.SX], Tuple[ca.SX, ca.SX]],
                      indices: Dict[str, Union[int, slice]],
                      lbx: List[Any],
                      ubx: List[Any],
                      lbg: List[Any],
                      ubg: List[Any],
                      var_names: List[str]) -> str:
    """
    Build the LP constraints string.

    Args:
        expand_f_g (Callable): A callable function for constraints.
        indices (Dict[str, Union[int, slice]]): Dictionary of variable indices.
        lbx (List[Any]): Lower bounds on variables.
        ubx (List[Any]): Upper bounds on variables.
        lbg (List[Any]): Lower bounds on constraints.
        ubg (List[Any]): Upper bounds on constraints.
        var_names (List[str]): List of variable names.

    Returns:
        str: The formatted constraints string.

    Raises:
        Exception: If bounds are invalid.
    """
    X = ca.SX.sym('X', expand_f_g.nnz_in())
    _, g = expand_f_g(X)
    Af = ca.Function('Af', [X], [ca.jacobian(g, X)])
    bf = ca.Function('bf', [X], [g])
    
    A = Af(0)
    A = ca.sparsify(A)
    b = bf(0)
    b = ca.sparsify(b)

    lbg = np.array(ca.veccat(*lbg))[:, 0]
    ubg = np.array(ca.veccat(*ubg))[:, 0]
    A_csc = A.tocsc()
    A_coo = A_csc.tocoo()
    b = np.array(b)[:, 0]

    constraints = [[] for _ in range(A.shape[0])]
    for i, j, c in zip(A_coo.row, A_coo.col, A_coo.data):
        constraints[i].extend(['+' if c > 0 else '-', str(abs(c)), var_names[j]])

    constraints_str_list = []
    for i, cur_constr in enumerate(constraints):
        l, u, b_i = lbg[i], ubg[i], b[i]
        if cur_constr:
            if cur_constr[0] == "-":
                cur_constr[1] = "-" + cur_constr[1]
            cur_constr.pop(0)
        c_str = " ".join(cur_constr)
        if np.isfinite(l) and np.isfinite(u) and l == u:
            constraint_line = "{} = {}".format(c_str, l - b_i)
        elif np.isfinite(l):
            constraint_line = "{} >= {}".format(c_str, l - b_i)
        elif np.isfinite(u):
            constraint_line = "{} <= {}".format(c_str, u - b_i)
        else:
            raise Exception("Invalid bounds:", l, u, b_i)
        constraints_str_list.append(constraint_line)
    constraints_str = "  " + "\n  ".join(constraints_str_list)
    return constraints_str

def build_bounds(var_names: List[str], lbx: List[Any], ubx: List[Any]) -> str:
    """
    Build the LP bounds string.

    Args:
        var_names (List[str]): List of variable names.
        lbx (List[Any]): Lower bounds on variables.
        ubx (List[Any]): Upper bounds on variables.

    Returns:
        str: The formatted bounds string.
    """
    bounds_list = []
    for v, l, u in zip(var_names, lbx, ubx):
        bounds_list.append("{} <= {} <= {}".format(l, v, u))
    bounds_str = "  " + "\n  ".join(bounds_list)
    return bounds_str

def sanitize_var_names(indices: Dict[str, Union[int, slice]], num_total: int) -> List[str]:
    """
    Sanitize and generate variable names compatible with LP solvers.

    Args:
        indices (Dict[str, Union[int, slice]]): Dictionary of indices.
        num_total (int): Total number of variables input by the function.

    Returns:
        List[str]: A list of sanitized variable names.
    """
    var_names = []
    for k, v in indices.items():
        if isinstance(v, int):
            var_names.append('{}__{}'.format(k, v))
        else:
            for i in range(0, v.stop - v.start, 1 if v.step is None else v.step):
                var_names.append('{}__{}'.format(k, i))
    n_derivatives = num_total - len(var_names)
    for i in range(n_derivatives):
        var_names.append("DERIVATIVE__{}".format(i))
    # CPLEX does not like [] in variable names
    for i, v in enumerate(var_names):
        v = v.replace("[", "_I").replace("]", "I_")
        var_names[i] = v
    return var_names

def write_lp_file(pickleid: str,
                  objective_str: str,
                  constraints_str: str,
                  bounds_str: str,
                  var_names: List[str],
                  discrete: List[bool]) -> None:
    """
    Write the LP file according to the LP format and copy it.

    Args:
        pickleid (str): Identifier for the pickle.
        objective_str (str): The objective function string.
        constraints_str (str): The constraints string.
        bounds_str (str): The bounds string.
        var_names (List[str]): List of variable names.
        discrete (List[bool]): Boolean list indicating discrete variables.
    """
    filename = "myproblem_{}.lp".format(pickleid)
    with open(filename, 'w') as o:
        o.write("Minimize\n")
        o.write(objective_str + "\n")
        o.write("Subject To\n")
        o.write(constraints_str + "\n")
        o.write("Bounds\n")
        o.write(bounds_str + "\n")
        if any(discrete):
            o.write("General\n")
            discrete_vars = "\n".join(v for v, is_discrete in zip(var_names, discrete) if is_discrete)
            o.write(discrete_vars + "\n")
        o.write("End")
    shutil.copy(filename, "myproblem.lp")

def main() -> None:
    """
    Main function to load data, build LP components, and write the LP file.
    """
    d, pickleid = load_latest_pickle()
    
    indices = d['indices'][0]
    expand_f_g = d['func']
    lbx, ubx, lbg, ubg, x0 = d['other']
    
    num_total = expand_f_g.nnz_in()
    var_names = sanitize_var_names(indices, num_total)
    
    obj_str = build_objective(expand_f_g, var_names)
    constr_str = build_constraints(expand_f_g, indices, lbx, ubx, lbg, ubg, var_names)
    bounds_str = build_bounds(var_names, lbx, ubx)
    
    write_lp_file(pickleid, obj_str, constr_str, bounds_str, var_names, d['discrete'])

if __name__ == "__main__":
    main()