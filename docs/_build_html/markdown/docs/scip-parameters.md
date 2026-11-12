# SCIP parameter catalogue

This catalogue covers all 3,082 native parameters in SCIP 10.0.2. Pass values through `scip_params` as described in the [solver option reference](solver-options.md#scip-controls). The native build determines available plugins and parameter names; another installed build can have a different catalogue.

Each row gives the native type, allowed range, default, advanced flag, and parameter description. `bool` maps to Python `bool`; `int` and `longint` to Python `int`; `real` to Python `float`; `char` to a one-character string; `string` to Python `str`. Character sets list allowed individual characters. Brackets give inclusive numeric endpoints. Special sentinels such as `-1` retain the meaning stated in the description. Defaults below are native defaults; Finance and CVXPY overrides are listed in the solver reference.

Descriptions and metadata follow the installed solver's public parameter records. The [SCIP parameter documentation](https://www.scipopt.org/doc/html/PARAMETERS.php) explains the native configuration model.

## benders

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `benders/solutiontol` | `real` | [0,1.79769313486232e+308] | 1e-06 | False | the tolerance used for checking optimality in Benders' decomposition. tol where optimality is given by LB + tol &gt; UB. |
| `benders/cutlpsol` | `bool` | {TRUE,FALSE} | TRUE | False | should Benders' cuts be generated from the solution to the LP relaxation? |
| `benders/copybenders` | `bool` | {TRUE,FALSE} | TRUE | False | should Benders' decomposition be copied for use in sub-SCIPs? |
| `benders/default/priority` | `int` | [-536870912,536870911] | 0 | False | priority of Benders' decomposition &lt;default&gt; |
| `benders/default/cutlp` | `bool` | {TRUE,FALSE} | TRUE | False | should Benders' cuts be generated for LP solutions? |
| `benders/default/cutpseudo` | `bool` | {TRUE,FALSE} | TRUE | False | should Benders' cuts be generated for pseudo solutions? |
| `benders/default/cutrelax` | `bool` | {TRUE,FALSE} | TRUE | False | should Benders' cuts be generated for relaxation solutions? |
| `benders/default/transfercuts` | `bool` | {TRUE,FALSE} | FALSE | False | should Benders' cuts from LNS heuristics be transferred to the main SCIP instance? |
| `benders/default/lnscheck` | `bool` | {TRUE,FALSE} | TRUE | False | should Benders' decomposition be used in LNS heurisics? |
| `benders/default/lnsmaxdepth` | `int` | [-1,1073741822] | -1 | True | maximum depth at which the LNS check is performed (-1: no limit) |
| `benders/default/lnsmaxcalls` | `int` | [-1,2147483647] | 10 | True | the maximum number of Benders' decomposition calls in LNS heuristics (-1: no limit) |
| `benders/default/lnsmaxcallsroot` | `int` | [-1,2147483647] | 0 | True | the maximum number of root node Benders' decomposition calls in LNS heuristics (-1: no limit) |
| `benders/default/cutsasconss` | `bool` | {TRUE,FALSE} | TRUE | False | should the transferred cuts be added as constraints? |
| `benders/default/subprobfrac` | `real` | [0,1] | 1 | False | fraction of subproblems that are solved in each iteration |
| `benders/default/updateauxvarbound` | `bool` | {TRUE,FALSE} | FALSE | False | should the auxiliary variable bound be updated by solving the subproblem? |
| `benders/default/auxvarsimplint` | `bool` | {TRUE,FALSE} | FALSE | False | if the subproblem objective is integer, then define the auxiliary variables as implicit integers? |
| `benders/default/cutcheck` | `bool` | {TRUE,FALSE} | TRUE | False | should Benders' cuts be generated while checking solutions? |
| `benders/default/cutstrengthenmult` | `real` | [0,1] | 0.5 | False | the convex combination multiplier for the cut strengthening |
| `benders/default/noimprovelimit` | `int` | [0,2147483647] | 5 | True | the maximum number of cut strengthening without improvement |
| `benders/default/corepointperturb` | `real` | [0,1] | 1e-06 | False | the constant use to perturb the cut strengthening core point |
| `benders/default/cutstrengthenenabled` | `bool` | {TRUE,FALSE} | FALSE | False | should the core point cut strengthening be employed (only applied to fractional solutions or continuous subproblems)? |
| `benders/default/cutstrengthenintpoint` | `char` | {lfiroz} | r | False | where should the strengthening interior point be sourced from ('l'p relaxation, 'f'irst solution, 'i'ncumbent solution, 'r'elative interior point, vector of 'o'nes, vector of 'z'eros) |
| `benders/default/execfeasphase` | `bool` | {TRUE,FALSE} | FALSE | False | should a feasibility phase be executed during the root node, i.e. adding slack variables to constraints to ensure feasibility |
| `benders/default/slackvarcoef` | `real` | [0,1e+20] | 1000000 | False | the initial objective coefficient of the slack variables in the subproblem |
| `benders/default/maxslackvarcoef` | `real` | [0,1e+20] | 1000000000 | False | the maximal objective coefficient of the slack variables in the subproblem |
| `benders/default/checkconsconvexity` | `bool` | {TRUE,FALSE} | TRUE | False | should the constraints of the subproblems be checked for convexity? |
| `benders/default/nlpiterlimit` | `int` | [0,2147483647] | 10000 | False | iteration limit for NLP solver |
| `benders/default/benderscut/feas/priority` | `int` | [-536870912,536870911] | 10000 | True | priority of Benders' cut &lt;feas&gt; |
| `benders/default/benderscut/feas/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | is this Benders' decomposition cut method used to generate cuts? |
| `benders/default/benderscut/feasalt/priority` | `int` | [-536870912,536870911] | 10001 | True | priority of Benders' cut &lt;feasalt&gt; |
| `benders/default/benderscut/feasalt/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | is this Benders' decomposition cut method used to generate cuts? |
| `benders/default/benderscut/integer/priority` | `int` | [-536870912,536870911] | 0 | True | priority of Benders' cut &lt;integer&gt; |
| `benders/default/benderscut/integer/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | is this Benders' decomposition cut method used to generate cuts? |
| `benders/default/benderscut/integer/cutsconstant` | `real` | [-1e+20,1e+20] | -10000 | False | the constant term of the integer Benders' cuts. |
| `benders/default/benderscut/integer/addcuts` | `bool` | {TRUE,FALSE} | FALSE | False | should cuts be generated and added to the cutpool instead of global constraints directly added to the problem. |
| `benders/default/benderscut/nogood/priority` | `int` | [-536870912,536870911] | 500 | True | priority of Benders' cut &lt;nogood&gt; |
| `benders/default/benderscut/nogood/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | is this Benders' decomposition cut method used to generate cuts? |
| `benders/default/benderscut/nogood/addcuts` | `bool` | {TRUE,FALSE} | FALSE | False | should cuts be generated and added to the cutpool instead of global constraints directly added to the problem. |
| `benders/default/benderscut/optimality/priority` | `int` | [-536870912,536870911] | 5000 | True | priority of Benders' cut &lt;optimality&gt; |
| `benders/default/benderscut/optimality/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | is this Benders' decomposition cut method used to generate cuts? |
| `benders/default/benderscut/optimality/addcuts` | `bool` | {TRUE,FALSE} | FALSE | False | should cuts be generated and added to the cutpool instead of global constraints directly added to the problem. |
| `benders/default/benderscut/optimality/mir` | `bool` | {TRUE,FALSE} | TRUE | False | should the mixed integer rounding procedure be applied to cuts |

## branching

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `branching/scorefunc` | `char` | {spq} | p | True | branching score function ('s'um, 'p'roduct, 'q'uotient) |
| `branching/scorefac` | `real` | [0,1] | 0.167 | True | branching score factor to weigh downward and upward gain prediction in sum score function |
| `branching/preferbinary` | `bool` | {TRUE,FALSE} | FALSE | False | should branching on binary variables be preferred? |
| `branching/clamp` | `real` | [0,0.5] | 0.2 | False | minimal relative distance of branching point to bounds when branching on a continuous variable |
| `branching/midpull` | `real` | [0,1] | 0.75 | False | fraction by which to move branching point of a continuous variable towards the middle of the domain; a value of 1.0 leads to branching always in the middle of the domain |
| `branching/midpullreldomtrig` | `real` | [0,1] | 0.5 | False | multiply midpull by relative domain width if the latter is below this value |
| `branching/lpgainnormalize` | `char` | {dls} | s | False | strategy for normalization of LP gain when updating pseudocosts of continuous variables (divide by movement of 'l'p value, reduction in 'd'omain width, or reduction in domain width of 's'ibling) |
| `branching/delaypscostupdate` | `bool` | {TRUE,FALSE} | TRUE | False | should updating pseudo costs for continuous variables be delayed to the time after separation? |
| `branching/divingpscost` | `bool` | {TRUE,FALSE} | TRUE | False | should pseudo costs be updated also in diving and probing mode? |
| `branching/collectancpscost` | `bool` | {TRUE,FALSE} | FALSE | False | should ancestral pseudo costs be updated? |
| `branching/forceallchildren` | `bool` | {TRUE,FALSE} | FALSE | True | should all strong branching children be regarded even if one is detected to be infeasible? (only with propagation) |
| `branching/firstsbchild` | `char` | {aduh} | a | True | child node to be regarded first during strong branching (only with propagation): 'u'p child, 'd'own child, 'h'istory-based, or 'a'utomatic |
| `branching/checksol` | `bool` | {TRUE,FALSE} | TRUE | True | should LP solutions during strong branching with propagation be checked for feasibility? |
| `branching/roundsbsol` | `bool` | {TRUE,FALSE} | TRUE | True | should LP solutions during strong branching with propagation be rounded? (only when checksbsol=TRUE) |
| `branching/sumadjustscore` | `bool` | {TRUE,FALSE} | FALSE | True | score adjustment near zero by adding epsilon (TRUE) or using maximum (FALSE) |
| `branching/relpscost/priority` | `int` | [-536870912,536870911] | 10000 | False | priority of branching rule &lt;relpscost&gt; |
| `branching/relpscost/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;relpscost&gt; should be used (-1 for no limit) |
| `branching/relpscost/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/relpscost/conflictweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 0.01 | True | weight in score calculations for conflict score |
| `branching/relpscost/conflictlengthweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 0 | True | weight in score calculations for conflict length score |
| `branching/relpscost/inferenceweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 0.0001 | True | weight in score calculations for inference score |
| `branching/relpscost/cutoffweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 0.0001 | True | weight in score calculations for cutoff score |
| `branching/relpscost/gmiavgeffweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 0 | True | weight in score calculations for average GMI cuts normalized efficacy |
| `branching/relpscost/gmilasteffweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1e-05 | True | weight in score calculations for last GMI cuts normalized efficacy |
| `branching/relpscost/pscostweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1 | True | weight in score calculations for pseudo cost score |
| `branching/relpscost/nlscoreweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 0.1 | True | weight in score calculations for nlcount score |
| `branching/relpscost/minreliable` | `real` | [0,1.79769313486232e+308] | 1 | True | minimal value for minimum pseudo cost size to regard pseudo cost value as reliable |
| `branching/relpscost/maxreliable` | `real` | [0,1.79769313486232e+308] | 5 | True | maximal value for minimum pseudo cost size to regard pseudo cost value as reliable |
| `branching/relpscost/sbiterquot` | `real` | [0,1.79769313486232e+308] | 0.5 | False | maximal fraction of strong branching LP iterations compared to node relaxation LP iterations |
| `branching/relpscost/dynamiclookaheadquot` | `real` | [0,1] | 0.6 | True | apply dynamic lookahead after this fraction maxlookahead is reached |
| `branching/relpscost/sbiterofs` | `int` | [0,2147483647] | 100000 | False | additional number of allowed strong branching LP iterations |
| `branching/relpscost/maxlookahead` | `int` | [1,2147483647] | 9 | True | maximal number of further variables evaluated without better score |
| `branching/relpscost/dynamiclookahead` | `bool` | {TRUE,FALSE} | FALSE | True | should we use a dynamic lookahead based on a tree size estimation of further strong branchings? |
| `branching/relpscost/initcand` | `int` | [0,2147483647] | 100 | False | maximal number of candidates initialized with strong branching per node |
| `branching/relpscost/dynamiclookdistribution` | `int` | [0,2] | 1 | True | which distribution should be used for dynamic lookahead? 0=exponential, 1=Pareto, 2=log-normal? |
| `branching/relpscost/inititer` | `int` | [0,2147483647] | 0 | False | iteration limit for strong branching initializations of pseudo cost entries (0: auto) |
| `branching/relpscost/maxbdchgs` | `int` | [-1,2147483647] | 5 | True | maximal number of bound tightenings before the node is reevaluated (-1: unlimited) |
| `branching/relpscost/maxproprounds` | `int` | [-2,2147483647] | -2 | True | maximum number of propagation rounds to be performed during strong branching before solving the LP (-1: no limit, -2: parameter settings) |
| `branching/relpscost/probingbounds` | `bool` | {TRUE,FALSE} | TRUE | True | should valid bounds be identified in a probing-like fashion during strong branching (only with propagation)? |
| `branching/relpscost/userelerrorreliability` | `bool` | {TRUE,FALSE} | FALSE | True | should reliability be based on relative errors? |
| `branching/relpscost/lowerrortol` | `real` | [0,1.79769313486232e+308] | 0.05 | True | low relative error tolerance for reliability |
| `branching/relpscost/higherrortol` | `real` | [0,1.79769313486232e+308] | 1 | True | high relative error tolerance for reliability |
| `branching/relpscost/storesemiinitcosts` | `bool` | {TRUE,FALSE} | FALSE | True | should strong branching result be considered for pseudo costs if the other direction was infeasible? |
| `branching/relpscost/usesblocalinfo` | `bool` | {TRUE,FALSE} | FALSE | True | should the scoring function use only local cutoff and inference information obtained for strong branching candidates? |
| `branching/relpscost/usehyptestforreliability` | `bool` | {TRUE,FALSE} | FALSE | True | should the strong branching decision be based on a hypothesis test? |
| `branching/relpscost/usedynamicconfidence` | `bool` | {TRUE,FALSE} | FALSE | True | should the confidence level be adjusted dynamically? |
| `branching/relpscost/skipbadinitcands` | `bool` | {TRUE,FALSE} | TRUE | True | should branching rule skip candidates that have a low probability to be better than the best strong-branching or pseudo-candidate? |
| `branching/relpscost/confidencelevel` | `int` | [0,4] | 2 | True | the confidence level for statistical methods, between 0 (Min) and 4 (Max). |
| `branching/relpscost/randinitorder` | `bool` | {TRUE,FALSE} | FALSE | True | should candidates be initialized in randomized order? |
| `branching/relpscost/usesmallweightsitlim` | `bool` | {TRUE,FALSE} | FALSE | True | should smaller weights be used for pseudo cost updates after hitting the LP iteration limit? |
| `branching/relpscost/dynamicweights` | `bool` | {TRUE,FALSE} | TRUE | True | should the weights of the branching rule be adjusted dynamically during solving based on objective and infeasible leaf counters? |
| `branching/relpscost/degeneracyaware` | `int` | [0,2] | 1 | True | should degeneracy be taken into account to update weights and skip strong branching? (0: off, 1: after root, 2: always) |
| `branching/relpscost/startrandseed` | `int` | [0,2147483647] | 5 | True | start seed for random number generation |
| `branching/relpscost/minsamplesize` | `int` | [0,2147483647] | 10 | True | minimum sample size to estimate the tree size for dynamic lookahead |
| `branching/relpscost/filtercandssym` | `bool` | {TRUE,FALSE} | FALSE | True | Use symmetry to filter branching candidates? |
| `branching/relpscost/transsympscost` | `bool` | {TRUE,FALSE} | FALSE | True | Transfer pscost information to symmetric variables? |
| `branching/relpscost/discountfactor` | `real` | [0,1] | 0.2 | False | discount factor for ancestral pseudo costs (0.0: disable discounted pseudo costs) |
| `branching/treemodel/enable` | `bool` | {TRUE,FALSE} | FALSE | False | should candidate branching variables be scored using the Treemodel branching rules? |
| `branching/treemodel/highrule` | `char` | {dsrt} | r | False | scoring function to use at nodes predicted to be high in the tree ('d'efault, 's'vts, 'r'atio, 't'ree sample) |
| `branching/treemodel/lowrule` | `char` | {dsrt} | r | False | scoring function to use at nodes predicted to be low in the tree ('d'efault, 's'vts, 'r'atio, 't'ree sample) |
| `branching/treemodel/height` | `int` | [0,2147483647] | 10 | False | estimated tree height at which we switch from using the low rule to the high rule |
| `branching/treemodel/filterhigh` | `char` | {atf} | a | True | should dominated candidates be filtered before using the high scoring function? ('a'uto, 't'rue, 'f'alse) |
| `branching/treemodel/filterlow` | `char` | {atf} | a | True | should dominated candidates be filtered before using the low scoring function? ('a'uto, 't'rue, 'f'alse) |
| `branching/treemodel/maxfpiter` | `int` | [1,2147483647] | 24 | True | maximum number of fixed-point iterations when computing the ratio |
| `branching/treemodel/maxsvtsheight` | `int` | [0,2147483647] | 100 | True | maximum height to compute the SVTS score exactly before approximating |
| `branching/treemodel/fallbackinf` | `char` | {dr} | r | True | which method should be used as a fallback if the tree size estimates are infinite? ('d'efault, 'r'atio) |
| `branching/treemodel/fallbacknoprim` | `char` | {dr} | r | True | which method should be used as a fallback if there is no primal bound available? ('d'efault, 'r'atio) |
| `branching/treemodel/smallpscost` | `real` | [0,1.79769313486232e+308] | 0.1 | True | threshold at which pseudocosts are considered small, making hybrid scores more likely to be the deciding factor in branching |
| `branching/pscost/priority` | `int` | [-536870912,536870911] | 2000 | False | priority of branching rule &lt;pscost&gt; |
| `branching/pscost/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;pscost&gt; should be used (-1 for no limit) |
| `branching/pscost/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/pscost/strategy` | `char` | {dsuv} | u | False | strategy for utilizing pseudo-costs of external branching candidates (multiply as in pseudo costs 'u'pdate rule, or by 'd'omain reduction, or by domain reduction of 's'ibling, or by 'v'ariable score) |
| `branching/pscost/minscoreweight` | `real` | [-1e+20,1e+20] | 0.8 | True | weight for minimum of scores of a branching candidate when building weighted sum of min/max/sum of scores |
| `branching/pscost/maxscoreweight` | `real` | [-1e+20,1e+20] | 1.3 | True | weight for maximum of scores of a branching candidate when building weighted sum of min/max/sum of scores |
| `branching/pscost/sumscoreweight` | `real` | [-1e+20,1e+20] | 0.1 | True | weight for sum of scores of a branching candidate when building weighted sum of min/max/sum of scores |
| `branching/pscost/nchildren` | `int` | [2,2147483647] | 2 | False | number of children to create in n-ary branching |
| `branching/pscost/narymaxdepth` | `int` | [-1,2147483647] | -1 | False | maximal depth where to do n-ary branching, -1 to turn off |
| `branching/pscost/naryminwidth` | `real` | [0,1] | 0.001 | False | minimal domain width in children when doing n-ary branching, relative to global bounds |
| `branching/pscost/narywidthfactor` | `real` | [1,1.79769313486232e+308] | 2 | False | factor of domain width in n-ary branching when creating nodes with increasing distance from branching value |
| `branching/pscost/discountfactor` | `real` | [0,1] | 0.2 | False | discount factor for ancestral pseudo costs (0.0: disable discounted pseudo costs) |
| `branching/inference/priority` | `int` | [-536870912,536870911] | 1000 | False | priority of branching rule &lt;inference&gt; |
| `branching/inference/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;inference&gt; should be used (-1 for no limit) |
| `branching/inference/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/inference/conflictweight` | `real` | [0,1.79769313486232e+308] | 1000 | True | weight in score calculations for conflict score |
| `branching/inference/inferenceweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1 | True | weight in score calculations for inference score |
| `branching/inference/cutoffweight` | `real` | [0,1.79769313486232e+308] | 1 | True | weight in score calculations for cutoff score |
| `branching/inference/fractionals` | `bool` | {TRUE,FALSE} | TRUE | True | should branching on LP solution be restricted to the fractional variables? |
| `branching/inference/useweightedsum` | `bool` | {TRUE,FALSE} | TRUE | False | should a weighted sum of inference, conflict and cutoff weights be used? |
| `branching/inference/reliablescore` | `real` | [0,1.79769313486232e+308] | 0.001 | True | weight in score calculations for conflict score |
| `branching/inference/conflictprio` | `int` | [0,2147483647] | 1 | False | priority value for using conflict weights in lex. order |
| `branching/inference/cutoffprio` | `int` | [0,2147483647] | 1 | False | priority value for using cutoff weights in lex. order |
| `branching/mostinf/priority` | `int` | [-536870912,536870911] | 100 | False | priority of branching rule &lt;mostinf&gt; |
| `branching/mostinf/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;mostinf&gt; should be used (-1 for no limit) |
| `branching/mostinf/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/leastinf/priority` | `int` | [-536870912,536870911] | 50 | False | priority of branching rule &lt;leastinf&gt; |
| `branching/leastinf/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;leastinf&gt; should be used (-1 for no limit) |
| `branching/leastinf/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/fullstrong/priority` | `int` | [-536870912,536870911] | 0 | False | priority of branching rule &lt;fullstrong&gt; |
| `branching/fullstrong/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;fullstrong&gt; should be used (-1 for no limit) |
| `branching/fullstrong/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/fullstrong/reevalage` | `longint` | [0,9223372036854775807] | 10 | True | number of intermediate LPs solved to trigger reevaluation of strong branching value for a variable that was already evaluated at the current node |
| `branching/fullstrong/maxproprounds` | `int` | [-3,2147483647] | -2 | True | maximum number of propagation rounds to be performed during strong branching before solving the LP (-1: no limit, -2: parameter settings) |
| `branching/fullstrong/probingbounds` | `bool` | {TRUE,FALSE} | TRUE | True | should valid bounds be identified in a probing-like fashion during strong branching (only with propagation)? |
| `branching/fullstrong/forcestrongbranch` | `bool` | {TRUE,FALSE} | FALSE | True | should strong branching be applied even if there is just a single candidate? |
| `branching/distribution/priority` | `int` | [-536870912,536870911] | 0 | False | priority of branching rule &lt;distribution&gt; |
| `branching/distribution/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;distribution&gt; should be used (-1 for no limit) |
| `branching/distribution/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/distribution/scoreparam` | `char` | {dhlvw} | v | True | the score;largest 'd'ifference, 'l'owest cumulative probability,'h'ighest c.p., 'v'otes lowest c.p., votes highest c.p.('w')  |
| `branching/distribution/onlyactiverows` | `bool` | {TRUE,FALSE} | FALSE | True | should only rows which are active at the current node be considered? |
| `branching/distribution/weightedscore` | `bool` | {TRUE,FALSE} | FALSE | True | should the branching score weigh up- and down-scores of a variable |
| `branching/lookahead/priority` | `int` | [-536870912,536870911] | 0 | False | priority of branching rule &lt;lookahead&gt; |
| `branching/lookahead/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;lookahead&gt; should be used (-1 for no limit) |
| `branching/lookahead/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/lookahead/useimpliedbincons` | `bool` | {TRUE,FALSE} | FALSE | True | should binary constraints be collected and applied? |
| `branching/lookahead/addbinconsrow` | `int` | [0,2] | 0 | True | should binary constraints be added as rows to the base LP? (0: no, 1: separate, 2: as initial rows) |
| `branching/lookahead/maxnviolatedcons` | `int` | [0,2147483647] | 1 | True | how many constraints that are violated by the base lp solution should be gathered until the rule is stopped and they are added? [0 for unrestricted] |
| `branching/lookahead/maxnviolatedbincons` | `int` | [0,2147483647] | 0 | True | how many binary constraints that are violated by the base lp solution should be gathered until the rule is stopped and they are added? [0 for unrestricted] |
| `branching/lookahead/maxnviolateddomreds` | `int` | [0,2147483647] | 1 | True | how many domain reductions that are violated by the base lp solution should be gathered until the rule is stopped and they are added? [0 for unrestricted] |
| `branching/lookahead/reevalage` | `longint` | [0,9223372036854775807] | 10 | True | max number of LPs solved after which a previous prob branching results are recalculated |
| `branching/lookahead/reevalagefsb` | `longint` | [0,9223372036854775807] | 10 | True | max number of LPs solved after which a previous FSB scoring results are recalculated |
| `branching/lookahead/recursiondepth` | `int` | [1,2147483647] | 2 | True | the max depth of LAB. |
| `branching/lookahead/usedomainreduction` | `bool` | {TRUE,FALSE} | TRUE | True | should domain reductions be collected and applied? |
| `branching/lookahead/mergedomainreductions` | `bool` | {TRUE,FALSE} | FALSE | True | should domain reductions of feasible siblings should be merged? |
| `branching/lookahead/prefersimplebounds` | `bool` | {TRUE,FALSE} | FALSE | True | should domain reductions only be applied if there are simple bound changes? |
| `branching/lookahead/onlyvioldomreds` | `bool` | {TRUE,FALSE} | FALSE | True | should only domain reductions that violate the LP solution be applied? |
| `branching/lookahead/addnonviocons` | `bool` | {TRUE,FALSE} | FALSE | True | should binary constraints, that are not violated by the base LP, be collected and added? |
| `branching/lookahead/abbreviated` | `bool` | {TRUE,FALSE} | TRUE | True | toggles the abbreviated LAB. |
| `branching/lookahead/maxncands` | `int` | [1,2147483647] | 4 | True | if abbreviated: The max number of candidates to consider at the node. |
| `branching/lookahead/maxndeepercands` | `int` | [0,2147483647] | 2 | True | if abbreviated: The max number of candidates to consider per deeper node. |
| `branching/lookahead/reusebasis` | `bool` | {TRUE,FALSE} | TRUE | True | if abbreviated: Should the information gathered to obtain the best candidates be reused? |
| `branching/lookahead/storeunviolatedsol` | `bool` | {TRUE,FALSE} | TRUE | True | if only non violating constraints are added, should the branching decision be stored till the next call? |
| `branching/lookahead/abbrevpseudo` | `bool` | {TRUE,FALSE} | FALSE | True | if abbreviated: Use pseudo costs to estimate the score of a candidate. |
| `branching/lookahead/level2avgscore` | `bool` | {TRUE,FALSE} | FALSE | True | should the average score be used for uninitialized scores in level 2? |
| `branching/lookahead/level2zeroscore` | `bool` | {TRUE,FALSE} | FALSE | True | should uninitialized scores in level 2 be set to 0? |
| `branching/lookahead/addclique` | `bool` | {TRUE,FALSE} | FALSE | True | add binary constraints with two variables found at the root node also as a clique |
| `branching/lookahead/propagate` | `bool` | {TRUE,FALSE} | TRUE | True | should domain propagation be executed before each temporary node is solved? |
| `branching/lookahead/uselevel2data` | `bool` | {TRUE,FALSE} | TRUE | True | should branching data generated at depth level 2 be stored for re-using it? |
| `branching/lookahead/applychildbounds` | `bool` | {TRUE,FALSE} | FALSE | True | should bounds known for child nodes be applied? |
| `branching/lookahead/enforcemaxdomreds` | `bool` | {TRUE,FALSE} | FALSE | True | should the maximum number of domain reductions maxnviolateddomreds be enforced? |
| `branching/lookahead/updatebranchingresults` | `bool` | {TRUE,FALSE} | FALSE | True | should branching results (and scores) be updated w.r.t. proven dual bounds? |
| `branching/lookahead/maxproprounds` | `int` | [-1,2147483647] | 0 | True | maximum number of propagation rounds to perform at each temporary node (-1: unlimited, 0: SCIP default) |
| `branching/lookahead/scoringfunction` | `char` | {dfswplcra} | a | True | scoring function to be used at the base level |
| `branching/lookahead/deeperscoringfunction` | `char` | {dfswlcrx} | x | True | scoring function to be used at deeper levels |
| `branching/lookahead/scoringscoringfunction` | `char` | {dfswlcr} | d | True | scoring function to be used during FSB scoring |
| `branching/lookahead/minweight` | `real` | [0,1.79769313486232e+308] | 0.8 | True | if scoringfunction is 's', this value is used to weight the min of the gains of two child problems in the convex combination |
| `branching/lookahead/worsefactor` | `real` | [-1,1.79769313486232e+308] | -1 | True | if the FSB score is of a candidate is worse than the best by this factor, skip this candidate (-1: disable) |
| `branching/lookahead/filterbymaxgain` | `bool` | {TRUE,FALSE} | FALSE | True | should lookahead branching only be applied if the max gain in level 1 is not uniquely that of the best candidate? |
| `branching/multaggr/priority` | `int` | [-536870912,536870911] | 0 | False | priority of branching rule &lt;multaggr&gt; |
| `branching/multaggr/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;multaggr&gt; should be used (-1 for no limit) |
| `branching/multaggr/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/multaggr/reevalage` | `longint` | [0,9223372036854775807] | 0 | True | number of intermediate LPs solved to trigger reevaluation of strong branching value for a variable that was already evaluated at the current node |
| `branching/multaggr/maxproprounds` | `int` | [-2,2147483647] | 0 | True | maximum number of propagation rounds to be performed during multaggr branching before solving the LP (-1: no limit, -2: parameter settings) |
| `branching/multaggr/probingbounds` | `bool` | {TRUE,FALSE} | TRUE | True | should valid bounds be identified in a probing-like fashion during multaggr branching (only with propagation)? |
| `branching/cloud/priority` | `int` | [-536870912,536870911] | 0 | False | priority of branching rule &lt;cloud&gt; |
| `branching/cloud/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;cloud&gt; should be used (-1 for no limit) |
| `branching/cloud/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/cloud/usecloud` | `bool` | {TRUE,FALSE} | TRUE | False | should a cloud of points be used? |
| `branching/cloud/onlyF2` | `bool` | {TRUE,FALSE} | FALSE | False | should only F2 be used? |
| `branching/cloud/useunion` | `bool` | {TRUE,FALSE} | FALSE | False | should the union of candidates be used? |
| `branching/cloud/maxpoints` | `int` | [-1,2147483647] | -1 | False | maximum number of points for the cloud (-1 means no limit) |
| `branching/cloud/minsuccessrate` | `real` | [0,1] | 0 | False | minimum success rate for the cloud |
| `branching/cloud/minsuccessunion` | `real` | [0,1] | 0 | False | minimum success rate for the union |
| `branching/cloud/maxdepthunion` | `int` | [0,65000] | 65000 | False | maximum depth for the union |
| `branching/allfullstrong/priority` | `int` | [-536870912,536870911] | -1000 | False | priority of branching rule &lt;allfullstrong&gt; |
| `branching/allfullstrong/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;allfullstrong&gt; should be used (-1 for no limit) |
| `branching/allfullstrong/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/gomory/priority` | `int` | [-536870912,536870911] | -1000 | False | priority of branching rule &lt;gomory&gt; |
| `branching/gomory/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;gomory&gt; should be used (-1 for no limit) |
| `branching/gomory/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/gomory/maxncands` | `int` | [-1,2147483647] | -1 | False | maximum amount of branching candidates to generate Gomory cuts for (-1: all candidates) |
| `branching/gomory/efficacyweight` | `real` | [-1,1] | 1 | False | weight of efficacy in the weighted sum cut scoring rule |
| `branching/gomory/objparallelweight` | `real` | [-1,1] | 0 | False | weight of objective parallelism in the weighted sum cut scoring rule |
| `branching/gomory/intsupportweight` | `real` | [-1,1] | 0 | False | weight of integer support in the weighted sum cut scoring rule |
| `branching/gomory/performrelpscost` | `bool` | {TRUE,FALSE} | FALSE | False | whether relpscost branching should be called without branching (used for bound inferences and conflicts) |
| `branching/gomory/useweakercuts` | `bool` | {TRUE,FALSE} | TRUE | False | use weaker cuts that are exactly derived from the branching split disjunction |
| `branching/vanillafullstrong/priority` | `int` | [-536870912,536870911] | -2000 | False | priority of branching rule &lt;vanillafullstrong&gt; |
| `branching/vanillafullstrong/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;vanillafullstrong&gt; should be used (-1 for no limit) |
| `branching/vanillafullstrong/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/vanillafullstrong/integralcands` | `bool` | {TRUE,FALSE} | FALSE | False | should integral variables in the current LP solution be considered as branching candidates? |
| `branching/vanillafullstrong/idempotent` | `bool` | {TRUE,FALSE} | FALSE | False | should strong branching side-effects be prevented (e.g., domain changes, stat updates etc.)? |
| `branching/vanillafullstrong/scoreall` | `bool` | {TRUE,FALSE} | FALSE | True | should strong branching scores be computed for all candidates, or can we early stop when a variable has infinite score? |
| `branching/vanillafullstrong/collectscores` | `bool` | {TRUE,FALSE} | FALSE | True | should strong branching scores be collected? |
| `branching/vanillafullstrong/donotbranch` | `bool` | {TRUE,FALSE} | FALSE | True | should candidates only be scored, but no branching be performed? |
| `branching/random/priority` | `int` | [-536870912,536870911] | -100000 | False | priority of branching rule &lt;random&gt; |
| `branching/random/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;random&gt; should be used (-1 for no limit) |
| `branching/random/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |
| `branching/random/seed` | `int` | [0,2147483647] | 41 | False | initial random seed value |
| `branching/nodereopt/priority` | `int` | [-536870912,536870911] | -9000000 | False | priority of branching rule &lt;nodereopt&gt; |
| `branching/nodereopt/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximal depth level, up to which branching rule &lt;nodereopt&gt; should be used (-1 for no limit) |
| `branching/nodereopt/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying branching rule (0.0: only on current best node, 1.0: on all nodes) |

## compression

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `compression/enable` | `bool` | {TRUE,FALSE} | FALSE | True | should automatic tree compression after the presolving be enabled? |
| `compression/largestrepr/priority` | `int` | [-536870912,536870911] | 2000 | True | priority of compression &lt;largestrepr&gt; |
| `compression/largestrepr/minnleaves` | `int` | [1,2147483647] | 20 | False | minimal number of leave nodes for calling tree compression &lt;largestrepr&gt; |
| `compression/largestrepr/iterations` | `int` | [1,2147483647] | 5 | False | number of runs in the constrained part. |
| `compression/largestrepr/mincommonvars` | `int` | [1,2147483647] | 3 | False | minimal number of common variables. |
| `compression/weakcompr/priority` | `int` | [-536870912,536870911] | 1000 | True | priority of compression &lt;weakcompr&gt; |
| `compression/weakcompr/minnleaves` | `int` | [1,2147483647] | 50 | False | minimal number of leave nodes for calling tree compression &lt;weakcompr&gt; |
| `compression/weakcompr/convertconss` | `bool` | {TRUE,FALSE} | FALSE | False | convert constraints into nodes |

## concurrent

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `concurrent/changeseeds` | `bool` | {TRUE,FALSE} | TRUE | False | set different random seeds in each concurrent solver? |
| `concurrent/changechildsel` | `bool` | {TRUE,FALSE} | TRUE | False | use different child selection rules in each concurrent solver? |
| `concurrent/commvarbnds` | `bool` | {TRUE,FALSE} | TRUE | False | should the concurrent solvers communicate global variable bound changes? |
| `concurrent/presolvebefore` | `bool` | {TRUE,FALSE} | TRUE | False | should the problem be presolved before it is copied to the concurrent solvers? |
| `concurrent/initseed` | `int` | [0,2147483647] | 5131912 | False | maximum number of solutions that will be shared in a one synchronization |
| `concurrent/sync/freqinit` | `real` | [0,1.79769313486232e+308] | 10 | False | initial frequency of synchronization with other threads |
| `concurrent/sync/freqmax` | `real` | [0,1.79769313486232e+308] | 10 | False | maximal frequency of synchronization with other threads |
| `concurrent/sync/freqfactor` | `real` | [1,1.79769313486232e+308] | 1.5 | False | factor by which the frequency of synchronization is changed |
| `concurrent/sync/targetprogress` | `real` | [0,1.79769313486232e+308] | 0.001 | False | when adapting the synchronization frequency this value is the targeted relative difference by which the absolute gap decreases per synchronization |
| `concurrent/sync/maxnsols` | `int` | [0,1000] | 3 | False | maximum number of solutions that will be shared in a single synchronization |
| `concurrent/sync/maxnsyncdelay` | `int` | [0,100] | 7 | True | maximum number of synchronizations before reading is enforced regardless of delay |
| `concurrent/sync/minsyncdelay` | `real` | [0,1.79769313486232e+308] | 10 | False | minimum delay before synchronization data is read |
| `concurrent/sync/nbestsols` | `int` | [0,2147483647] | 10 | False | how many of the N best solutions should be considered for synchronization? |
| `concurrent/paramsetprefix` | `string` | String; interpretation stated in description | "" | False | path prefix for parameter setting files of concurrent solvers |
| `concurrent/scip/prefprio` | `real` | [0,1] | 1 | False | the preferred number concurrent solvers of type &lt;scip&gt; with respect to the number of threads |
| `concurrent/scip-default/prefprio` | `real` | [0,1] | 0 | False | the preferred number concurrent solvers of type &lt;scip-default&gt; with respect to the number of threads |
| `concurrent/scip-cpsolver/prefprio` | `real` | [0,1] | 0 | False | the preferred number concurrent solvers of type &lt;scip-cpsolver&gt; with respect to the number of threads |
| `concurrent/scip-easycip/prefprio` | `real` | [0,1] | 0 | False | the preferred number concurrent solvers of type &lt;scip-easycip&gt; with respect to the number of threads |
| `concurrent/scip-feas/prefprio` | `real` | [0,1] | 0 | False | the preferred number concurrent solvers of type &lt;scip-feas&gt; with respect to the number of threads |
| `concurrent/scip-hardlp/prefprio` | `real` | [0,1] | 0 | False | the preferred number concurrent solvers of type &lt;scip-hardlp&gt; with respect to the number of threads |
| `concurrent/scip-opti/prefprio` | `real` | [0,1] | 0 | False | the preferred number concurrent solvers of type &lt;scip-opti&gt; with respect to the number of threads |
| `concurrent/scip-counter/prefprio` | `real` | [0,1] | 0 | False | the preferred number concurrent solvers of type &lt;scip-counter&gt; with respect to the number of threads |

## conflict

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `conflict/enable` | `bool` | {TRUE,FALSE} | TRUE | False | should conflict analysis be enabled? |
| `conflict/cleanboundexceedings` | `bool` | {TRUE,FALSE} | TRUE | True | should conflicts based on an old cutoff bound be removed from the conflict pool after improving the primal bound? |
| `conflict/uselocalrows` | `bool` | {TRUE,FALSE} | TRUE | True | use local rows to construct infeasibility proofs |
| `conflict/useprop` | `bool` | {TRUE,FALSE} | TRUE | False | should propagation conflict analysis be used? |
| `conflict/usegenres` | `bool` | {TRUE,FALSE} | FALSE | False | should generalized resolution conflict analysis be used? |
| `conflict/useinflp` | `char` | {ocdb} | b | False | should infeasible LP conflict analysis be used? ('o'ff, 'c'onflict graph, 'd'ual ray, 'b'oth conflict graph and dual ray) |
| `conflict/useboundlp` | `char` | {ocdb} | b | False | should bound exceeding LP conflict analysis be used? ('o'ff, 'c'onflict graph, 'd'ual ray, 'b'oth conflict graph and dual ray) |
| `conflict/reduction` | `char` | {om} | m | False | which tightening reduction should be used? ('o'ff, 'm'ir) |
| `conflict/mbreduction` | `bool` | {TRUE,FALSE} | TRUE | True | should apply the mixed binary reduction? |
| `conflict/usesb` | `bool` | {TRUE,FALSE} | TRUE | False | should infeasible/bound exceeding strong branching conflict analysis be used? |
| `conflict/usepseudo` | `bool` | {TRUE,FALSE} | TRUE | False | should pseudo solution conflict analysis be used? |
| `conflict/maxvarsfac` | `real` | [0,1] | 0.15 | True | maximal fraction of variables involved in a conflict constraint |
| `conflict/maxvarsfracres` | `real` | [0,1] | 0.2 | True | maximal fraction of variables involved in a resolution conflict constraint |
| `conflict/minmaxvars` | `int` | [0,2147483647] | 0 | True | minimal absolute maximum of variables involved in a conflict constraint |
| `conflict/maxlploops` | `int` | [-1,2147483647] | 2 | True | maximal number of LP resolving loops during conflict analysis (-1: no limit) |
| `conflict/lpiterations` | `int` | [-1,2147483647] | 10 | True | maximal number of LP iterations in each LP resolving loop (-1: no limit) |
| `conflict/fuiplevels` | `int` | [-1,2147483647] | -1 | True | number of depth levels up to which first UIP's are used in conflict analysis (-1: use All-FirstUIP rule) |
| `conflict/resfuiplevels` | `int` | [-1,2147483647] | 1 | True | number of depth levels up to which first UIP's are used in conflict analysis (-1: use All-FirstUIP rule) |
| `conflict/interconss` | `int` | [-1,2147483647] | -1 | True | maximal number of intermediate conflict constraints generated in conflict graph (-1: use every intermediate constraint) |
| `conflict/reconvlevels` | `int` | [-1,2147483647] | -1 | True | number of depth levels up to which UIP reconvergence constraints are generated (-1: generate reconvergence constraints in all depth levels) |
| `conflict/maxconss` | `int` | [-1,2147483647] | 10 | True | maximal number of conflict constraints accepted at an infeasible node (-1: use all generated conflict constraints) |
| `conflict/maxstoresize` | `int` | [-1,2147483647] | 10000 | True | maximal size of conflict store (-1: auto, 0: disable storage) |
| `conflict/preferbinary` | `bool` | {TRUE,FALSE} | FALSE | False | should binary conflicts be preferred? |
| `conflict/prefinfproof` | `bool` | {TRUE,FALSE} | TRUE | True | prefer infeasibility proof to boundexceeding proof |
| `conflict/allowlocal` | `bool` | {TRUE,FALSE} | TRUE | True | should conflict constraints be generated that are only valid locally? |
| `conflict/settlelocal` | `bool` | {TRUE,FALSE} | FALSE | True | should conflict constraints be attached only to the local subtree where they can be useful? |
| `conflict/repropagate` | `bool` | {TRUE,FALSE} | TRUE | True | should earlier nodes be repropagated in order to replace branching decisions by deductions? |
| `conflict/keepreprop` | `bool` | {TRUE,FALSE} | TRUE | True | should constraints be kept for repropagation even if they are too long? |
| `conflict/separate` | `bool` | {TRUE,FALSE} | TRUE | True | should the conflict constraints be separated? |
| `conflict/dynamic` | `bool` | {TRUE,FALSE} | TRUE | True | should the conflict constraints be subject to aging? |
| `conflict/removable` | `bool` | {TRUE,FALSE} | TRUE | True | should the conflict's relaxations be subject to LP aging and cleanup? |
| `conflict/fixandcontinue` | `bool` | {TRUE,FALSE} | FALSE | True | should we fix unresolvable bound changes and continue? |
| `conflict/graph/depthscorefac` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1 | True | score factor for depth level in bound relaxation heuristic |
| `conflict/proofscorefac` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1 | True | score factor for impact on acticity in bound relaxation heuristic |
| `conflict/uplockscorefac` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 0 | True | score factor for up locks in bound relaxation heuristic |
| `conflict/downlockscorefac` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 0 | True | score factor for down locks in bound relaxation heuristic |
| `conflict/scorefac` | `real` | [1e-06,1] | 0.98 | True | factor to decrease importance of variables' earlier conflict scores |
| `conflict/restartnum` | `int` | [0,2147483647] | 0 | False | number of successful conflict analysis calls that trigger a restart (0: disable conflict restarts) |
| `conflict/restartfac` | `real` | [0,1.79769313486232e+308] | 1.5 | False | factor to increase restartnum with after each restart |
| `conflict/ignorerelaxedbd` | `bool` | {TRUE,FALSE} | FALSE | True | should relaxed bounds be ignored? |
| `conflict/maxvarsdetectimpliedbounds` | `int` | [0,2147483647] | 250 | True | maximal number of variables to try to detect global bound implications and shorten the whole conflict set (0: disabled) |
| `conflict/fullshortenconflict` | `bool` | {TRUE,FALSE} | TRUE | True | try to shorten the whole conflict set or terminate early (depending on the 'maxvarsdetectimpliedbounds' parameter) |
| `conflict/conflictweight` | `real` | [0,1] | 0 | False | the weight the VSIDS score is weight by updating the VSIDS for a variable if it is part of a conflict |
| `conflict/conflictgraphweight` | `real` | [0,1] | 1 | False | the weight the VSIDS score is weight by updating the VSIDS for a variable if it is part of a conflict graph |
| `conflict/minimprove` | `real` | [0,1] | 0.05 | True | minimal improvement of primal bound to remove conflicts based on a previous incumbent |
| `conflict/weightsize` | `real` | [0,1] | 0.001 | True | weight of the size of a conflict used in score calculation |
| `conflict/weightrepropdepth` | `real` | [0,1] | 0.1 | True | weight of the repropagation depth of a conflict used in score calculation |
| `conflict/weightvaliddepth` | `real` | [0,1] | 1 | True | weight of the valid depth of a conflict used in score calculation |
| `conflict/maxcoefquot` | `real` | [1,1.79769313486232e+308] | 1000000 | False |  largest allowed quotient of max, min coefficient in a conflict constraint generated by generalized resolution |
| `conflict/sepaaltproofs` | `bool` | {TRUE,FALSE} | FALSE | False | apply cut generating functions to construct alternative proofs |
| `conflict/linear/priority` | `int` | [-2147483648,2147483647] | -1000000 | True | priority of conflict handler &lt;linear&gt; |
| `conflict/bounddisjunction/continuousfrac` | `real` | [0,1] | 0.4 | False | maximal percantage of continuous variables within a conflict |
| `conflict/bounddisjunction/priority` | `int` | [-2147483648,2147483647] | -3000000 | True | priority of conflict handler &lt;bounddisjunction&gt; |
| `conflict/indicatorconflict/priority` | `int` | [-2147483648,2147483647] | 200000 | True | priority of conflict handler &lt;indicatorconflict&gt; |
| `conflict/logicor/priority` | `int` | [-2147483648,2147483647] | 800000 | True | priority of conflict handler &lt;logicor&gt; |
| `conflict/setppc/priority` | `int` | [-2147483648,2147483647] | 700000 | True | priority of conflict handler &lt;setppc&gt; |

## constraints

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `constraints/agelimit` | `int` | [-1,2147483647] | 0 | True | maximum age an unnecessary constraint can reach before it is deleted (0: dynamic, -1: keep all constraints) |
| `constraints/obsoleteage` | `int` | [-1,2147483647] | -1 | True | age of a constraint after which it is marked obsolete (0: dynamic, -1 do not mark constraints obsolete) |
| `constraints/disableenfops` | `bool` | {TRUE,FALSE} | FALSE | True | should enforcement of pseudo solution be disabled? |
| `constraints/nonlinear/sepafreq` | `int` | [-1,1073741822] | 1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/nonlinear/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/nonlinear/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/nonlinear/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/nonlinear/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/nonlinear/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/nonlinear/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/nonlinear/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/nonlinear/maxproprounds` | `int` | [0,2147483647] | 10 | False | limit on number of propagation rounds for a set of constraints within one round of SCIP propagation |
| `constraints/nonlinear/propauxvars` | `bool` | {TRUE,FALSE} | TRUE | True | whether to check bounds of all auxiliary variable to seed reverse propagation |
| `constraints/nonlinear/varboundrelax` | `char` | {nabr} | r | True | strategy on how to relax variable bounds during bound tightening: relax (n)ot, relax by (a)bsolute value, relax always by a(b)solute value, relax by (r)relative value |
| `constraints/nonlinear/varboundrelaxamount` | `real` | [0,1] | 1e-09 | True | by how much to relax variable bounds during bound tightening if strategy 'a', 'b', or 'r' |
| `constraints/nonlinear/conssiderelaxamount` | `real` | [0,1] | 1e-09 | True | by how much to relax constraint sides during bound tightening |
| `constraints/nonlinear/vpmaxperturb` | `real` | [0,1] | 0.001 | True | maximal relative perturbation of reference point when computing facet of envelope of vertex-polyhedral function (dim&gt;2) |
| `constraints/nonlinear/vpadjfacetthresh` | `real` | [0,1.79769313486232e+308] | 10 | True | adjust computed facet of envelope of vertex-polyhedral function up to a violation of this value times LP feasibility tolerance |
| `constraints/nonlinear/vpdualsimplex` | `bool` | {TRUE,FALSE} | TRUE | True | whether to use dual simplex instead of primal simplex for LP that computes facet of vertex-polyhedral function |
| `constraints/nonlinear/bilinmaxnauxexprs` | `int` | [0,2147483647] | 10 | False | maximal number of auxiliary expressions per bilinear term |
| `constraints/nonlinear/reformbinprods` | `bool` | {TRUE,FALSE} | TRUE | False | whether to reformulate products of binary variables during presolving |
| `constraints/nonlinear/reformbinprodsand` | `bool` | {TRUE,FALSE} | TRUE | False | whether to use the AND constraint handler for reformulating binary products |
| `constraints/nonlinear/reformbinprodsfac` | `int` | [1,2147483647] | 50 | False | minimum number of terms to reformulate bilinear binary products by factorizing variables (&lt;= 1: disabled) |
| `constraints/nonlinear/forbidmultaggrnlvar` | `bool` | {TRUE,FALSE} | TRUE | True | whether to forbid multiaggregation of nonlinear variables |
| `constraints/nonlinear/tightenlpfeastol` | `bool` | {TRUE,FALSE} | TRUE | True | whether to tighten LP feasibility tolerance during enforcement, if it seems useful |
| `constraints/nonlinear/propinenforce` | `bool` | {TRUE,FALSE} | FALSE | True | whether to (re)run propagation in enforcement |
| `constraints/nonlinear/weakcutthreshold` | `real` | [0,1] | 0.2 | True | threshold for when to regard a cut from an estimator as weak (lower values allow more weak cuts) |
| `constraints/nonlinear/strongcutmaxcoef` | `real` | [1,1e+20] | 1000 | True | "strong" cuts will be scaled to have their maximal coef in [1/strongcutmaxcoef,strongcutmaxcoef] |
| `constraints/nonlinear/strongcutefficacy` | `bool` | {TRUE,FALSE} | FALSE | True | consider efficacy requirement when deciding whether a cut is "strong" |
| `constraints/nonlinear/forcestrongcut` | `bool` | {TRUE,FALSE} | FALSE | True | whether to force "strong" cuts in enforcement |
| `constraints/nonlinear/enfoauxviolfactor` | `real` | [0,1] | 0.01 | True | an expression will be enforced if the "auxiliary" violation is at least this factor times the "original" violation |
| `constraints/nonlinear/weakcutminviolfactor` | `real` | [0,2] | 0.5 | True | retry enfo of constraint with weak cuts if violation is least this factor of maximal violated constraints |
| `constraints/nonlinear/rownotremovable` | `char` | {oea} | o | True | whether to make rows to be non-removable in the node where they are added (can prevent some cycling): 'o'ff, in 'e'nforcement only, 'a'lways |
| `constraints/nonlinear/violscale` | `char` | {nag} | n | True | method how to scale violations to make them comparable (not used for feasibility check): (n)one, (a)ctivity and side, norm of (g)radient |
| `constraints/nonlinear/checkvarlocks` | `char` | {bdt} | t | True | whether variables contained in a single constraint should be forced to be at their lower or upper bounds ('d'isable, change 't'ype, add 'b'ound disjunction) |
| `constraints/nonlinear/branching/aux` | `int` | [0,2147483647] | 2147483647 | False | from which depth on in the tree to allow branching on auxiliary variables (variables added for extended formulation) |
| `constraints/nonlinear/branching/external` | `bool` | {TRUE,FALSE} | FALSE | False | whether to use external branching candidates and branching rules for branching |
| `constraints/nonlinear/branching/highviolfactor` | `real` | [0,1] | 0 | False | consider a constraint highly violated if its violation is &gt;= this factor * maximal violation among all constraints |
| `constraints/nonlinear/branching/highscorefactor` | `real` | [0,1] | 0.9 | False | consider a variable branching score high if its branching score &gt;= this factor * maximal branching score among all variables |
| `constraints/nonlinear/branching/violweight` | `real` | [0,1e+20] | 1 | False | weight by how much to consider the violation assigned to a variable for its branching score |
| `constraints/nonlinear/branching/fracweight` | `real` | [0,1e+20] | 1 | False | weight by how much to consider fractionality of integer variables in branching score for spatial branching |
| `constraints/nonlinear/branching/dualweight` | `real` | [0,1e+20] | 0 | False | weight by how much to consider the dual values of rows that contain a variable for its branching score |
| `constraints/nonlinear/branching/pscostweight` | `real` | [0,1e+20] | 1 | False | weight by how much to consider the pseudo cost of a variable for its branching score |
| `constraints/nonlinear/branching/domainweight` | `real` | [0,1e+20] | 0 | False | weight by how much to consider the domain width in branching score |
| `constraints/nonlinear/branching/vartypeweight` | `real` | [0,1e+20] | 0.5 | False | weight by how much to consider variable type (continuous: 0, binary: 1, integer: 0.1, impl-integer: 0.01) in branching score |
| `constraints/nonlinear/branching/scoreagg` | `char` | {ams} | s | False | how to aggregate several branching scores given for the same expression: 'a'verage, 'm'aximum, 's'um |
| `constraints/nonlinear/branching/violsplit` | `char` | {umdl} | m | False | method used to split violation in expression onto variables: 'u'niform, 'm'idness of solution, 'd'omain width, 'l'ogarithmic domain width |
| `constraints/nonlinear/branching/pscostreliable` | `real` | [0,1e+20] | 2 | False | minimum pseudo-cost update count required to consider pseudo-costs reliable |
| `constraints/nonlinear/branching/mixfractional` | `real` | [0,1e+20] | 1e+20 | False | minimal average pseudo cost count for discrete variables at which to start considering spatial branching before branching on fractional integer variables |
| `constraints/nonlinear/linearizeheursol` | `char` | {oie} | o | False | whether tight linearizations of nonlinear constraints should be added to cutpool when some heuristics finds a new solution ('o'ff, on new 'i'ncumbents, on 'e'very solution) |
| `constraints/nonlinear/assumeconvex` | `bool` | {TRUE,FALSE} | FALSE | True | whether to assume that any constraint in the presolved problem is convex |
| `constraints/linear/sepafreq` | `int` | [-1,1073741822] | 0 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/linear/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/linear/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/linear/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/linear/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/linear/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/linear/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/linear/presoltiming` | `int` | [4,60] | 20 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/nonlinear/upgrade/linear` | `bool` | {TRUE,FALSE} | TRUE | False | enable nonlinear upgrading for constraint handler &lt;linear&gt; |
| `constraints/linear/tightenboundsfreq` | `int` | [-1,1073741822] | 1 | True | multiplier on propagation frequency, how often the bounds are tightened (-1: never, 0: only at root) |
| `constraints/linear/maxrounds` | `int` | [-1,2147483647] | 5 | False | maximal number of separation rounds per node (-1: unlimited) |
| `constraints/linear/maxroundsroot` | `int` | [-1,2147483647] | -1 | False | maximal number of separation rounds per node in the root node (-1: unlimited) |
| `constraints/linear/maxsepacuts` | `int` | [0,2147483647] | 50 | False | maximal number of cuts separated per separation round |
| `constraints/linear/maxsepacutsroot` | `int` | [0,2147483647] | 200 | False | maximal number of cuts separated per separation round in the root node |
| `constraints/linear/presolpairwise` | `bool` | {TRUE,FALSE} | TRUE | True | should pairwise constraint comparison be performed in presolving? |
| `constraints/linear/presolusehashing` | `bool` | {TRUE,FALSE} | TRUE | True | should hash table be used for detecting redundant constraints in advance |
| `constraints/linear/nmincomparisons` | `int` | [1,2147483647] | 200000 | True | number for minimal pairwise presolve comparisons |
| `constraints/linear/mingainpernmincomparisons` | `real` | [0,1] | 1e-06 | True | minimal gain per minimal pairwise presolve comparisons to repeat pairwise comparison round |
| `constraints/linear/maxaggrnormscale` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal allowed relative gain in maximum norm for constraint aggregation (0.0: disable constraint aggregation) |
| `constraints/linear/maxeasyactivitydelta` | `real` | [0,1.79769313486232e+308] | 1000000 | True | maximum activity delta to run easy propagation on linear constraint (faster, but numerically less stable) |
| `constraints/linear/maxcardbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for separating knapsack cardinality cuts |
| `constraints/linear/separateall` | `bool` | {TRUE,FALSE} | FALSE | False | should all constraints be subject to cardinality cut generation instead of only the ones with non-zero dual value? |
| `constraints/linear/aggregatevariables` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving search for aggregations in equations |
| `constraints/linear/simplifyinequalities` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving try to simplify inequalities |
| `constraints/linear/dualpresolving` | `bool` | {TRUE,FALSE} | TRUE | True | should dual presolving steps be performed? |
| `constraints/linear/singletonstuffing` | `bool` | {TRUE,FALSE} | TRUE | True | should stuffing of singleton continuous variables be performed? |
| `constraints/linear/singlevarstuffing` | `bool` | {TRUE,FALSE} | FALSE | True | should single variable stuffing be performed, which tries to fulfill constraints using the cheapest variable? |
| `constraints/linear/sortvars` | `bool` | {TRUE,FALSE} | TRUE | True | apply binaries sorting in decr. order of coeff abs value? |
| `constraints/linear/checkrelmaxabs` | `bool` | {TRUE,FALSE} | FALSE | True | should the violation for a constraint with side 0.0 be checked relative to 1.0 (FALSE) or to the maximum absolute value in the activity (TRUE)? |
| `constraints/linear/detectcutoffbound` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving try to detect constraints parallel to the objective function defining an upper bound and prevent these constraints from entering the LP? |
| `constraints/linear/detectlowerbound` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving try to detect constraints parallel to the objective function defining a lower bound and prevent these constraints from entering the LP? |
| `constraints/linear/detectpartialobjective` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving try to detect subsets of constraints parallel to the objective function? |
| `constraints/linear/rangedrowpropagation` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving and propagation try to improve bounds, detect infeasibility, and extract sub-constraints from ranged rows and equations? |
| `constraints/linear/rangedrowartcons` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving and propagation extract sub-constraints from ranged rows and equations? |
| `constraints/linear/rangedrowmaxdepth` | `int` | [0,2147483647] | 2147483647 | True | maximum depth to apply ranged row propagation |
| `constraints/linear/rangedrowfreq` | `int` | [1,1073741822] | 1 | True | frequency for applying ranged row propagation |
| `constraints/linear/multaggrremove` | `bool` | {TRUE,FALSE} | FALSE | True | should multi-aggregations only be performed if the constraint can be removed afterwards? |
| `constraints/linear/maxmultaggrquot` | `real` | [1,1.79769313486232e+308] | 1000 | True | maximum coefficient dynamism (ie. maxabsval / minabsval) for primal multiaggregation |
| `constraints/linear/maxdualmultaggrquot` | `real` | [1,1.79769313486232e+308] | 1e+20 | True | maximum coefficient dynamism (ie. maxabsval / minabsval) for dual multiaggregation |
| `constraints/linear/extractcliques` | `bool` | {TRUE,FALSE} | TRUE | True | should Cliques be extracted? |
| `constraints/exactlinear/sepafreq` | `int` | [-1,1073741822] | 0 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/exactlinear/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/exactlinear/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/exactlinear/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/exactlinear/maxprerounds` | `int` | [-1,2147483647] | 0 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/exactlinear/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/exactlinear/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/exactlinear/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/exactlinear/tightenboundsfreq` | `int` | [-1,1073741822] | 1 | True | multiplier on propagation frequency, how often the bounds are tightened (-1: never, 0: only at root) |
| `constraints/exactlinear/maxrounds` | `int` | [-1,2147483647] | 5 | False | maximal number of separation rounds per node (-1: unlimited) |
| `constraints/exactlinear/maxroundsroot` | `int` | [-1,2147483647] | -1 | False | maximal number of separation rounds per node in the root node (-1: unlimited) |
| `constraints/exactlinear/maxsepacuts` | `int` | [0,2147483647] | 50 | False | maximal number of cuts separated per separation round |
| `constraints/exactlinear/maxsepacutsroot` | `int` | [0,2147483647] | 200 | False | maximal number of cuts separated per separation round in the root node |
| `constraints/exactlinear/sortvars` | `bool` | {TRUE,FALSE} | TRUE | True | apply binaries sorting in decr. order of coeff abs value? |
| `constraints/exactlinear/propcont` | `bool` | {TRUE,FALSE} | TRUE | True | should bounds on continuous variables be tightened by propagation? |
| `constraints/exactlinear/limitdenom` | `bool` | {TRUE,FALSE} | FALSE | True | should denominators of rational bounds on continuous variables be controlled? |
| `constraints/exactlinear/boundmaxdenom` | `longint` | [1,9223372036854775807] | 256 | True | maximal denominator for rational bounds on continuous variables after propagation |
| `constraints/exactsol/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/exactsol/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/exactsol/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/exactsol/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/exactsol/maxprerounds` | `int` | [-1,2147483647] | 0 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/exactsol/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/exactsol/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/exactsol/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/exactsol/checkfpfeasibility` | `bool` | {TRUE,FALSE} | TRUE | True | should a solution be checked in floating-point arithmetic prior to being processed? |
| `constraints/exactsol/checkcontimplint` | `bool` | {TRUE,FALSE} | TRUE | True | should integrality of continuous implied integral variables be ensured? |
| `constraints/exactsol/abortfrac` | `real` | [0,0.5] | 1e-09 | True | fractionality of enforced integral value above which reparation is aborted |
| `constraints/exactsol/unfixfrac` | `real` | [0,0.5] | 0 | True | fractionality of weakly implied value up to which reparation fixes variable |
| `constraints/exactsol/maxstalls` | `int` | [0,2147483647] | 1000 | True | maximal number of consecutive repair calls without success |
| `constraints/exactsol/solbufsize` | `int` | [0,2147483647] | 10 | True | size of solution buffer |
| `constraints/exactsol/minimprove` | `real` | [0,1.79769313486232e+308] | 0.2 | True | minimal percentage of primal improvement to trigger solution processing |
| `constraints/and/sepafreq` | `int` | [-1,1073741822] | 1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/and/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/and/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/and/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/and/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/and/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/and/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/and/presoltiming` | `int` | [4,60] | 20 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/and/presolpairwise` | `bool` | {TRUE,FALSE} | TRUE | True | should pairwise constraint comparison be performed in presolving? |
| `constraints/and/presolusehashing` | `bool` | {TRUE,FALSE} | TRUE | True | should hash table be used for detecting redundant constraints in advance |
| `constraints/and/linearize` | `bool` | {TRUE,FALSE} | FALSE | True | should the AND-constraint get linearized and removed (in presolving)? |
| `constraints/and/enforcecuts` | `bool` | {TRUE,FALSE} | TRUE | True | should cuts be separated during LP enforcing? |
| `constraints/and/aggrlinearization` | `bool` | {TRUE,FALSE} | FALSE | True | should an aggregated linearization be used? |
| `constraints/and/upgraderesultant` | `bool` | {TRUE,FALSE} | FALSE | True | should implied integrality of resultant variables be detected? |
| `constraints/and/dualpresolving` | `bool` | {TRUE,FALSE} | TRUE | True | should dual presolving be performed? |
| `constraints/bounddisjunction/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/bounddisjunction/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/bounddisjunction/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/bounddisjunction/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/bounddisjunction/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/bounddisjunction/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/bounddisjunction/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/bounddisjunction/presoltiming` | `int` | [4,60] | 4 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/cardinality/sepafreq` | `int` | [-1,1073741822] | 10 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/cardinality/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/cardinality/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/cardinality/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/cardinality/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/cardinality/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/cardinality/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/cardinality/presoltiming` | `int` | [4,60] | 4 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/cardinality/branchbalanced` | `bool` | {TRUE,FALSE} | FALSE | True | whether to use balanced instead of unbalanced branching |
| `constraints/cardinality/balanceddepth` | `int` | [-1,2147483647] | 20 | True | maximum depth for using balanced branching (-1: no limit) |
| `constraints/cardinality/balancedcutoff` | `real` | [0.01,1.79769313486232e+308] | 2 | True | determines that balanced branching is only used if the branching cut off value w.r.t. the current LP solution is greater than a given value |
| `constraints/conjunction/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/conjunction/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/conjunction/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/conjunction/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/conjunction/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/conjunction/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/conjunction/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/conjunction/presoltiming` | `int` | [4,60] | 4 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/countsols/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/countsols/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/countsols/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/countsols/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/countsols/maxprerounds` | `int` | [-1,2147483647] | 0 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/countsols/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/countsols/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/countsols/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/countsols/active` | `bool` | {TRUE,FALSE} | FALSE | False | is the constraint handler active? |
| `constraints/countsols/sparsetest` | `bool` | {TRUE,FALSE} | TRUE | False | should the sparse solution test be turned on? |
| `constraints/countsols/discardsols` | `bool` | {TRUE,FALSE} | TRUE | False | is it allowed to discard solutions? |
| `constraints/countsols/collect` | `bool` | {TRUE,FALSE} | FALSE | False | should the solutions be collected? |
| `constraints/countsols/sollimit` | `longint` | [-1,9223372036854775807] | -1 | False | counting stops, if the given number of solutions were found (-1: no limit) |
| `constraints/cumulative/sepafreq` | `int` | [-1,1073741822] | 1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/cumulative/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/cumulative/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/cumulative/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/cumulative/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/cumulative/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/cumulative/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/cumulative/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/cumulative/maxtime` | `int` | [0,2147483647] | 2000000000 | True | maximum range for time horizon |
| `constraints/cumulative/ttinfer` | `bool` | {TRUE,FALSE} | TRUE | False | should time-table (core-times) propagator be used to infer bounds? |
| `constraints/cumulative/efcheck` | `bool` | {TRUE,FALSE} | FALSE | False | should edge-finding be used to detect an overload? |
| `constraints/cumulative/efinfer` | `bool` | {TRUE,FALSE} | FALSE | False | should edge-finding be used to infer bounds? |
| `constraints/cumulative/useadjustedjobs` | `bool` | {TRUE,FALSE} | FALSE | True | should edge-finding be executed? |
| `constraints/cumulative/ttefcheck` | `bool` | {TRUE,FALSE} | TRUE | False | should time-table edge-finding be used to detect an overload? |
| `constraints/cumulative/ttefinfer` | `bool` | {TRUE,FALSE} | TRUE | False | should time-table edge-finding be used to infer bounds? |
| `constraints/cumulative/usebinvars` | `bool` | {TRUE,FALSE} | FALSE | False | should the binary representation be used? |
| `constraints/cumulative/localcuts` | `bool` | {TRUE,FALSE} | FALSE | False | should cuts be added only locally? |
| `constraints/cumulative/usecovercuts` | `bool` | {TRUE,FALSE} | TRUE | False | should covering cuts be added every node? |
| `constraints/cumulative/cutsasconss` | `bool` | {TRUE,FALSE} | TRUE | False | should the cumulative constraint create cuts as knapsack constraints? |
| `constraints/cumulative/sepaold` | `bool` | {TRUE,FALSE} | TRUE | False | shall old sepa algo be applied? |
| `constraints/cumulative/fillbranchcands` | `bool` | {TRUE,FALSE} | FALSE | False | should branching candidates be added to storage? |
| `constraints/cumulative/dualpresolve` | `bool` | {TRUE,FALSE} | TRUE | False | should dual presolving be applied? |
| `constraints/cumulative/coeftightening` | `bool` | {TRUE,FALSE} | FALSE | False | should coefficient tightening be applied? |
| `constraints/cumulative/normalize` | `bool` | {TRUE,FALSE} | TRUE | False | should demands and capacity be normalized? |
| `constraints/cumulative/presolpairwise` | `bool` | {TRUE,FALSE} | TRUE | True | should pairwise constraint comparison be performed in presolving? |
| `constraints/cumulative/disjunctive` | `bool` | {TRUE,FALSE} | TRUE | False | extract disjunctive constraints? |
| `constraints/cumulative/maxnodes` | `longint` | [-1,9223372036854775807] | 10000 | False | number of branch-and-bound nodes to solve an independent cumulative constraint (-1: no limit)? |
| `constraints/cumulative/detectdisjunctive` | `bool` | {TRUE,FALSE} | TRUE | False | search for conflict set via maximal cliques to detect disjunctive constraints |
| `constraints/cumulative/detectvarbounds` | `bool` | {TRUE,FALSE} | TRUE | False | search for conflict set via maximal cliques to detect variable bound constraints |
| `constraints/cumulative/usebdwidening` | `bool` | {TRUE,FALSE} | TRUE | False | should bound widening be used during the conflict analysis? |
| `constraints/disjunction/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/disjunction/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/disjunction/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/disjunction/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/disjunction/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/disjunction/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/disjunction/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/disjunction/presoltiming` | `int` | [4,60] | 4 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/disjunction/alwaysbranch` | `bool` | {TRUE,FALSE} | TRUE | False | alawys perform branching if one of the constraints is violated, otherwise only if all integers are fixed |
| `constraints/fixedvar/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/fixedvar/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/fixedvar/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/fixedvar/eagerfreq` | `int` | [-1,1073741822] | -1 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/fixedvar/maxprerounds` | `int` | [-1,2147483647] | 0 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/fixedvar/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/fixedvar/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/fixedvar/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/fixedvar/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | whether to check and enforce bounds on fixed variables |
| `constraints/fixedvar/subscips` | `bool` | {TRUE,FALSE} | TRUE | False | whether to act on subSCIPs |
| `constraints/fixedvar/prefercut` | `bool` | {TRUE,FALSE} | TRUE | False | whether to prefer separation over tightening LP feastol in enforcement |
| `constraints/indicator/sepafreq` | `int` | [-1,1073741822] | 10 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/indicator/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/indicator/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/indicator/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/indicator/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/indicator/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/indicator/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/indicator/presoltiming` | `int` | [4,60] | 4 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/linear/upgrade/indicator` | `bool` | {TRUE,FALSE} | TRUE | False | enable linear upgrading for constraint handler &lt;indicator&gt; |
| `constraints/indicator/branchindicators` | `bool` | {TRUE,FALSE} | FALSE | True | Branch on indicator constraints in enforcing? |
| `constraints/indicator/genlogicor` | `bool` | {TRUE,FALSE} | FALSE | True | Generate logicor constraints instead of cuts? |
| `constraints/indicator/addcoupling` | `bool` | {TRUE,FALSE} | TRUE | True | Add coupling constraints or rows if big-M is small enough? |
| `constraints/indicator/maxcouplingvalue` | `real` | [0,1000000000] | 10000 | True | maximum coefficient for binary variable in coupling constraint |
| `constraints/indicator/addcouplingcons` | `bool` | {TRUE,FALSE} | FALSE | True | Add initial variable upper bound constraints, if 'addcoupling' is true? |
| `constraints/indicator/sepacouplingcuts` | `bool` | {TRUE,FALSE} | TRUE | True | Should the coupling inequalities be separated dynamically? |
| `constraints/indicator/sepacouplinglocal` | `bool` | {TRUE,FALSE} | FALSE | True | Allow to use local bounds in order to separate coupling inequalities? |
| `constraints/indicator/sepacouplingvalue` | `real` | [0,1000000000] | 10000 | True | maximum coefficient for binary variable in separated coupling constraint |
| `constraints/indicator/sepaperspective` | `bool` | {TRUE,FALSE} | FALSE | True | Separate cuts based on perspective formulation? |
| `constraints/indicator/sepapersplocal` | `bool` | {TRUE,FALSE} | TRUE | True | Allow to use local bounds in order to separate perspective cuts? |
| `constraints/indicator/maxsepanonviolated` | `int` | [0,2147483647] | 3 | False | maximal number of separated non violated IISs, before separation is stopped |
| `constraints/indicator/updatebounds` | `bool` | {TRUE,FALSE} | FALSE | True | Update bounds of original variables for separation? |
| `constraints/indicator/maxconditionaltlp` | `real` | [0,1.79769313486232e+308] | 0 | True | maximum estimated condition of the solution basis matrix of the alternative LP to be trustworthy (0.0 to disable check) |
| `constraints/indicator/maxsepacuts` | `int` | [0,2147483647] | 100 | False | maximal number of cuts separated per separation round |
| `constraints/indicator/maxsepacutsroot` | `int` | [0,2147483647] | 2000 | False | maximal number of cuts separated per separation round in the root node |
| `constraints/indicator/removeindicators` | `bool` | {TRUE,FALSE} | FALSE | True | Remove indicator constraint if corresponding variable bound constraint has been added? |
| `constraints/indicator/generatebilinear` | `bool` | {TRUE,FALSE} | FALSE | True | Do not generate indicator constraint, but a bilinear constraint instead? |
| `constraints/indicator/scaleslackvar` | `bool` | {TRUE,FALSE} | FALSE | True | Scale slack variable coefficient at construction time? |
| `constraints/indicator/trysolutions` | `bool` | {TRUE,FALSE} | TRUE | True | Try to make solutions feasible by setting indicator variables? |
| `constraints/indicator/enforcecuts` | `bool` | {TRUE,FALSE} | FALSE | True | In enforcing try to generate cuts (only if sepaalternativelp is true)? |
| `constraints/indicator/dualreductions` | `bool` | {TRUE,FALSE} | TRUE | True | Should dual reduction steps be performed? |
| `constraints/indicator/addopposite` | `bool` | {TRUE,FALSE} | FALSE | True | Add opposite inequality in nodes in which the binary variable has been fixed to 0? |
| `constraints/indicator/conflictsupgrade` | `bool` | {TRUE,FALSE} | FALSE | True | Try to upgrade bounddisjunction conflicts by replacing slack variables? |
| `constraints/indicator/restartfrac` | `real` | [0,1] | 0.9 | True | fraction of binary variables that need to be fixed before restart occurs (in forcerestart) |
| `constraints/indicator/useotherconss` | `bool` | {TRUE,FALSE} | FALSE | True | Collect other constraints to alternative LP? |
| `constraints/indicator/useobjectivecut` | `bool` | {TRUE,FALSE} | FALSE | True | Use objective cut with current best solution to alternative LP? |
| `constraints/indicator/trysolfromcover` | `bool` | {TRUE,FALSE} | FALSE | True | Try to construct a feasible solution from a cover? |
| `constraints/indicator/upgradelinear` | `bool` | {TRUE,FALSE} | FALSE | True | Try to upgrade linear constraints to indicator constraints? |
| `constraints/indicator/usesameslackvar` | `bool` | {TRUE,FALSE} | FALSE | True | Use same slack variable for indicator constraints with common binary variable? |
| `constraints/indicator/sepaalternativelp` | `bool` | {TRUE,FALSE} | FALSE | True | Separate using the alternative LP? |
| `constraints/indicator/forcerestart` | `bool` | {TRUE,FALSE} | FALSE | True | Force restart if absolute gap is 1 or enough binary variables have been fixed? |
| `constraints/indicator/nolinconscont` | `bool` | {TRUE,FALSE} | FALSE | True | Decompose problem (do not generate linear constraint if all variables are continuous)? |
| `constraints/integral/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/integral/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/integral/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/integral/eagerfreq` | `int` | [-1,1073741822] | -1 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/integral/maxprerounds` | `int` | [-1,2147483647] | 0 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/integral/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/integral/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/integral/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/knapsack/sepafreq` | `int` | [-1,1073741822] | 0 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/knapsack/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/knapsack/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/knapsack/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/knapsack/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/knapsack/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/knapsack/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/knapsack/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/linear/upgrade/knapsack` | `bool` | {TRUE,FALSE} | TRUE | False | enable linear upgrading for constraint handler &lt;knapsack&gt; |
| `constraints/knapsack/sepacardfreq` | `int` | [-1,1073741822] | 1 | True | multiplier on separation frequency, how often knapsack cuts are separated (-1: never, 0: only at root) |
| `constraints/knapsack/maxcardbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for separating knapsack cuts |
| `constraints/knapsack/cliqueextractfactor` | `real` | [0,1] | 0.5 | True | lower clique size limit for greedy clique extraction algorithm (relative to largest clique) |
| `constraints/knapsack/maxrounds` | `int` | [-1,2147483647] | 5 | False | maximal number of separation rounds per node (-1: unlimited) |
| `constraints/knapsack/maxroundsroot` | `int` | [-1,2147483647] | -1 | False | maximal number of separation rounds per node in the root node (-1: unlimited) |
| `constraints/knapsack/maxsepacuts` | `int` | [0,2147483647] | 50 | False | maximal number of cuts separated per separation round |
| `constraints/knapsack/maxsepacutsroot` | `int` | [0,2147483647] | 200 | False | maximal number of cuts separated per separation round in the root node |
| `constraints/knapsack/disaggregation` | `bool` | {TRUE,FALSE} | TRUE | True | should disaggregation of knapsack constraints be allowed in preprocessing? |
| `constraints/knapsack/simplifyinequalities` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving try to simplify knapsacks |
| `constraints/knapsack/negatedclique` | `bool` | {TRUE,FALSE} | TRUE | True | should negated clique information be used in solving process |
| `constraints/knapsack/presolpairwise` | `bool` | {TRUE,FALSE} | TRUE | True | should pairwise constraint comparison be performed in presolving? |
| `constraints/knapsack/presolusehashing` | `bool` | {TRUE,FALSE} | TRUE | True | should hash table be used for detecting redundant constraints in advance |
| `constraints/knapsack/dualpresolving` | `bool` | {TRUE,FALSE} | TRUE | True | should dual presolving steps be performed? |
| `constraints/knapsack/usegubs` | `bool` | {TRUE,FALSE} | FALSE | True | should GUB information be used for separation? |
| `constraints/knapsack/detectcutoffbound` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving try to detect constraints parallel to the objective function defining an upper bound and prevent these constraints from entering the LP? |
| `constraints/knapsack/detectlowerbound` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving try to detect constraints parallel to the objective function defining a lower bound and prevent these constraints from entering the LP? |
| `constraints/knapsack/updatecliquepartitions` | `bool` | {TRUE,FALSE} | FALSE | True | should clique partition information be updated when old partition seems outdated? |
| `constraints/knapsack/clqpartupdatefac` | `real` | [1,10] | 1.5 | True | factor on the growth of global cliques to decide when to update a previous (negated) clique partition (used only if updatecliquepartitions is set to TRUE) |
| `constraints/linking/sepafreq` | `int` | [-1,1073741822] | 1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/linking/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/linking/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/linking/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/linking/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/linking/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/linking/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/linking/presoltiming` | `int` | [4,60] | 8 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/linking/linearize` | `bool` | {TRUE,FALSE} | FALSE | False | this constraint will not propagate or separate, linear and setppc are used? |
| `constraints/logicor/sepafreq` | `int` | [-1,1073741822] | 0 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/logicor/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/logicor/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/logicor/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/logicor/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/logicor/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/logicor/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/logicor/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/linear/upgrade/logicor` | `bool` | {TRUE,FALSE} | TRUE | False | enable linear upgrading for constraint handler &lt;logicor&gt; |
| `constraints/logicor/presolpairwise` | `bool` | {TRUE,FALSE} | TRUE | True | should pairwise constraint comparison be performed in presolving? |
| `constraints/logicor/presolusehashing` | `bool` | {TRUE,FALSE} | TRUE | True | should hash table be used for detecting redundant constraints in advance |
| `constraints/logicor/dualpresolving` | `bool` | {TRUE,FALSE} | TRUE | True | should dual presolving steps be performed? |
| `constraints/logicor/negatedclique` | `bool` | {TRUE,FALSE} | TRUE | True | should negated clique information be used in presolving |
| `constraints/logicor/implications` | `bool` | {TRUE,FALSE} | TRUE | True | should implications/cliques be used in presolving |
| `constraints/logicor/strengthen` | `bool` | {TRUE,FALSE} | TRUE | True | should pairwise constraint comparison try to strengthen constraints by removing superflous non-zeros? |
| `constraints/or/sepafreq` | `int` | [-1,1073741822] | 0 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/or/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/or/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/or/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/or/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/or/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/or/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/or/presoltiming` | `int` | [4,60] | 8 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/orbisack/sepafreq` | `int` | [-1,1073741822] | 5 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/orbisack/propfreq` | `int` | [-1,1073741822] | 5 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/orbisack/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/orbisack/eagerfreq` | `int` | [-1,1073741822] | -1 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/orbisack/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/orbisack/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/orbisack/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/orbisack/presoltiming` | `int` | [4,60] | 16 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/orbisack/coverseparation` | `bool` | {TRUE,FALSE} | TRUE | True | Separate cover inequalities for orbisacks? |
| `constraints/orbisack/orbiSeparation` | `bool` | {TRUE,FALSE} | FALSE | True | Separate orbisack inequalities? |
| `constraints/orbisack/coeffbound` | `real` | [0,1.79769313486232e+308] | 1000000 | True | Maximum size of coefficients for orbisack inequalities |
| `constraints/orbisack/checkpporbisack` | `bool` | {TRUE,FALSE} | TRUE | True | Upgrade orbisack constraints to packing/partioning orbisacks? |
| `constraints/orbisack/forceconscopy` | `bool` | {TRUE,FALSE} | FALSE | True | Whether orbisack constraints should be forced to be copied to sub SCIPs. |
| `constraints/orbitope_full/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/orbitope_full/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/orbitope_full/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/orbitope_full/eagerfreq` | `int` | [-1,1073741822] | -1 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/orbitope_full/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/orbitope_full/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/orbitope_full/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/orbitope_full/presoltiming` | `int` | [4,60] | 8 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/orbitope_full/forceconscopy` | `bool` | {TRUE,FALSE} | FALSE | True | Whether orbitope constraints should be forced to be copied to sub SCIPs. |
| `constraints/orbitope_pp/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/orbitope_pp/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/orbitope_pp/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/orbitope_pp/eagerfreq` | `int` | [-1,1073741822] | -1 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/orbitope_pp/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/orbitope_pp/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/orbitope_pp/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/orbitope_pp/presoltiming` | `int` | [4,60] | 8 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/orbitope_pp/forceconscopy` | `bool` | {TRUE,FALSE} | FALSE | True | Whether orbitope constraints should be forced to be copied to sub SCIPs. |
| `constraints/pseudoboolean/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/pseudoboolean/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/pseudoboolean/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/pseudoboolean/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/pseudoboolean/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/pseudoboolean/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/pseudoboolean/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/pseudoboolean/presoltiming` | `int` | [4,60] | 8 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/pseudoboolean/decomposenormal` | `bool` | {TRUE,FALSE} | FALSE | True | decompose every normal pseudo boolean constraint into a "linear" constraint and "and" constraints |
| `constraints/pseudoboolean/decomposeindicator` | `bool` | {TRUE,FALSE} | TRUE | True | decompose every soft pseudo boolean constraint into "indicator" constraints and "and" constraints |
| `constraints/pseudoboolean/nlcseparate` | `bool` | {TRUE,FALSE} | TRUE | True | should the nonlinear constraints be separated during LP processing? |
| `constraints/pseudoboolean/nlcpropagate` | `bool` | {TRUE,FALSE} | TRUE | True | should the nonlinear constraints be propagated during node processing? |
| `constraints/pseudoboolean/nlcremovable` | `bool` | {TRUE,FALSE} | TRUE | True | should the nonlinear constraints be removable? |
| `constraints/setppc/sepafreq` | `int` | [-1,1073741822] | 0 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/setppc/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/setppc/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/setppc/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/setppc/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/setppc/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/setppc/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/setppc/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/linear/upgrade/setppc` | `bool` | {TRUE,FALSE} | TRUE | False | enable linear upgrading for constraint handler &lt;setppc&gt; |
| `constraints/nonlinear/upgrade/setppc` | `bool` | {TRUE,FALSE} | TRUE | False | enable nonlinear upgrading for constraint handler &lt;setppc&gt; |
| `constraints/setppc/npseudobranches` | `int` | [0,2147483647] | 2 | True | number of children created in pseudo branching (0: disable pseudo branching) |
| `constraints/setppc/presolpairwise` | `bool` | {TRUE,FALSE} | TRUE | True | should pairwise constraint comparison be performed in presolving? |
| `constraints/setppc/presolusehashing` | `bool` | {TRUE,FALSE} | TRUE | True | should hash table be used for detecting redundant constraints in advance |
| `constraints/setppc/dualpresolving` | `bool` | {TRUE,FALSE} | TRUE | True | should dual presolving steps be performed? |
| `constraints/setppc/cliquelifting` | `bool` | {TRUE,FALSE} | FALSE | True |  should we try to lift variables into other clique constraints, fix variables, aggregate them, and also shrink the amount of variables in clique constraints |
| `constraints/setppc/addvariablesascliques` | `bool` | {TRUE,FALSE} | FALSE | True | should we try to generate extra cliques out of all binary variables to maybe fasten redundant constraint detection |
| `constraints/setppc/cliqueshrinking` | `bool` | {TRUE,FALSE} | TRUE | True | should we try to shrink the number of variables in a clique constraints, by replacing more than one variable by only one |
| `constraints/SOS1/sepafreq` | `int` | [-1,1073741822] | 10 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/SOS1/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/SOS1/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/SOS1/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/SOS1/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/SOS1/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/SOS1/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/SOS1/presoltiming` | `int` | [4,60] | 8 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/SOS1/maxsosadjacency` | `int` | [-1,2147483647] | 10000 | True | do not create an adjacency matrix if number of SOS1 variables is larger than predefined value (-1: no limit) |
| `constraints/SOS1/maxextensions` | `int` | [-1,2147483647] | 1 | True | maximal number of extensions that will be computed for each SOS1 constraint  (-1: no limit) |
| `constraints/SOS1/maxtightenbds` | `int` | [-1,2147483647] | 5 | True | maximal number of bound tightening rounds per presolving round (-1: no limit) |
| `constraints/SOS1/perfimplanalysis` | `bool` | {TRUE,FALSE} | FALSE | True | if TRUE then perform implication graph analysis (might add additional SOS1 constraints) |
| `constraints/SOS1/depthimplanalysis` | `int` | [-1,2147483647] | -1 | True | number of recursive calls of implication graph analysis (-1: no limit) |
| `constraints/SOS1/conflictprop` | `bool` | {TRUE,FALSE} | TRUE | True | whether to use conflict graph propagation |
| `constraints/SOS1/implprop` | `bool` | {TRUE,FALSE} | TRUE | True | whether to use implication graph propagation |
| `constraints/SOS1/sosconsprop` | `bool` | {TRUE,FALSE} | FALSE | True | whether to use SOS1 constraint propagation |
| `constraints/SOS1/branchingrule` | `char` | {nbs} | n | True | which branching rule should be applied ? ('n': neighborhood, 'b': bipartite, 's': SOS1/clique) (note: in some cases an automatic switching to SOS1 branching is possible) |
| `constraints/SOS1/autosos1branch` | `bool` | {TRUE,FALSE} | TRUE | True | if TRUE then automatically switch to SOS1 branching if the SOS1 constraints do not overlap |
| `constraints/SOS1/fixnonzero` | `bool` | {TRUE,FALSE} | FALSE | True | if neighborhood branching is used, then fix the branching variable (if positive in sign) to the value of the feasibility tolerance |
| `constraints/SOS1/addcomps` | `bool` | {TRUE,FALSE} | FALSE | True | if TRUE then add complementarity constraints to the branching nodes (can be used in combination with neighborhood or bipartite branching) |
| `constraints/SOS1/maxaddcomps` | `int` | [-1,2147483647] | -1 | True | maximal number of complementarity constraints added per branching node (-1: no limit) |
| `constraints/SOS1/addcompsfeas` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | -0.6 | True | minimal feasibility value for complementarity constraints in order to be added to the branching node |
| `constraints/SOS1/addbdsfeas` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1 | True | minimal feasibility value for bound inequalities in order to be added to the branching node |
| `constraints/SOS1/addextendedbds` | `bool` | {TRUE,FALSE} | TRUE | True | should added complementarity constraints be extended to SOS1 constraints to get tighter bound inequalities |
| `constraints/SOS1/branchsos` | `bool` | {TRUE,FALSE} | TRUE | False | Use SOS1 branching in enforcing (otherwise leave decision to branching rules)? This value can only be set to false if all SOS1 variables are binary |
| `constraints/SOS1/branchnonzeros` | `bool` | {TRUE,FALSE} | FALSE | False | Branch on SOS constraint with most number of nonzeros? |
| `constraints/SOS1/branchweight` | `bool` | {TRUE,FALSE} | FALSE | False | Branch on SOS cons. with highest nonzero-variable weight for branching (needs branchnonzeros = false)? |
| `constraints/SOS1/addcompsdepth` | `int` | [-1,2147483647] | 30 | True | only add complementarity constraints to branching nodes for predefined depth (-1: no limit) |
| `constraints/SOS1/nstrongrounds` | `int` | [-1,2147483647] | 0 | True | maximal number of strong branching rounds to perform for each node (-1: auto); only available for neighborhood and bipartite branching |
| `constraints/SOS1/nstrongiter` | `int` | [-2,2147483647] | 10000 | True | maximal number LP iterations to perform for each strong branching round (-2: auto, -1: no limit) |
| `constraints/SOS1/boundcutsfromsos1` | `bool` | {TRUE,FALSE} | FALSE | True | if TRUE separate bound inequalities from initial SOS1 constraints |
| `constraints/SOS1/boundcutsfromgraph` | `bool` | {TRUE,FALSE} | TRUE | True | if TRUE separate bound inequalities from the conflict graph |
| `constraints/SOS1/autocutsfromsos1` | `bool` | {TRUE,FALSE} | TRUE | True | if TRUE then automatically switch to separating initial SOS1 constraints if the SOS1 constraints do not overlap |
| `constraints/SOS1/boundcutsfreq` | `int` | [-1,1073741822] | 10 | True | frequency for separating bound cuts; zero means to separate only in the root node |
| `constraints/SOS1/boundcutsdepth` | `int` | [-1,2147483647] | 40 | True | node depth of separating bound cuts (-1: no limit) |
| `constraints/SOS1/maxboundcuts` | `int` | [0,2147483647] | 50 | True | maximal number of bound cuts separated per branching node |
| `constraints/SOS1/maxboundcutsroot` | `int` | [0,2147483647] | 150 | True | maximal number of bound cuts separated per iteration in the root node |
| `constraints/SOS1/strthenboundcuts` | `bool` | {TRUE,FALSE} | TRUE | True | if TRUE then bound cuts are strengthened in case bound variables are available |
| `constraints/SOS1/implcutsfreq` | `int` | [-1,1073741822] | 0 | True | frequency for separating implied bound cuts; zero means to separate only in the root node |
| `constraints/SOS1/implcutsdepth` | `int` | [-1,2147483647] | 40 | True | node depth of separating implied bound cuts (-1: no limit) |
| `constraints/SOS1/maximplcuts` | `int` | [0,2147483647] | 50 | True | maximal number of implied bound cuts separated per branching node |
| `constraints/SOS1/maximplcutsroot` | `int` | [0,2147483647] | 150 | True | maximal number of implied bound cuts separated per iteration in the root node |
| `constraints/SOS2/sepafreq` | `int` | [-1,1073741822] | 0 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/SOS2/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/SOS2/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/SOS2/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/SOS2/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/SOS2/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/SOS2/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/SOS2/presoltiming` | `int` | [4,60] | 4 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/superindicator/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/superindicator/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/superindicator/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/superindicator/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/superindicator/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/superindicator/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/superindicator/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/superindicator/presoltiming` | `int` | [4,60] | 8 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/superindicator/checkslacktype` | `bool` | {TRUE,FALSE} | TRUE | True | should type of slack constraint be checked when creating superindicator constraint? |
| `constraints/superindicator/maxupgdcoeflinear` | `real` | [0,1e+15] | 10000 | True | maximum big-M coefficient of binary variable in upgrade to a linear constraint (relative to smallest coefficient) |
| `constraints/superindicator/upgdprioindicator` | `int` | [-1,2147483647] | 1 | True | priority for upgrading to an indicator constraint (-1: never) |
| `constraints/superindicator/upgdpriolinear` | `int` | [-1,2147483647] | 2 | True | priority for upgrading to an indicator constraint (-1: never) |
| `constraints/symresack/sepafreq` | `int` | [-1,1073741822] | 5 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/symresack/propfreq` | `int` | [-1,1073741822] | 5 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/symresack/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/symresack/eagerfreq` | `int` | [-1,1073741822] | -1 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/symresack/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/symresack/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/symresack/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/symresack/presoltiming` | `int` | [4,60] | 16 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/symresack/ppsymresack` | `bool` | {TRUE,FALSE} | TRUE | True | Upgrade symresack constraints to packing/partioning symresacks? |
| `constraints/symresack/checkmonotonicity` | `bool` | {TRUE,FALSE} | TRUE | True | Check whether permutation is monotone when upgrading to packing/partioning symresacks? |
| `constraints/symresack/forceconscopy` | `bool` | {TRUE,FALSE} | FALSE | True | Whether symresack constraints should be forced to be copied to sub SCIPs. |
| `constraints/varbound/sepafreq` | `int` | [-1,1073741822] | 0 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/varbound/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/varbound/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/varbound/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/varbound/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/varbound/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/varbound/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/varbound/presoltiming` | `int` | [4,60] | 12 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/linear/upgrade/varbound` | `bool` | {TRUE,FALSE} | TRUE | False | enable linear upgrading for constraint handler &lt;varbound&gt; |
| `constraints/varbound/presolpairwise` | `bool` | {TRUE,FALSE} | TRUE | True | should pairwise constraint comparison be performed in presolving? |
| `constraints/varbound/maxlpcoef` | `real` | [0,1e+20] | 1000000000 | True | maximum coefficient in varbound constraint to be added as a row into LP |
| `constraints/varbound/usebdwidening` | `bool` | {TRUE,FALSE} | TRUE | False | should bound widening be used in conflict analysis? |
| `constraints/xor/sepafreq` | `int` | [-1,1073741822] | 0 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/xor/propfreq` | `int` | [-1,1073741822] | 1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/xor/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/xor/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/xor/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/xor/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/xor/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/xor/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/linear/upgrade/xor` | `bool` | {TRUE,FALSE} | TRUE | False | enable linear upgrading for constraint handler &lt;xor&gt; |
| `constraints/xor/presolpairwise` | `bool` | {TRUE,FALSE} | TRUE | True | should pairwise constraint comparison be performed in presolving? |
| `constraints/xor/presolusehashing` | `bool` | {TRUE,FALSE} | TRUE | True | should hash table be used for detecting redundant constraints in advance? |
| `constraints/xor/addextendedform` | `bool` | {TRUE,FALSE} | FALSE | True | should the extended formulation be added in presolving? |
| `constraints/xor/addflowextended` | `bool` | {TRUE,FALSE} | FALSE | True | should the extended flow formulation be added (nonsymmetric formulation otherwise)? |
| `constraints/xor/separateparity` | `bool` | {TRUE,FALSE} | FALSE | True | should parity inequalities be separated? |
| `constraints/xor/gausspropfreq` | `int` | [-1,1073741822] | 5 | True | frequency for applying the Gauss propagator |
| `constraints/components/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/components/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/components/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/components/eagerfreq` | `int` | [-1,1073741822] | -1 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/components/maxprerounds` | `int` | [-1,2147483647] | -1 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/components/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/components/delayprop` | `bool` | {TRUE,FALSE} | TRUE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/components/presoltiming` | `int` | [4,60] | 32 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/components/maxdepth` | `int` | [-1,2147483647] | 2147483647 | False | maximum depth of a node to run components detection (-1: disable component detection during solving) |
| `constraints/components/maxintvars` | `int` | [-1,2147483647] | 200 | True | maximum number of integer (or binary) variables to solve a subproblem during presolving (-1: unlimited) |
| `constraints/components/minsize` | `int` | [0,2147483647] | 50 | True | minimum absolute size (in terms of variables) to solve a component individually during branch-and-bound |
| `constraints/components/minrelsize` | `real` | [0,1] | 0.1 | True | minimum relative size (in terms of variables) to solve a component individually during branch-and-bound |
| `constraints/components/nodelimit` | `longint` | [-1,9223372036854775807] | 10000 | False | maximum number of nodes to be solved in subproblems during presolving |
| `constraints/components/maxcompweight` | `real` | [0,1.79769313486232e+308] | 200 | False | the maximum weight of a component, in terms of the used factors |
| `constraints/components/intfactor` | `real` | [0,1.79769313486232e+308] | 1 | False | the weight of an integer variable compared to binary variables |
| `constraints/components/contfactor` | `real` | [0,1.79769313486232e+308] | 0.2 | False | the weight of a continuous variable compared to binary variables |
| `constraints/components/feastolfactor` | `real` | [0,1000000] | 1 | True | factor to increase the feasibility tolerance of the main SCIP in all sub-SCIPs, default value 1.0 |
| `constraints/benders/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/benders/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/benders/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/benders/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/benders/maxprerounds` | `int` | [-1,2147483647] | 0 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/benders/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/benders/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/benders/presoltiming` | `int` | [4,60] | 4 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/benders/active` | `bool` | {TRUE,FALSE} | FALSE | False | is the Benders' decomposition constraint handler active? |
| `constraints/benderslp/sepafreq` | `int` | [-1,1073741822] | -1 | False | frequency for separating cuts (-1: never, 0: only in root node) |
| `constraints/benderslp/propfreq` | `int` | [-1,1073741822] | -1 | False | frequency for propagating domains (-1: never, 0: only in root node) |
| `constraints/benderslp/proptiming` | `int` | [1,15] | 1 | True | timing when constraint propagation should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS) |
| `constraints/benderslp/eagerfreq` | `int` | [-1,1073741822] | 100 | True | frequency for using all instead of only the useful constraints in separation, propagation and enforcement (-1: never, 0: only in first evaluation) |
| `constraints/benderslp/maxprerounds` | `int` | [-1,2147483647] | 0 | True | maximal number of presolving rounds the constraint handler participates in (-1: no limit) |
| `constraints/benderslp/delaysepa` | `bool` | {TRUE,FALSE} | FALSE | True | should separation method be delayed, if other separators found cuts? |
| `constraints/benderslp/delayprop` | `bool` | {TRUE,FALSE} | FALSE | True | should propagation method be delayed, if other propagators found reductions? |
| `constraints/benderslp/presoltiming` | `int` | [4,60] | 28 | True | timing mask of the constraint handler's presolving method (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `constraints/benderslp/maxdepth` | `int` | [-1,1073741822] | 0 | True | depth at which Benders' decomposition cuts are generated from the LP solution (-1: always, 0: only at root) |
| `constraints/benderslp/depthfreq` | `int` | [0,1073741822] | 0 | True | the depth frequency for generating LP cuts after the max depth is reached (0: never, 1: all nodes, ...) |
| `constraints/benderslp/stalllimit` | `int` | [0,2147483647] | 100 | True | the number of nodes processed without a dual bound improvement before enforcing the LP relaxation, 0: no stall count applied |
| `constraints/benderslp/iterlimit` | `int` | [0,2147483647] | 100 | True | after the root node, only iterlimit fractional LP solutions are used at each node to generate Benders' decomposition cuts. |
| `constraints/benderslp/active` | `bool` | {TRUE,FALSE} | FALSE | False | is the Benders' decomposition LP cut constraint handler active? |

## cutselection

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `cutselection/hybrid/priority` | `int` | [-536870912,1073741823] | 8000 | False | priority of cut selection rule &lt;hybrid&gt; |
| `cutselection/hybrid/efficacyweight` | `real` | [0,1e+98] | 1 | False | weight of efficacy in cut score calculation |
| `cutselection/hybrid/dircutoffdistweight` | `real` | [0,1e+98] | 0 | False | weight of directed cutoff distance in cut score calculation |
| `cutselection/hybrid/objparalweight` | `real` | [0,1e+98] | 0.1 | False | weight of objective parallelism in cut score calculation |
| `cutselection/hybrid/intsupportweight` | `real` | [0,1e+98] | 0.1 | False | weight of integral support in cut score calculation |
| `cutselection/hybrid/minortho` | `real` | [0,1] | 0.9 | False | minimal orthogonality for a cut to enter the LP |
| `cutselection/hybrid/minorthoroot` | `real` | [0,1] | 0.9 | False | minimal orthogonality for a cut to enter the LP in the root node |
| `cutselection/ensemble/priority` | `int` | [-536870912,1073741823] | 7000 | False | priority of cut selection rule &lt;ensemble&gt; |
| `cutselection/ensemble/efficacyweight` | `real` | [0,1e+98] | 0.75 | False | weight of normed-efficacy in cut score calculation |
| `cutselection/ensemble/dircutoffdistweight` | `real` | [0,1e+98] | 0 | False | weight of normed-directed cutoff distance in cut score calculation |
| `cutselection/ensemble/objparalweight` | `real` | [0,1e+98] | 0.25 | False | weight of objective parallelism in cut score calculation |
| `cutselection/ensemble/intsupportweight` | `real` | [0,1e+98] | 0.45 | False | weight of integral support in cut score calculation |
| `cutselection/ensemble/expimprovweight` | `real` | [0,1e+98] | 0.1 | False | weight of normed-expected obj improvement in cut score calculation |
| `cutselection/ensemble/minscore` | `real` | [-1e+98,1e+98] | 0 | False | minimum score s.t. a cut can be added |
| `cutselection/ensemble/pscostweight` | `real` | [0,1e+98] | 0.75 | False | weight of normed-pseudo-costs in cut score calculation |
| `cutselection/ensemble/locksweight` | `real` | [0,1e+98] | 0.25 | False | weight of normed-num-locks in cut score calculation |
| `cutselection/ensemble/maxsparsitybonus` | `real` | [0,1e+98] | 0.5 | False | weight of maximum sparsity reward in cut score calculation |
| `cutselection/ensemble/goodnumericsbonus` | `real` | [0,1e+98] | 0 | False | weight of good numerics bonus (ratio of coefficients) in cut score calculation |
| `cutselection/ensemble/endsparsitybonus` | `real` | [0,1e+98] | 0.2 | False | max sparsity value for which a bonus is applied in cut score calculation |
| `cutselection/ensemble/maxparal` | `real` | [0,1] | 0.95 | False | threshold for when two cuts are considered parallel to each other |
| `cutselection/ensemble/paralpenalty` | `real` | [0,1e+98] | 0.25 | True | penalty for weaker of two parallel cuts if penalising parallel cuts |
| `cutselection/ensemble/maxcutdensity` | `real` | [0,1] | 0.425 | True | max allowed cut density if filtering dense cuts |
| `cutselection/ensemble/maxnonzerorootround` | `real` | [0,1e+98] | 4.5 | False | max non-zeros per round applied cuts (root). multiple num LP cols. |
| `cutselection/ensemble/maxnonzerotreeround` | `real` | [0,1e+98] | 9.5 | False | max non-zeros per round applied cuts (tree). multiple num LP cols. |
| `cutselection/ensemble/filterparalcuts` | `bool` | {TRUE,FALSE} | FALSE | False | should cuts be filtered so no two parallel cuts are added |
| `cutselection/ensemble/penaliseparalcuts` | `bool` | {TRUE,FALSE} | TRUE | True | should two parallel cuts be penalised instead of outright filtered |
| `cutselection/ensemble/filterdensecuts` | `bool` | {TRUE,FALSE} | TRUE | True | should cuts over a given density threshold be filtered |
| `cutselection/ensemble/penaliselocks` | `bool` | {TRUE,FALSE} | TRUE | True | should the number of locks be penalised instead of rewarded |
| `cutselection/ensemble/penaliseobjparal` | `bool` | {TRUE,FALSE} | TRUE | True | should objective parallelism be penalised instead of rewarded |
| `cutselection/ensemble/maxcoefratiobonus` | `int` | [1,1000000] | 10000 | True | max coefficient ratio for which numeric bonus is applied. |
| `cutselection/ensemble/maxcuts` | `int` | [1,1000000] | 200 | True | max number of cuts such that cut selector is applied. |
| `cutselection/ensemble/maxnumvars` | `int` | [1,1000000] | 50000 | True | max number of variables such that cut selector is applied. |
| `cutselection/dynamic/priority` | `int` | [-536870912,1073741823] | 7000 | False | priority of cut selection rule &lt;dynamic&gt; |
| `cutselection/dynamic/efficacyweight` | `real` | [0,1e+98] | 1 | False | weight of efficacy in cut score calculation |
| `cutselection/dynamic/dircutoffdistweight` | `real` | [0,1e+98] | 0 | False | weight of directed cutoff distance in cut score calculation |
| `cutselection/dynamic/objparalweight` | `real` | [0,1e+98] | 0 | False | weight of objective parallelism in cut score calculation |
| `cutselection/dynamic/intsupportweight` | `real` | [0,1e+98] | 0 | False | weight of integral support in cut score calculation |
| `cutselection/dynamic/mingain` | `real` | [0,1] | 0.01 | False | minimal efficacy gain for a cut to enter the LP |
| `cutselection/dynamic/filtermode` | `char` | {df} | d | False | filtering strategy during cut selection |
| `cutselection/dynamic/minortho` | `real` | [0,1] | 0.9 | False | minimal orthogonality for a cut to enter the LP |
| `cutselection/dynamic/maxdepth` | `int` | [-1,1073741822] | -1 | False | maximum depth at which this cutselector is employed |

## decomposition

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `decomposition/benderslabels` | `bool` | {TRUE,FALSE} | FALSE | False | should the variables be labelled for the application of Benders' decomposition? |
| `decomposition/applybenders` | `bool` | {TRUE,FALSE} | FALSE | False | if a decomposition exists, should Benders' decomposition be applied? |
| `decomposition/maxgraphedge` | `int` | [-1,2147483647] | 10000 | False | maximum number of edges in block graph computation (-1: no limit, 0: disable block graph computation) |
| `decomposition/disablemeasures` | `bool` | {TRUE,FALSE} | FALSE | False | disable expensive measures |

## display

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `display/verblevel` | `int` | [0,5] | 4 | False | verbosity level of output |
| `display/width` | `int` | [0,2147483647] | 143 | False | maximal number of characters in a node information line |
| `display/freq` | `int` | [-1,2147483647] | 100 | False | frequency for displaying node information lines |
| `display/headerfreq` | `int` | [-1,2147483647] | 15 | False | frequency for displaying header lines (every n'th node information line) |
| `display/lpinfo` | `bool` | {TRUE,FALSE} | FALSE | False | should the LP solver display status messages? |
| `display/allviols` | `bool` | {TRUE,FALSE} | FALSE | False | display all violations for a given start solution / the best solution after the solving process? |
| `display/relevantstats` | `bool` | {TRUE,FALSE} | TRUE | False | should the relevant statistics be displayed at the end of solving? |
| `display/sols/active` | `int` | [0,2] | 0 | False | display activation status of display column &lt;sols&gt; (0: off, 1: auto, 2:on) |
| `display/feasST/active` | `int` | [0,2] | 0 | False | display activation status of display column &lt;feasST&gt; (0: off, 1: auto, 2:on) |
| `display/completed/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;completed&gt; (0: off, 1: auto, 2:on) |
| `display/nrank1nodes/active` | `int` | [0,2] | 0 | False | display activation status of display column &lt;nrank1nodes&gt; (0: off, 1: auto, 2:on) |
| `display/nnodesbelowinc/active` | `int` | [0,2] | 0 | False | display activation status of display column &lt;nnodesbelowinc&gt; (0: off, 1: auto, 2:on) |
| `display/solfound/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;solfound&gt; (0: off, 1: auto, 2:on) |
| `display/concsolfound/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;concsolfound&gt; (0: off, 1: auto, 2:on) |
| `display/time/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;time&gt; (0: off, 1: auto, 2:on) |
| `display/nnodes/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;nnodes&gt; (0: off, 1: auto, 2:on) |
| `display/nodesleft/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;nodesleft&gt; (0: off, 1: auto, 2:on) |
| `display/nobjleaves/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;nobjleaves&gt; (0: off, 1: auto, 2:on) |
| `display/ninfeasleaves/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;ninfeasleaves&gt; (0: off, 1: auto, 2:on) |
| `display/lpiterations/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;lpiterations&gt; (0: off, 1: auto, 2:on) |
| `display/lpavgiterations/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;lpavgiterations&gt; (0: off, 1: auto, 2:on) |
| `display/lpcond/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;lpcond&gt; (0: off, 1: auto, 2:on) |
| `display/memused/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;memused&gt; (0: off, 1: auto, 2:on) |
| `display/concmemused/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;concmemused&gt; (0: off, 1: auto, 2:on) |
| `display/memtotal/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;memtotal&gt; (0: off, 1: auto, 2:on) |
| `display/depth/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;depth&gt; (0: off, 1: auto, 2:on) |
| `display/maxdepth/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;maxdepth&gt; (0: off, 1: auto, 2:on) |
| `display/plungedepth/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;plungedepth&gt; (0: off, 1: auto, 2:on) |
| `display/nfrac/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;nfrac&gt; (0: off, 1: auto, 2:on) |
| `display/nexternbranchcands/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;nexternbranchcands&gt; (0: off, 1: auto, 2:on) |
| `display/vars/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;vars&gt; (0: off, 1: auto, 2:on) |
| `display/conss/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;conss&gt; (0: off, 1: auto, 2:on) |
| `display/curconss/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;curconss&gt; (0: off, 1: auto, 2:on) |
| `display/curcols/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;curcols&gt; (0: off, 1: auto, 2:on) |
| `display/currows/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;currows&gt; (0: off, 1: auto, 2:on) |
| `display/cuts/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;cuts&gt; (0: off, 1: auto, 2:on) |
| `display/separounds/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;separounds&gt; (0: off, 1: auto, 2:on) |
| `display/poolsize/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;poolsize&gt; (0: off, 1: auto, 2:on) |
| `display/conflicts/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;conflicts&gt; (0: off, 1: auto, 2:on) |
| `display/strongbranchs/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;strongbranchs&gt; (0: off, 1: auto, 2:on) |
| `display/pseudoobj/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;pseudoobj&gt; (0: off, 1: auto, 2:on) |
| `display/lpobj/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;lpobj&gt; (0: off, 1: auto, 2:on) |
| `display/curdualbound/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;curdualbound&gt; (0: off, 1: auto, 2:on) |
| `display/estimate/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;estimate&gt; (0: off, 1: auto, 2:on) |
| `display/avgdualbound/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;avgdualbound&gt; (0: off, 1: auto, 2:on) |
| `display/dualbound/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;dualbound&gt; (0: off, 1: auto, 2:on) |
| `display/primalbound/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;primalbound&gt; (0: off, 1: auto, 2:on) |
| `display/concdualbound/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;concdualbound&gt; (0: off, 1: auto, 2:on) |
| `display/concprimalbound/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;concprimalbound&gt; (0: off, 1: auto, 2:on) |
| `display/cutoffbound/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;cutoffbound&gt; (0: off, 1: auto, 2:on) |
| `display/gap/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;gap&gt; (0: off, 1: auto, 2:on) |
| `display/concgap/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;concgap&gt; (0: off, 1: auto, 2:on) |
| `display/primalgap/active` | `int` | [0,2] | 0 | False | display activation status of display column &lt;primalgap&gt; (0: off, 1: auto, 2:on) |
| `display/nsols/active` | `int` | [0,2] | 1 | False | display activation status of display column &lt;nsols&gt; (0: off, 1: auto, 2:on) |

## estimation

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `estimation/restarts/restartpolicy` | `char` | {acen} | e | False | restart policy: (a)lways, (c)ompletion, (e)stimation, (n)ever |
| `estimation/method` | `char` | {bceglostw} | w | False | tree size estimation method: (c)ompletion, (e)nsemble, time series forecasts on either (g)ap, (l)eaf frequency, (o)open nodes, tree (w)eight, (s)sg, or (t)ree profile or w(b)e |
| `estimation/restarts/restartlimit` | `int` | [-1,2147483647] | 1 | False | restart limit |
| `estimation/restarts/minnodes` | `longint` | [-1,9223372036854775807] | 1000 | False | minimum number of nodes before restart |
| `estimation/restarts/countonlyleaves` | `bool` | {TRUE,FALSE} | FALSE | False | should only leaves count for the minnodes parameter? |
| `estimation/restarts/restartfactor` | `real` | [1,1.79769313486232e+308] | 50 | False | factor by which the estimated number of nodes should exceed the current number of nodes |
| `estimation/restarts/restartnonlinear` | `bool` | {TRUE,FALSE} | FALSE | False | whether to apply a restart when nonlinear constraints are present |
| `estimation/restarts/restartactpricers` | `bool` | {TRUE,FALSE} | FALSE | False | whether to apply a restart when active pricers are used |
| `estimation/coefmonoweight` | `real` | [0,1] | 0.3667 | False | coefficient of tree weight in monotone approximation of search completion |
| `estimation/coefmonossg` | `real` | [0,1] | 0.6333 | False | coefficient of 1 - SSG in monotone approximation of search completion |
| `estimation/restarts/hitcounterlim` | `int` | [1,2147483647] | 50 | False | limit on the number of successive samples to really trigger a restart |
| `estimation/reportfreq` | `int` | [-1,1073741823] | -1 | True | report frequency on estimation: -1: never, 0:always, k &gt;= 1: k times evenly during search |
| `estimation/regforestfilename` | `string` | String; interpretation stated in description | "-" | False | user regression forest in RFCSV format |
| `estimation/completiontype` | `char` | {agmrsw} | a | False | approximation of search tree completion: (a)uto, (g)ap, tree (w)eight, (m)onotone regression, (r)egression forest, (s)sg |
| `estimation/treeprofile/enabled` | `bool` | {TRUE,FALSE} | FALSE | False | should the event handler collect data? |
| `estimation/treeprofile/minnodesperdepth` | `real` | [1,1.79769313486232e+308] | 20 | False | minimum average number of nodes at each depth before producing estimations |
| `estimation/useleafts` | `bool` | {TRUE,FALSE} | TRUE | True | use leaf nodes as basic observations for time series, or all nodes? |
| `estimation/showstats` | `bool` | {TRUE,FALSE} | FALSE | True | should statistics be shown at the end? |
| `estimation/ssg/nmaxsubtrees` | `int` | [-1,1073741823] | -1 | False | the maximum number of individual SSG subtrees; -1: no limit |
| `estimation/ssg/nminnodeslastsplit` | `longint` | [0,9223372036854775807] | 0 | False | minimum number of nodes to process between two consecutive SSG splits |

## expr

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `expr/log/minzerodistance` | `real` | [0,1] | 1e-09 | False | minimal distance from zero to enforce for child in bound tightening |
| `expr/pow/minzerodistance` | `real` | [0,1] | 1e-09 | False | minimal distance from zero to enforce for child in bound tightening |
| `expr/pow/expandmaxexponent` | `int` | [1,2147483647] | 2 | False | maximal exponent when to expand power of sum in simplify |
| `expr/pow/distribfracexponent` | `bool` | {TRUE,FALSE} | FALSE | False | whether a fractional exponent is distributed onto factors on power of product |
| `expr/prod/expandalways` | `bool` | {TRUE,FALSE} | FALSE | False | whether to expand products of a sum and several factors in simplify |

## heuristics

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `heuristics/useuctsubscip` | `bool` | {TRUE,FALSE} | FALSE | True | should setting of common subscip parameters include the activation of the UCT node selector? |
| `heuristics/dks/priority` | `int` | [-536870912,536870911] | -1102500 | True | priority of heuristic &lt;dks&gt; |
| `heuristics/dks/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;dks&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/dks/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;dks&gt; |
| `heuristics/dks/maxdepth` | `int` | [-1,1073741822] | 0 | True | maximal depth level to call primal heuristic &lt;dks&gt; (-1: no limit) |
| `heuristics/dks/maxbucks` | `int` | [1,100] | 20 | True | maximal number of buckets to be investigated |
| `heuristics/dks/kernelsizefactor` | `real` | [1,10] | 2 | True | factor with which the initial kernel size can grow max |
| `heuristics/dks/addUseConss` | `bool` | {TRUE,FALSE} | TRUE | True | should a constraint be added ensuring that bucket variables are used? |
| `heuristics/dks/linkbucksize` | `bool` | {TRUE,FALSE} | TRUE | True | should the linking variables in the kernel influence the size of the buckets? |
| `heuristics/dks/translbkernel` | `bool` | {TRUE,FALSE} | TRUE | True | should a variable with different lower bound in transformed and original problem be in the kernel? |
| `heuristics/dks/lesslockskernel` | `bool` | {TRUE,FALSE} | FALSE | True | should a variable with max one uplock and one downlock be in the kernel? |
| `heuristics/dks/usetransprob` | `bool` | {TRUE,FALSE} | TRUE | True | should dks use the transformed problem? |
| `heuristics/dks/buckmaxgap` | `real` | [0,1] | 0.01 | True | defines the maximum mipgap a bucket can be solved to |
| `heuristics/dks/maxlinkscore` | `real` | [0,1] | 1 | True | defines a bound to the linkscore of the decomp |
| `heuristics/dks/maxbuckfrac` | `real` | [0,1] | 0.1 | True | defines a maximal share of bin/int variables for a bucket to be respected |
| `heuristics/dks/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in all subproblems |
| `heuristics/dks/usetwolevel` | `bool` | {TRUE,FALSE} | TRUE | False | should a two level bucket structure be used if possible? |
| `heuristics/dks/usedecomp` | `bool` | {TRUE,FALSE} | TRUE | False | should a decomposition be used if given? |
| `heuristics/dks/usebestsol` | `bool` | {TRUE,FALSE} | TRUE | False | should the best solution instead of the LP solution be used? |
| `heuristics/dks/redcostsort` | `bool` | {TRUE,FALSE} | TRUE | False | should the bucket variables be sorted by reduced costs in the LP solution? |
| `heuristics/dks/primalonly` | `bool` | {TRUE,FALSE} | FALSE | False | should the heuristic terminate after the first primal solution is found? |
| `heuristics/dks/redcostlogsort` | `bool` | {TRUE,FALSE} | TRUE | False | should the bucket variables be sorted logarithmically by reduced costs in the LP solution? |
| `heuristics/dks/objcutoff` | `bool` | {TRUE,FALSE} | TRUE | False | should the next solution at least satisfy the old objective? |
| `heuristics/dks/runbinprobsonly` | `bool` | {TRUE,FALSE} | FALSE | False | should the heuristic be used only for binary problems or problems with integer and binary variables? |
| `heuristics/dps/priority` | `int` | [-536870912,536870911] | 75000 | True | priority of heuristic &lt;dps&gt; |
| `heuristics/dps/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;dps&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/dps/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;dps&gt; |
| `heuristics/dps/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;dps&gt; (-1: no limit) |
| `heuristics/dps/maxiterations` | `int` | [1,2147483647] | 50 | False | maximal number of iterations |
| `heuristics/dps/maxlinkscore` | `real` | [0,1] | 1 | False | maximal linking score of used decomposition (equivalent to percentage of linking constraints) |
| `heuristics/dps/penalty` | `real` | [0,1.79769313486232e+308] | 100 | False | multiplier for absolute increase of penalty parameters (0: no increase) |
| `heuristics/dps/reoptimize` | `bool` | {TRUE,FALSE} | FALSE | False | should the problem get reoptimized with the original objective function? |
| `heuristics/dps/reuse` | `bool` | {TRUE,FALSE} | FALSE | False | should solutions get reused in subproblems? |
| `heuristics/dps/reoptlimits` | `bool` | {TRUE,FALSE} | TRUE | False | should strict limits for reoptimization be set? |
| `heuristics/dps/timing` | `int` | [0,2] | 0 | False | should the heuristic run before or after the processing of the node? (0: before, 1: after, 2: both) |
| `heuristics/padm/priority` | `int` | [-536870912,536870911] | 70000 | True | priority of heuristic &lt;padm&gt; |
| `heuristics/padm/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;padm&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/padm/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;padm&gt; |
| `heuristics/padm/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;padm&gt; (-1: no limit) |
| `heuristics/padm/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in all subproblems |
| `heuristics/padm/minnodes` | `longint` | [0,9223372036854775807] | 50 | True | minimum number of nodes to regard in one subproblem |
| `heuristics/padm/nodefac` | `real` | [0,0.99] | 0.8 | True | factor to control nodelimits of subproblems |
| `heuristics/padm/admiterations` | `int` | [1,100] | 4 | True | maximal number of ADM iterations in each penalty loop |
| `heuristics/padm/penaltyiterations` | `int` | [1,100000] | 100 | True | maximal number of penalty iterations |
| `heuristics/padm/gap` | `real` | [0,16] | 2 | True | mipgap at start |
| `heuristics/padm/reoptimize` | `bool` | {TRUE,FALSE} | TRUE | False | should the problem get reoptimized with the original objective function? |
| `heuristics/padm/scaling` | `bool` | {TRUE,FALSE} | TRUE | True | enable sigmoid rescaling of penalty parameters |
| `heuristics/padm/assignlinking` | `bool` | {TRUE,FALSE} | TRUE | False | should linking constraints be assigned? |
| `heuristics/padm/original` | `bool` | {TRUE,FALSE} | FALSE | True | should the original problem be used? This is only for testing and not recommended! |
| `heuristics/padm/timing` | `int` | [0,2] | 0 | False | should the heuristic run before or after the processing of the node? (0: before, 1: after, 2: both) |
| `heuristics/ofins/priority` | `int` | [-536870912,536870911] | 60000 | True | priority of heuristic &lt;ofins&gt; |
| `heuristics/ofins/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;ofins&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/ofins/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;ofins&gt; |
| `heuristics/ofins/maxdepth` | `int` | [-1,1073741822] | 0 | True | maximal depth level to call primal heuristic &lt;ofins&gt; (-1: no limit) |
| `heuristics/ofins/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/ofins/minnodes` | `longint` | [0,9223372036854775807] | 50 | True | minimum number of nodes required to start the subproblem |
| `heuristics/ofins/maxchangerate` | `real` | [0,1] | 0.5 | False | maximal rate of changed coefficients |
| `heuristics/ofins/maxchange` | `real` | [0,1] | 0.04 | False | maximal rate of change per coefficient to get fixed |
| `heuristics/ofins/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/ofins/addallsols` | `bool` | {TRUE,FALSE} | FALSE | True | should all subproblem solutions be added to the original SCIP? |
| `heuristics/ofins/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/ofins/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/ofins/minimprove` | `real` | [0,1] | 0.01 | True | factor by which RENS should at least improve the incumbent |
| `heuristics/ofins/lplimfac` | `real` | [1,1.79769313486232e+308] | 2 | True | factor by which the limit on the number of LP depends on the node limit |
| `heuristics/reoptsols/priority` | `int` | [-536870912,536870911] | 40000 | True | priority of heuristic &lt;reoptsols&gt; |
| `heuristics/reoptsols/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;reoptsols&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/reoptsols/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;reoptsols&gt; |
| `heuristics/reoptsols/maxdepth` | `int` | [-1,1073741822] | 0 | True | maximal depth level to call primal heuristic &lt;reoptsols&gt; (-1: no limit) |
| `heuristics/reoptsols/maxsols` | `int` | [-1,2147483647] | 1000 | True | maximal number solutions which should be checked. (-1: all) |
| `heuristics/reoptsols/maxruns` | `int` | [-1,2147483647] | -1 | True | check solutions of the last k runs. (-1: all) |
| `heuristics/trivialnegation/priority` | `int` | [-536870912,536870911] | 39990 | True | priority of heuristic &lt;trivialnegation&gt; |
| `heuristics/trivialnegation/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;trivialnegation&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/trivialnegation/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;trivialnegation&gt; |
| `heuristics/trivialnegation/maxdepth` | `int` | [-1,1073741822] | 0 | True | maximal depth level to call primal heuristic &lt;trivialnegation&gt; (-1: no limit) |
| `heuristics/trivial/priority` | `int` | [-536870912,536870911] | 10000 | True | priority of heuristic &lt;trivial&gt; |
| `heuristics/trivial/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;trivial&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/trivial/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;trivial&gt; |
| `heuristics/trivial/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;trivial&gt; (-1: no limit) |
| `heuristics/clique/priority` | `int` | [-536870912,536870911] | 5000 | True | priority of heuristic &lt;clique&gt; |
| `heuristics/clique/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;clique&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/clique/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;clique&gt; |
| `heuristics/clique/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;clique&gt; (-1: no limit) |
| `heuristics/clique/minintfixingrate` | `real` | [0,1] | 0.65 | False | minimum percentage of integer variables that have to be fixable |
| `heuristics/clique/minmipfixingrate` | `real` | [0,1] | 0.65 | False | minimum percentage of fixed variables in the sub-MIP |
| `heuristics/clique/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/clique/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/clique/minnodes` | `longint` | [0,9223372036854775807] | 500 | True | minimum number of nodes required to start the subproblem |
| `heuristics/clique/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/clique/minimprove` | `real` | [0,1] | 0.01 | True | factor by which clique heuristic should at least improve the incumbent |
| `heuristics/clique/maxproprounds` | `int` | [-1,536870911] | 2 | True | maximum number of propagation rounds during probing (-1 infinity) |
| `heuristics/clique/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/clique/uselockfixings` | `bool` | {TRUE,FALSE} | FALSE | True | should more variables be fixed based on variable locks if the fixing rate was not reached? |
| `heuristics/clique/maxbacktracks` | `int` | [-1,536870911] | 10 | True | maximum number of backtracks during the fixing process |
| `heuristics/locks/priority` | `int` | [-536870912,536870911] | 3000 | True | priority of heuristic &lt;locks&gt; |
| `heuristics/locks/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;locks&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/locks/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;locks&gt; |
| `heuristics/locks/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;locks&gt; (-1: no limit) |
| `heuristics/locks/maxproprounds` | `int` | [-2,2147483647] | 2 | True | maximum number of propagation rounds to be performed in each propagation call (-1: no limit, -2: parameter settings) |
| `heuristics/locks/minfixingrate` | `real` | [0,1] | 0.65 | False | minimum percentage of integer variables that have to be fixable |
| `heuristics/locks/roundupprobability` | `real` | [0,1] | 0.67 | False | probability for rounding a variable up in case of ties |
| `heuristics/locks/usefinalsubmip` | `bool` | {TRUE,FALSE} | TRUE | True | should a final sub-MIP be solved to costruct a feasible solution if the LP was not roundable? |
| `heuristics/locks/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/locks/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/locks/minnodes` | `longint` | [0,9223372036854775807] | 500 | True | minimum number of nodes required to start the subproblem |
| `heuristics/locks/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/locks/minimprove` | `real` | [0,1] | 0.01 | True | factor by which locks heuristic should at least improve the incumbent |
| `heuristics/locks/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/locks/updatelocks` | `bool` | {TRUE,FALSE} | TRUE | True | should the locks be updated based on LP rows? |
| `heuristics/locks/minfixingratelp` | `real` | [0,1] | 0 | True | minimum fixing rate over all variables (including continuous) to solve LP |
| `heuristics/vbounds/priority` | `int` | [-536870912,536870911] | 2500 | True | priority of heuristic &lt;vbounds&gt; |
| `heuristics/vbounds/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;vbounds&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/vbounds/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;vbounds&gt; |
| `heuristics/vbounds/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;vbounds&gt; (-1: no limit) |
| `heuristics/vbounds/minintfixingrate` | `real` | [0,1] | 0.65 | False | minimum percentage of integer variables that have to be fixed |
| `heuristics/vbounds/minmipfixingrate` | `real` | [0,1] | 0.65 | False | minimum percentage of variables that have to be fixed within sub-SCIP (integer and continuous) |
| `heuristics/vbounds/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/vbounds/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/vbounds/minnodes` | `longint` | [0,9223372036854775807] | 500 | True | minimum number of nodes required to start the subproblem |
| `heuristics/vbounds/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/vbounds/minimprove` | `real` | [0,1] | 0.01 | True | factor by which vbounds heuristic should at least improve the incumbent |
| `heuristics/vbounds/maxproprounds` | `int` | [-1,536870911] | 2 | True | maximum number of propagation rounds during probing (-1 infinity) |
| `heuristics/vbounds/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/vbounds/uselockfixings` | `bool` | {TRUE,FALSE} | FALSE | True | should more variables be fixed based on variable locks if the fixing rate was not reached? |
| `heuristics/vbounds/maxbacktracks` | `int` | [-1,536870911] | 10 | True | maximum number of backtracks during the fixing process |
| `heuristics/vbounds/feasvariant` | `int` | [0,7] | 6 | True | which variants of the vbounds heuristic that try to stay feasible should be called? (0: off, 1: w/o looking at obj, 2: only fix to best bound, 4: only fix to worst bound |
| `heuristics/vbounds/tightenvariant` | `int` | [0,7] | 7 | True | which tightening variants of the vbounds heuristic should be called? (0: off, 1: w/o looking at obj, 2: only fix to best bound, 4: only fix to worst bound |
| `heuristics/shiftandpropagate/priority` | `int` | [-536870912,536870911] | 1000 | True | priority of heuristic &lt;shiftandpropagate&gt; |
| `heuristics/shiftandpropagate/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;shiftandpropagate&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/shiftandpropagate/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;shiftandpropagate&gt; |
| `heuristics/shiftandpropagate/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;shiftandpropagate&gt; (-1: no limit) |
| `heuristics/shiftandpropagate/nproprounds` | `int` | [-1,1000] | 10 | True | The number of propagation rounds used for each propagation |
| `heuristics/shiftandpropagate/relax` | `bool` | {TRUE,FALSE} | TRUE | True | Should continuous variables be relaxed? |
| `heuristics/shiftandpropagate/probing` | `bool` | {TRUE,FALSE} | TRUE | True | Should domains be reduced by probing? |
| `heuristics/shiftandpropagate/onlywithoutsol` | `bool` | {TRUE,FALSE} | TRUE | True | Should heuristic only be executed if no primal solution was found, yet? |
| `heuristics/shiftandpropagate/cutoffbreaker` | `int` | [-1,1000000] | 15 | True | The number of cutoffs before heuristic stops |
| `heuristics/shiftandpropagate/sortkey` | `char` | {nrtuv} | v | True | the key for variable sorting: (n)orms down, norms (u)p, (v)iolations down, viola(t)ions up, or (r)andom |
| `heuristics/shiftandpropagate/sortvars` | `bool` | {TRUE,FALSE} | TRUE | True | Should variables be sorted for the heuristic? |
| `heuristics/shiftandpropagate/collectstats` | `bool` | {TRUE,FALSE} | TRUE | True | should variable statistics be collected during probing? |
| `heuristics/shiftandpropagate/stopafterfeasible` | `bool` | {TRUE,FALSE} | TRUE | True | Should the heuristic stop calculating optimal shift values when no more rows are violated? |
| `heuristics/shiftandpropagate/preferbinaries` | `bool` | {TRUE,FALSE} | TRUE | True | Should binary variables be shifted first? |
| `heuristics/shiftandpropagate/nozerofixing` | `bool` | {TRUE,FALSE} | FALSE | True | should variables with a zero shifting value be delayed instead of being fixed? |
| `heuristics/shiftandpropagate/fixbinlocks` | `bool` | {TRUE,FALSE} | TRUE | True | should binary variables with no locks in one direction be fixed to that direction? |
| `heuristics/shiftandpropagate/binlocksfirst` | `bool` | {TRUE,FALSE} | FALSE | True | should binary variables with no locks be preferred in the ordering? |
| `heuristics/shiftandpropagate/normalize` | `bool` | {TRUE,FALSE} | TRUE | True | should coefficients be normalized by max row coeff for col norm? |
| `heuristics/shiftandpropagate/updateweights` | `bool` | {TRUE,FALSE} | FALSE | True | should row weight be increased every time the row is violated? |
| `heuristics/shiftandpropagate/impliscontinuous` | `bool` | {TRUE,FALSE} | TRUE | True | should implicit integer variables be treated as continuous variables? |
| `heuristics/shiftandpropagate/selectbest` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic choose the best candidate in every round? (set to FALSE for static order)? |
| `heuristics/shiftandpropagate/maxcutoffquot` | `real` | [0,2] | 0 | True | maximum percentage of allowed cutoffs before stopping the heuristic |
| `heuristics/shiftandpropagate/minfixingratelp` | `real` | [0,1] | 0 | True | minimum fixing rate over all variables (including continuous) to solve LP |
| `heuristics/zeroobj/priority` | `int` | [-536870912,536870911] | 100 | True | priority of heuristic &lt;zeroobj&gt; |
| `heuristics/zeroobj/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;zeroobj&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/zeroobj/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;zeroobj&gt; |
| `heuristics/zeroobj/maxdepth` | `int` | [-1,1073741822] | 0 | True | maximal depth level to call primal heuristic &lt;zeroobj&gt; (-1: no limit) |
| `heuristics/zeroobj/maxnodes` | `longint` | [0,9223372036854775807] | 1000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/zeroobj/nodesofs` | `longint` | [0,9223372036854775807] | 100 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/zeroobj/minnodes` | `longint` | [0,9223372036854775807] | 100 | True | minimum number of nodes required to start the subproblem |
| `heuristics/zeroobj/maxlpiters` | `longint` | [-1,9223372036854775807] | 5000 | True | maximum number of LP iterations to be performed in the subproblem |
| `heuristics/zeroobj/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/zeroobj/minimprove` | `real` | [0,1] | 0.01 | True | factor by which zeroobj should at least improve the incumbent |
| `heuristics/zeroobj/addallsols` | `bool` | {TRUE,FALSE} | FALSE | True | should all subproblem solutions be added to the original SCIP? |
| `heuristics/zeroobj/onlywithoutsol` | `bool` | {TRUE,FALSE} | TRUE | True | should heuristic only be executed if no primal solution was found, yet? |
| `heuristics/zeroobj/useuct` | `bool` | {TRUE,FALSE} | FALSE | True | should uct node selection be used at the beginning of the search? |
| `heuristics/completesol/priority` | `int` | [-536870912,536870911] | 0 | True | priority of heuristic &lt;completesol&gt; |
| `heuristics/completesol/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;completesol&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/completesol/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;completesol&gt; |
| `heuristics/completesol/maxdepth` | `int` | [-1,1073741822] | 0 | True | maximal depth level to call primal heuristic &lt;completesol&gt; (-1: no limit) |
| `heuristics/completesol/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/completesol/minnodes` | `longint` | [0,9223372036854775807] | 50 | True | minimum number of nodes required to start the subproblem |
| `heuristics/completesol/maxunknownrate` | `real` | [0,1] | 0.85 | False | maximal rate of unknown solution values |
| `heuristics/completesol/addallsols` | `bool` | {TRUE,FALSE} | FALSE | True | should all subproblem solutions be added to the original SCIP? |
| `heuristics/completesol/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/completesol/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/completesol/lplimfac` | `real` | [1,1.79769313486232e+308] | 2 | True | factor by which the limit on the number of LP depends on the node limit |
| `heuristics/completesol/objweight` | `real` | [0.001,1] | 1 | True | weight of the original objective function (1: only original objective) |
| `heuristics/completesol/boundwidening` | `real` | [0,1] | 0.1 | True | bound widening factor applied to continuous variables (0: fix variables to given solution values, 1: relax to global bounds) |
| `heuristics/completesol/minimprove` | `real` | [0,1] | 0.01 | True | factor by which the incumbent should be improved at least |
| `heuristics/completesol/ignorecont` | `bool` | {TRUE,FALSE} | FALSE | False | should number of continuous variables be ignored? |
| `heuristics/completesol/solutions` | `int` | [-1,2147483647] | 5 | False | heuristic stops, if the given number of improving solutions were found (-1: no limit) |
| `heuristics/completesol/maxproprounds` | `int` | [-1,2147483647] | 10 | False | maximal number of iterations in propagation (-1: no limit) |
| `heuristics/completesol/beforepresol` | `bool` | {TRUE,FALSE} | TRUE | False | should the heuristic run before presolving? |
| `heuristics/completesol/maxlpiter` | `longint` | [-1,9223372036854775807] | -1 | False | maximal number of LP iterations (-1: no limit) |
| `heuristics/completesol/maxcontvars` | `int` | [-1,2147483647] | -1 | False | maximal number of continuous variables after presolving |
| `heuristics/dualval/priority` | `int` | [-536870912,536870911] | -10 | True | priority of heuristic &lt;dualval&gt; |
| `heuristics/dualval/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;dualval&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/dualval/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;dualval&gt; |
| `heuristics/dualval/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;dualval&gt; (-1: no limit) |
| `heuristics/dualval/forceimprovements` | `bool` | {TRUE,FALSE} | FALSE | True | exit if objective doesn't improve |
| `heuristics/dualval/onlycheaper` | `bool` | {TRUE,FALSE} | TRUE | True | add constraint to ensure that discrete vars are improving |
| `heuristics/dualval/onlyleaves` | `bool` | {TRUE,FALSE} | FALSE | False | disable the heuristic if it was not called at a leaf of the B&amp;B tree |
| `heuristics/dualval/relaxindicators` | `bool` | {TRUE,FALSE} | FALSE | False | relax the indicator variables by introducing continuous copies |
| `heuristics/dualval/relaxcontvars` | `bool` | {TRUE,FALSE} | FALSE | False | relax the continous variables |
| `heuristics/dualval/heurverblevel` | `int` | [0,4] | 0 | False | verblevel of the heuristic, default is 0 to display nothing |
| `heuristics/dualval/nlpverblevel` | `int` | [0,1] | 0 | False | verblevel of the nlp solver, can be 0 or 1 |
| `heuristics/dualval/rankvalue` | `int` | [0,2147483647] | 10 | False | number of ranks that should be displayed when the heuristic is called |
| `heuristics/dualval/maxcalls` | `int` | [0,2147483647] | 25 | False | maximal number of recursive calls of the heuristic (if dynamicdepth is off) |
| `heuristics/dualval/dynamicdepth` | `int` | [0,1] | 0 | False | says if and how the recursion depth is computed at runtime |
| `heuristics/dualval/maxequalranks` | `int` | [-1,2147483647] | 50 | False | maximal number of variables that may have maximal rank, quit if there are more, turn off by setting -1 |
| `heuristics/dualval/mingap` | `real` | [0,100] | 5 | False | minimal gap for which we still run the heuristic, if gap is less we return without doing anything |
| `heuristics/dualval/lambdaslack` | `real` | [0.1,1e+20] | 1 | False | value added to objective of slack variables, must not be zero |
| `heuristics/dualval/lambdaobj` | `real` | [0,1] | 0 | False | scaling factor for the objective function |
| `heuristics/repair/priority` | `int` | [-536870912,536870911] | -20 | True | priority of heuristic &lt;repair&gt; |
| `heuristics/repair/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;repair&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/repair/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;repair&gt; |
| `heuristics/repair/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;repair&gt; (-1: no limit) |
| `heuristics/repair/filename` | `string` | String; interpretation stated in description | "-" | False | file name of a solution to be used as infeasible starting point, [-] if not available |
| `heuristics/repair/roundit` | `bool` | {TRUE,FALSE} | TRUE | False | True : fractional variables which are not fractional in the given solution are rounded, FALSE : solving process of this heuristic is stopped.  |
| `heuristics/repair/useobjfactor` | `bool` | {TRUE,FALSE} | FALSE | False | should a scaled objective function for original variables be used in repair subproblem? |
| `heuristics/repair/usevarfix` | `bool` | {TRUE,FALSE} | TRUE | False | should variable fixings be used in repair subproblem? |
| `heuristics/repair/useslackvars` | `bool` | {TRUE,FALSE} | FALSE | False | should slack variables be used in repair subproblem? |
| `heuristics/repair/alpha` | `real` | [0,100] | 2 | True | factor for the potential of var fixings |
| `heuristics/repair/nodesofs` | `int` | [0,2147483647] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/repair/maxnodes` | `int` | [0,2147483647] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/repair/minnodes` | `int` | [0,2147483647] | 50 | True | minimum number of nodes required to start the subproblem |
| `heuristics/repair/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/repair/minfixingrate` | `real` | [0,1] | 0.3 | False | minimum percentage of integer variables that have to be fixed |
| `heuristics/simplerounding/priority` | `int` | [-536870912,536870911] | -30 | True | priority of heuristic &lt;simplerounding&gt; |
| `heuristics/simplerounding/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling primal heuristic &lt;simplerounding&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/simplerounding/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;simplerounding&gt; |
| `heuristics/simplerounding/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;simplerounding&gt; (-1: no limit) |
| `heuristics/simplerounding/oncepernode` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic only be called once per node? |
| `heuristics/randrounding/priority` | `int` | [-536870912,536870911] | -200 | True | priority of heuristic &lt;randrounding&gt; |
| `heuristics/randrounding/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;randrounding&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/randrounding/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;randrounding&gt; |
| `heuristics/randrounding/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;randrounding&gt; (-1: no limit) |
| `heuristics/randrounding/oncepernode` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic only be called once per node? |
| `heuristics/randrounding/usesimplerounding` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic apply the variable lock strategy of simple rounding, if possible? |
| `heuristics/randrounding/propagateonlyroot` | `bool` | {TRUE,FALSE} | TRUE | True | should the probing part of the heuristic be applied exclusively at the root node? |
| `heuristics/randrounding/maxproprounds` | `int` | [-1,2147483647] | 1 | True | limit of rounds for each propagation call |
| `heuristics/zirounding/priority` | `int` | [-536870912,536870911] | -500 | True | priority of heuristic &lt;zirounding&gt; |
| `heuristics/zirounding/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling primal heuristic &lt;zirounding&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/zirounding/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;zirounding&gt; |
| `heuristics/zirounding/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;zirounding&gt; (-1: no limit) |
| `heuristics/zirounding/maxroundingloops` | `int` | [-1,2147483647] | 2 | True | determines maximum number of rounding loops |
| `heuristics/zirounding/stopziround` | `bool` | {TRUE,FALSE} | TRUE | True | flag to determine if Zirounding is deactivated after a certain percentage of unsuccessful calls |
| `heuristics/zirounding/stoppercentage` | `real` | [0,1] | 0.02 | True | if percentage of found solutions falls below this parameter, Zirounding will be deactivated |
| `heuristics/zirounding/minstopncalls` | `int` | [1,2147483647] | 1000 | True | determines the minimum number of calls before percentage-based deactivation of Zirounding is applied |
| `heuristics/rounding/priority` | `int` | [-536870912,536870911] | -1000 | True | priority of heuristic &lt;rounding&gt; |
| `heuristics/rounding/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling primal heuristic &lt;rounding&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/rounding/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;rounding&gt; |
| `heuristics/rounding/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;rounding&gt; (-1: no limit) |
| `heuristics/rounding/successfactor` | `int` | [-1,2147483647] | 100 | True | number of calls per found solution that are considered as standard success, a higher factor causes the heuristic to be called more often |
| `heuristics/rounding/oncepernode` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic only be called once per node? |
| `heuristics/shifting/priority` | `int` | [-536870912,536870911] | -5000 | True | priority of heuristic &lt;shifting&gt; |
| `heuristics/shifting/freq` | `int` | [-1,1073741822] | 5 | False | frequency for calling primal heuristic &lt;shifting&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/shifting/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;shifting&gt; |
| `heuristics/shifting/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;shifting&gt; (-1: no limit) |
| `heuristics/intshifting/priority` | `int` | [-536870912,536870911] | -10000 | True | priority of heuristic &lt;intshifting&gt; |
| `heuristics/intshifting/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;intshifting&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/intshifting/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;intshifting&gt; |
| `heuristics/intshifting/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;intshifting&gt; (-1: no limit) |
| `heuristics/oneopt/priority` | `int` | [-536870912,536870911] | -20000 | True | priority of heuristic &lt;oneopt&gt; |
| `heuristics/oneopt/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling primal heuristic &lt;oneopt&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/oneopt/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;oneopt&gt; |
| `heuristics/oneopt/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;oneopt&gt; (-1: no limit) |
| `heuristics/oneopt/weightedobj` | `bool` | {TRUE,FALSE} | TRUE | True | should the objective be weighted with the potential shifting value when sorting the shifting candidates? |
| `heuristics/oneopt/duringroot` | `bool` | {TRUE,FALSE} | TRUE | True | should the heuristic be called before and during the root node? |
| `heuristics/oneopt/forcelpconstruction` | `bool` | {TRUE,FALSE} | FALSE | True | should the construction of the LP be forced even if LP solving is deactivated? |
| `heuristics/oneopt/beforepresol` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic be called before presolving? |
| `heuristics/oneopt/useloop` | `bool` | {TRUE,FALSE} | TRUE | True | should the heuristic continue to run as long as improvements are found? |
| `heuristics/twoopt/priority` | `int` | [-536870912,536870911] | -20100 | True | priority of heuristic &lt;twoopt&gt; |
| `heuristics/twoopt/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;twoopt&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/twoopt/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;twoopt&gt; |
| `heuristics/twoopt/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;twoopt&gt; (-1: no limit) |
| `heuristics/twoopt/intopt` | `bool` | {TRUE,FALSE} | FALSE | True |  Should Integer-2-Optimization be applied or not? |
| `heuristics/twoopt/waitingnodes` | `int` | [0,10000] | 0 | True | user parameter to determine number of nodes to wait after last best solution before calling heuristic |
| `heuristics/twoopt/maxnslaves` | `int` | [-1,1000000] | 199 | True | maximum number of slaves for one master variable |
| `heuristics/twoopt/matchingrate` | `real` | [0,1] | 0.5 | True | parameter to determine the percentage of rows two variables have to share before they are considered equal |
| `heuristics/indicator/priority` | `int` | [-536870912,536870911] | -20200 | True | priority of heuristic &lt;indicator&gt; |
| `heuristics/indicator/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling primal heuristic &lt;indicator&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/indicator/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;indicator&gt; |
| `heuristics/indicator/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;indicator&gt; (-1: no limit) |
| `heuristics/indicator/oneopt` | `bool` | {TRUE,FALSE} | FALSE | True | whether the one-opt heuristic should be started |
| `heuristics/indicator/improvesols` | `bool` | {TRUE,FALSE} | FALSE | True | Try to improve other solutions by one-opt? |
| `heuristics/scheduler/priority` | `int` | [-536870912,536870911] | -30000 | True | priority of heuristic &lt;scheduler&gt; |
| `heuristics/scheduler/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;scheduler&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/scheduler/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;scheduler&gt; |
| `heuristics/scheduler/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;scheduler&gt; (-1: no limit) |
| `heuristics/scheduler/rens/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/scheduler/rens/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/scheduler/rens/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/scheduler/rens/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/scheduler/rins/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/scheduler/rins/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/scheduler/rins/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/scheduler/rins/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/scheduler/mutation/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/scheduler/mutation/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/scheduler/mutation/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/scheduler/mutation/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/scheduler/localbranching/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/scheduler/localbranching/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/scheduler/localbranching/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/scheduler/localbranching/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/scheduler/crossover/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/scheduler/crossover/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/scheduler/crossover/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/scheduler/crossover/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/scheduler/crossover/nsols` | `int` | [2,10] | 2 | True | the number of solutions that crossover should combine |
| `heuristics/scheduler/proximity/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/scheduler/proximity/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/scheduler/proximity/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/scheduler/proximity/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/scheduler/zeroobjective/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/scheduler/zeroobjective/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/scheduler/zeroobjective/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/scheduler/zeroobjective/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/scheduler/dins/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/scheduler/dins/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/scheduler/dins/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/scheduler/dins/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/scheduler/dins/npoolsols` | `int` | [1,100] | 5 | True | number of pool solutions where binary solution values must agree |
| `heuristics/scheduler/trustregion/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/scheduler/trustregion/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/scheduler/trustregion/active` | `bool` | {TRUE,FALSE} | FALSE | True | is this neighborhood active? |
| `heuristics/scheduler/trustregion/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/scheduler/trustregion/violpenalty` | `real` | [0,1.79769313486232e+308] | 100 | False | the penalty for each change in the binary variables from the candidate solution |
| `heuristics/scheduler/maxnodes` | `longint` | [0,9223372036854775807] | 500 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/scheduler/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | offset added to the nodes budget |
| `heuristics/scheduler/minnodes` | `longint` | [0,9223372036854775807] | 50 | True | minimum number of nodes required to start a sub-SCIP |
| `heuristics/scheduler/waitingnodes` | `longint` | [0,9223372036854775807] | 0 | True | number of nodes since last incumbent solution that the heuristic should wait |
| `heuristics/scheduler/initlnsnodelimit` | `int` | [0,2147483647] | 50 | True | initial node limit for LNS heuristics |
| `heuristics/scheduler/initdivingnodelimit` | `longint` | [0,9223372036854775807] | 500 | True | initial node limit for diving heuristics |
| `heuristics/scheduler/nodesquot` | `real` | [0,1] | 0.1 | False | fraction of nodes compared to the main SCIP for budget computation |
| `heuristics/scheduler/nodesquotmin` | `real` | [0,1] | 0 | False | lower bound fraction of nodes compared to the main SCIP for budget computation |
| `heuristics/scheduler/nsolslim` | `int` | [-1,2147483647] | 3 | False | limit on the number of improving solutions in a sub-SCIP call |
| `heuristics/scheduler/banditalgo` | `char` | {uegi} | i | True | the bandit algorithm: (u)pper confidence bounds, (e)xp.3, epsilon (g)reedy, exp.3-(i)x |
| `heuristics/scheduler/gamma` | `real` | [0,1] | 0.07041455 | True | weight between uniform (gamma ~ 1) and weight driven (gamma ~ 0) probability distribution for exp3 |
| `heuristics/scheduler/beta` | `real` | [0,1] | 0 | True | reward offset between 0 and 1 at every observation for Exp.3 |
| `heuristics/scheduler/alpha` | `real` | [0,100] | 0.0016 | True | parameter to increase the confidence width in UCB |
| `heuristics/scheduler/usedistances` | `bool` | {TRUE,FALSE} | TRUE | True | distances from fixed variables be used for variable prioritization |
| `heuristics/scheduler/useredcost` | `bool` | {TRUE,FALSE} | TRUE | True | should reduced cost scores be used for variable prioritization? |
| `heuristics/scheduler/usepscost` | `bool` | {TRUE,FALSE} | TRUE | True | should pseudo cost scores be used for variable priorization? |
| `heuristics/scheduler/uselocalredcost` | `bool` | {TRUE,FALSE} | FALSE | True | should local reduced costs be used for generic (un)fixing? |
| `heuristics/scheduler/usesubscipheurs` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic activate other sub-SCIP heuristics during its search? |
| `heuristics/scheduler/targetnodefactor` | `real` | [1,100000] | 1.05 | True | factor by which target node number is eventually increased |
| `heuristics/scheduler/seed` | `int` | [0,2147483647] | 113 | False | initial random seed for bandit algorithms and random decisions by neighborhoods |
| `heuristics/scheduler/maxcallssamesol` | `int` | [-1,100] | -1 | True | number of allowed executions of the heuristic on the same incumbent solution (-1: no limit, 0: number of active neighborhoods) |
| `heuristics/scheduler/eps` | `real` | [0,1] | 0.4685844 | True | increase exploration in epsilon-greedy bandit algorithm |
| `heuristics/scheduler/epsgreedy_usemod` | `bool` | {TRUE,FALSE} | TRUE | True | TRUE if modified version of the epsilon-greedy bandit algorithm should be used |
| `heuristics/scheduler/solrewardweight` | `real` | [0,1] | 0.3 | True | weight by how much finding a new incumbent is rewarded in reward function |
| `heuristics/scheduler/effortrewardweight` | `real` | [0,1] | 0.2 | True | weight by how much effort is rewarded in reward function |
| `heuristics/scheduler/qualrewardweight` | `real` | [0,1] | 0.3 | True | weight by how much quality of a new incumbent is rewarded in reward function |
| `heuristics/scheduler/conflictrewardweight` | `real` | [0,1] | 0.2 | True | weight by how much number of conflicts found by diving is rewarded in reward function |
| `heuristics/scheduler/resetweights` | `bool` | {TRUE,FALSE} | FALSE | True | should the bandit algorithms be reset when a new problem is read? |
| `heuristics/scheduler/subsciprandseeds` | `bool` | {TRUE,FALSE} | FALSE | True | should random seeds of sub-SCIPs be altered to increase diversification? |
| `heuristics/scheduler/copycuts` | `bool` | {TRUE,FALSE} | FALSE | True | should cutting planes be copied to the sub-SCIP? |
| `heuristics/scheduler/fixtol` | `real` | [0,1] | 0.1 | True | tolerance by which the fixing rate may be missed without generic fixing |
| `heuristics/scheduler/unfixtol` | `real` | [0,1] | 0.1 | True | tolerance by which the fixing rate may be exceeded without generic unfixing |
| `heuristics/scheduler/initduringroot` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic be executed multiple times during the root node? |
| `heuristics/scheduler/defaultroot` | `bool` | {TRUE,FALSE} | TRUE | True | should the default priorities be used at the root node? |
| `heuristics/scheduler/nselections` | `int` | [-1,100] | 5 | True | number of heuristics picked by the scheduler in one call (-1: number of controlled heuristics, 0: until new incumbent is found) |
| `heuristics/adaptivediving/priority` | `int` | [-536870912,536870911] | -70000 | True | priority of heuristic &lt;adaptivediving&gt; |
| `heuristics/adaptivediving/freq` | `int` | [-1,1073741822] | 5 | False | frequency for calling primal heuristic &lt;adaptivediving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/adaptivediving/freqofs` | `int` | [0,1073741822] | 3 | False | frequency offset for calling primal heuristic &lt;adaptivediving&gt; |
| `heuristics/adaptivediving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;adaptivediving&gt; (-1: no limit) |
| `heuristics/adaptivediving/epsilon` | `real` | [0,1.79769313486232e+308] | 1 | False | parameter that increases probability of exploration among divesets (only active if seltype is 'e') |
| `heuristics/adaptivediving/scoretype` | `char` | {cdinsu} | c | False | score parameter for selection: minimize either average 'n'odes, LP 'i'terations,backtrack/'c'onflict ratio, 'd'epth, 1 / 's'olutions, or 1 / solutions'u'ccess |
| `heuristics/adaptivediving/seltype` | `char` | {enw} | w | False | selection strategy: (e)psilon-greedy, (w)eighted distribution, (n)ext diving |
| `heuristics/adaptivediving/useadaptivecontext` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic use its own statistics, or shared statistics? |
| `heuristics/adaptivediving/selconfidencecoeff` | `real` | [1,2147483647] | 10 | False | coefficient c to decrease initial confidence (calls + 1.0) / (calls + c) in scores |
| `heuristics/adaptivediving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/adaptivediving/maxlpiterofs` | `longint` | [0,2147483647] | 1500 | False | additional number of allowed LP iterations |
| `heuristics/adaptivediving/bestsolweight` | `real` | [0,1.79769313486232e+308] | 10 | False | weight of incumbent solutions compared to other solutions in computation of LP iteration limit |
| `heuristics/indicatordiving/priority` | `int` | [-536870912,536870911] | -150000 | True | priority of heuristic &lt;indicatordiving&gt; |
| `heuristics/indicatordiving/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;indicatordiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/indicatordiving/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;indicatordiving&gt; |
| `heuristics/indicatordiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;indicatordiving&gt; (-1: no limit) |
| `heuristics/indicatordiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/indicatordiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/indicatordiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/indicatordiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/indicatordiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/indicatordiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/indicatordiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/indicatordiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/indicatordiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/indicatordiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/indicatordiving/lpsolvefreq` | `int` | [0,2147483647] | 30 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/indicatordiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | FALSE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/indicatordiving/roundingfrac` | `real` | [0,1] | 0.5 | False | in violation case all fractional below this value are fixed to constant |
| `heuristics/indicatordiving/roundingmode` | `int` | [0,1] | 0 | False | decides which roundingmode is selected (0: conservative, 1: aggressive) |
| `heuristics/indicatordiving/semicontscoremode` | `int` | [0,2] | 0 | False | which values of semi-continuous variables should get a high score? (0: low, 1: middle, 2: high) |
| `heuristics/indicatordiving/usevarbounds` | `bool` | {TRUE,FALSE} | TRUE | False | should varbound constraints be considered? |
| `heuristics/indicatordiving/runwithoutscinds` | `bool` | {TRUE,FALSE} | FALSE | False | should heur run if there are no indicator constraints modeling semicont. vars? |
| `heuristics/fixandinfer/priority` | `int` | [-536870912,536870911] | -500000 | True | priority of heuristic &lt;fixandinfer&gt; |
| `heuristics/fixandinfer/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;fixandinfer&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/fixandinfer/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;fixandinfer&gt; |
| `heuristics/fixandinfer/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;fixandinfer&gt; (-1: no limit) |
| `heuristics/fixandinfer/proprounds` | `int` | [-1,2147483647] | 0 | True | maximal number of propagation rounds in probing subproblems (-1: no limit, 0: auto) |
| `heuristics/fixandinfer/minfixings` | `int` | [0,2147483647] | 100 | True | minimal number of fixings to apply before dive may be aborted |
| `heuristics/farkasdiving/priority` | `int` | [-536870912,536870911] | -900000 | True | priority of heuristic &lt;farkasdiving&gt; |
| `heuristics/farkasdiving/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;farkasdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/farkasdiving/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;farkasdiving&gt; |
| `heuristics/farkasdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;farkasdiving&gt; (-1: no limit) |
| `heuristics/farkasdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/farkasdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/farkasdiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/farkasdiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/farkasdiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/farkasdiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/farkasdiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/farkasdiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/farkasdiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/farkasdiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/farkasdiving/lpsolvefreq` | `int` | [0,2147483647] | 1 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/farkasdiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | FALSE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/farkasdiving/checkcands` | `bool` | {TRUE,FALSE} | FALSE | True | should diving candidates be checked before running? |
| `heuristics/farkasdiving/scalescore` | `bool` | {TRUE,FALSE} | TRUE | True | should the score be scaled? |
| `heuristics/farkasdiving/rootsuccess` | `bool` | {TRUE,FALSE} | TRUE | True | should the heuristic only run within the tree if at least one solution was found at the root node? |
| `heuristics/farkasdiving/maxobjocc` | `real` | [0,1] | 1 | True | maximal occurance factor of an objective coefficient |
| `heuristics/farkasdiving/objdynamism` | `real` | [0,1e+20] | 0.0001 | True | minimal objective dynamism (log) to run |
| `heuristics/farkasdiving/scaletype` | `char` | {fi} | i | True | scale score by [f]ractionality or [i]mpact on farkasproof |
| `heuristics/feaspump/priority` | `int` | [-536870912,536870911] | -1000000 | True | priority of heuristic &lt;feaspump&gt; |
| `heuristics/feaspump/freq` | `int` | [-1,1073741822] | 20 | False | frequency for calling primal heuristic &lt;feaspump&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/feaspump/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;feaspump&gt; |
| `heuristics/feaspump/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;feaspump&gt; (-1: no limit) |
| `heuristics/feaspump/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/feaspump/objfactor` | `real` | [0,1] | 0.1 | False | factor by which the regard of the objective is decreased in each round, 1.0 for dynamic |
| `heuristics/feaspump/alpha` | `real` | [0,1] | 1 | False | initial weight of the objective function in the convex combination |
| `heuristics/feaspump/alphadiff` | `real` | [0,1] | 1 | False | threshold difference for the convex parameter to perform perturbation |
| `heuristics/feaspump/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/feaspump/maxsols` | `int` | [-1,2147483647] | 10 | True | total number of feasible solutions found up to which heuristic is called (-1: no limit) |
| `heuristics/feaspump/maxloops` | `int` | [-1,2147483647] | 10000 | True | maximal number of pumping loops (-1: no limit) |
| `heuristics/feaspump/maxstallloops` | `int` | [-1,2147483647] | 10 | True | maximal number of pumping rounds without fractionality improvement (-1: no limit) |
| `heuristics/feaspump/minflips` | `int` | [1,2147483647] | 10 | True | minimum number of random variables to flip, if a 1-cycle is encountered |
| `heuristics/feaspump/cyclelength` | `int` | [1,100] | 3 | True | maximum length of cycles to be checked explicitly in each round |
| `heuristics/feaspump/perturbfreq` | `int` | [1,2147483647] | 100 | True | number of iterations until a random perturbation is forced |
| `heuristics/feaspump/neighborhoodsize` | `int` | [1,2147483647] | 18 | False | radius (using Manhattan metric) of the neighborhood to be searched in stage 3 |
| `heuristics/feaspump/beforecuts` | `bool` | {TRUE,FALSE} | TRUE | False | should the feasibility pump be called at root node before cut separation? |
| `heuristics/feaspump/usefp20` | `bool` | {TRUE,FALSE} | FALSE | False | should an iterative round-and-propagate scheme be used to find the integral points? |
| `heuristics/feaspump/pertsolfound` | `bool` | {TRUE,FALSE} | TRUE | False | should a random perturbation be performed if a feasible solution was found? |
| `heuristics/feaspump/stage3` | `bool` | {TRUE,FALSE} | FALSE | False | should we solve a local branching sub-MIP if no solution could be found? |
| `heuristics/feaspump/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/conflictdiving/priority` | `int` | [-536870912,536870911] | -1000100 | True | priority of heuristic &lt;conflictdiving&gt; |
| `heuristics/conflictdiving/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;conflictdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/conflictdiving/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;conflictdiving&gt; |
| `heuristics/conflictdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;conflictdiving&gt; (-1: no limit) |
| `heuristics/conflictdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/conflictdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/conflictdiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/conflictdiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/conflictdiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/conflictdiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/conflictdiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/conflictdiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/conflictdiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/conflictdiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/conflictdiving/lpsolvefreq` | `int` | [0,2147483647] | 0 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/conflictdiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | FALSE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/conflictdiving/maxviol` | `bool` | {TRUE,FALSE} | TRUE | True | try to maximize the violation |
| `heuristics/conflictdiving/likecoef` | `bool` | {TRUE,FALSE} | FALSE | True | perform rounding like coefficient diving |
| `heuristics/conflictdiving/minconflictlocks` | `int` | [0,2147483647] | 5 | True | minimal number of conflict locks per variable |
| `heuristics/conflictdiving/lockweight` | `real` | [0,1] | 0.75 | True | weight used in a convex combination of conflict and variable locks |
| `heuristics/coefdiving/priority` | `int` | [-536870912,536870911] | -1001000 | True | priority of heuristic &lt;coefdiving&gt; |
| `heuristics/coefdiving/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;coefdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/coefdiving/freqofs` | `int` | [0,1073741822] | 1 | False | frequency offset for calling primal heuristic &lt;coefdiving&gt; |
| `heuristics/coefdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;coefdiving&gt; (-1: no limit) |
| `heuristics/coefdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/coefdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/coefdiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/coefdiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/coefdiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/coefdiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/coefdiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/coefdiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/coefdiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/coefdiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/coefdiving/lpsolvefreq` | `int` | [0,2147483647] | 0 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/coefdiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | FALSE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/pscostdiving/priority` | `int` | [-536870912,536870911] | -1002000 | True | priority of heuristic &lt;pscostdiving&gt; |
| `heuristics/pscostdiving/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;pscostdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/pscostdiving/freqofs` | `int` | [0,1073741822] | 2 | False | frequency offset for calling primal heuristic &lt;pscostdiving&gt; |
| `heuristics/pscostdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;pscostdiving&gt; (-1: no limit) |
| `heuristics/pscostdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/pscostdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/pscostdiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/pscostdiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/pscostdiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/pscostdiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/pscostdiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/pscostdiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/pscostdiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/pscostdiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/pscostdiving/lpsolvefreq` | `int` | [0,2147483647] | 0 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/pscostdiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | TRUE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/fracdiving/priority` | `int` | [-536870912,536870911] | -1003000 | True | priority of heuristic &lt;fracdiving&gt; |
| `heuristics/fracdiving/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;fracdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/fracdiving/freqofs` | `int` | [0,1073741822] | 3 | False | frequency offset for calling primal heuristic &lt;fracdiving&gt; |
| `heuristics/fracdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;fracdiving&gt; (-1: no limit) |
| `heuristics/fracdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/fracdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/fracdiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/fracdiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/fracdiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/fracdiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/fracdiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/fracdiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/fracdiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/fracdiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/fracdiving/lpsolvefreq` | `int` | [0,2147483647] | 0 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/fracdiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | FALSE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/nlpdiving/priority` | `int` | [-536870912,536870911] | -1003010 | True | priority of heuristic &lt;nlpdiving&gt; |
| `heuristics/nlpdiving/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;nlpdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/nlpdiving/freqofs` | `int` | [0,1073741822] | 3 | False | frequency offset for calling primal heuristic &lt;nlpdiving&gt; |
| `heuristics/nlpdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;nlpdiving&gt; (-1: no limit) |
| `heuristics/nlpdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/nlpdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/nlpdiving/maxnlpiterabs` | `int` | [0,2147483647] | 200 | False | minimial absolute number of allowed NLP iterations |
| `heuristics/nlpdiving/maxnlpiterrel` | `int` | [0,2147483647] | 10 | False | additional allowed number of NLP iterations relative to successfully found solutions |
| `heuristics/nlpdiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/nlpdiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/nlpdiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/nlpdiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/nlpdiving/maxfeasnlps` | `int` | [1,2147483647] | 10 | False | maximal number of NLPs with feasible solution to solve during one dive |
| `heuristics/nlpdiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/nlpdiving/lp` | `bool` | {TRUE,FALSE} | FALSE | True | should the LP relaxation be solved before the NLP relaxation? |
| `heuristics/nlpdiving/preferlpfracs` | `bool` | {TRUE,FALSE} | FALSE | True | prefer variables that are also fractional in LP solution? |
| `heuristics/nlpdiving/minsuccquot` | `real` | [0,1] | 0.1 | False | heuristic will not run if less then this percentage of calls succeeded (0.0: no limit) |
| `heuristics/nlpdiving/fixquot` | `real` | [0,1] | 0.2 | False | percentage of fractional variables that should be fixed before the next NLP solve |
| `heuristics/nlpdiving/prefercover` | `bool` | {TRUE,FALSE} | TRUE | False | should variables in a minimal cover be preferred? |
| `heuristics/nlpdiving/solvesubmip` | `bool` | {TRUE,FALSE} | FALSE | False | should a sub-MIP be solved if all cover variables are fixed? |
| `heuristics/nlpdiving/nlpfastfail` | `bool` | {TRUE,FALSE} | TRUE | False | should the NLP solver stop early if it converges slow? |
| `heuristics/nlpdiving/nlpstart` | `char` | {fns} | s | True | which point should be used as starting point for the NLP solver? ('n'one, last 'f'easible, from dive's'tart) |
| `heuristics/nlpdiving/varselrule` | `char` | {fcpgdv} | d | False | which variable selection should be used? ('f'ractionality, 'c'oefficient, 'p'seudocost, 'g'uided, 'd'ouble, 'v'eclen) |
| `heuristics/veclendiving/priority` | `int` | [-536870912,536870911] | -1003100 | True | priority of heuristic &lt;veclendiving&gt; |
| `heuristics/veclendiving/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;veclendiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/veclendiving/freqofs` | `int` | [0,1073741822] | 4 | False | frequency offset for calling primal heuristic &lt;veclendiving&gt; |
| `heuristics/veclendiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;veclendiving&gt; (-1: no limit) |
| `heuristics/veclendiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/veclendiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/veclendiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/veclendiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/veclendiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/veclendiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/veclendiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/veclendiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/veclendiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/veclendiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/veclendiving/lpsolvefreq` | `int` | [0,2147483647] | 0 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/veclendiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | FALSE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/distributiondiving/priority` | `int` | [-536870912,536870911] | -1003300 | True | priority of heuristic &lt;distributiondiving&gt; |
| `heuristics/distributiondiving/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;distributiondiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/distributiondiving/freqofs` | `int` | [0,1073741822] | 3 | False | frequency offset for calling primal heuristic &lt;distributiondiving&gt; |
| `heuristics/distributiondiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;distributiondiving&gt; (-1: no limit) |
| `heuristics/distributiondiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/distributiondiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/distributiondiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/distributiondiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/distributiondiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/distributiondiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/distributiondiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/distributiondiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/distributiondiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/distributiondiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/distributiondiving/lpsolvefreq` | `int` | [0,2147483647] | 0 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/distributiondiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | TRUE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/distributiondiving/scoreparam` | `char` | {lvdhwr} | r | True | the score;largest 'd'ifference, 'l'owest cumulative probability,'h'ighest c.p., 'v'otes lowest c.p., votes highest c.p.('w'), 'r'evolving |
| `heuristics/intdiving/priority` | `int` | [-536870912,536870911] | -1003500 | True | priority of heuristic &lt;intdiving&gt; |
| `heuristics/intdiving/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;intdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/intdiving/freqofs` | `int` | [0,1073741822] | 9 | False | frequency offset for calling primal heuristic &lt;intdiving&gt; |
| `heuristics/intdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;intdiving&gt; (-1: no limit) |
| `heuristics/intdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/intdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/intdiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/intdiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/intdiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/intdiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/intdiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/intdiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/intdiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/actconsdiving/priority` | `int` | [-536870912,536870911] | -1003700 | True | priority of heuristic &lt;actconsdiving&gt; |
| `heuristics/actconsdiving/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;actconsdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/actconsdiving/freqofs` | `int` | [0,1073741822] | 5 | False | frequency offset for calling primal heuristic &lt;actconsdiving&gt; |
| `heuristics/actconsdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;actconsdiving&gt; (-1: no limit) |
| `heuristics/actconsdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/actconsdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/actconsdiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/actconsdiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/actconsdiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/actconsdiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/actconsdiving/maxdiveubquotnosol` | `real` | [0,1] | 1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/actconsdiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 1 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/actconsdiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/actconsdiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/actconsdiving/lpsolvefreq` | `int` | [0,2147483647] | 0 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/actconsdiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | TRUE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/objpscostdiving/priority` | `int` | [-536870912,536870911] | -1004000 | True | priority of heuristic &lt;objpscostdiving&gt; |
| `heuristics/objpscostdiving/freq` | `int` | [-1,1073741822] | 20 | False | frequency for calling primal heuristic &lt;objpscostdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/objpscostdiving/freqofs` | `int` | [0,1073741822] | 4 | False | frequency offset for calling primal heuristic &lt;objpscostdiving&gt; |
| `heuristics/objpscostdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;objpscostdiving&gt; (-1: no limit) |
| `heuristics/objpscostdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/objpscostdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/objpscostdiving/maxlpiterquot` | `real` | [0,1] | 0.05 | False | maximal fraction of diving LP iterations compared to total iteration number |
| `heuristics/objpscostdiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/objpscostdiving/maxsols` | `int` | [-1,2147483647] | -1 | True | total number of feasible solutions found up to which heuristic is called (-1: no limit) |
| `heuristics/objpscostdiving/depthfac` | `real` | [0,1.79769313486232e+308] | 0.5 | True | maximal diving depth: number of binary/integer variables times depthfac |
| `heuristics/objpscostdiving/depthfacnosol` | `real` | [0,1.79769313486232e+308] | 2 | True | maximal diving depth factor if no feasible solution was found yet |
| `heuristics/rootsoldiving/priority` | `int` | [-536870912,536870911] | -1005000 | True | priority of heuristic &lt;rootsoldiving&gt; |
| `heuristics/rootsoldiving/freq` | `int` | [-1,1073741822] | 20 | False | frequency for calling primal heuristic &lt;rootsoldiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/rootsoldiving/freqofs` | `int` | [0,1073741822] | 5 | False | frequency offset for calling primal heuristic &lt;rootsoldiving&gt; |
| `heuristics/rootsoldiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;rootsoldiving&gt; (-1: no limit) |
| `heuristics/rootsoldiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/rootsoldiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/rootsoldiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.01 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/rootsoldiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/rootsoldiving/maxsols` | `int` | [-1,2147483647] | -1 | True | total number of feasible solutions found up to which heuristic is called (-1: no limit) |
| `heuristics/rootsoldiving/depthfac` | `real` | [0,1.79769313486232e+308] | 0.5 | True | maximal diving depth: number of binary/integer variables times depthfac |
| `heuristics/rootsoldiving/depthfacnosol` | `real` | [0,1.79769313486232e+308] | 2 | True | maximal diving depth factor if no feasible solution was found yet |
| `heuristics/rootsoldiving/alpha` | `real` | [0,1] | 0.9 | True | soft rounding factor to fade out objective coefficients |
| `heuristics/linesearchdiving/priority` | `int` | [-536870912,536870911] | -1006000 | True | priority of heuristic &lt;linesearchdiving&gt; |
| `heuristics/linesearchdiving/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;linesearchdiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/linesearchdiving/freqofs` | `int` | [0,1073741822] | 6 | False | frequency offset for calling primal heuristic &lt;linesearchdiving&gt; |
| `heuristics/linesearchdiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;linesearchdiving&gt; (-1: no limit) |
| `heuristics/linesearchdiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/linesearchdiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/linesearchdiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/linesearchdiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/linesearchdiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/linesearchdiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/linesearchdiving/maxdiveubquotnosol` | `real` | [0,1] | 0.1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/linesearchdiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/linesearchdiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/linesearchdiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/linesearchdiving/lpsolvefreq` | `int` | [0,2147483647] | 0 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/linesearchdiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | FALSE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/guideddiving/priority` | `int` | [-536870912,536870911] | -1007000 | True | priority of heuristic &lt;guideddiving&gt; |
| `heuristics/guideddiving/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;guideddiving&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/guideddiving/freqofs` | `int` | [0,1073741822] | 7 | False | frequency offset for calling primal heuristic &lt;guideddiving&gt; |
| `heuristics/guideddiving/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;guideddiving&gt; (-1: no limit) |
| `heuristics/guideddiving/minreldepth` | `real` | [0,1] | 0 | True | minimal relative depth to start diving |
| `heuristics/guideddiving/maxreldepth` | `real` | [0,1] | 1 | True | maximal relative depth to start diving |
| `heuristics/guideddiving/maxlpiterquot` | `real` | [0,1.79769313486232e+308] | 0.05 | False | maximal fraction of diving LP iterations compared to node LP iterations |
| `heuristics/guideddiving/maxlpiterofs` | `int` | [0,2147483647] | 1000 | False | additional number of allowed LP iterations |
| `heuristics/guideddiving/maxdiveubquot` | `real` | [0,1] | 0.8 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/guideddiving/maxdiveavgquot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal quotient (curlowerbound - lowerbound)/(avglowerbound - lowerbound) where diving is performed (0.0: no limit) |
| `heuristics/guideddiving/maxdiveubquotnosol` | `real` | [0,1] | 1 | True | maximal UBQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/guideddiving/maxdiveavgquotnosol` | `real` | [0,1.79769313486232e+308] | 1 | True | maximal AVGQUOT when no solution was found yet (0.0: no limit) |
| `heuristics/guideddiving/backtrack` | `bool` | {TRUE,FALSE} | TRUE | False | use one level of backtracking if infeasibility is encountered? |
| `heuristics/guideddiving/lpresolvedomchgquot` | `real` | [0,1.79769313486232e+308] | 0.15 | False | percentage of immediate domain changes during probing to trigger LP resolve |
| `heuristics/guideddiving/lpsolvefreq` | `int` | [0,2147483647] | 0 | False | LP solve frequency for diving heuristics (0: only after enough domain changes have been found) |
| `heuristics/guideddiving/onlylpbranchcands` | `bool` | {TRUE,FALSE} | FALSE | False | should only LP branching candidates be considered instead of the slower but more general constraint handler diving variable selection? |
| `heuristics/octane/priority` | `int` | [-536870912,536870911] | -1008000 | True | priority of heuristic &lt;octane&gt; |
| `heuristics/octane/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;octane&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/octane/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;octane&gt; |
| `heuristics/octane/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;octane&gt; (-1: no limit) |
| `heuristics/octane/fmax` | `int` | [1,2147483647] | 100 | True | number of 0-1-points to be tested as possible solutions by OCTANE |
| `heuristics/octane/ffirst` | `int` | [1,2147483647] | 10 | True | number of 0-1-points to be tested at first whether they violate a common row |
| `heuristics/octane/usefracspace` | `bool` | {TRUE,FALSE} | TRUE | True | execute OCTANE only in the space of fractional variables (TRUE) or in the full space? |
| `heuristics/octane/useobjray` | `bool` | {TRUE,FALSE} | TRUE | True | should the inner normal of the objective be used as one ray direction? |
| `heuristics/octane/useavgray` | `bool` | {TRUE,FALSE} | TRUE | True | should the average of the basic cone be used as one ray direction? |
| `heuristics/octane/usediffray` | `bool` | {TRUE,FALSE} | FALSE | True | should the difference between the root solution and the current LP solution be used as one ray direction? |
| `heuristics/octane/useavgwgtray` | `bool` | {TRUE,FALSE} | TRUE | True | should the weighted average of the basic cone be used as one ray direction? |
| `heuristics/octane/useavgnbray` | `bool` | {TRUE,FALSE} | TRUE | True | should the weighted average of the nonbasic cone be used as one ray direction? |
| `heuristics/rens/priority` | `int` | [-536870912,536870911] | -1100000 | True | priority of heuristic &lt;rens&gt; |
| `heuristics/rens/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;rens&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/rens/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;rens&gt; |
| `heuristics/rens/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;rens&gt; (-1: no limit) |
| `heuristics/rens/minfixingrate` | `real` | [0,1] | 0.5 | False | minimum percentage of integer variables that have to be fixable |
| `heuristics/rens/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/rens/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/rens/minnodes` | `longint` | [0,9223372036854775807] | 50 | True | minimum number of nodes required to start the subproblem |
| `heuristics/rens/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/rens/minimprove` | `real` | [0,1] | 0.01 | True | factor by which RENS should at least improve the incumbent |
| `heuristics/rens/lplimfac` | `real` | [1,1.79769313486232e+308] | 2 | True | factor by which the limit on the number of LP depends on the node limit |
| `heuristics/rens/startsol` | `char` | {nl} | l | False | solution that is used for fixing values ('l'p relaxation, 'n'lp relaxation) |
| `heuristics/rens/binarybounds` | `bool` | {TRUE,FALSE} | TRUE | True | should general integers get binary bounds [floor(.),ceil(.)] ? |
| `heuristics/rens/uselprows` | `bool` | {TRUE,FALSE} | FALSE | True | should subproblem be created out of the rows in the LP rows? |
| `heuristics/rens/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | if uselprows == FALSE, should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/rens/extratime` | `bool` | {TRUE,FALSE} | FALSE | True | should the RENS sub-CIP get its own full time limit? This is only for testing and not recommended! |
| `heuristics/rens/addallsols` | `bool` | {TRUE,FALSE} | FALSE | True | should all subproblem solutions be added to the original SCIP? |
| `heuristics/rens/fullscale` | `bool` | {TRUE,FALSE} | FALSE | True | should the RENS sub-CIP be solved with cuts, conflicts, strong branching,... This is only for testing and not recommended! |
| `heuristics/rens/bestsollimit` | `int` | [-1,2147483647] | -1 | False | limit on number of improving incumbent solutions in sub-CIP |
| `heuristics/rens/useuct` | `bool` | {TRUE,FALSE} | FALSE | True | should uct node selection be used at the beginning of the search? |
| `heuristics/alns/priority` | `int` | [-536870912,536870911] | -1100500 | True | priority of heuristic &lt;alns&gt; |
| `heuristics/alns/freq` | `int` | [-1,1073741822] | 20 | False | frequency for calling primal heuristic &lt;alns&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/alns/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;alns&gt; |
| `heuristics/alns/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;alns&gt; (-1: no limit) |
| `heuristics/alns/rens/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/alns/rens/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/alns/rens/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/alns/rens/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/alns/rins/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/alns/rins/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/alns/rins/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/alns/rins/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/alns/mutation/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/alns/mutation/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/alns/mutation/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/alns/mutation/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/alns/localbranching/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/alns/localbranching/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/alns/localbranching/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/alns/localbranching/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/alns/crossover/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/alns/crossover/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/alns/crossover/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/alns/crossover/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/alns/crossover/nsols` | `int` | [2,10] | 2 | True | the number of solutions that crossover should combine |
| `heuristics/alns/proximity/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/alns/proximity/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/alns/proximity/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/alns/proximity/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/alns/zeroobjective/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/alns/zeroobjective/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/alns/zeroobjective/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/alns/zeroobjective/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/alns/dins/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/alns/dins/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/alns/dins/active` | `bool` | {TRUE,FALSE} | TRUE | True | is this neighborhood active? |
| `heuristics/alns/dins/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/alns/dins/npoolsols` | `int` | [1,100] | 5 | True | number of pool solutions where binary solution values must agree |
| `heuristics/alns/trustregion/minfixingrate` | `real` | [0,1] | 0.3 | True | minimum fixing rate for this neighborhood |
| `heuristics/alns/trustregion/maxfixingrate` | `real` | [0,1] | 0.9 | True | maximum fixing rate for this neighborhood |
| `heuristics/alns/trustregion/active` | `bool` | {TRUE,FALSE} | FALSE | True | is this neighborhood active? |
| `heuristics/alns/trustregion/priority` | `real` | [0.01,1] | 1 | True | positive call priority to initialize bandit algorithms |
| `heuristics/alns/trustregion/violpenalty` | `real` | [0,1.79769313486232e+308] | 100 | False | the penalty for each change in the binary variables from the candidate solution |
| `heuristics/alns/shownbstats` | `bool` | {TRUE,FALSE} | FALSE | True | show statistics on neighborhoods? |
| `heuristics/alns/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/alns/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | offset added to the nodes budget |
| `heuristics/alns/minnodes` | `longint` | [0,9223372036854775807] | 50 | True | minimum number of nodes required to start a sub-SCIP |
| `heuristics/alns/waitingnodes` | `longint` | [0,9223372036854775807] | 25 | True | number of nodes since last incumbent solution that the heuristic should wait |
| `heuristics/alns/nodesquot` | `real` | [0,1] | 0.1 | False | fraction of nodes compared to the main SCIP for budget computation |
| `heuristics/alns/nodesquotmin` | `real` | [0,1] | 0 | False | lower bound fraction of nodes compared to the main SCIP for budget computation |
| `heuristics/alns/startminimprove` | `real` | [0,1] | 0.01 | True | initial factor by which ALNS should at least improve the incumbent |
| `heuristics/alns/minimprovelow` | `real` | [0,1] | 0.01 | True | lower threshold for the minimal improvement over the incumbent |
| `heuristics/alns/minimprovehigh` | `real` | [0,1] | 0.01 | True | upper bound for the minimal improvement over the incumbent |
| `heuristics/alns/nsolslim` | `int` | [-1,2147483647] | 3 | False | limit on the number of improving solutions in a sub-SCIP call |
| `heuristics/alns/banditalgo` | `char` | {uegi} | i | True | the bandit algorithm: (u)pper confidence bounds, (e)xp.3, epsilon (g)reedy, exp.3-(i)x |
| `heuristics/alns/gamma` | `real` | [0,1] | 0.07041455 | True | weight between uniform (gamma ~ 1) and weight driven (gamma ~ 0) probability distribution for exp3 |
| `heuristics/alns/beta` | `real` | [0,1] | 0 | True | reward offset between 0 and 1 at every observation for Exp.3 |
| `heuristics/alns/alpha` | `real` | [0,100] | 0.0016 | True | parameter to increase the confidence width in UCB |
| `heuristics/alns/usedistances` | `bool` | {TRUE,FALSE} | TRUE | True | distances from fixed variables be used for variable prioritization |
| `heuristics/alns/useredcost` | `bool` | {TRUE,FALSE} | TRUE | True | should reduced cost scores be used for variable prioritization? |
| `heuristics/alns/domorefixings` | `bool` | {TRUE,FALSE} | TRUE | True | should the ALNS heuristic do more fixings by itself based on variable prioritization until the target fixing rate is reached? |
| `heuristics/alns/adjustfixingrate` | `bool` | {TRUE,FALSE} | TRUE | True | should the heuristic adjust the target fixing rate based on the success? |
| `heuristics/alns/usesubscipheurs` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic activate other sub-SCIP heuristics during its search? |
| `heuristics/alns/rewardcontrol` | `real` | [0,1] | 0.8 | True | reward control to increase the weight of the simple solution indicator and decrease the weight of the closed gap reward |
| `heuristics/alns/targetnodefactor` | `real` | [1,100000] | 1.05 | True | factor by which target node number is eventually increased |
| `heuristics/alns/seed` | `int` | [0,2147483647] | 113 | False | initial random seed for bandit algorithms and random decisions by neighborhoods |
| `heuristics/alns/maxcallssamesol` | `int` | [-1,100] | -1 | True | number of allowed executions of the heuristic on the same incumbent solution (-1: no limit, 0: number of active neighborhoods) |
| `heuristics/alns/adjustminimprove` | `bool` | {TRUE,FALSE} | FALSE | True | should the factor by which the minimum improvement is bound be dynamically updated? |
| `heuristics/alns/adjusttargetnodes` | `bool` | {TRUE,FALSE} | TRUE | True | should the target nodes be dynamically adjusted? |
| `heuristics/alns/eps` | `real` | [0,1] | 0.4685844 | True | increase exploration in epsilon-greedy bandit algorithm |
| `heuristics/alns/rewardbaseline` | `real` | [0,0.99] | 0.5 | True | the reward baseline to separate successful and failed calls |
| `heuristics/alns/resetweights` | `bool` | {TRUE,FALSE} | TRUE | True | should the bandit algorithms be reset when a new problem is read? |
| `heuristics/alns/rewardfilename` | `string` | String; interpretation stated in description | "-" | True | file name to store all rewards and the selection of the bandit |
| `heuristics/alns/subsciprandseeds` | `bool` | {TRUE,FALSE} | FALSE | True | should random seeds of sub-SCIPs be altered to increase diversification? |
| `heuristics/alns/scalebyeffort` | `bool` | {TRUE,FALSE} | TRUE | True | should the reward be scaled by the effort? |
| `heuristics/alns/copycuts` | `bool` | {TRUE,FALSE} | FALSE | True | should cutting planes be copied to the sub-SCIP? |
| `heuristics/alns/fixtol` | `real` | [0,1] | 0.1 | True | tolerance by which the fixing rate may be missed without generic fixing |
| `heuristics/alns/unfixtol` | `real` | [0,1] | 0.1 | True | tolerance by which the fixing rate may be exceeded without generic unfixing |
| `heuristics/alns/uselocalredcost` | `bool` | {TRUE,FALSE} | FALSE | True | should local reduced costs be used for generic (un)fixing? |
| `heuristics/alns/usepscost` | `bool` | {TRUE,FALSE} | TRUE | True | should pseudo cost scores be used for variable priorization? |
| `heuristics/alns/initduringroot` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic be executed multiple times during the root node? |
| `heuristics/rins/priority` | `int` | [-536870912,536870911] | -1101000 | True | priority of heuristic &lt;rins&gt; |
| `heuristics/rins/freq` | `int` | [-1,1073741822] | 15 | False | frequency for calling primal heuristic &lt;rins&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/rins/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;rins&gt; |
| `heuristics/rins/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;rins&gt; (-1: no limit) |
| `heuristics/rins/nodesofs` | `int` | [0,2147483647] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/rins/maxnodes` | `int` | [0,2147483647] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/rins/minnodes` | `int` | [0,2147483647] | 50 | True | minimum number of nodes required to start the subproblem |
| `heuristics/rins/nodesquot` | `real` | [0,1] | 0.3 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/rins/nwaitingnodes` | `int` | [0,2147483647] | 200 | True | number of nodes without incumbent change that heuristic should wait |
| `heuristics/rins/minimprove` | `real` | [0,1] | 0.01 | True | factor by which rins should at least improve the incumbent |
| `heuristics/rins/minfixingrate` | `real` | [0,1] | 0.3 | False | minimum percentage of integer variables that have to be fixed |
| `heuristics/rins/lplimfac` | `real` | [1,1.79769313486232e+308] | 2 | True | factor by which the limit on the number of LP depends on the node limit |
| `heuristics/rins/uselprows` | `bool` | {TRUE,FALSE} | FALSE | True | should subproblem be created out of the rows in the LP rows? |
| `heuristics/rins/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | if uselprows == FALSE, should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/rins/useuct` | `bool` | {TRUE,FALSE} | FALSE | True | should uct node selection be used at the beginning of the search? |
| `heuristics/localbranching/priority` | `int` | [-536870912,536870911] | -1102000 | True | priority of heuristic &lt;localbranching&gt; |
| `heuristics/localbranching/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;localbranching&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/localbranching/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;localbranching&gt; |
| `heuristics/localbranching/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;localbranching&gt; (-1: no limit) |
| `heuristics/localbranching/nodesofs` | `int` | [0,2147483647] | 1000 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/localbranching/neighborhoodsize` | `int` | [1,2147483647] | 18 | False | radius (using Manhattan metric) of the incumbent's neighborhood to be searched |
| `heuristics/localbranching/nodesquot` | `real` | [0,1] | 0.05 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/localbranching/lplimfac` | `real` | [1,1.79769313486232e+308] | 1.5 | True | factor by which the limit on the number of LP depends on the node limit |
| `heuristics/localbranching/minnodes` | `int` | [0,2147483647] | 1000 | True | minimum number of nodes required to start the subproblem |
| `heuristics/localbranching/maxnodes` | `int` | [0,2147483647] | 10000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/localbranching/nwaitingnodes` | `int` | [0,2147483647] | 200 | True | number of nodes without incumbent change that heuristic should wait |
| `heuristics/localbranching/minimprove` | `real` | [0,1] | 0.01 | True | factor by which localbranching should at least improve the incumbent |
| `heuristics/localbranching/uselprows` | `bool` | {TRUE,FALSE} | FALSE | True | should subproblem be created out of the rows in the LP rows? |
| `heuristics/localbranching/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | if uselprows == FALSE, should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/localbranching/bestsollimit` | `int` | [-1,2147483647] | 3 | False | limit on number of improving incumbent solutions in sub-CIP |
| `heuristics/trustregion/priority` | `int` | [-536870912,536870911] | -1102010 | True | priority of heuristic &lt;trustregion&gt; |
| `heuristics/trustregion/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;trustregion&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/trustregion/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;trustregion&gt; |
| `heuristics/trustregion/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;trustregion&gt; (-1: no limit) |
| `heuristics/trustregion/nodesofs` | `int` | [0,2147483647] | 1000 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/trustregion/minbinvars` | `int` | [1,2147483647] | 10 | False | the number of binary variables necessary to run the heuristic |
| `heuristics/trustregion/nodesquot` | `real` | [0,1] | 0.05 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/trustregion/lplimfac` | `real` | [1,1.79769313486232e+308] | 1.5 | True | factor by which the limit on the number of LP depends on the node limit |
| `heuristics/trustregion/minnodes` | `int` | [0,2147483647] | 100 | True | minimum number of nodes required to start the subproblem |
| `heuristics/trustregion/maxnodes` | `int` | [0,2147483647] | 10000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/trustregion/nwaitingnodes` | `int` | [0,2147483647] | 1 | True | number of nodes without incumbent change that heuristic should wait |
| `heuristics/trustregion/uselprows` | `bool` | {TRUE,FALSE} | FALSE | True | should subproblem be created out of the rows in the LP rows? |
| `heuristics/trustregion/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | if uselprows == FALSE, should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/trustregion/bestsollimit` | `int` | [-1,2147483647] | 3 | False | limit on number of improving incumbent solutions in sub-CIP |
| `heuristics/trustregion/violpenalty` | `real` | [0,1.79769313486232e+308] | 100 | False | the penalty for each change in the binary variables from the candidate solution |
| `heuristics/trustregion/objminimprove` | `real` | [0,1.79769313486232e+308] | 0.01 | False | the minimum absolute improvement in the objective function value |
| `heuristics/gins/priority` | `int` | [-536870912,536870911] | -1103000 | True | priority of heuristic &lt;gins&gt; |
| `heuristics/gins/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling primal heuristic &lt;gins&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/gins/freqofs` | `int` | [0,1073741822] | 8 | False | frequency offset for calling primal heuristic &lt;gins&gt; |
| `heuristics/gins/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;gins&gt; (-1: no limit) |
| `heuristics/gins/nodesofs` | `int` | [0,2147483647] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/gins/maxnodes` | `int` | [0,2147483647] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/gins/minnodes` | `int` | [0,2147483647] | 50 | True | minimum number of nodes required to start the subproblem |
| `heuristics/gins/nwaitingnodes` | `int` | [0,2147483647] | 100 | True | number of nodes without incumbent change that heuristic should wait |
| `heuristics/gins/nodesquot` | `real` | [0,1] | 0.15 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/gins/minfixingrate` | `real` | [1e-06,0.999999] | 0.66 | False | percentage of integer variables that have to be fixed |
| `heuristics/gins/minimprove` | `real` | [0,1] | 0.01 | True | factor by which gins should at least improve the incumbent |
| `heuristics/gins/uselprows` | `bool` | {TRUE,FALSE} | FALSE | True | should subproblem be created out of the rows in the LP rows? |
| `heuristics/gins/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | if uselprows == FALSE, should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/gins/fixcontvars` | `bool` | {TRUE,FALSE} | FALSE | True | should continuous variables outside the neighborhoods be fixed? |
| `heuristics/gins/bestsollimit` | `int` | [-1,2147483647] | 3 | False | limit on number of improving incumbent solutions in sub-CIP |
| `heuristics/gins/maxdistance` | `int` | [-1,2147483647] | 3 | False | maximum distance to selected variable to enter the subproblem, or -1 to select the distance that best approximates the minimum fixing rate from below |
| `heuristics/gins/potential` | `char` | {lpr} | r | True | the reference point to compute the neighborhood potential: (r)oot, (l)ocal lp, or (p)seudo solution |
| `heuristics/gins/userollinghorizon` | `bool` | {TRUE,FALSE} | TRUE | True | should the heuristic solve a sequence of sub-MIP's around the first selected variable |
| `heuristics/gins/relaxdenseconss` | `bool` | {TRUE,FALSE} | FALSE | True | should dense constraints (at least as dense as 1 - minfixingrate) be ignored by connectivity graph? |
| `heuristics/gins/rollhorizonlimfac` | `real` | [0,1] | 0.4 | True | limiting percentage for variables already used in sub-SCIPs to terminate rolling horizon approach |
| `heuristics/gins/overlap` | `real` | [0,1] | 0 | True | overlap of blocks between runs - 0.0: no overlap, 1.0: shift by only 1 block |
| `heuristics/gins/usedecomp` | `bool` | {TRUE,FALSE} | TRUE | True | should user decompositions be considered, if available? |
| `heuristics/gins/usedecomprollhorizon` | `bool` | {TRUE,FALSE} | FALSE | True | should user decompositions be considered for initial selection in rolling horizon, if available? |
| `heuristics/gins/useselfallback` | `bool` | {TRUE,FALSE} | TRUE | True | should random initial variable selection be used if decomposition was not successful? |
| `heuristics/gins/consecutiveblocks` | `bool` | {TRUE,FALSE} | TRUE | True | should blocks be treated consecutively (sorted by ascending label?) |
| `heuristics/mutation/priority` | `int` | [-536870912,536870911] | -1103010 | True | priority of heuristic &lt;mutation&gt; |
| `heuristics/mutation/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;mutation&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/mutation/freqofs` | `int` | [0,1073741822] | 8 | False | frequency offset for calling primal heuristic &lt;mutation&gt; |
| `heuristics/mutation/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;mutation&gt; (-1: no limit) |
| `heuristics/mutation/nodesofs` | `int` | [0,2147483647] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/mutation/maxnodes` | `int` | [0,2147483647] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/mutation/minnodes` | `int` | [0,2147483647] | 500 | True | minimum number of nodes required to start the subproblem |
| `heuristics/mutation/nwaitingnodes` | `int` | [0,2147483647] | 200 | True | number of nodes without incumbent change that heuristic should wait |
| `heuristics/mutation/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/mutation/minfixingrate` | `real` | [1e-06,0.999999] | 0.8 | False | percentage of integer variables that have to be fixed |
| `heuristics/mutation/minimprove` | `real` | [0,1] | 0.01 | True | factor by which mutation should at least improve the incumbent |
| `heuristics/mutation/uselprows` | `bool` | {TRUE,FALSE} | FALSE | True | should subproblem be created out of the rows in the LP rows? |
| `heuristics/mutation/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | if uselprows == FALSE, should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/mutation/bestsollimit` | `int` | [-1,2147483647] | -1 | False | limit on number of improving incumbent solutions in sub-CIP |
| `heuristics/mutation/useuct` | `bool` | {TRUE,FALSE} | FALSE | True | should uct node selection be used at the beginning of the search? |
| `heuristics/crossover/priority` | `int` | [-536870912,536870911] | -1104000 | True | priority of heuristic &lt;crossover&gt; |
| `heuristics/crossover/freq` | `int` | [-1,1073741822] | 15 | False | frequency for calling primal heuristic &lt;crossover&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/crossover/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;crossover&gt; |
| `heuristics/crossover/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;crossover&gt; (-1: no limit) |
| `heuristics/crossover/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/crossover/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/crossover/minnodes` | `longint` | [0,9223372036854775807] | 50 | True | minimum number of nodes required to start the subproblem |
| `heuristics/crossover/nusedsols` | `int` | [2,2147483647] | 3 | False | number of solutions to be taken into account |
| `heuristics/crossover/nwaitingnodes` | `longint` | [0,9223372036854775807] | 200 | True | number of nodes without incumbent change that heuristic should wait |
| `heuristics/crossover/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/crossover/minfixingrate` | `real` | [0,1] | 0.666 | False | minimum percentage of integer variables that have to be fixed |
| `heuristics/crossover/minimprove` | `real` | [0,1] | 0.01 | True | factor by which Crossover should at least improve the incumbent |
| `heuristics/crossover/lplimfac` | `real` | [1,1.79769313486232e+308] | 2 | True | factor by which the limit on the number of LP depends on the node limit |
| `heuristics/crossover/randomization` | `bool` | {TRUE,FALSE} | TRUE | True | should the choice which sols to take be randomized? |
| `heuristics/crossover/dontwaitatroot` | `bool` | {TRUE,FALSE} | FALSE | True | should the nwaitingnodes parameter be ignored at the root node? |
| `heuristics/crossover/uselprows` | `bool` | {TRUE,FALSE} | FALSE | True | should subproblem be created out of the rows in the LP rows? |
| `heuristics/crossover/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | if uselprows == FALSE, should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/crossover/permute` | `bool` | {TRUE,FALSE} | FALSE | True | should the subproblem be permuted to increase diversification? |
| `heuristics/crossover/bestsollimit` | `int` | [-1,2147483647] | -1 | False | limit on number of improving incumbent solutions in sub-CIP |
| `heuristics/crossover/useuct` | `bool` | {TRUE,FALSE} | FALSE | True | should uct node selection be used at the beginning of the search? |
| `heuristics/lpface/priority` | `int` | [-536870912,536870911] | -1104010 | True | priority of heuristic &lt;lpface&gt; |
| `heuristics/lpface/freq` | `int` | [-1,1073741822] | 15 | False | frequency for calling primal heuristic &lt;lpface&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/lpface/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;lpface&gt; |
| `heuristics/lpface/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;lpface&gt; (-1: no limit) |
| `heuristics/lpface/nodesofs` | `longint` | [0,9223372036854775807] | 200 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/lpface/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/lpface/minnodes` | `longint` | [0,9223372036854775807] | 50 | True | minimum number of nodes required to start the subproblem |
| `heuristics/lpface/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/lpface/minfixingrate` | `real` | [0,1] | 0.1 | False | required percentage of fixed integer variables in sub-MIP to run |
| `heuristics/lpface/lplimfac` | `real` | [1,1.79769313486232e+308] | 2 | True | factor by which the limit on the number of LP depends on the node limit |
| `heuristics/lpface/uselprows` | `bool` | {TRUE,FALSE} | TRUE | True | should subproblem be created out of the rows in the LP rows? |
| `heuristics/lpface/dualbasisequations` | `bool` | {TRUE,FALSE} | FALSE | True | should dually nonbasic rows be turned into equations? |
| `heuristics/lpface/keepsubscip` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic continue solving the same sub-SCIP? |
| `heuristics/lpface/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | if uselprows == FALSE, should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/lpface/subscipobjective` | `char` | {forzi} | z | True | objective function in the sub-SCIP: (z)ero, (r)oot-LP-difference, (i)nference, LP (f)ractionality, (o)riginal |
| `heuristics/lpface/minpathlen` | `int` | [0,65531] | 5 | True | the minimum active search tree path length along which lower bound hasn't changed before heuristic becomes active |
| `heuristics/dins/priority` | `int` | [-536870912,536870911] | -1105000 | True | priority of heuristic &lt;dins&gt; |
| `heuristics/dins/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;dins&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/dins/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;dins&gt; |
| `heuristics/dins/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;dins&gt; (-1: no limit) |
| `heuristics/dins/nodesofs` | `longint` | [0,9223372036854775807] | 5000 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/dins/nodesquot` | `real` | [0,1] | 0.05 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/dins/minnodes` | `longint` | [0,9223372036854775807] | 50 | False | minimum number of nodes required to start the subproblem |
| `heuristics/dins/solnum` | `int` | [1,2147483647] | 5 | False | number of pool-solutions to be checked for flag array update (for hard fixing of binary variables) |
| `heuristics/dins/neighborhoodsize` | `int` | [1,2147483647] | 18 | False | radius (using Manhattan metric) of the incumbent's neighborhood to be searched |
| `heuristics/dins/maxnodes` | `longint` | [0,9223372036854775807] | 5000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/dins/minimprove` | `real` | [0,1] | 0.01 | True | factor by which dins should at least improve the incumbent |
| `heuristics/dins/nwaitingnodes` | `longint` | [0,9223372036854775807] | 200 | True | number of nodes without incumbent change that heuristic should wait |
| `heuristics/dins/lplimfac` | `real` | [1,1.79769313486232e+308] | 1.5 | True | factor by which the limit on the number of LP depends on the node limit |
| `heuristics/dins/minfixingrate` | `real` | [0,1] | 0.3 | False | minimum percentage of integer variables that have to be fixable |
| `heuristics/dins/uselprows` | `bool` | {TRUE,FALSE} | FALSE | True | should subproblem be created out of the rows in the LP rows? |
| `heuristics/dins/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | if uselprows == FALSE, should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/dins/useuct` | `bool` | {TRUE,FALSE} | FALSE | True | should uct node selection be used at the beginning of the search? |
| `heuristics/dins/bestsollimit` | `int` | [-1,2147483647] | 3 | False | limit on number of improving incumbent solutions in sub-CIP |
| `heuristics/bound/priority` | `int` | [-536870912,536870911] | -1107000 | True | priority of heuristic &lt;bound&gt; |
| `heuristics/bound/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;bound&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/bound/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;bound&gt; |
| `heuristics/bound/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;bound&gt; (-1: no limit) |
| `heuristics/bound/onlywithoutsol` | `bool` | {TRUE,FALSE} | TRUE | True | Should heuristic only be executed if no primal solution was found, yet? |
| `heuristics/bound/maxproprounds` | `int` | [-1,536870911] | 0 | True | maximum number of propagation rounds during probing (-1 infinity, -2 parameter settings) |
| `heuristics/bound/bound` | `char` | {lub} | l | False | to which bound should integer variables be fixed? ('l'ower, 'u'pper, or 'b'oth) |
| `heuristics/undercover/priority` | `int` | [-536870912,536870911] | -1110000 | True | priority of heuristic &lt;undercover&gt; |
| `heuristics/undercover/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;undercover&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/undercover/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;undercover&gt; |
| `heuristics/undercover/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;undercover&gt; (-1: no limit) |
| `heuristics/undercover/fixingalts` | `string` | String; interpretation stated in description | "li" | False | prioritized sequence of fixing values used ('l'p relaxation, 'n'lp relaxation, 'i'ncumbent solution) |
| `heuristics/undercover/maxnodes` | `longint` | [0,9223372036854775807] | 500 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/undercover/minnodes` | `longint` | [0,9223372036854775807] | 500 | True | minimum number of nodes required to start the subproblem |
| `heuristics/undercover/nodesofs` | `longint` | [0,9223372036854775807] | 500 | False | number of nodes added to the contingent of the total nodes |
| `heuristics/undercover/conflictweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1000 | True | weight for conflict score in fixing order |
| `heuristics/undercover/cutoffweight` | `real` | [0,1.79769313486232e+308] | 1 | True | weight for cutoff score in fixing order |
| `heuristics/undercover/inferenceweight` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1 | True | weight for inference score in fixing order |
| `heuristics/undercover/maxcoversizevars` | `real` | [0,1] | 1 | True | maximum coversize (as fraction of total number of variables) |
| `heuristics/undercover/maxcoversizeconss` | `real` | [0,1.79769313486232e+308] | 1.79769313486232e+308 | True | maximum coversize (as ratio to the percentage of non-affected constraints) |
| `heuristics/undercover/mincoveredrel` | `real` | [0,1] | 0.15 | True | minimum percentage of nonlinear constraints in the original problem |
| `heuristics/undercover/minimprove` | `real` | [-1,1] | 0 | True | factor by which the heuristic should at least improve the incumbent |
| `heuristics/undercover/nodesquot` | `real` | [0,1] | 0.1 | False | contingent of sub problem nodes in relation to the number of nodes of the original problem |
| `heuristics/undercover/recoverdiv` | `real` | [0,1] | 0.9 | True | fraction of covering variables in the last cover which need to change their value when recovering |
| `heuristics/undercover/mincoveredabs` | `int` | [0,2147483647] | 5 | True | minimum number of nonlinear constraints in the original problem |
| `heuristics/undercover/maxbacktracks` | `int` | [0,2147483647] | 6 | True | maximum number of backtracks in fix-and-propagate |
| `heuristics/undercover/maxrecovers` | `int` | [0,2147483647] | 0 | True | maximum number of recoverings |
| `heuristics/undercover/maxreorders` | `int` | [0,2147483647] | 1 | True | maximum number of reorderings of the fixing order |
| `heuristics/undercover/coveringobj` | `char` | {cdlmtu} | u | True | objective function of the covering problem (influenced nonlinear 'c'onstraints/'t'erms, 'd'omain size, 'l'ocks, 'm'in of up/down locks, 'u'nit penalties) |
| `heuristics/undercover/fixingorder` | `char` | {CcVv} | v | True | order in which variables should be fixed (increasing 'C'onflict score, decreasing 'c'onflict score, increasing 'V'ariable index, decreasing 'v'ariable index |
| `heuristics/undercover/beforecuts` | `bool` | {TRUE,FALSE} | TRUE | True | should the heuristic be called at root node before cut separation? |
| `heuristics/undercover/fixintfirst` | `bool` | {TRUE,FALSE} | FALSE | True | should integer variables in the cover be fixed first? |
| `heuristics/undercover/locksrounding` | `bool` | {TRUE,FALSE} | TRUE | True | shall LP values for integer vars be rounded according to locks? |
| `heuristics/undercover/onlyconvexify` | `bool` | {TRUE,FALSE} | FALSE | False | should we only fix variables in order to obtain a convex problem? |
| `heuristics/undercover/postnlp` | `bool` | {TRUE,FALSE} | TRUE | False | should the NLP heuristic be called to polish a feasible solution? |
| `heuristics/undercover/coverand` | `bool` | {TRUE,FALSE} | TRUE | True | should and constraints be covered (or just copied)? |
| `heuristics/undercover/coverbd` | `bool` | {TRUE,FALSE} | FALSE | True | should bounddisjunction constraints be covered (or just copied)? |
| `heuristics/undercover/coverind` | `bool` | {TRUE,FALSE} | FALSE | True | should indicator constraints be covered (or just copied)? |
| `heuristics/undercover/covernl` | `bool` | {TRUE,FALSE} | TRUE | True | should nonlinear constraints be covered (or just copied)? |
| `heuristics/undercover/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | should all active cuts from cutpool be copied to constraints in subproblem? |
| `heuristics/undercover/reusecover` | `bool` | {TRUE,FALSE} | FALSE | True | shall the cover be reused if a conflict was added after an infeasible subproblem? |
| `heuristics/proximity/priority` | `int` | [-536870912,536870911] | -2000000 | True | priority of heuristic &lt;proximity&gt; |
| `heuristics/proximity/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling primal heuristic &lt;proximity&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/proximity/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;proximity&gt; |
| `heuristics/proximity/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;proximity&gt; (-1: no limit) |
| `heuristics/proximity/uselprows` | `bool` | {TRUE,FALSE} | FALSE | True | should subproblem be constructed based on LP row information? |
| `heuristics/proximity/restart` | `bool` | {TRUE,FALSE} | TRUE | True | should the heuristic immediately run again on its newly found solution? |
| `heuristics/proximity/usefinallp` | `bool` | {TRUE,FALSE} | FALSE | True | should the heuristic solve a final LP in case of continuous objective variables? |
| `heuristics/proximity/maxnodes` | `longint` | [0,9223372036854775807] | 10000 | True | maximum number of nodes to regard in the subproblem |
| `heuristics/proximity/nodesofs` | `longint` | [0,9223372036854775807] | 50 | True | number of nodes added to the contingent of the total nodes |
| `heuristics/proximity/minnodes` | `longint` | [0,9223372036854775807] | 1 | True | minimum number of nodes required to start the subproblem |
| `heuristics/proximity/maxlpiters` | `longint` | [-1,9223372036854775807] | 100000 | True | maximum number of LP iterations to be performed in the subproblem |
| `heuristics/proximity/minlpiters` | `longint` | [0,9223372036854775807] | 200 | True | minimum number of LP iterations performed in subproblem |
| `heuristics/proximity/waitingnodes` | `longint` | [0,9223372036854775807] | 100 | True | waiting nodes since last incumbent before heuristic is executed |
| `heuristics/proximity/minimprove` | `real` | [0,1] | 0.02 | True | factor by which proximity should at least improve the incumbent |
| `heuristics/proximity/nodesquot` | `real` | [0,1e+20] | 0.1 | True | sub-MIP node limit w.r.t number of original nodes |
| `heuristics/proximity/binvarquot` | `real` | [0,1] | 0.1 | True | threshold for percentage of binary variables required to start |
| `heuristics/proximity/lpitersquot` | `real` | [0,1] | 0.2 | True | quotient of sub-MIP LP iterations with respect to LP iterations so far |
| `heuristics/proximity/mingap` | `real` | [0,1e+20] | 0.01 | True | minimum primal-dual gap for which the heuristic is executed |
| `heuristics/proximity/useuct` | `bool` | {TRUE,FALSE} | FALSE | True | should uct node selection be used at the beginning of the search? |
| `heuristics/subnlp/priority` | `int` | [-536870912,536870911] | -2000010 | True | priority of heuristic &lt;subnlp&gt; |
| `heuristics/subnlp/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling primal heuristic &lt;subnlp&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/subnlp/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;subnlp&gt; |
| `heuristics/subnlp/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;subnlp&gt; (-1: no limit) |
| `heuristics/subnlp/nlpverblevel` | `int` | [0,65535] | 0 | False | verbosity level of NLP solver |
| `heuristics/subnlp/nodesoffset` | `int` | [0,2147483647] | 1600 | False | number of nodes added to the current number of nodes when computing itercontingent (higher value runs heuristic more often in early search) |
| `heuristics/subnlp/nodesfactor` | `real` | [0,1e+20] | 0.3 | False | factor on number of nodes in SCIP (plus nodesoffset) to compute itercontingent (higher value runs heuristics more frequently) |
| `heuristics/subnlp/successrateexp` | `real` | [0,1.79769313486232e+308] | 1 | False | exponent for power of success rate to be multiplied with itercontingent (lower value decreases impact of success rate) |
| `heuristics/subnlp/iterinit` | `int` | [0,2147483647] | 300 | False | number of iterations used for initial NLP solves |
| `heuristics/subnlp/ninitsolves` | `int` | [0,2147483647] | 2 | False | number of successful NLP solves until switching to iterlimit guess and using success rate |
| `heuristics/subnlp/itermin` | `int` | [0,2147483647] | 20 | False | minimal number of iterations for NLP solves |
| `heuristics/subnlp/opttol` | `real` | [0,1] | 1e-07 | True | absolute optimality tolerance to use for NLP solves |
| `heuristics/subnlp/feastolfactor` | `real` | [0,1] | 0.1 | False | factor on SCIP feasibility tolerance for NLP solves if resolving when NLP solution not feasible in CIP |
| `heuristics/subnlp/maxpresolverounds` | `int` | [-1,2147483647] | -1 | False | limit on number of presolve rounds in sub-SCIP (-1 for unlimited, 0 for no presolve) |
| `heuristics/subnlp/presolveemphasis` | `int` | [0,3] | 2 | False | presolve emphasis in sub-SCIP (0: default, 1: aggressive, 2: fast, 3: off) |
| `heuristics/subnlp/setcutoff` | `bool` | {TRUE,FALSE} | TRUE | False | whether to set cutoff in sub-SCIP to current primal bound |
| `heuristics/subnlp/forbidfixings` | `bool` | {TRUE,FALSE} | FALSE | False | whether to add constraints that forbid specific fixings that turned out to be infeasible |
| `heuristics/subnlp/keepcopy` | `bool` | {TRUE,FALSE} | TRUE | True | whether to keep SCIP copy or to create new copy each time heuristic is applied |
| `heuristics/subnlp/expectinfeas` | `real` | [0,1] | 0 | False | percentage of NLP solves with infeasible status required to tell NLP solver to expect an infeasible NLP |
| `heuristics/mpec/priority` | `int` | [-536870912,536870911] | -2050000 | True | priority of heuristic &lt;mpec&gt; |
| `heuristics/mpec/freq` | `int` | [-1,1073741822] | 50 | False | frequency for calling primal heuristic &lt;mpec&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/mpec/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;mpec&gt; |
| `heuristics/mpec/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;mpec&gt; (-1: no limit) |
| `heuristics/mpec/inittheta` | `real` | [0,0.25] | 0.125 | False | initial regularization right-hand side value |
| `heuristics/mpec/sigma` | `real` | [0,1] | 0.5 | False | regularization update factor |
| `heuristics/mpec/subnlptrigger` | `real` | [0,1] | 0.001 | False | maximum number of NLP iterations per solve |
| `heuristics/mpec/maxnlpcost` | `real` | [0,1e+20] | 100000000 | False | maximum cost available for solving NLPs per call of the heuristic |
| `heuristics/mpec/minimprove` | `real` | [0,1] | 0.01 | False | factor by which heuristic should at least improve the incumbent |
| `heuristics/mpec/mingapleft` | `real` | [0,1e+20] | 0.05 | False | minimum amount of gap left in order to call the heuristic |
| `heuristics/mpec/maxiter` | `int` | [0,2147483647] | 100 | False | maximum number of iterations of the MPEC loop |
| `heuristics/mpec/maxnlpiter` | `int` | [0,2147483647] | 500 | False | maximum number of NLP iterations per solve |
| `heuristics/mpec/maxnunsucc` | `int` | [0,2147483647] | 10 | False | maximum number of consecutive calls for which the heuristic did not find an improving solution |
| `heuristics/multistart/priority` | `int` | [-536870912,536870911] | -2100000 | True | priority of heuristic &lt;multistart&gt; |
| `heuristics/multistart/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling primal heuristic &lt;multistart&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/multistart/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;multistart&gt; |
| `heuristics/multistart/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;multistart&gt; (-1: no limit) |
| `heuristics/multistart/nrndpoints` | `int` | [0,2147483647] | 100 | False | number of random points generated per execution call |
| `heuristics/multistart/maxboundsize` | `real` | [0,1e+20] | 20000 | False | maximum variable domain size for unbounded variables |
| `heuristics/multistart/maxiter` | `int` | [0,2147483647] | 300 | False | number of iterations to reduce the maximum violation of a point |
| `heuristics/multistart/minimprfac` | `real` | [-1e+20,1e+20] | 0.05 | False | minimum required improving factor to proceed in improvement of a single point |
| `heuristics/multistart/minimpriter` | `int` | [1,2147483647] | 10 | False | number of iteration when checking the minimum improvement |
| `heuristics/multistart/maxreldist` | `real` | [0,1e+20] | 0.15 | False | maximum distance between two points in the same cluster |
| `heuristics/multistart/gradlimit` | `real` | [0,1e+20] | 5000000 | False | limit for gradient computations for all improvePoint() calls (0 for no limit) |
| `heuristics/multistart/maxncluster` | `int` | [0,2147483647] | 3 | False | maximum number of considered clusters per heuristic call |
| `heuristics/multistart/onlynlps` | `bool` | {TRUE,FALSE} | TRUE | False | should the heuristic run only on continuous problems? |
| `heuristics/trysol/priority` | `int` | [-536870912,536870911] | -3000010 | True | priority of heuristic &lt;trysol&gt; |
| `heuristics/trysol/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling primal heuristic &lt;trysol&gt; (-1: never, 0: only at depth freqofs) |
| `heuristics/trysol/freqofs` | `int` | [0,1073741822] | 0 | False | frequency offset for calling primal heuristic &lt;trysol&gt; |
| `heuristics/trysol/maxdepth` | `int` | [-1,1073741822] | -1 | True | maximal depth level to call primal heuristic &lt;trysol&gt; (-1: no limit) |

## history

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `history/valuebased` | `bool` | {TRUE,FALSE} | FALSE | False | should statistics be collected for variable domain value pairs? |
| `history/allowmerge` | `bool` | {TRUE,FALSE} | FALSE | False | should variable histories be merged from sub-SCIPs whenever possible? |
| `history/allowtransfer` | `bool` | {TRUE,FALSE} | FALSE | False | should variable histories be transferred to initialize SCIP copies? |

## iis

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `iis/irreducible` | `bool` | {TRUE,FALSE} | TRUE | False | should the resultant infeasible set be irreducible, i.e., an IIS not an IS |
| `iis/removebounds` | `bool` | {TRUE,FALSE} | FALSE | False | should bounds of the problem be considered for removal |
| `iis/silent` | `bool` | {TRUE,FALSE} | FALSE | False | should the IIS finders be run silently and output suppressed |
| `iis/stopafterone` | `bool` | {TRUE,FALSE} | TRUE | True | should the IIS search stop after a single IIS finder is run (excluding post processing) |
| `iis/removeunusedvars` | `bool` | {TRUE,FALSE} | TRUE | True | should vars that do not feature in any constraints be removed at the end of the IIS process |
| `iis/time` | `real` | [0,1e+20] | 1e+20 | False | maximal time in seconds for all IIS finders to run |
| `iis/nodes` | `longint` | [-1,9223372036854775807] | -1 | False | maximal number of nodes to process for all IIS finders (-1: no limit) |
| `iis/greedy/priority` | `int` | [-536870912,1073741823] | 8000 | False | priority of iis generation rule &lt;greedy&gt; |
| `iis/greedy/timelimperiter` | `real` | [0,1e+98] | 1e+20 | False | time limit of optimization process for each individual subproblem |
| `iis/greedy/nodelimperiter` | `longint` | [-1,9223372036854775807] | -1 | False | node limit of optimization process for each individual subproblem |
| `iis/greedy/additive` | `bool` | {TRUE,FALSE} | TRUE | False | should an additive constraint approach be used instead of deletion |
| `iis/greedy/conservative` | `bool` | {TRUE,FALSE} | TRUE | True | should an unsolved problem (by e.g. user interrupt, node limit, time limit) be considered feasible when deleting constraints |
| `iis/greedy/delafteradd` | `bool` | {TRUE,FALSE} | TRUE | True | should the deletion routine be performed after the addition routine (in the case of additive) |
| `iis/greedy/dynamicreordering` | `bool` | {TRUE,FALSE} | TRUE | True | should satisfied constraints outside the batch of an intermediate solve be added during the additive method |
| `iis/greedy/initbatchsize` | `int` | [1,2147483647] | 16 | False | the initial batchsize for the first iteration, ignored if initrelbatchsize is positive |
| `iis/greedy/initrelbatchsize` | `real` | [0,1] | 0.03125 | False | the initial batchsize relative to the original problem for the first iteration (0.0: use initbatchsize) |
| `iis/greedy/maxbatchsize` | `int` | [1,2147483647] | 2147483647 | True | the maximum batchsize per iteration |
| `iis/greedy/maxrelbatchsize` | `real` | [0,1] | 0.5 | True | the maximum batchsize relative to the original problem per iteration |
| `iis/greedy/batchingfactor` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 2 | True | the factor with which the batchsize is multiplied in every update |
| `iis/greedy/batchingoffset` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 0 | True | the offset which is added to the multiplied batchsize in every update |
| `iis/greedy/batchupdateinterval` | `int` | [1,2147483647] | 1 | True | the number of iterations to run with a constant batchsize before updating (1: always update) |

## limits

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `limits/time` | `real` | [0,1e+20] | 1e+20 | False | maximal time in seconds to run |
| `limits/nodes` | `longint` | [-1,9223372036854775807] | -1 | False | maximal number of nodes to process (-1: no limit) |
| `limits/totalnodes` | `longint` | [-1,9223372036854775807] | -1 | False | maximal number of total nodes (incl. restarts) to process (-1: no limit) |
| `limits/stallnodes` | `longint` | [-1,9223372036854775807] | -1 | False | solving stops, if the given number of nodes was processed since the last improvement of the primal solution value (-1: no limit) |
| `limits/memory` | `real` | [0,8796093022207] | 8796093022207 | False | maximal memory usage in MB; reported memory usage is lower than real memory usage! |
| `limits/gap` | `real` | [0,1.79769313486232e+308] | 0 | False | solving stops, if the relative gap = &#124;primal - dual&#124;/MIN(&#124;dual&#124;,&#124;primal&#124;) is below the given value, the gap is 'Infinity', if primal and dual bound have opposite signs |
| `limits/absgap` | `real` | [0,1.79769313486232e+308] | 0 | False | solving stops, if the absolute gap = &#124;primalbound - dualbound&#124; is below the given value |
| `limits/primal` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1e+99 | False | solving stops, if primal bound is at least as good as given value |
| `limits/dual` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1e+99 | False | solving stops, if dual bound is at least as good as given value |
| `limits/solutions` | `int` | [-1,2147483647] | -1 | False | solving stops, if the given number of solutions were found; this limit is first checked in presolving (-1: no limit) |
| `limits/bestsol` | `int` | [-1,2147483647] | -1 | False | solving stops, if the given number of solution improvements were found (-1: no limit) |
| `limits/maxsol` | `int` | [1,2147483647] | 100 | False | maximal number of solutions to store in the solution storage |
| `limits/maxorigsol` | `int` | [0,2147483647] | 10 | False | maximal number of solutions candidates to store in the solution storage of the original problem |
| `limits/restarts` | `int` | [-1,2147483647] | -1 | False | solving stops, if the given number of restarts was triggered (-1: no limit) |
| `limits/autorestartnodes` | `int` | [-1,2147483647] | -1 | False | if solve exceeds this number of nodes for the first time, an automatic restart is triggered (-1: no automatic restart) |
| `limits/softtime` | `real` | [-1,1.79769313486232e+308] | -1 | False | soft time limit which should be applied after first solution was found (-1.0: disabled) |

## lp

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `lp/solvefreq` | `int` | [-1,1073741822] | 1 | False | frequency for solving LP at the nodes (-1: never; 0: only root LP) |
| `lp/iterlim` | `longint` | [-1,9223372036854775807] | -1 | True | iteration limit for each single LP solve (-1: no limit) |
| `lp/rootiterlim` | `longint` | [-1,9223372036854775807] | -1 | True | iteration limit for initial root LP solve (-1: no limit) |
| `lp/solvedepth` | `int` | [-1,1073741822] | -1 | False | maximal depth for solving LP at the nodes (-1: no depth limit) |
| `lp/minsolvedepth` | `int` | [0,1073741822] | 0 | False | minimal depth for solving LP at the nodes |
| `lp/initalgorithm` | `char` | {spdbc} | s | False | LP algorithm for solving initial LP relaxations (automatic 's'implex, 'p'rimal simplex, 'd'ual simplex, 'b'arrier, barrier with 'c'rossover) |
| `lp/resolvealgorithm` | `char` | {spdbc} | s | False | LP algorithm for resolving LP relaxations if a starting basis exists (automatic 's'implex, 'p'rimal simplex, 'd'ual simplex, 'b'arrier, barrier with 'c'rossover) |
| `lp/pricing` | `char` | {lafpsqd} | l | False | LP pricing strategy ('l'pi default, 'a'uto, 'f'ull pricing, 'p'artial, 's'teepest edge pricing, 'q'uickstart steepest edge pricing, 'd'evex pricing) |
| `lp/clearinitialprobinglp` | `bool` | {TRUE,FALSE} | TRUE | True | should lp state be cleared at the end of probing mode when lp was initially unsolved, e.g., when called right after presolving? |
| `lp/resolverestore` | `bool` | {TRUE,FALSE} | FALSE | True | should the LP be resolved to restore the state at start of diving (if FALSE we buffer the solution values)? |
| `lp/freesolvalbuffers` | `bool` | {TRUE,FALSE} | FALSE | True | should the buffers for storing LP solution values during diving be freed at end of diving? |
| `lp/colagelimit` | `int` | [-1,2147483647] | 10 | True | maximum age a dynamic column can reach before it is deleted from the LP (-1: don't delete columns due to aging) |
| `lp/rowagelimit` | `int` | [-1,2147483647] | 10 | True | maximum age a dynamic row can reach before it is deleted from the LP (-1: don't delete rows due to aging) |
| `lp/cleanupcols` | `bool` | {TRUE,FALSE} | FALSE | True | should new non-basic columns be removed after LP solving? |
| `lp/cleanupcolsroot` | `bool` | {TRUE,FALSE} | FALSE | True | should new non-basic columns be removed after root LP solving? |
| `lp/cleanuprows` | `bool` | {TRUE,FALSE} | TRUE | True | should new basic rows be removed after LP solving? |
| `lp/cleanuprowsroot` | `bool` | {TRUE,FALSE} | TRUE | True | should new basic rows be removed after root LP solving? |
| `lp/checkstability` | `bool` | {TRUE,FALSE} | TRUE | True | should LP solver's return status be checked for stability? |
| `lp/conditionlimit` | `real` | [-1,1.79769313486232e+308] | -1 | True | maximum condition number of LP basis counted as stable (-1.0: no limit) |
| `lp/minmarkowitz` | `real` | [0.0001,0.9999] | 0.01 | True | minimal Markowitz threshold to control sparsity/stability in LU factorization |
| `lp/checkprimfeas` | `bool` | {TRUE,FALSE} | TRUE | True | should LP solutions be checked for primal feasibility, resolving LP when numerical troubles occur? |
| `lp/checkdualfeas` | `bool` | {TRUE,FALSE} | TRUE | True | should LP solutions be checked for dual feasibility, resolving LP when numerical troubles occur? |
| `lp/checkfarkas` | `bool` | {TRUE,FALSE} | TRUE | True | should infeasibility proofs from the LP be checked? |
| `lp/fastmip` | `int` | [0,1] | 1 | True | which FASTMIP setting of LP solver should be used? 0: off, 1: low |
| `lp/scaling` | `int` | [0,2] | 1 | True | LP scaling (0: none, 1: normal, 2: aggressive) |
| `lp/presolving` | `bool` | {TRUE,FALSE} | TRUE | True | should presolving of LP solver be used? |
| `lp/lexdualalgo` | `bool` | {TRUE,FALSE} | FALSE | True | should the lexicographic dual algorithm be used? |
| `lp/lexdualrootonly` | `bool` | {TRUE,FALSE} | TRUE | True | should the lexicographic dual algorithm be applied only at the root node |
| `lp/lexdualmaxrounds` | `int` | [-1,2147483647] | 2 | True | maximum number of rounds in the lexicographic dual algorithm (-1: unbounded) |
| `lp/lexdualbasic` | `bool` | {TRUE,FALSE} | FALSE | True | choose fractional basic variables in lexicographic dual algorithm? |
| `lp/lexdualstalling` | `bool` | {TRUE,FALSE} | TRUE | True | turn on the lex dual algorithm only when stalling? |
| `lp/disablecutoff` | `int` | [0,2] | 2 | True | disable the cutoff bound in the LP solver? (0: enabled, 1: disabled, 2: auto) |
| `lp/rowrepswitch` | `real` | [-1,1.79769313486232e+308] | 1.2 | True | simplex algorithm shall use row representation of the basis if number of rows divided by number of columns exceeds this value (-1.0 to disable row representation) |
| `lp/threads` | `int` | [0,64] | 0 | True | number of threads used for solving the LP (0: automatic) |
| `lp/resolveiterfac` | `real` | [-1,1.79769313486232e+308] | -1 | True | factor of average LP iterations that is used as LP iteration limit for LP resolve (-1: unlimited) |
| `lp/resolveitermin` | `int` | [1,2147483647] | 1000 | True | minimum number of iterations that are allowed for LP resolve |
| `lp/solutionpolishing` | `int` | [0,3] | 3 | True | LP solution polishing method (0: disabled, 1: only root, 2: always, 3: auto) |
| `lp/refactorinterval` | `int` | [0,2147483647] | 0 | True | LP refactorization interval (0: auto) |
| `lp/alwaysgetduals` | `bool` | {TRUE,FALSE} | FALSE | False | should the Farkas duals always be collected when an LP is found to be infeasible? |

## memory

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `memory/savefac` | `real` | [0,1] | 0.8 | False | fraction of maximal memory usage resulting in switch to memory saving mode |
| `memory/arraygrowfac` | `real` | [1,10] | 1.2 | True | memory growing factor for dynamically allocated arrays |
| `memory/arraygrowinit` | `int` | [0,2147483647] | 4 | True | initial size of dynamically allocated arrays |
| `memory/treegrowfac` | `real` | [1,10] | 2 | True | memory growing factor for tree array |
| `memory/treegrowinit` | `int` | [0,2147483647] | 65536 | True | initial size of tree array |
| `memory/pathgrowfac` | `real` | [1,10] | 2 | True | memory growing factor for path array |
| `memory/pathgrowinit` | `int` | [0,2147483647] | 256 | True | initial size of path array |

## misc

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `misc/catchctrlc` | `bool` | {TRUE,FALSE} | TRUE | False | should the CTRL-C interrupt be caught by SCIP? |
| `misc/usevartable` | `bool` | {TRUE,FALSE} | TRUE | False | should a hashtable be used to map from variable names to variables? |
| `misc/useconstable` | `bool` | {TRUE,FALSE} | TRUE | False | should a hashtable be used to map from constraint names to constraints? |
| `misc/usesmalltables` | `bool` | {TRUE,FALSE} | FALSE | False | should smaller hashtables be used? yields better performance for small problems with about 100 variables |
| `misc/resetstat` | `bool` | {TRUE,FALSE} | TRUE | False | should the statistics be reset if the transformed problem is freed (in case of a Benders' decomposition this parameter should be set to FALSE) |
| `misc/improvingsols` | `bool` | {TRUE,FALSE} | FALSE | False | should only solutions be checked which improve the primal bound |
| `misc/printreason` | `bool` | {TRUE,FALSE} | TRUE | False | should the reason be printed if a given start solution is infeasible |
| `misc/estimexternmem` | `bool` | {TRUE,FALSE} | TRUE | False | should the usage of external memory be estimated? |
| `misc/avoidmemout` | `bool` | {TRUE,FALSE} | TRUE | False | try to avoid running into memory limit by restricting plugins like heuristics? |
| `misc/transorigsols` | `bool` | {TRUE,FALSE} | TRUE | False | should SCIP try to transfer original solutions to the transformed space (after presolving)? |
| `misc/transsolsorig` | `bool` | {TRUE,FALSE} | TRUE | False | should SCIP try to transfer transformed solutions to the original space (after solving)? |
| `misc/calcintegral` | `bool` | {TRUE,FALSE} | TRUE | False | should SCIP calculate the primal dual integral value? |
| `misc/finitesolutionstore` | `bool` | {TRUE,FALSE} | FALSE | False | should SCIP try to remove infinite fixings from solutions copied to the solution store? |
| `misc/outputorigsol` | `bool` | {TRUE,FALSE} | TRUE | False | should the best solution be transformed to the orignal space and be output in command line run? |
| `misc/allowstrongdualreds` | `bool` | {TRUE,FALSE} | TRUE | False | should strong dual reductions be allowed in propagation and presolving? |
| `misc/allowweakdualreds` | `bool` | {TRUE,FALSE} | TRUE | False | should weak dual reductions be allowed in propagation and presolving? |
| `misc/scaleobj` | `bool` | {TRUE,FALSE} | TRUE | False | should the objective function be scaled so that it is always integer? |
| `misc/showdivingstats` | `bool` | {TRUE,FALSE} | FALSE | False | should detailed statistics for diving heuristics be shown? |
| `misc/referencevalue` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1e+99 | False | objective value for reference purposes |
| `misc/usesymmetry` | `int` | [0,7] | 7 | False | bitset describing used symmetry handling technique: (0: off; 1: constraint-based (orbitopes, symresacks); lexicographic and orbitopal reduction) if dynamic; 2: orbital reduction; 3: orbitopes and symresacks, and lexicographic/orbital reduction; 4: Schreier Sims cuts; 5: Schreier Sims cuts, orbitopes, symresacks, and/or lexicographic reduction; 6: Schreier Sims cuts, orbital reduction; 7: Schreier Sims cuts, orbitopes, symresacks, and/or lexicographic/orbital reduction;) See type_symmetry.h. |

## nlhdlr

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `nlhdlr/default/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | should this nonlinear handler be used |
| `nlhdlr/convex/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | should this nonlinear handler be used |
| `nlhdlr/convex/detectsum` | `bool` | {TRUE,FALSE} | FALSE | False | whether to run convexity detection when the root of an expression is a non-quadratic sum |
| `nlhdlr/convex/extendedform` | `bool` | {TRUE,FALSE} | TRUE | False | whether to create extended formulations instead of looking for maximal convex expressions |
| `nlhdlr/convex/maxperturb` | `real` | [0,1] | 0.01 | False | maximal relative perturbation of non-differentiable reference point |
| `nlhdlr/convex/cvxquadratic` | `bool` | {TRUE,FALSE} | TRUE | True | whether to use convexity check on quadratics |
| `nlhdlr/convex/cvxsignomial` | `bool` | {TRUE,FALSE} | TRUE | True | whether to use convexity check on signomials |
| `nlhdlr/convex/cvxprodcomp` | `bool` | {TRUE,FALSE} | TRUE | True | whether to use convexity check on product composition f(h)*h |
| `nlhdlr/convex/handletrivial` | `bool` | {TRUE,FALSE} | FALSE | True | whether to also handle trivial convex expressions |
| `nlhdlr/concave/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | should this nonlinear handler be used |
| `nlhdlr/concave/detectsum` | `bool` | {TRUE,FALSE} | FALSE | False | whether to run convexity detection when the root of an expression is a sum |
| `nlhdlr/concave/cvxquadratic` | `bool` | {TRUE,FALSE} | FALSE | True | whether to use convexity check on quadratics |
| `nlhdlr/concave/cvxsignomial` | `bool` | {TRUE,FALSE} | TRUE | True | whether to use convexity check on signomials |
| `nlhdlr/concave/cvxprodcomp` | `bool` | {TRUE,FALSE} | TRUE | True | whether to use convexity check on product composition f(h)*h |
| `nlhdlr/concave/handletrivial` | `bool` | {TRUE,FALSE} | FALSE | True | whether to also handle trivial convex expressions |
| `nlhdlr/bilinear/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | should this nonlinear handler be used |
| `nlhdlr/bilinear/useinteval` | `bool` | {TRUE,FALSE} | TRUE | False | whether to use the interval evaluation callback of the nlhdlr |
| `nlhdlr/bilinear/usereverseprop` | `bool` | {TRUE,FALSE} | TRUE | False | whether to use the reverse propagation callback of the nlhdlr |
| `nlhdlr/bilinear/maxseparoundsroot` | `int` | [0,2147483647] | 10 | False | maximum number of separation rounds in the root node |
| `nlhdlr/bilinear/maxseparounds` | `int` | [0,2147483647] | 1 | False | maximum number of separation rounds in a local node |
| `nlhdlr/bilinear/maxsepadepth` | `int` | [0,2147483647] | 2147483647 | False | maximum depth to apply separation |
| `nlhdlr/perspective/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | should this nonlinear handler be used |
| `nlhdlr/perspective/maxproprounds` | `int` | [-1,2147483647] | 1 | False | maximal number of propagation rounds in probing |
| `nlhdlr/perspective/mindomreduction` | `real` | [0,1] | 0.1 | False | minimal relative reduction in a variable's domain for applying probing |
| `nlhdlr/perspective/minviolprobing` | `real` | [0,1.79769313486232e+308] | 1e-05 | False | minimal violation w.r.t. auxiliary variables for applying probing |
| `nlhdlr/perspective/probingonlyinsepa` | `bool` | {TRUE,FALSE} | TRUE | False | whether to do probing only in separation |
| `nlhdlr/perspective/probingfreq` | `int` | [-1,2147483647] | 1 | False | probing frequency (-1 - no probing, 0 - root node only) |
| `nlhdlr/perspective/convexonly` | `bool` | {TRUE,FALSE} | FALSE | False | whether perspective cuts are added only for convex expressions |
| `nlhdlr/perspective/tightenbounds` | `bool` | {TRUE,FALSE} | TRUE | False | whether variable semicontinuity is used to tighten variable bounds |
| `nlhdlr/perspective/adjrefpoint` | `bool` | {TRUE,FALSE} | TRUE | False | whether to adjust the reference point |
| `nlhdlr/quadratic/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | should this nonlinear handler be used |
| `nlhdlr/quadratic/useintersectioncuts` | `bool` | {TRUE,FALSE} | FALSE | False | whether to use intersection cuts for quadratic constraints to separate |
| `nlhdlr/quadratic/usestrengthening` | `bool` | {TRUE,FALSE} | FALSE | False | whether the strengthening should be used |
| `nlhdlr/quadratic/usemonoidal` | `bool` | {TRUE,FALSE} | TRUE | False | whether monoidal strengthening should be used |
| `nlhdlr/quadratic/useminrep` | `bool` | {TRUE,FALSE} | TRUE | False | whether the minimal representation of the S-free set should be used (instead of the gauge) |
| `nlhdlr/quadratic/useboundsasrays` | `bool` | {TRUE,FALSE} | FALSE | False | use bounds of variables in quadratic as rays for intersection cuts |
| `nlhdlr/quadratic/ncutslimit` | `int` | [0,2147483647] | 2 | False | limit for number of cuts generated consecutively |
| `nlhdlr/quadratic/ncutslimitroot` | `int` | [0,2147483647] | 20 | False | limit for number of cuts generated at root node |
| `nlhdlr/quadratic/maxrank` | `int` | [0,2147483647] | 2147483647 | False | maximal rank a slackvar can have |
| `nlhdlr/quadratic/mincutviolation` | `real` | [0,1e+20] | 0.0001 | False | minimal cut violation the generated cuts must fulfill to be added to the LP |
| `nlhdlr/quadratic/minviolation` | `real` | [0,1e+20] | 0.0001 | False | minimal violation the constraint must fulfill such that a cut is generated |
| `nlhdlr/quadratic/atwhichnodes` | `int` | [-1,2147483647] | 1 | False | determines at which nodes cut is used (if it's -1, it's used only at the root node, if it's n &gt;= 0, it's used at every multiple of n |
| `nlhdlr/quadratic/nstrengthlimit` | `int` | [0,2147483647] | 2147483647 | False | limit for number of rays we do the strengthening for |
| `nlhdlr/quadratic/sparsifycuts` | `bool` | {TRUE,FALSE} | FALSE | False | should we try to sparisfy the intersection cut? |
| `nlhdlr/quadratic/ignorebadrayrestriction` | `bool` | {TRUE,FALSE} | TRUE | False | should cut be generated even with bad numerics when restricting to ray? |
| `nlhdlr/quadratic/ignorenhighre` | `bool` | {TRUE,FALSE} | TRUE | False | should cut be added even when range / efficacy is large? |
| `nlhdlr/quadratic/trackmore` | `bool` | {TRUE,FALSE} | FALSE | False | for monoidal strengthening, should we track more statistics (more expensive)? |
| `nlhdlr/quotient/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | should this nonlinear handler be used |
| `nlhdlr/signomial/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | should this nonlinear handler be used |
| `nlhdlr/signomial/maxnundervars` | `int` | [2,14] | 14 | True | maximum number of variables when underestimating a concave power function |
| `nlhdlr/signomial/mincutscale` | `real` | [1e-06,1000000] | 1e-05 | True | minimum scale factor when scaling a cut |
| `nlhdlr/soc/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | should this nonlinear handler be used |
| `nlhdlr/soc/mincutefficacy` | `real` | [0,1e+20] | 1e-05 | False | Minimum efficacy which a cut needs in order to be added. |
| `nlhdlr/soc/compeigenvalues` | `bool` | {TRUE,FALSE} | TRUE | False | Should Eigenvalue computations be done to detect complex cases in quadratic constraints? |

## nlp

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `nlp/solver` | `string` | String; interpretation stated in description | "" | False | solver to use for solving NLPs; leave empty to select NLPI with highest priority |
| `nlp/disable` | `bool` | {TRUE,FALSE} | FALSE | False | should the NLP relaxation be always disabled (also for NLPs/MINLPs)? |

## nlpi

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `nlpi/ipopt/priority` | `int` | [-536870912,536870911] | 1000 | False | priority of NLPI &lt;ipopt&gt; |
| `nlpi/ipopt/optfile` | `string` | String; interpretation stated in description | "" | False | name of Ipopt options file |
| `nlpi/ipopt/warm_start_push` | `real` | [0,1] | 1e-09 | False | amount (relative and absolute) by which starting point is moved away from bounds in warmstarts |
| `nlpi/ipopt/linear_solver` | `string` | String; interpretation stated in description | "" | False | Linear solver used for step computations. Valid values if not empty: ma27 ma57 ma77 ma86 ma97 pardiso pardisomkl mumps custom |
| `nlpi/ipopt/hsllib` | `string` | String; interpretation stated in description | "" | False | Name of library containing HSL routines for load at runtime |
| `nlpi/ipopt/pardisolib` | `string` | String; interpretation stated in description | "" | False | Name of library containing Pardiso routines (from pardiso-project.org) for load at runtime |
| `nlpi/ipopt/linear_system_scaling` | `string` | String; interpretation stated in description | "" | False | Method for scaling the linear system. Valid values if not empty: none mc19 slack-based |
| `nlpi/ipopt/nlp_scaling_method` | `string` | String; interpretation stated in description | "" | False | Select the technique used for scaling the NLP. Valid values if not empty: none user-scaling gradient-based equilibration-based |
| `nlpi/ipopt/mu_strategy` | `string` | String; interpretation stated in description | "" | False | Update strategy for barrier parameter. Valid values if not empty: monotone adaptive |
| `nlpi/ipopt/hessian_approximation` | `string` | String; interpretation stated in description | "" | False | Indicates what Hessian information is to be used. Valid values if not empty: exact limited-memory |
| `nlpi/ipopt/print_level` | `int` | [-1,12] | -1 | False | Output verbosity level. -1 to use NLPI or Ipopt default. |

## nodeselection

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `nodeselection/childsel` | `char` | {dupilrh} | h | False | child selection rule ('d'own, 'u'p, 'p'seudo costs, 'i'nference, 'l'p value, 'r'oot LP value difference, 'h'ybrid inference/root LP value difference) |
| `nodeselection/estimate/stdpriority` | `int` | [-536870912,1073741823] | 200000 | False | priority of node selection rule &lt;estimate&gt; in standard mode |
| `nodeselection/estimate/memsavepriority` | `int` | [-536870912,536870911] | 100 | True | priority of node selection rule &lt;estimate&gt; in memory saving mode |
| `nodeselection/estimate/minplungedepth` | `int` | [-1,2147483647] | -1 | True | minimal plunging depth, before new best node may be selected (-1 for dynamic setting) |
| `nodeselection/estimate/maxplungedepth` | `int` | [-1,2147483647] | -1 | True | maximal plunging depth, before new best node is forced to be selected (-1 for dynamic setting) |
| `nodeselection/estimate/maxplungequot` | `real` | [0,1.79769313486232e+308] | 0.25 | True | maximal quotient (estimate - lowerbound)/(cutoffbound - lowerbound) where plunging is performed |
| `nodeselection/estimate/bestnodefreq` | `int` | [0,2147483647] | 10 | False | frequency at which the best node instead of the best estimate is selected (0: never) |
| `nodeselection/estimate/breadthfirstdepth` | `int` | [-1,2147483647] | -1 | False | depth until breadth-first search is applied |
| `nodeselection/estimate/plungeoffset` | `int` | [0,2147483647] | 0 | False | number of nodes before doing plunging the first time |
| `nodeselection/bfs/stdpriority` | `int` | [-536870912,1073741823] | 100000 | False | priority of node selection rule &lt;bfs&gt; in standard mode |
| `nodeselection/bfs/memsavepriority` | `int` | [-536870912,536870911] | 0 | True | priority of node selection rule &lt;bfs&gt; in memory saving mode |
| `nodeselection/bfs/minplungedepth` | `int` | [-1,2147483647] | -1 | True | minimal plunging depth, before new best node may be selected (-1 for dynamic setting) |
| `nodeselection/bfs/maxplungedepth` | `int` | [-1,2147483647] | -1 | True | maximal plunging depth, before new best node is forced to be selected (-1 for dynamic setting) |
| `nodeselection/bfs/maxplungequot` | `real` | [0,1.79769313486232e+308] | 0.25 | True | maximal quotient (curlowerbound - lowerbound)/(cutoffbound - lowerbound) where plunging is performed |
| `nodeselection/hybridestim/stdpriority` | `int` | [-536870912,1073741823] | 50000 | False | priority of node selection rule &lt;hybridestim&gt; in standard mode |
| `nodeselection/hybridestim/memsavepriority` | `int` | [-536870912,536870911] | 50 | True | priority of node selection rule &lt;hybridestim&gt; in memory saving mode |
| `nodeselection/hybridestim/minplungedepth` | `int` | [-1,2147483647] | -1 | True | minimal plunging depth, before new best node may be selected (-1 for dynamic setting) |
| `nodeselection/hybridestim/maxplungedepth` | `int` | [-1,2147483647] | -1 | True | maximal plunging depth, before new best node is forced to be selected (-1 for dynamic setting) |
| `nodeselection/hybridestim/maxplungequot` | `real` | [0,1.79769313486232e+308] | 0.25 | True | maximal quotient (estimate - lowerbound)/(cutoffbound - lowerbound) where plunging is performed |
| `nodeselection/hybridestim/bestnodefreq` | `int` | [0,2147483647] | 1000 | False | frequency at which the best node instead of the hybrid best estimate / best bound is selected (0: never) |
| `nodeselection/hybridestim/estimweight` | `real` | [0,1] | 0.1 | True | weight of estimate value in node selection score (0: pure best bound search, 1: pure best estimate search) |
| `nodeselection/restartdfs/stdpriority` | `int` | [-536870912,1073741823] | 10000 | False | priority of node selection rule &lt;restartdfs&gt; in standard mode |
| `nodeselection/restartdfs/memsavepriority` | `int` | [-536870912,536870911] | 50000 | True | priority of node selection rule &lt;restartdfs&gt; in memory saving mode |
| `nodeselection/restartdfs/selectbestfreq` | `int` | [0,2147483647] | 100 | False | frequency for selecting the best node instead of the deepest one |
| `nodeselection/restartdfs/countonlyleaves` | `bool` | {TRUE,FALSE} | TRUE | False | count only leaf nodes (otherwise all nodes)? |
| `nodeselection/uct/stdpriority` | `int` | [-536870912,1073741823] | 10 | False | priority of node selection rule &lt;uct&gt; in standard mode |
| `nodeselection/uct/memsavepriority` | `int` | [-536870912,536870911] | 0 | True | priority of node selection rule &lt;uct&gt; in memory saving mode |
| `nodeselection/uct/nodelimit` | `int` | [0,1000000] | 31 | True | maximum number of nodes before switching to default rule |
| `nodeselection/uct/weight` | `real` | [0,1] | 0.1 | True | weight for visit quotient of node selection rule |
| `nodeselection/uct/useestimate` | `bool` | {TRUE,FALSE} | FALSE | True | should the estimate (TRUE) or lower bound of a node be used for UCT score? |
| `nodeselection/dfs/stdpriority` | `int` | [-536870912,1073741823] | 0 | False | priority of node selection rule &lt;dfs&gt; in standard mode |
| `nodeselection/dfs/memsavepriority` | `int` | [-536870912,536870911] | 100000 | True | priority of node selection rule &lt;dfs&gt; in memory saving mode |
| `nodeselection/breadthfirst/stdpriority` | `int` | [-536870912,1073741823] | -10000 | False | priority of node selection rule &lt;breadthfirst&gt; in standard mode |
| `nodeselection/breadthfirst/memsavepriority` | `int` | [-536870912,536870911] | -1000000 | True | priority of node selection rule &lt;breadthfirst&gt; in memory saving mode |

## numerics

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `numerics/infinity` | `real` | [10000000000,1e+98] | 1e+20 | False | values larger than this are considered infinity |
| `numerics/epsilon` | `real` | [1e-20,0.001] | 1e-09 | False | absolute values smaller than this are considered zero |
| `numerics/sumepsilon` | `real` | [1e-17,0.001] | 1e-06 | False | absolute values of sums smaller than this are considered zero |
| `numerics/feastol` | `real` | [1e-17,0.001] | 1e-06 | False | feasibility tolerance for constraints |
| `numerics/checkfeastolfac` | `real` | [0,1.79769313486232e+308] | 1 | False | feasibility tolerance factor; for checking the feasibility of the best solution |
| `numerics/lpfeastolfactor` | `real` | [1e-06,1] | 1 | False | factor w.r.t. primal feasibility tolerance that determines default (and maximal) primal feasibility tolerance of LP solver |
| `numerics/dualfeastol` | `real` | [1e-17,0.001] | 1e-07 | False | feasibility tolerance for reduced costs in LP solution |
| `numerics/barrierconvtol` | `real` | [1e-17,0.001] | 1e-10 | True | LP convergence tolerance used in barrier algorithm |
| `numerics/boundstreps` | `real` | [1e-17,1e+98] | 0.05 | True | minimal relative improve for strengthening bounds |
| `numerics/pseudocosteps` | `real` | [1e-17,1] | 0.1 | True | minimal variable distance value to use for branching pseudo cost updates |
| `numerics/pseudocostdelta` | `real` | [0,1.79769313486232e+308] | 0.0001 | True | minimal objective distance value to use for branching pseudo cost updates |
| `numerics/recomputefac` | `real` | [0,1.79769313486232e+308] | 1000000 | True | minimal decrease factor that causes the recomputation of a value (e.g., pseudo objective) instead of an update |
| `numerics/hugeval` | `real` | [0,1e+98] | 1e+15 | True | values larger than this are considered huge and should be handled separately (e.g., in activity computation) |

## parallel

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `parallel/mode` | `int` | [0,1] | 1 | False | parallel optimisation mode, 0: opportunistic or 1: deterministic. |
| `parallel/minnthreads` | `int` | [0,64] | 1 | False | the minimum number of threads used during parallel solve |
| `parallel/maxnthreads` | `int` | [0,64] | 8 | False | the maximum number of threads used during parallel solve |

## presolving

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `presolving/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds (-1: unlimited, 0: off) |
| `presolving/abortfac` | `real` | [0,1] | 0.0008 | True | abort presolve, if at most this fraction of the problem was changed in last presolve round |
| `presolving/maxrestarts` | `int` | [-1,2147483647] | -1 | False | maximal number of restarts (-1: unlimited) |
| `presolving/restartfac` | `real` | [0,1] | 0.025 | True | fraction of integer variables that were fixed in the root node triggering a restart with preprocessing after root node evaluation |
| `presolving/clqtablefac` | `real` | [0,1.79769313486232e+308] | 2 | True | limit on number of entries in clique table relative to number of problem nonzeros |
| `presolving/immrestartfac` | `real` | [0,1] | 0.05 | True | fraction of integer variables that were fixed in the root node triggering an immediate restart with preprocessing |
| `presolving/subrestartfac` | `real` | [0,1] | 1 | True | fraction of integer variables that were globally fixed during the solving process triggering a restart with preprocessing |
| `presolving/restartminred` | `real` | [0,1] | 0.05 | True | minimal fraction of integer variables removed after restart to allow for an additional restart |
| `presolving/donotmultaggr` | `bool` | {TRUE,FALSE} | FALSE | True | should multi-aggregation of variables be forbidden? |
| `presolving/donotaggr` | `bool` | {TRUE,FALSE} | FALSE | True | should aggregation of variables be forbidden? |
| `presolving/trivial/priority` | `int` | [-536870912,536870911] | 9000000 | True | priority of presolver &lt;trivial&gt; |
| `presolving/trivial/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/trivial/timing` | `int` | [4,60] | 4 | True | timing mask of presolver &lt;trivial&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/boundshift/priority` | `int` | [-536870912,536870911] | 7900000 | True | priority of presolver &lt;boundshift&gt; |
| `presolving/boundshift/maxrounds` | `int` | [-1,2147483647] | 0 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/boundshift/timing` | `int` | [4,60] | 4 | True | timing mask of presolver &lt;boundshift&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/boundshift/maxshift` | `longint` | [0,9223372036854775807] | 9223372036854775807 | True | absolute value of maximum shift |
| `presolving/boundshift/flipping` | `bool` | {TRUE,FALSE} | TRUE | True | is flipping allowed (multiplying with -1)? |
| `presolving/boundshift/integer` | `bool` | {TRUE,FALSE} | TRUE | True | shift only integer ranges? |
| `presolving/inttobinary/priority` | `int` | [-536870912,536870911] | 7000000 | True | priority of presolver &lt;inttobinary&gt; |
| `presolving/inttobinary/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/inttobinary/timing` | `int` | [4,60] | 4 | True | timing mask of presolver &lt;inttobinary&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/convertinttobin/priority` | `int` | [-536870912,536870911] | 6000000 | True | priority of presolver &lt;convertinttobin&gt; |
| `presolving/convertinttobin/maxrounds` | `int` | [-1,2147483647] | 0 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/convertinttobin/timing` | `int` | [4,60] | 4 | True | timing mask of presolver &lt;convertinttobin&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/convertinttobin/maxdomainsize` | `longint` | [0,9223372036854775807] | 9223372036854775807 | True | absolute value of maximum domain size for converting an integer variable to binaries variables |
| `presolving/convertinttobin/onlypoweroftwo` | `bool` | {TRUE,FALSE} | FALSE | True | should only integer variables with a domain size of 2^p - 1 be converted(, there we don't need an knapsack-constraint for restricting the sum of the binaries) |
| `presolving/convertinttobin/samelocksinbothdirections` | `bool` | {TRUE,FALSE} | FALSE | True | should only integer variables with uplocks equals downlocks be converted |
| `presolving/gateextraction/priority` | `int` | [-536870912,536870911] | 1000000 | True | priority of presolver &lt;gateextraction&gt; |
| `presolving/gateextraction/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/gateextraction/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;gateextraction&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/gateextraction/onlysetpart` | `bool` | {TRUE,FALSE} | FALSE | True | should we only try to extract set-partitioning constraints and no and-constraints |
| `presolving/gateextraction/searchequations` | `bool` | {TRUE,FALSE} | TRUE | True | should we try to extract set-partitioning constraint out of one logicor and one corresponding set-packing constraint |
| `presolving/gateextraction/sorting` | `int` | [-1,1] | 1 | True | order logicor contraints to extract big-gates before smaller ones (-1), do not order them (0) or order them to extract smaller gates at first (1) |
| `presolving/implint/priority` | `int` | [-536870912,536870911] | -900000 | True | priority of presolver &lt;implint&gt; |
| `presolving/implint/maxrounds` | `int` | [-1,2147483647] | 0 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/implint/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;implint&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/implint/convertintegers` | `bool` | {TRUE,FALSE} | FALSE | False | should implied integrality also be detected for enforced integral variables? |
| `presolving/implint/columnrowratio` | `real` | [0,1e+98] | 50 | True | use the network row addition algorithm when the column to row ratio becomes larger than this threshold |
| `presolving/implint/numericslimit` | `real` | [1,1e+98] | 100000000 | True | a row that contains variables with coefficients that are greater in absolute value than this limit is not considered for implied integrality detection |
| `presolving/qpkktref/priority` | `int` | [-536870912,536870911] | -1 | True | priority of presolver &lt;qpkktref&gt; |
| `presolving/qpkktref/maxrounds` | `int` | [-1,2147483647] | 0 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/qpkktref/timing` | `int` | [4,60] | 8 | True | timing mask of presolver &lt;qpkktref&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/qpkktref/addkktbinary` | `bool` | {TRUE,FALSE} | FALSE | True | if TRUE then allow binary variables for KKT update |
| `presolving/qpkktref/updatequadbounded` | `bool` | {TRUE,FALSE} | TRUE | True | if TRUE then only apply the update to QPs with bounded variables; if the variables are not bounded then a finite optimal solution might not exist and the KKT conditions would then be invalid |
| `presolving/qpkktref/updatequadindef` | `bool` | {TRUE,FALSE} | FALSE | True | if TRUE then apply quadratic constraint update even if the quadratic constraint matrix is known to be indefinite |
| `presolving/dualcomp/priority` | `int` | [-536870912,536870911] | -50 | True | priority of presolver &lt;dualcomp&gt; |
| `presolving/dualcomp/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/dualcomp/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;dualcomp&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/dualcomp/componlydisvars` | `bool` | {TRUE,FALSE} | FALSE | False | should only discrete variables be compensated? |
| `presolving/stuffing/priority` | `int` | [-536870912,536870911] | -100 | True | priority of presolver &lt;stuffing&gt; |
| `presolving/stuffing/maxrounds` | `int` | [-1,2147483647] | 0 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/stuffing/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;stuffing&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/domcol/priority` | `int` | [-536870912,536870911] | -1000 | True | priority of presolver &lt;domcol&gt; |
| `presolving/domcol/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/domcol/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;domcol&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/domcol/numminpairs` | `int` | [100,1048576] | 1024 | False | minimal number of pair comparisons |
| `presolving/domcol/nummaxpairs` | `int` | [1024,1000000000] | 1048576 | False | maximal number of pair comparisons |
| `presolving/domcol/predbndstr` | `bool` | {TRUE,FALSE} | FALSE | False | should predictive bound strengthening be applied? |
| `presolving/domcol/continuousred` | `bool` | {TRUE,FALSE} | TRUE | False | should reductions for continuous variables be performed? |
| `presolving/tworowbnd/priority` | `int` | [-536870912,536870911] | -2000 | True | priority of presolver &lt;tworowbnd&gt; |
| `presolving/tworowbnd/maxrounds` | `int` | [-1,2147483647] | 0 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/tworowbnd/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;tworowbnd&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/tworowbnd/enablecopy` | `bool` | {TRUE,FALSE} | TRUE | True | should tworowbnd presolver be copied to sub-SCIPs? |
| `presolving/tworowbnd/maxconsiderednonzeros` | `int` | [-1,2147483647] | 100 | False | maximal number of considered non-zeros within one row (-1: no limit) |
| `presolving/tworowbnd/maxretrievefails` | `int` | [-1,2147483647] | 1000 | False | maximal number of consecutive useless hashtable retrieves |
| `presolving/tworowbnd/maxcombinefails` | `int` | [-1,2147483647] | 1000 | False | maximal number of consecutive useless row combines |
| `presolving/tworowbnd/maxhashfac` | `int` | [-1,2147483647] | 10 | False | Maximum number of hashlist entries as multiple of number of rows in the problem (-1: no limit) |
| `presolving/tworowbnd/maxpairfac` | `int` | [-1,2147483647] | 1 | False | Maximum number of processed row pairs as multiple of the number of rows in the problem (-1: no limit) |
| `presolving/dualinfer/priority` | `int` | [-536870912,536870911] | -3000 | True | priority of presolver &lt;dualinfer&gt; |
| `presolving/dualinfer/maxrounds` | `int` | [-1,2147483647] | 0 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/dualinfer/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;dualinfer&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/dualinfer/twocolcombine` | `bool` | {TRUE,FALSE} | TRUE | False | use convex combination of columns for determining dual bounds |
| `presolving/dualinfer/maxdualbndloops` | `int` | [-1,2147483647] | 12 | False | maximal number of dual bound strengthening loops |
| `presolving/dualinfer/maxconsiderednonzeros` | `int` | [-1,2147483647] | 100 | True | maximal number of considered non-zeros within one column (-1: no limit) |
| `presolving/dualinfer/maxretrievefails` | `int` | [-1,2147483647] | 1000 | True | maximal number of consecutive useless hashtable retrieves |
| `presolving/dualinfer/maxcombinefails` | `int` | [-1,2147483647] | 1000 | True | maximal number of consecutive useless column combines |
| `presolving/dualinfer/maxhashfac` | `int` | [-1,2147483647] | 10 | True | Maximum number of hashlist entries as multiple of number of columns in the problem (-1: no limit) |
| `presolving/dualinfer/maxpairfac` | `int` | [-1,2147483647] | 1 | True | Maximum number of processed column pairs as multiple of the number of columns in the problem (-1: no limit) |
| `presolving/dualinfer/maxrowsupport` | `int` | [2,2147483647] | 3 | False | Maximum number of row's non-zeros for changing inequality to equality |
| `presolving/implics/priority` | `int` | [-536870912,536870911] | -10000 | True | priority of presolver &lt;implics&gt; |
| `presolving/implics/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/implics/timing` | `int` | [4,60] | 8 | True | timing mask of presolver &lt;implics&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/dualagg/priority` | `int` | [-536870912,536870911] | -12000 | True | priority of presolver &lt;dualagg&gt; |
| `presolving/dualagg/maxrounds` | `int` | [-1,2147483647] | 0 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/dualagg/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;dualagg&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/sparsify/priority` | `int` | [-536870912,536870911] | -24000 | True | priority of presolver &lt;sparsify&gt; |
| `presolving/sparsify/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/sparsify/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;sparsify&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/sparsify/enablecopy` | `bool` | {TRUE,FALSE} | TRUE | True | should sparsify presolver be copied to sub-SCIPs? |
| `presolving/sparsify/cancellinear` | `bool` | {TRUE,FALSE} | TRUE | True | should we cancel nonzeros in constraints of the linear constraint handler? |
| `presolving/sparsify/preserveintcoefs` | `bool` | {TRUE,FALSE} | TRUE | True | should we forbid cancellations that destroy integer coefficients? |
| `presolving/sparsify/maxcontfillin` | `int` | [-1,2147483647] | 0 | False | maximal fillin for continuous variables (-1: unlimited) |
| `presolving/sparsify/maxbinfillin` | `int` | [-1,2147483647] | 0 | False | maximal fillin for binary variables (-1: unlimited) |
| `presolving/sparsify/maxintfillin` | `int` | [-1,2147483647] | 0 | False | maximal fillin for integer variables including binaries (-1: unlimited) |
| `presolving/sparsify/maxnonzeros` | `int` | [-1,2147483647] | -1 | True | maximal support of one equality to be used for cancelling (-1: no limit) |
| `presolving/sparsify/maxconsiderednonzeros` | `int` | [-1,2147483647] | 70 | True | maximal number of considered non-zeros within one row (-1: no limit) |
| `presolving/sparsify/rowsort` | `char` | {nid} | d | True | order in which to process inequalities ('n'o sorting, 'i'ncreasing nonzeros, 'd'ecreasing nonzeros) |
| `presolving/sparsify/maxretrievefac` | `real` | [0,1.79769313486232e+308] | 100 | True | limit on the number of useless vs. useful hashtable retrieves as a multiple of the number of constraints |
| `presolving/sparsify/waitingfac` | `real` | [0,1.79769313486232e+308] | 2 | True | number of calls to wait until next execution as a multiple of the number of useless calls |
| `presolving/dualsparsify/priority` | `int` | [-536870912,536870911] | -240000 | True | priority of presolver &lt;dualsparsify&gt; |
| `presolving/dualsparsify/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/dualsparsify/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;dualsparsify&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `presolving/dualsparsify/enablecopy` | `bool` | {TRUE,FALSE} | TRUE | True | should dualsparsify presolver be copied to sub-SCIPs? |
| `presolving/dualsparsify/preserveintcoefs` | `bool` | {TRUE,FALSE} | FALSE | True | should we forbid cancellations that destroy integer coefficients? |
| `presolving/dualsparsify/preservegoodlocks` | `bool` | {TRUE,FALSE} | FALSE | True | should we preserve good locked properties of variables (at most one lock in one direction)? |
| `presolving/dualsparsify/maxcontfillin` | `int` | [-1,2147483647] | 1 | False | maximal fillin for continuous variables (-1: unlimited) |
| `presolving/dualsparsify/maxbinfillin` | `int` | [-1,2147483647] | 1 | False | maximal fillin for binary variables (-1: unlimited) |
| `presolving/dualsparsify/maxintfillin` | `int` | [-1,2147483647] | 1 | False | maximal fillin for integer variables including binaries (-1: unlimited) |
| `presolving/dualsparsify/maxconsiderednonzeros` | `int` | [-1,2147483647] | 70 | True | maximal number of considered nonzeros within one column (-1: no limit) |
| `presolving/dualsparsify/mineliminatednonzeros` | `int` | [0,2147483647] | 100 | False | minimal eliminated nonzeros within one column if we need to add a constraint to the problem |
| `presolving/dualsparsify/maxretrievefac` | `real` | [0,1.79769313486232e+308] | 100 | True | limit on the number of useless vs. useful hashtable retrieves as a multiple of the number of constraints |
| `presolving/dualsparsify/waitingfac` | `real` | [0,1.79769313486232e+308] | 2 | True | number of calls to wait until next execution as a multiple of the number of useless calls |
| `presolving/redvub/priority` | `int` | [-536870912,536870911] | -9000000 | True | priority of presolver &lt;redvub&gt; |
| `presolving/redvub/maxrounds` | `int` | [-1,2147483647] | 0 | False | maximal number of presolving rounds the presolver participates in (-1: no limit) |
| `presolving/redvub/timing` | `int` | [4,60] | 16 | True | timing mask of presolver &lt;redvub&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |

## pricing

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `pricing/maxvars` | `int` | [1,2147483647] | 100 | False | maximal number of variables priced in per pricing round |
| `pricing/maxvarsroot` | `int` | [1,2147483647] | 2000 | False | maximal number of priced variables at the root node |
| `pricing/abortfac` | `real` | [1,1.79769313486232e+308] | 2 | False | pricing is aborted, if fac * pricing/maxvars pricing candidates were found |
| `pricing/delvars` | `bool` | {TRUE,FALSE} | FALSE | False | should variables created at the current node be deleted when the node is solved in case they are not present in the LP anymore? |
| `pricing/delvarsroot` | `bool` | {TRUE,FALSE} | FALSE | False | should variables created at the root node be deleted when the root is solved in case they are not present in the LP anymore? |

## propagating

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `propagating/maxrounds` | `int` | [-1,2147483647] | 100 | False | maximal number of propagation rounds per node (-1: unlimited) |
| `propagating/maxroundsroot` | `int` | [-1,2147483647] | 1000 | False | maximal number of propagation rounds in the root node (-1: unlimited) |
| `propagating/abortoncutoff` | `bool` | {TRUE,FALSE} | TRUE | False | should propagation be aborted immediately? setting this to FALSE could help conflict analysis to produce more conflict constraints |
| `propagating/rootredcost/priority` | `int` | [-536870912,536870911] | 10000000 | True | priority of propagator &lt;rootredcost&gt; |
| `propagating/rootredcost/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling propagator &lt;rootredcost&gt; (-1: never, 0: only in root node) |
| `propagating/rootredcost/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/rootredcost/timingmask` | `int` | [0,15] | 5 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/rootredcost/presolpriority` | `int` | [-536870912,536870911] | 0 | True | presolving priority of propagator &lt;rootredcost&gt; |
| `propagating/rootredcost/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/rootredcost/presoltiming` | `int` | [2,60] | 28 | True | timing mask of the presolving method of propagator &lt;rootredcost&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/rootredcost/onlybinary` | `bool` | {TRUE,FALSE} | FALSE | True | should only binary variables be propagated? |
| `propagating/rootredcost/force` | `bool` | {TRUE,FALSE} | FALSE | True | should the propagator be forced even if active pricer are present? |
| `propagating/dualfix/priority` | `int` | [-536870912,536870911] | 8000000 | True | priority of propagator &lt;dualfix&gt; |
| `propagating/dualfix/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling propagator &lt;dualfix&gt; (-1: never, 0: only in root node) |
| `propagating/dualfix/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/dualfix/timingmask` | `int` | [0,15] | 1 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/dualfix/presolpriority` | `int` | [-536870912,536870911] | 8000000 | True | presolving priority of propagator &lt;dualfix&gt; |
| `propagating/dualfix/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/dualfix/presoltiming` | `int` | [2,60] | 4 | True | timing mask of the presolving method of propagator &lt;dualfix&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/genvbounds/priority` | `int` | [-536870912,536870911] | 3000000 | True | priority of propagator &lt;genvbounds&gt; |
| `propagating/genvbounds/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling propagator &lt;genvbounds&gt; (-1: never, 0: only in root node) |
| `propagating/genvbounds/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/genvbounds/timingmask` | `int` | [0,15] | 15 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/genvbounds/presolpriority` | `int` | [-536870912,536870911] | -2000000 | True | presolving priority of propagator &lt;genvbounds&gt; |
| `propagating/genvbounds/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/genvbounds/presoltiming` | `int` | [2,60] | 4 | True | timing mask of the presolving method of propagator &lt;genvbounds&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/genvbounds/global` | `bool` | {TRUE,FALSE} | TRUE | True | apply global propagation? |
| `propagating/genvbounds/propinrootnode` | `bool` | {TRUE,FALSE} | TRUE | True | apply genvbounds in root node if no new incumbent was found? |
| `propagating/genvbounds/sort` | `bool` | {TRUE,FALSE} | TRUE | True | sort genvbounds and wait for bound change events? |
| `propagating/genvbounds/propasconss` | `bool` | {TRUE,FALSE} | FALSE | True | should genvbounds be transformed to (linear) constraints? |
| `propagating/vbounds/priority` | `int` | [-536870912,536870911] | 3000000 | True | priority of propagator &lt;vbounds&gt; |
| `propagating/vbounds/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling propagator &lt;vbounds&gt; (-1: never, 0: only in root node) |
| `propagating/vbounds/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/vbounds/timingmask` | `int` | [0,15] | 5 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/vbounds/presolpriority` | `int` | [-536870912,536870911] | -90000 | True | presolving priority of propagator &lt;vbounds&gt; |
| `propagating/vbounds/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/vbounds/presoltiming` | `int` | [2,60] | 24 | True | timing mask of the presolving method of propagator &lt;vbounds&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/vbounds/usebdwidening` | `bool` | {TRUE,FALSE} | TRUE | False | should bound widening be used to initialize conflict analysis? |
| `propagating/vbounds/useimplics` | `bool` | {TRUE,FALSE} | FALSE | True | should implications be propagated? |
| `propagating/vbounds/usecliques` | `bool` | {TRUE,FALSE} | FALSE | True | should cliques be propagated? |
| `propagating/vbounds/usevbounds` | `bool` | {TRUE,FALSE} | TRUE | True | should vbounds be propagated? |
| `propagating/vbounds/dotoposort` | `bool` | {TRUE,FALSE} | TRUE | False | should the bounds be topologically sorted in advance? |
| `propagating/vbounds/sortcliques` | `bool` | {TRUE,FALSE} | FALSE | True | should cliques be regarded for the topological sort? |
| `propagating/vbounds/detectcycles` | `bool` | {TRUE,FALSE} | FALSE | False | should cycles in the variable bound graph be identified? |
| `propagating/vbounds/minnewcliques` | `real` | [0,1] | 0.1 | False | minimum percentage of new cliques to trigger another clique table analysis |
| `propagating/vbounds/maxcliquesmedium` | `real` | [0,1.79769313486232e+308] | 50 | False | maximum number of cliques per variable to run clique table analysis in medium presolving |
| `propagating/vbounds/maxcliquesexhaustive` | `real` | [0,1.79769313486232e+308] | 100 | False | maximum number of cliques per variable to run clique table analysis in exhaustive presolving |
| `propagating/pseudoobj/priority` | `int` | [-536870912,536870911] | 3000000 | True | priority of propagator &lt;pseudoobj&gt; |
| `propagating/pseudoobj/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling propagator &lt;pseudoobj&gt; (-1: never, 0: only in root node) |
| `propagating/pseudoobj/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/pseudoobj/timingmask` | `int` | [0,15] | 7 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/pseudoobj/presolpriority` | `int` | [-536870912,536870911] | 6000000 | True | presolving priority of propagator &lt;pseudoobj&gt; |
| `propagating/pseudoobj/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/pseudoobj/presoltiming` | `int` | [2,60] | 4 | True | timing mask of the presolving method of propagator &lt;pseudoobj&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/pseudoobj/minuseless` | `int` | [0,2147483647] | 100 | True | minimal number of successive non-binary variable propagations without a bound reduction before aborted |
| `propagating/pseudoobj/maxvarsfrac` | `real` | [0,1] | 0.1 | True | maximal fraction of non-binary variables with non-zero objective without a bound reduction before aborted |
| `propagating/pseudoobj/propfullinroot` | `bool` | {TRUE,FALSE} | TRUE | True | whether to propagate all non-binary variables when we are propagating the root node |
| `propagating/pseudoobj/propcutoffbound` | `bool` | {TRUE,FALSE} | TRUE | True | propagate new cutoff bound directly globally |
| `propagating/pseudoobj/force` | `bool` | {TRUE,FALSE} | FALSE | True | should the propagator be forced even if active pricer are present? |
| `propagating/pseudoobj/maxnewvars` | `int` | [0,2147483647] | 1000 | True | number of variables added after the propagator is reinitialized? |
| `propagating/pseudoobj/propuseimplics` | `bool` | {TRUE,FALSE} | TRUE | True | use implications to strengthen the propagation of binary variable (increasing the objective change)? |
| `propagating/pseudoobj/respropuseimplics` | `bool` | {TRUE,FALSE} | TRUE | True | use implications to strengthen the resolve propagation of binary variable (increasing the objective change)? |
| `propagating/pseudoobj/maximplvars` | `int` | [-1,2147483647] | 50000 | True | maximum number of binary variables the implications are used if turned on (-1: unlimited)? |
| `propagating/redcost/priority` | `int` | [-536870912,536870911] | 1000000 | True | priority of propagator &lt;redcost&gt; |
| `propagating/redcost/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling propagator &lt;redcost&gt; (-1: never, 0: only in root node) |
| `propagating/redcost/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/redcost/timingmask` | `int` | [0,15] | 6 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/redcost/presolpriority` | `int` | [-536870912,536870911] | 0 | True | presolving priority of propagator &lt;redcost&gt; |
| `propagating/redcost/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/redcost/presoltiming` | `int` | [2,60] | 28 | True | timing mask of the presolving method of propagator &lt;redcost&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/redcost/continuous` | `bool` | {TRUE,FALSE} | FALSE | False | should reduced cost fixing be also applied to continuous variables? |
| `propagating/redcost/useimplics` | `bool` | {TRUE,FALSE} | FALSE | False | should implications be used to strength the reduced cost for binary variables? |
| `propagating/redcost/force` | `bool` | {TRUE,FALSE} | FALSE | True | should the propagator be forced even if active pricer are present? |
| `propagating/probing/priority` | `int` | [-536870912,536870911] | -100000 | True | priority of propagator &lt;probing&gt; |
| `propagating/probing/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling propagator &lt;probing&gt; (-1: never, 0: only in root node) |
| `propagating/probing/delay` | `bool` | {TRUE,FALSE} | TRUE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/probing/timingmask` | `int` | [0,15] | 4 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/probing/presolpriority` | `int` | [-536870912,536870911] | -100000 | True | presolving priority of propagator &lt;probing&gt; |
| `propagating/probing/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/probing/presoltiming` | `int` | [2,60] | 16 | True | timing mask of the presolving method of propagator &lt;probing&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/probing/maxruns` | `int` | [-1,2147483647] | 1 | False | maximal number of runs, probing participates in (-1: no limit) |
| `propagating/probing/proprounds` | `int` | [-1,2147483647] | -1 | True | maximal number of propagation rounds in probing subproblems (-1: no limit, 0: auto) |
| `propagating/probing/maxfixings` | `int` | [0,2147483647] | 25 | True | maximal number of fixings found, until probing is interrupted (0: don't iterrupt) |
| `propagating/probing/maxuseless` | `int` | [0,2147483647] | 1000 | True | maximal number of successive probings without fixings, until probing is aborted (0: don't abort) |
| `propagating/probing/maxtotaluseless` | `int` | [0,2147483647] | 50 | True | maximal number of successive probings without fixings, bound changes, and implications, until probing is aborted (0: don't abort) |
| `propagating/probing/maxsumuseless` | `int` | [0,2147483647] | 0 | True | maximal number of probings without fixings, until probing is aborted (0: don't abort) |
| `propagating/probing/maxdepth` | `int` | [-1,2147483647] | -1 | True | maximal depth until propagation is executed(-1: no limit) |
| `propagating/symmetry/priority` | `int` | [-536870912,536870911] | -1000000 | True | priority of propagator &lt;symmetry&gt; |
| `propagating/symmetry/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling propagator &lt;symmetry&gt; (-1: never, 0: only in root node) |
| `propagating/symmetry/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/symmetry/timingmask` | `int` | [0,15] | 1 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/symmetry/presolpriority` | `int` | [-536870912,536870911] | -10000000 | True | presolving priority of propagator &lt;symmetry&gt; |
| `propagating/symmetry/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/symmetry/presoltiming` | `int` | [2,60] | 16 | True | timing mask of the presolving method of propagator &lt;symmetry&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/symmetry/maxgenerators` | `int` | [0,2147483647] | 1500 | True | limit on the number of generators that should be produced within symmetry detection (0 = no limit) |
| `propagating/symmetry/checksymmetries` | `bool` | {TRUE,FALSE} | FALSE | True | Should all symmetries be checked after computation? |
| `propagating/symmetry/displaynorbitvars` | `bool` | {TRUE,FALSE} | FALSE | True | Should the number of variables affected by some symmetry be displayed? |
| `propagating/symmetry/doubleequations` | `bool` | {TRUE,FALSE} | FALSE | True | Double equations to positive/negative version? |
| `propagating/symmetry/dispsyminfo` | `bool` | {TRUE,FALSE} | FALSE | True | Shall symmetry information be printed to the terminal? |
| `propagating/symmetry/conssaddlp` | `bool` | {TRUE,FALSE} | TRUE | True | Should the symmetry breaking constraints be added to the LP? |
| `propagating/symmetry/addsymresacks` | `bool` | {TRUE,FALSE} | TRUE | True | Add inequalities for symresacks for each generator? |
| `propagating/symmetry/detectdoublelex` | `bool` | {TRUE,FALSE} | TRUE | True | Should we check whether the components of the symmetry group can be handled by double lex matrices? |
| `propagating/symmetry/detectorbitopes` | `bool` | {TRUE,FALSE} | TRUE | True | Should we check whether the components of the symmetry group can be handled by orbitopes? |
| `propagating/symmetry/detectsubgroups` | `bool` | {TRUE,FALSE} | TRUE | True | Should we try to detect symmetric subgroups of the symmetry group on binary variables? |
| `propagating/symmetry/addweaksbcs` | `bool` | {TRUE,FALSE} | TRUE | True | Should we add weak SBCs for enclosing orbit of symmetric subgroups? |
| `propagating/symmetry/addconsstiming` | `int` | [0,2] | 2 | True | timing of adding constraints (0 = before presolving, 1 = during presolving, 2 = after presolving) [disabled parameter] |
| `propagating/symmetry/ofsymcomptiming` | `int` | [0,2] | 2 | True | timing of symmetry computation (0 = before presolving, 1 = during presolving, 2 = at first call) [disabled parameter] |
| `propagating/symmetry/performpresolving` | `bool` | {TRUE,FALSE} | FALSE | True | run orbital fixing during presolving? (disabled) |
| `propagating/symmetry/recomputerestart` | `int` | [0,0] | 0 | True | recompute symmetries after a restart has occurred? (0 = never) |
| `propagating/symmetry/compresssymmetries` | `bool` | {TRUE,FALSE} | TRUE | True | Should non-affected variables be removed from permutation to save memory? |
| `propagating/symmetry/compressthreshold` | `real` | [0,1] | 0.5 | True | Compression is used if percentage of moved vars is at most the threshold. |
| `propagating/symmetry/usecolumnsparsity` | `bool` | {TRUE,FALSE} | FALSE | True | Should the number of conss a variable is contained in be exploited in symmetry detection? |
| `propagating/symmetry/maxnconsssubgroup` | `int` | [0,2147483647] | 500000 | True | maximum number of constraints up to which subgroup structures are detected |
| `propagating/symmetry/usedynamicprop` | `bool` | {TRUE,FALSE} | TRUE | True | whether dynamified symmetry handling constraint methods should be used |
| `propagating/symmetry/addstrongsbcs` | `bool` | {TRUE,FALSE} | FALSE | True | Should strong SBCs for enclosing orbit of symmetric subgroups be added if orbitopes are not used? |
| `propagating/symmetry/ssttiebreakrule` | `int` | [0,2] | 1 | True | rule to select the orbit in Schreier Sims inequalities (variable in 0: minimum size orbit; 1: maximum size orbit; 2: orbit with most variables in conflict with leader) |
| `propagating/symmetry/sstleaderrule` | `int` | [0,2] | 0 | True | rule to select the leader in an orbit (0: first var; 1: last var; 2: var having most conflicting vars in orbit) |
| `propagating/symmetry/sstleadervartype` | `int` | [1,7] | 6 | True | bitset encoding which variable types can be leaders (1: binary; 2: integer; 4: continuous);if multiple types are allowed, take the one with most affected vars |
| `propagating/symmetry/addconflictcuts` | `bool` | {TRUE,FALSE} | TRUE | True | Should Schreier Sims constraints be added if we use a conflict based rule? |
| `propagating/symmetry/sstaddcuts` | `bool` | {TRUE,FALSE} | TRUE | True | Should Schreier Sims constraints be added? |
| `propagating/symmetry/sstmixedcomponents` | `bool` | {TRUE,FALSE} | TRUE | True | Should Schreier Sims constraints be added if a symmetry component contains variables of different types? |
| `propagating/symmetry/symfixnonbinaryvars` | `bool` | {TRUE,FALSE} | FALSE | True | Whether all non-binary variables shall be not affected by symmetries if OF is active? (disabled) |
| `propagating/symmetry/enforcecomputesymmetry` | `bool` | {TRUE,FALSE} | FALSE | True | Is only symmetry on binary variables used? |
| `propagating/symmetry/preferlessrows` | `bool` | {TRUE,FALSE} | TRUE | True | Shall orbitopes with less rows be preferred in detection? |
| `propagating/symmetry/symtype` | `int` | [0,1] | 0 | True | Type of symmetries that shall be computed? |
| `propagating/symmetry/handlesignedorbitopes` | `bool` | {TRUE,FALSE} | TRUE | True | Should orbitopes on which proper signed permutations act be handled? |
| `propagating/symmetry/usesimplesgncomp` | `bool` | {TRUE,FALSE} | TRUE | True | Should components consisting of a single full reflection be handled? |
| `propagating/symmetry/symtiming` | `int` | [0,2] | 2 | True | timing of symmetry computation and handling (0 = before presolving, 1 = during presolving, 2 = after presolving) |
| `propagating/symmetry/maxnnewivolus` | `int` | [0,2000] | 100 | True | maximum number of newly generated involutions per symmetry component |
| `propagating/symmetry/nautymaxlevel` | `int` | [-1,2147483647] | 10000 | True | terminate symmetry detection using Nauty when depth level of Nauty's search tree exceeds this number (-1: unlimited) |
| `propagating/symmetry/orbitopalreduction/columnordering` | `int` | [0,4] | 4 | True | The column ordering variant, respects enum SCIP_ColumnOrdering. |
| `propagating/obbt/priority` | `int` | [-536870912,536870911] | -1000000 | True | priority of propagator &lt;obbt&gt; |
| `propagating/obbt/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling propagator &lt;obbt&gt; (-1: never, 0: only in root node) |
| `propagating/obbt/delay` | `bool` | {TRUE,FALSE} | TRUE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/obbt/timingmask` | `int` | [0,15] | 4 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/obbt/presolpriority` | `int` | [-536870912,536870911] | 0 | True | presolving priority of propagator &lt;obbt&gt; |
| `propagating/obbt/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/obbt/presoltiming` | `int` | [2,60] | 28 | True | timing mask of the presolving method of propagator &lt;obbt&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/obbt/creategenvbounds` | `bool` | {TRUE,FALSE} | TRUE | True | should obbt try to provide genvbounds if possible? |
| `propagating/obbt/normalize` | `bool` | {TRUE,FALSE} | TRUE | True | should coefficients in filtering be normalized w.r.t. the domains sizes? |
| `propagating/obbt/applyfilterrounds` | `bool` | {TRUE,FALSE} | FALSE | True | try to filter bounds in so-called filter rounds by solving auxiliary LPs? |
| `propagating/obbt/applytrivialfilter` | `bool` | {TRUE,FALSE} | TRUE | True | try to filter bounds with the LP solution after each solve? |
| `propagating/obbt/genvbdsduringfilter` | `bool` | {TRUE,FALSE} | TRUE | True | should we try to generate genvbounds during trivial and aggressive filtering? |
| `propagating/obbt/genvbdsduringsepa` | `bool` | {TRUE,FALSE} | TRUE | True | try to create genvbounds during separation process? |
| `propagating/obbt/minfilter` | `int` | [1,2147483647] | 2 | True | minimal number of filtered bounds to apply another filter round |
| `propagating/obbt/itlimitfactor` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 10 | False | multiple of root node LP iterations used as total LP iteration limit for obbt (&lt;= 0: no limit ) |
| `propagating/obbt/itlimitfactorbilin` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 3 | False | multiple of OBBT LP limit used as total LP iteration limit for solving bilinear inequality LPs (&lt; 0 for no limit) |
| `propagating/obbt/minnonconvexity` | `real` | [0,1.79769313486232e+308] | 0.1 | False | minimum absolute value of nonconvex eigenvalues for a bilinear term |
| `propagating/obbt/minitlimit` | `longint` | [0,9223372036854775807] | 5000 | False | minimum LP iteration limit |
| `propagating/obbt/dualfeastol` | `real` | [0,1.79769313486232e+308] | 1e-09 | False | feasibility tolerance for reduced costs used in obbt; this value is used if SCIP's dual feastol is greater |
| `propagating/obbt/conditionlimit` | `real` | [-1,1.79769313486232e+308] | -1 | False | maximum condition limit used in LP solver (-1.0: no limit) |
| `propagating/obbt/boundstreps` | `real` | [0,1] | 0.001 | False | minimal relative improve for strengthening bounds |
| `propagating/obbt/indicatorthreshold` | `real` | [0,1.79769313486232e+308] | 1000000 | True | threshold whether upper bounds of vars of indicator conss are considered or tightened |
| `propagating/obbt/onlynonconvexvars` | `bool` | {TRUE,FALSE} | TRUE | True | only apply obbt on non-convex variables |
| `propagating/obbt/indicators` | `bool` | {TRUE,FALSE} | FALSE | True | apply obbt on variables of indicator constraints? (independent of convexity) |
| `propagating/obbt/tightintboundsprobing` | `bool` | {TRUE,FALSE} | TRUE | True | should integral bounds be tightened during the probing mode? |
| `propagating/obbt/tightcontboundsprobing` | `bool` | {TRUE,FALSE} | FALSE | True | should continuous bounds be tightened during the probing mode? |
| `propagating/obbt/createbilinineqs` | `bool` | {TRUE,FALSE} | TRUE | True | solve auxiliary LPs in order to find valid inequalities for bilinear terms? |
| `propagating/obbt/createlincons` | `bool` | {TRUE,FALSE} | FALSE | True | create linear constraints from inequalities for bilinear terms? |
| `propagating/obbt/orderingalgo` | `int` | [0,2] | 1 | True | select the type of ordering algorithm which should be used (0: no special ordering, 1: greedy, 2: greedy reverse) |
| `propagating/obbt/separatesol` | `bool` | {TRUE,FALSE} | FALSE | True | should the obbt LP solution be separated? |
| `propagating/obbt/sepaminiter` | `int` | [0,2147483647] | 0 | True | minimum number of iteration spend to separate an obbt LP solution |
| `propagating/obbt/sepamaxiter` | `int` | [0,2147483647] | 10 | True | maximum number of iteration spend to separate an obbt LP solution |
| `propagating/obbt/propagatefreq` | `int` | [0,2147483647] | 0 | True | trigger a propagation round after that many bound tightenings (0: no propagation) |
| `propagating/nlobbt/priority` | `int` | [-536870912,536870911] | -1100000 | True | priority of propagator &lt;nlobbt&gt; |
| `propagating/nlobbt/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling propagator &lt;nlobbt&gt; (-1: never, 0: only in root node) |
| `propagating/nlobbt/delay` | `bool` | {TRUE,FALSE} | TRUE | True | should propagator be delayed, if other propagators found reductions? |
| `propagating/nlobbt/timingmask` | `int` | [0,15] | 4 | True | timing when propagator should be called (1:BEFORELP, 2:DURINGLPLOOP, 4:AFTERLPLOOP, 15:ALWAYS)) |
| `propagating/nlobbt/presolpriority` | `int` | [-536870912,536870911] | 0 | True | presolving priority of propagator &lt;nlobbt&gt; |
| `propagating/nlobbt/maxprerounds` | `int` | [-1,2147483647] | -1 | False | maximal number of presolving rounds the propagator participates in (-1: no limit) |
| `propagating/nlobbt/presoltiming` | `int` | [2,60] | 28 | True | timing mask of the presolving method of propagator &lt;nlobbt&gt; (4:FAST, 8:MEDIUM, 16:EXHAUSTIVE, 32:FINAL) |
| `propagating/nlobbt/feastolfac` | `real` | [0,1] | 0.01 | True | factor for NLP feasibility tolerance |
| `propagating/nlobbt/relobjtolfac` | `real` | [0,1] | 0.01 | True | factor for NLP relative objective tolerance |
| `propagating/nlobbt/minnonconvexfrac` | `real` | [0,1e+20] | 0.2 | True | (#convex nlrows)/(#nonconvex nlrows) threshold to apply propagator |
| `propagating/nlobbt/minlinearfrac` | `real` | [0,1e+20] | 0.02 | True | minimum (#convex nlrows)/(#linear nlrows) threshold to apply propagator |
| `propagating/nlobbt/addlprows` | `bool` | {TRUE,FALSE} | TRUE | False | should non-initial LP rows be used? |
| `propagating/nlobbt/nlpiterlimit` | `int` | [0,2147483647] | 500 | True | iteration limit of NLP solver; 0 for no limit |
| `propagating/nlobbt/nlptimelimit` | `real` | [0,1.79769313486232e+308] | 0 | True | time limit of NLP solver; 0.0 for no limit |
| `propagating/nlobbt/nlpverblevel` | `int` | [0,5] | 0 | True | verbosity level of NLP solver |
| `propagating/nlobbt/itlimitfactor` | `real` | [0,1.79769313486232e+308] | 2 | True | LP iteration limit for nlobbt will be this factor times total LP iterations in root node |

## randomization

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `randomization/randomseedshift` | `int` | [0,2147483647] | 0 | False | global shift of all random seeds in the plugins and the LP random seed |
| `randomization/randomseedshiftmultiplier` | `int` | [0,2147483647] | 10 | False | multiplier for global shift of all random seeds in the plugins and the LP random seed; this multiplier will be changed with every SCIP major release |
| `randomization/permutationseed` | `int` | [0,2147483647] | 0 | False | seed value for permuting the problem after reading/transformation (0: no permutation) |
| `randomization/permuteconss` | `bool` | {TRUE,FALSE} | TRUE | True | should order of constraints be permuted (depends on permutationseed)? |
| `randomization/permutevars` | `bool` | {TRUE,FALSE} | FALSE | True | should order of variables be permuted (depends on permutationseed)? |
| `randomization/lpseed` | `int` | [0,2147483647] | 0 | False | random seed for LP solver, e.g. for perturbations in the simplex (0: LP default) |

## reading

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `reading/initialconss` | `bool` | {TRUE,FALSE} | TRUE | False | should model constraints be marked as initial? |
| `reading/dynamicconss` | `bool` | {TRUE,FALSE} | TRUE | False | should model constraints be subject to aging? |
| `reading/dynamiccols` | `bool` | {TRUE,FALSE} | FALSE | False | should columns be added and removed dynamically to the LP? |
| `reading/dynamicrows` | `bool` | {TRUE,FALSE} | FALSE | False | should rows be added and removed dynamically to the LP? |
| `reading/mpsreader/linearize-and-constraints` | `bool` | {TRUE,FALSE} | TRUE | True | should possible "and" constraint be linearized when writing the mps file? |
| `reading/mpsreader/aggrlinearization-ands` | `bool` | {TRUE,FALSE} | TRUE | True | should an aggregated linearization for and constraints be used? |
| `reading/lpreader/linearize-and-constraints` | `bool` | {TRUE,FALSE} | TRUE | True | should possible "and" constraint be linearized when writing the lp file? |
| `reading/lpreader/aggrlinearization-ands` | `bool` | {TRUE,FALSE} | TRUE | True | should an aggregated linearization for and constraints be used? |
| `reading/nlreader/binary` | `bool` | {TRUE,FALSE} | FALSE | False | should nl files be written in binary format |
| `reading/nlreader/comments` | `bool` | {TRUE,FALSE} | FALSE | False | should comments be written to nl files |
| `reading/gmsreader/replaceforbiddenchars` | `bool` | {TRUE,FALSE} | FALSE | False | shall characters '#', '*', '+', '/', and '-' in variable and constraint names be replaced by '_'? |
| `reading/gmsreader/bigmdefault` | `real` | [0,1.79769313486232e+308] | 1000000 | False | default M value for big-M reformulation of indicator constraints in case no bound on slack variable is given |
| `reading/gmsreader/indicatorreform` | `char` | {bs} | s | False | which reformulation to use for indicator constraints: 'b'ig-M, 's'os1 |
| `reading/opbreader/dynamicconss` | `bool` | {TRUE,FALSE} | FALSE | False | should model constraints be subject to aging? |
| `reading/opbreader/multisymbol` | `bool` | {TRUE,FALSE} | FALSE | True | use '*' between coefficients and variables by writing to problem? |
| `reading/opbreader/maxintsize` | `int` | [-1,2147483647] | -1 | True | maximum allowed 'intsize' (i.e. the number of bits required to represent the sum of absolute values of all integers that appear in a constraint or objective function) or -1 for unlimited |
| `reading/cnfreader/useobj` | `bool` | {TRUE,FALSE} | FALSE | False | should an artificial objective, depending on the number of clauses a variable appears in, be used? |
| `reading/cipreader/writefixedvars` | `bool` | {TRUE,FALSE} | TRUE | False | should fixed and aggregated variables be printed (if not, re-parsing might fail) |
| `reading/storeader/usebenders` | `bool` | {TRUE,FALSE} | FALSE | False | should Benders' decomposition be used? |
| `reading/bndreader/improveonly` | `bool` | {TRUE,FALSE} | FALSE | False | only use improving bounds |
| `reading/ppmreader/rgbrelativ` | `bool` | {TRUE,FALSE} | TRUE | False | should the coloring values be relativ or absolute |
| `reading/ppmreader/rgbascii` | `bool` | {TRUE,FALSE} | TRUE | False | should the output format be binary(P6) (otherwise plain(P3) format) |
| `reading/ppmreader/coefficientlimit` | `int` | [3,16] | 3 | False | splitting coefficients in this number of intervals |
| `reading/ppmreader/rgblimit` | `int` | [0,255] | 160 | False | maximal color value |
| `reading/pbmreader/binary` | `bool` | {TRUE,FALSE} | TRUE | False | should the output format be binary(P4) (otherwise plain(P1) format) |
| `reading/pbmreader/maxrows` | `int` | [-1,2147483647] | 1000 | False | maximum number of rows in the scaled picture (-1 for no limit) |
| `reading/pbmreader/maxcols` | `int` | [-1,2147483647] | 1000 | False | maximum number of columns in the scaled picture (-1 for no limit) |

## relaxing

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `relaxing/benders/priority` | `int` | [-536870912,536870911] | 1 | False | priority of relaxation handler &lt;benders&gt; |
| `relaxing/benders/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling relaxation handler &lt;benders&gt; (-1: never, 0: only in root node) |
| `relaxing/benders/continueorig` | `bool` | {TRUE,FALSE} | FALSE | False | continue solving the original SCIP instance if the optimal solution is not found by Benders' decomposition |
| `relaxing/benders/nodelimit` | `longint` | [-1,9223372036854775807] | -1 | False | the node limit applied only to the Benders' decomposition solve (-1 indicates that the original SCIP node limit is used). |

## reoptimization

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `reoptimization/enable` | `bool` | {TRUE,FALSE} | FALSE | False | should reoptimization used? |
| `reoptimization/maxsavednodes` | `int` | [-1,2147483647] | 2147483647 | True | maximal number of saved nodes |
| `reoptimization/maxdiffofnodes` | `int` | [0,2147483647] | 2147483647 | True | maximal number of bound changes between two stored nodes on one path |
| `reoptimization/globalcons/sepainfsubtrees` | `bool` | {TRUE,FALSE} | TRUE | False | save global constraints to separate infeasible subtrees. |
| `reoptimization/sepabestsol` | `bool` | {TRUE,FALSE} | FALSE | True | separate the optimal solution, i.e., for constrained shortest path |
| `reoptimization/storevarhistory` | `bool` | {TRUE,FALSE} | FALSE | True | use variable history of the previous solve if the objctive function has changed only slightly |
| `reoptimization/usepscost` | `bool` | {TRUE,FALSE} | FALSE | True | re-use pseudo costs if the objective function changed only slightly  |
| `reoptimization/solvelp` | `int` | [1,5] | 1 | True | at which reopttype should the LP be solved? (1: transit, 3: strong branched, 4: w/ added logicor, 5: only leafs). |
| `reoptimization/solvelpdiff` | `int` | [0,2147483647] | 1 | True | maximal number of bound changes at node to skip solving the LP |
| `reoptimization/savesols` | `int` | [0,2147483647] | 2147483647 | True | number of best solutions which should be saved for the following runs. (-1: save all) |
| `reoptimization/objsimrootLP` | `real` | [-1,1] | 0.8 | True | similarity of two sequential objective function to disable solving the root LP. |
| `reoptimization/objsimsol` | `real` | [-1,1] | -1 | True | similarity of two objective functions to re-use stored solutions |
| `reoptimization/delay` | `real` | [-1,1] | -1 | True | minimum similarity for using reoptimization of the search tree. |
| `reoptimization/commontimelimit` | `bool` | {TRUE,FALSE} | FALSE | True | time limit over all reoptimization rounds?. |
| `reoptimization/shrinkinner` | `bool` | {TRUE,FALSE} | TRUE | True | replace branched inner nodes by their child nodes, if the number of bound changes is not to large |
| `reoptimization/strongbranchinginit` | `bool` | {TRUE,FALSE} | TRUE | True | try to fix variables at the root node before reoptimizing by probing like strong branching |
| `reoptimization/reducetofrontier` | `bool` | {TRUE,FALSE} | TRUE | True | delete stored nodes which were not reoptimized |
| `reoptimization/forceheurrestart` | `int` | [1,2147483647] | 3 | True | force a restart if the last n optimal solutions were found by heuristic reoptsols |
| `reoptimization/saveconsprop` | `bool` | {TRUE,FALSE} | FALSE | True | save constraint and propagator propagations |
| `reoptimization/usesplitcons` | `bool` | {TRUE,FALSE} | TRUE | True | use constraints to reconstruct the subtree pruned be dual reduction when reactivating the node |
| `reoptimization/varorderinterdiction` | `char` | {dir} | d | True | use 'd'efault, 'r'andom or a variable ordering based on 'i'nference score for interdiction branching used during reoptimization |
| `reoptimization/usecuts` | `bool` | {TRUE,FALSE} | FALSE | True | reoptimize cuts found at the root node |
| `reoptimization/maxcutage` | `int` | [0,2147483647] | 0 | True | maximal age of a cut to be use for reoptimization |

## separating

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `separating/maxbounddist` | `real` | [0,1] | 1 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separation (0.0: only on current best node, 1.0: on all nodes) |
| `separating/maxlocalbounddist` | `real` | [0,1] | 0 | False | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying local separation (0.0: only on current best node, 1.0: on all nodes) |
| `separating/maxcoefratio` | `real` | [1,1e+98] | 10000 | False | maximal ratio between coefficients in strongcg, cmir, and flowcover cuts |
| `separating/maxcoefratiofacrowprep` | `real` | [0,1.79769313486232e+308] | 10 | False | maximal ratio between coefficients (as factor of 1/feastol) to ensure in rowprep cleanup |
| `separating/minefficacy` | `real` | [0,1e+98] | 0.0001 | False | minimal efficacy for a cut to enter the LP |
| `separating/minefficacyroot` | `real` | [0,1e+98] | 0.0001 | False | minimal efficacy for a cut to enter the LP in the root node |
| `separating/minactivityquot` | `real` | [0,1] | 0.8 | False | minimum cut activity quotient to convert cuts into constraints during a restart (0.0: all cuts are converted) |
| `separating/maxcutsgenfactor` | `real` | [-1,1.79769313486232e+308] | 2 | False | factor w.r.t. maxcuts for maximal number of cuts generated per separation round (-1.0: no limit, &gt;= 0.0: valid finite limit) |
| `separating/maxcutsrootgenfactor` | `real` | [-1,1.79769313486232e+308] | 2 | False | factor w.r.t. maxcutsroot for maximal number of generated cuts per separation round at the root node (-1.0: no limit, &gt;= 0.0: valid finite limit) |
| `separating/orthofunc` | `char` | {ed} | e | True | function used for calc. scalar prod. in orthogonality test ('e'uclidean, 'd'iscrete) |
| `separating/efficacynorm` | `char` | {emsd} | e | True | row norm to use for efficacy calculation ('e'uclidean, 'm'aximum, 's'um, 'd'iscrete) |
| `separating/cutselrestart` | `char` | {aq} | a | True | cut selection during restart ('a'ge, activity 'q'uotient) |
| `separating/cutselsubscip` | `char` | {aq} | a | True | cut selection for sub SCIPs  ('a'ge, activity 'q'uotient) |
| `separating/filtercutpoolrel` | `bool` | {TRUE,FALSE} | FALSE | True | should cutpool separate only cuts with high relative efficacy? |
| `separating/maxruns` | `int` | [-1,2147483647] | -1 | True | maximal number of runs for which separation is enabled (-1: unlimited) |
| `separating/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of separation rounds per node (-1: unlimited) |
| `separating/maxroundsroot` | `int` | [-1,2147483647] | -1 | False | maximal number of separation rounds in the root node (-1: unlimited) |
| `separating/maxroundsrootsubrun` | `int` | [-1,2147483647] | -1 | True | maximal number of separation rounds in the root node of a subsequent run (-1: unlimited) |
| `separating/maxaddrounds` | `int` | [-1,2147483647] | 1 | True | maximal additional number of separation rounds in subsequent price-and-cut loops (-1: no additional restriction) |
| `separating/maxstallrounds` | `int` | [-1,2147483647] | 1 | False | maximal number of consecutive separation rounds without objective or integrality improvement in local nodes (-1: no additional restriction) |
| `separating/maxstallroundsroot` | `int` | [-1,2147483647] | 10 | False | maximal number of consecutive separation rounds without objective or integrality improvement in the root node (-1: no additional restriction) |
| `separating/maxcuts` | `int` | [0,2147483647] | 100 | False | maximal number of cuts separated per separation round (0: disable local separation) |
| `separating/maxcutsroot` | `int` | [0,2147483647] | 2000 | False | maximal number of separated cuts per separation round at the root node (0: disable root node separation) |
| `separating/cutagelimit` | `int` | [-1,2147483647] | 80 | True | maximum age a cut can reach before it is deleted from the global cut pool, or -1 to keep all cuts |
| `separating/poolfreq` | `int` | [-1,1073741822] | 10 | False | separation frequency for the global cut pool (-1: disable global cut pool, 0: only separate pool at the root) |
| `separating/closecuts/priority` | `int` | [-536870912,536870911] | 1000000 | True | priority of separator &lt;closecuts&gt; |
| `separating/closecuts/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling separator &lt;closecuts&gt; (-1: never, 0: only in root node) |
| `separating/closecuts/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;closecuts&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/closecuts/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/closecuts/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;closecuts&gt; is called (1: call at each multiple of frequency) |
| `separating/closecuts/separelint` | `bool` | {TRUE,FALSE} | TRUE | True | generate close cuts w.r.t. relative interior point (best solution otherwise)? |
| `separating/closecuts/sepacombvalue` | `real` | [0,1] | 0.3 | True | convex combination value for close cuts |
| `separating/closecuts/closethres` | `int` | [-1,2147483647] | 50 | True | threshold on number of generated cuts below which the ordinary separation is started |
| `separating/closecuts/inclobjcutoff` | `bool` | {TRUE,FALSE} | FALSE | True | include an objective cutoff when computing the relative interior? |
| `separating/closecuts/recomputerelint` | `bool` | {TRUE,FALSE} | FALSE | True | recompute relative interior point in each separation call? |
| `separating/closecuts/maxunsuccessful` | `int` | [-1,2147483647] | 0 | True | turn off separation in current node after unsuccessful calls (-1 never turn off) |
| `separating/closecuts/maxlpiterfactor` | `real` | [-1,1.79769313486232e+308] | 10 | True | factor for maximal LP iterations in relative interior computation compared to node LP iterations (negative for no limit) |
| `separating/flower/priority` | `int` | [-536870912,536870911] | 100000 | True | priority of separator &lt;flower&gt; |
| `separating/flower/freq` | `int` | [-1,1073741822] | 1 | False | frequency for calling separator &lt;flower&gt; (-1: never, 0: only in root node) |
| `separating/flower/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;flower&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/flower/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/flower/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;flower&gt; is called (1: call at each multiple of frequency) |
| `separating/flower/scanand` | `bool` | {TRUE,FALSE} | TRUE | False | Whether to scan AND constraints when constructing hypergraph |
| `separating/flower/scanproduct` | `bool` | {TRUE,FALSE} | FALSE | False | Whether to scan product expressions when constructing hypergraph |
| `separating/flower/maxstandard` | `int` | [0,2147483647] | 0 | False | Maximum number of standard relaxation inequalities per cut round |
| `separating/flower/maxoneflower` | `int` | [0,2147483647] | 10000000 | False | Maximum number of 1-flower inequalities per cut round |
| `separating/flower/maxtwoflower` | `int` | [0,2147483647] | 10000000 | False | Maximum number of 2-flower inequalities per cut round |
| `separating/flower/minnoverlaps` | `int` | [0,2147483647] | 1 | False | Minimum number of overlaps necessary to try separation |
| `separating/flower/delaystandard` | `bool` | {TRUE,FALSE} | FALSE | False | Whether to only generate standard inequalities if also flowers were generated |
| `separating/flower/maxuselessoneflower` | `int` | [0,2147483647] | 1 | False | Number of useless separation rounds after which we stop separating 1-flowers |
| `separating/flower/maxuselesstwoflower` | `int` | [0,2147483647] | 1 | False | Number of useless separation rounds after which we stop separating 2-flowers |
| `separating/rlt/priority` | `int` | [-536870912,536870911] | 10 | True | priority of separator &lt;rlt&gt; |
| `separating/rlt/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling separator &lt;rlt&gt; (-1: never, 0: only in root node) |
| `separating/rlt/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;rlt&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/rlt/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/rlt/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;rlt&gt; is called (1: call at each multiple of frequency) |
| `separating/rlt/maxncuts` | `int` | [-1,2147483647] | -1 | False | maximal number of rlt-cuts that are added per round (-1: unlimited) |
| `separating/rlt/maxunknownterms` | `int` | [-1,2147483647] | 0 | False | maximal number of unknown bilinear terms a row is still used with (-1: unlimited) |
| `separating/rlt/maxusedvars` | `int` | [-1,2147483647] | 100 | False | maximal number of variables used to compute rlt cuts (-1: unlimited) |
| `separating/rlt/maxrounds` | `int` | [-1,2147483647] | 1 | False | maximal number of separation rounds per node (-1: unlimited) |
| `separating/rlt/maxroundsroot` | `int` | [-1,2147483647] | 10 | False | maximal number of separation rounds in the root node (-1: unlimited) |
| `separating/rlt/onlyeqrows` | `bool` | {TRUE,FALSE} | FALSE | False | if set to true, only equality rows are used for rlt cuts |
| `separating/rlt/onlycontrows` | `bool` | {TRUE,FALSE} | FALSE | False | if set to true, only continuous rows are used for rlt cuts |
| `separating/rlt/onlyoriginal` | `bool` | {TRUE,FALSE} | TRUE | False | if set to true, only original rows and variables are used |
| `separating/rlt/useinsubscip` | `bool` | {TRUE,FALSE} | FALSE | False | if set to true, rlt is also used in sub-scips |
| `separating/rlt/useprojection` | `bool` | {TRUE,FALSE} | FALSE | False | if set to true, projected rows are checked first |
| `separating/rlt/detecthidden` | `bool` | {TRUE,FALSE} | FALSE | False | if set to true, hidden products are detected and separated by McCormick cuts |
| `separating/rlt/hiddenrlt` | `bool` | {TRUE,FALSE} | FALSE | False | whether RLT cuts (TRUE) or only McCormick inequalities (FALSE) should be added for hidden products |
| `separating/rlt/addtopool` | `bool` | {TRUE,FALSE} | TRUE | False | if set to true, globally valid RLT cuts are added to the global cut pool |
| `separating/rlt/goodscore` | `real` | [0,1] | 1 | True | threshold for score of cut relative to best score to be considered good, so that less strict filtering is applied |
| `separating/rlt/badscore` | `real` | [0,1] | 0.5 | True | threshold for score of cut relative to best score to be discarded |
| `separating/rlt/objparalweight` | `real` | [0,1] | 0 | True | weight of objective parallelism in cut score calculation |
| `separating/rlt/efficacyweight` | `real` | [0,1] | 1 | True | weight of efficacy in cut score calculation |
| `separating/rlt/dircutoffdistweight` | `real` | [0,1] | 0 | True | weight of directed cutoff distance in cut score calculation |
| `separating/rlt/goodmaxparall` | `real` | [0,1] | 0.1 | True | maximum parallelism for good cuts |
| `separating/rlt/maxparall` | `real` | [0,1] | 0.1 | True | maximum parallelism for non-good cuts |
| `separating/disjunctive/priority` | `int` | [-536870912,536870911] | 10 | True | priority of separator &lt;disjunctive&gt; |
| `separating/disjunctive/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling separator &lt;disjunctive&gt; (-1: never, 0: only in root node) |
| `separating/disjunctive/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;disjunctive&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/disjunctive/delay` | `bool` | {TRUE,FALSE} | TRUE | True | should separator be delayed, if other separators found cuts? |
| `separating/disjunctive/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;disjunctive&gt; is called (1: call at each multiple of frequency) |
| `separating/disjunctive/strengthen` | `bool` | {TRUE,FALSE} | TRUE | True | strengthen cut if integer variables are present. |
| `separating/disjunctive/maxdepth` | `int` | [-1,2147483647] | -1 | True | node depth of separating bipartite disjunctive cuts (-1: no limit) |
| `separating/disjunctive/maxrounds` | `int` | [-1,2147483647] | 25 | True | maximal number of separation rounds per iteration in a branching node (-1: no limit) |
| `separating/disjunctive/maxroundsroot` | `int` | [-1,2147483647] | 100 | True | maximal number of separation rounds in the root node (-1: no limit) |
| `separating/disjunctive/maxinvcuts` | `int` | [0,2147483647] | 50 | True | maximal number of cuts investigated per iteration in a branching node |
| `separating/disjunctive/maxinvcutsroot` | `int` | [0,2147483647] | 250 | True | maximal number of cuts investigated per iteration in the root node |
| `separating/disjunctive/maxconfsdelay` | `int` | [-1,2147483647] | 100000 | True | delay separation if number of conflict graph edges is larger than predefined value (-1: no limit) |
| `separating/disjunctive/maxrank` | `int` | [-1,2147483647] | 20 | False | maximal rank of a disj. cut that could not be scaled to integral coefficients (-1: unlimited) |
| `separating/disjunctive/maxrankintegral` | `int` | [-1,2147483647] | -1 | False | maximal rank of a disj. cut that could be scaled to integral coefficients (-1: unlimited) |
| `separating/disjunctive/maxweightrange` | `real` | [1,1.79769313486232e+308] | 1000 | True | maximal valid range max(&#124;weights&#124;)/min(&#124;weights&#124;) of row weights |
| `separating/gauge/priority` | `int` | [-536870912,536870911] | 0 | True | priority of separator &lt;gauge&gt; |
| `separating/gauge/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling separator &lt;gauge&gt; (-1: never, 0: only in root node) |
| `separating/gauge/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;gauge&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/gauge/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/gauge/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;gauge&gt; is called (1: call at each multiple of frequency) |
| `separating/gauge/nlpiterlimit` | `int` | [0,2147483647] | 1000 | True | iteration limit of NLP solver; 0 for no limit |
| `separating/interminor/priority` | `int` | [-536870912,536870911] | 0 | True | priority of separator &lt;interminor&gt; |
| `separating/interminor/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling separator &lt;interminor&gt; (-1: never, 0: only in root node) |
| `separating/interminor/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;interminor&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/interminor/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/interminor/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;interminor&gt; is called (1: call at each multiple of frequency) |
| `separating/interminor/usestrengthening` | `bool` | {TRUE,FALSE} | FALSE | False | whether to use strengthened intersection cuts to separate minors |
| `separating/interminor/usebounds` | `bool` | {TRUE,FALSE} | FALSE | False | whether to also enforce nonegativity bounds of principle minors |
| `separating/interminor/mincutviol` | `real` | [0,1.79769313486232e+308] | 0.0001 | False | minimum required violation of a cut |
| `separating/interminor/maxrounds` | `int` | [-1,2147483647] | 10 | False | maximal number of separation rounds per node (-1: unlimited) |
| `separating/interminor/maxroundsroot` | `int` | [-1,2147483647] | -1 | False | maximal number of separation rounds in the root node (-1: unlimited) |
| `separating/minor/priority` | `int` | [-536870912,536870911] | 0 | True | priority of separator &lt;minor&gt; |
| `separating/minor/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;minor&gt; (-1: never, 0: only in root node) |
| `separating/minor/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;minor&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/minor/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/minor/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;minor&gt; is called (1: call at each multiple of frequency) |
| `separating/minor/maxminorsconst` | `int` | [0,2147483647] | 3000 | False | constant for the maximum number of minors, i.e., max(const, fac * # quadratic terms) |
| `separating/minor/maxminorsfac` | `real` | [0,1.79769313486232e+308] | 10 | False | factor for the maximum number of minors, i.e., max(const, fac * # quadratic terms) |
| `separating/minor/mincutviol` | `real` | [0,1.79769313486232e+308] | 0.0001 | False | minimum required violation of a cut |
| `separating/minor/maxrounds` | `int` | [-1,2147483647] | 10 | False | maximal number of separation rounds per node (-1: unlimited) |
| `separating/minor/maxroundsroot` | `int` | [-1,2147483647] | -1 | False | maximal number of separation rounds in the root node (-1: unlimited) |
| `separating/minor/ignorepackingconss` | `bool` | {TRUE,FALSE} | TRUE | False | whether to ignore circle packing constraints during minor detection |
| `separating/convexproj/priority` | `int` | [-536870912,536870911] | 0 | True | priority of separator &lt;convexproj&gt; |
| `separating/convexproj/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling separator &lt;convexproj&gt; (-1: never, 0: only in root node) |
| `separating/convexproj/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;convexproj&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/convexproj/delay` | `bool` | {TRUE,FALSE} | TRUE | True | should separator be delayed, if other separators found cuts? |
| `separating/convexproj/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;convexproj&gt; is called (1: call at each multiple of frequency) |
| `separating/convexproj/maxdepth` | `int` | [-1,2147483647] | -1 | False | maximal depth at which the separator is applied (-1: unlimited) |
| `separating/convexproj/nlpiterlimit` | `int` | [0,2147483647] | 250 | True | iteration limit of NLP solver; 0 for no limit |
| `separating/mixing/priority` | `int` | [-536870912,536870911] | -50 | True | priority of separator &lt;mixing&gt; |
| `separating/mixing/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;mixing&gt; (-1: never, 0: only in root node) |
| `separating/mixing/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;mixing&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/mixing/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/mixing/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;mixing&gt; is called (1: call at each multiple of frequency) |
| `separating/mixing/uselocalbounds` | `bool` | {TRUE,FALSE} | FALSE | True | Should local bounds be used? |
| `separating/mixing/iscutsonints` | `bool` | {TRUE,FALSE} | FALSE | True | Should general integer variables be used to generate cuts? |
| `separating/mixing/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of mixing separation rounds per node (-1: unlimited) |
| `separating/mixing/maxroundsroot` | `int` | [-1,2147483647] | -1 | False | maximal number of mixing separation rounds in the root node (-1: unlimited) |
| `separating/mixing/maxnunsuccessful` | `int` | [-1,2147483647] | 10 | False | maximal number of consecutive unsuccessful iterations |
| `separating/impliedbounds/priority` | `int` | [-536870912,536870911] | -50 | True | priority of separator &lt;impliedbounds&gt; |
| `separating/impliedbounds/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;impliedbounds&gt; (-1: never, 0: only in root node) |
| `separating/impliedbounds/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;impliedbounds&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/impliedbounds/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/impliedbounds/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;impliedbounds&gt; is called (1: call at each multiple of frequency) |
| `separating/impliedbounds/usetwosizecliques` | `bool` | {TRUE,FALSE} | TRUE | True | should violated inequalities for cliques with 2 variables be separated? |
| `separating/intobj/priority` | `int` | [-536870912,536870911] | -100 | True | priority of separator &lt;intobj&gt; |
| `separating/intobj/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling separator &lt;intobj&gt; (-1: never, 0: only in root node) |
| `separating/intobj/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;intobj&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/intobj/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/intobj/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;intobj&gt; is called (1: call at each multiple of frequency) |
| `separating/cgmip/priority` | `int` | [-536870912,536870911] | -1000 | True | priority of separator &lt;cgmip&gt; |
| `separating/cgmip/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling separator &lt;cgmip&gt; (-1: never, 0: only in root node) |
| `separating/cgmip/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;cgmip&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/cgmip/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/cgmip/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;cgmip&gt; is called (1: call at each multiple of frequency) |
| `separating/cgmip/maxrounds` | `int` | [-1,2147483647] | 5 | False | maximal number of cgmip separation rounds per node (-1: unlimited) |
| `separating/cgmip/maxroundsroot` | `int` | [-1,2147483647] | 50 | False | maximal number of cgmip separation rounds in the root node (-1: unlimited) |
| `separating/cgmip/maxdepth` | `int` | [-1,2147483647] | -1 | False | maximal depth at which the separator is applied (-1: unlimited) |
| `separating/cgmip/decisiontree` | `bool` | {TRUE,FALSE} | FALSE | False | Use decision tree to turn separation on/off? |
| `separating/cgmip/timelimit` | `real` | [0,1.79769313486232e+308] | 1e+20 | True | time limit for sub-MIP |
| `separating/cgmip/memorylimit` | `real` | [0,1.79769313486232e+308] | 1e+20 | True | memory limit for sub-MIP |
| `separating/cgmip/minnodelimit` | `longint` | [-1,9223372036854775807] | 500 | False | minimum number of nodes considered for sub-MIP (-1: unlimited) |
| `separating/cgmip/maxnodelimit` | `longint` | [-1,9223372036854775807] | 5000 | False | maximum number of nodes considered for sub-MIP (-1: unlimited) |
| `separating/cgmip/cutcoefbnd` | `real` | [0,1.79769313486232e+308] | 1000 | True | bounds on the values of the coefficients in the CG-cut |
| `separating/cgmip/onlyactiverows` | `bool` | {TRUE,FALSE} | FALSE | False | Use only active rows to generate cuts? |
| `separating/cgmip/maxrowage` | `int` | [-1,2147483647] | -1 | False | maximal age of rows to consider if onlyactiverows is false |
| `separating/cgmip/onlyrankone` | `bool` | {TRUE,FALSE} | FALSE | False | Separate only rank 1 inequalities w.r.t. CG-MIP separator? |
| `separating/cgmip/onlyintvars` | `bool` | {TRUE,FALSE} | FALSE | False | Generate cuts for problems with only integer variables? |
| `separating/cgmip/contconvert` | `bool` | {TRUE,FALSE} | FALSE | False | Convert some integral variables to be continuous to reduce the size of the sub-MIP? |
| `separating/cgmip/contconvfrac` | `real` | [0,1] | 0.1 | False | fraction of integral variables converted to be continuous (if contconvert) |
| `separating/cgmip/contconvmin` | `int` | [-1,2147483647] | 100 | False | minimum number of integral variables before some are converted to be continuous |
| `separating/cgmip/intconvert` | `bool` | {TRUE,FALSE} | FALSE | False | Convert some integral variables attaining fractional values to have integral value? |
| `separating/cgmip/intconvfrac` | `real` | [0,1] | 0.1 | False | fraction of frac. integral variables converted to have integral value (if intconvert) |
| `separating/cgmip/intconvmin` | `int` | [-1,2147483647] | 100 | False | minimum number of integral variables before some are converted to have integral value |
| `separating/cgmip/skipmultbounds` | `bool` | {TRUE,FALSE} | TRUE | False | Skip the upper bounds on the multipliers in the sub-MIP? |
| `separating/cgmip/objlone` | `bool` | {TRUE,FALSE} | FALSE | False | Should the objective of the sub-MIP minimize the l1-norm of the multipliers? |
| `separating/cgmip/objweight` | `real` | [0,1.79769313486232e+308] | 0.001 | True | weight used for the row combination coefficient in the sub-MIP objective |
| `separating/cgmip/objweightsize` | `bool` | {TRUE,FALSE} | TRUE | False | Weight each row by its size? |
| `separating/cgmip/dynamiccuts` | `bool` | {TRUE,FALSE} | TRUE | False | should generated cuts be removed from the LP if they are no longer tight? |
| `separating/cgmip/usecmir` | `bool` | {TRUE,FALSE} | TRUE | False | use CMIR-generator (otherwise add cut directly)? |
| `separating/cgmip/usestrongcg` | `bool` | {TRUE,FALSE} | FALSE | False | use strong CG-function to strengthen cut? |
| `separating/cgmip/cmirownbounds` | `bool` | {TRUE,FALSE} | FALSE | False | tell CMIR-generator which bounds to used in rounding? |
| `separating/cgmip/usecutpool` | `bool` | {TRUE,FALSE} | TRUE | False | use cutpool to store CG-cuts even if the are not efficient? |
| `separating/cgmip/primalseparation` | `bool` | {TRUE,FALSE} | TRUE | False | only separate cuts that are tight for the best feasible solution? |
| `separating/cgmip/earlyterm` | `bool` | {TRUE,FALSE} | TRUE | False | terminate separation if a violated (but possibly sub-optimal) cut has been found? |
| `separating/cgmip/addviolationcons` | `bool` | {TRUE,FALSE} | FALSE | False | add constraint to subscip that only allows violated cuts (otherwise add obj. limit)? |
| `separating/cgmip/addviolconshdlr` | `bool` | {TRUE,FALSE} | FALSE | False | add constraint handler to filter out violated cuts? |
| `separating/cgmip/conshdlrusenorm` | `bool` | {TRUE,FALSE} | TRUE | False | should the violation constraint handler use the norm of a cut to check for feasibility? |
| `separating/cgmip/useobjub` | `bool` | {TRUE,FALSE} | FALSE | False | Use upper bound on objective function (via primal solution)? |
| `separating/cgmip/useobjlb` | `bool` | {TRUE,FALSE} | FALSE | False | Use lower bound on objective function (via primal solution)? |
| `separating/cgmip/subscipfast` | `bool` | {TRUE,FALSE} | TRUE | False | Should the settings for the sub-MIP be optimized for speed? |
| `separating/cgmip/output` | `bool` | {TRUE,FALSE} | FALSE | False | Should information about the sub-MIP and cuts be displayed? |
| `separating/cgmip/genprimalsols` | `bool` | {TRUE,FALSE} | FALSE | False | Try to generate primal solutions from Gomory cuts? |
| `separating/gomory/priority` | `int` | [-536870912,536870911] | -1000 | True | priority of separator &lt;gomory&gt; |
| `separating/gomory/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;gomory&gt; (-1: never, 0: only in root node) |
| `separating/gomory/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;gomory&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/gomory/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/gomory/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;gomory&gt; is called (1: call at each multiple of frequency) |
| `separating/strongcg/priority` | `int` | [-536870912,536870911] | -100000 | True | priority of separator &lt;strongcg&gt; |
| `separating/strongcg/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;strongcg&gt; (-1: never, 0: only in root node) |
| `separating/strongcg/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;strongcg&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/strongcg/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/strongcg/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;strongcg&gt; is called (1: call at each multiple of frequency) |
| `separating/gomorymi/priority` | `int` | [-536870912,536870911] | -100000 | True | priority of separator &lt;gomorymi&gt; |
| `separating/gomorymi/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;gomorymi&gt; (-1: never, 0: only in root node) |
| `separating/gomorymi/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;gomorymi&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/gomorymi/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/gomorymi/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;gomorymi&gt; is called (1: call at each multiple of frequency) |
| `separating/gomory/maxrounds` | `int` | [-1,2147483647] | 5 | False | maximal number of gomory separation rounds per node (-1: unlimited) |
| `separating/gomory/maxroundsroot` | `int` | [-1,2147483647] | 10 | False | maximal number of gomory separation rounds in the root node (-1: unlimited) |
| `separating/gomory/maxsepacuts` | `int` | [0,2147483647] | 50 | False | maximal number of gomory cuts separated per separation round |
| `separating/gomory/maxsepacutsroot` | `int` | [0,2147483647] | 200 | False | maximal number of gomory cuts separated per separation round in the root node |
| `separating/gomory/maxrank` | `int` | [-1,2147483647] | -1 | False | maximal rank of a gomory cut that could not be scaled to integral coefficients (-1: unlimited) |
| `separating/gomory/maxrankintegral` | `int` | [-1,2147483647] | -1 | False | maximal rank of a gomory cut that could be scaled to integral coefficients (-1: unlimited) |
| `separating/gomory/away` | `real` | [0.0001,0.5] | 0.01 | False | minimal integrality violation of a basis variable in order to try Gomory cut |
| `separating/gomory/dynamiccuts` | `bool` | {TRUE,FALSE} | TRUE | False | should generated cuts be removed from the LP if they are no longer tight? |
| `separating/gomory/makeintegral` | `bool` | {TRUE,FALSE} | FALSE | True | try to scale cuts to integral coefficients |
| `separating/gomory/forcecuts` | `bool` | {TRUE,FALSE} | TRUE | True | if conversion to integral coefficients failed still consider the cut |
| `separating/gomory/separaterows` | `bool` | {TRUE,FALSE} | TRUE | True | separate rows with integral slack |
| `separating/gomory/delayedcuts` | `bool` | {TRUE,FALSE} | FALSE | True | should cuts be added to the delayed cut pool? |
| `separating/gomory/sidetypebasis` | `bool` | {TRUE,FALSE} | TRUE | True | choose side types of row (lhs/rhs) based on basis information? |
| `separating/gomory/trystrongcg` | `bool` | {TRUE,FALSE} | TRUE | True | try to generate strengthened Chvatal-Gomory cuts? |
| `separating/gomory/genbothgomscg` | `bool` | {TRUE,FALSE} | TRUE | True | Should both Gomory and strong CG cuts be generated (otherwise take best)? |
| `separating/flowcover/priority` | `int` | [-536870912,536870911] | -100000 | True | priority of separator &lt;flowcover&gt; |
| `separating/flowcover/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;flowcover&gt; (-1: never, 0: only in root node) |
| `separating/flowcover/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;flowcover&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/flowcover/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/flowcover/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;flowcover&gt; is called (1: call at each multiple of frequency) |
| `separating/cmir/priority` | `int` | [-536870912,536870911] | -100000 | True | priority of separator &lt;cmir&gt; |
| `separating/cmir/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;cmir&gt; (-1: never, 0: only in root node) |
| `separating/cmir/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;cmir&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/cmir/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/cmir/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;cmir&gt; is called (1: call at each multiple of frequency) |
| `separating/knapsackcover/priority` | `int` | [-536870912,536870911] | -100000 | True | priority of separator &lt;knapsackcover&gt; |
| `separating/knapsackcover/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;knapsackcover&gt; (-1: never, 0: only in root node) |
| `separating/knapsackcover/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;knapsackcover&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/knapsackcover/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/knapsackcover/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;knapsackcover&gt; is called (1: call at each multiple of frequency) |
| `separating/aggregation/priority` | `int` | [-536870912,536870911] | -3000 | True | priority of separator &lt;aggregation&gt; |
| `separating/aggregation/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;aggregation&gt; (-1: never, 0: only in root node) |
| `separating/aggregation/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;aggregation&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/aggregation/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/aggregation/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;aggregation&gt; is called (1: call at each multiple of frequency) |
| `separating/aggregation/maxrounds` | `int` | [-1,2147483647] | -1 | False | maximal number of cmir separation rounds per node (-1: unlimited) |
| `separating/aggregation/maxroundsroot` | `int` | [-1,2147483647] | -1 | False | maximal number of cmir separation rounds in the root node (-1: unlimited) |
| `separating/aggregation/maxtries` | `int` | [-1,2147483647] | 200 | True | maximal number of rows to start aggregation with per separation round (-1: unlimited) |
| `separating/aggregation/maxtriesroot` | `int` | [-1,2147483647] | -1 | True | maximal number of rows to start aggregation with per separation round in the root node (-1: unlimited) |
| `separating/aggregation/maxfails` | `int` | [-1,2147483647] | 20 | True | maximal number of consecutive unsuccessful aggregation tries (-1: unlimited) |
| `separating/aggregation/maxfailsroot` | `int` | [-1,2147483647] | 100 | True | maximal number of consecutive unsuccessful aggregation tries in the root node (-1: unlimited) |
| `separating/aggregation/maxaggrs` | `int` | [0,2147483647] | 3 | True | maximal number of aggregations for each row per separation round |
| `separating/aggregation/maxaggrsroot` | `int` | [0,2147483647] | 6 | True | maximal number of aggregations for each row per separation round in the root node |
| `separating/aggregation/maxsepacuts` | `int` | [0,2147483647] | 100 | False | maximal number of cmir cuts separated per separation round |
| `separating/aggregation/maxsepacutsroot` | `int` | [0,2147483647] | 500 | False | maximal number of cmir cuts separated per separation round in the root node |
| `separating/aggregation/maxslack` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal slack of rows to be used in aggregation |
| `separating/aggregation/maxslackroot` | `real` | [0,1.79769313486232e+308] | 0.1 | True | maximal slack of rows to be used in aggregation in the root node |
| `separating/aggregation/densityscore` | `real` | [0,1.79769313486232e+308] | 0.0001 | True | weight of row density in the aggregation scoring of the rows |
| `separating/aggregation/slackscore` | `real` | [0,1.79769313486232e+308] | 0.001 | True | weight of slack in the aggregation scoring of the rows |
| `separating/aggregation/maxaggdensity` | `real` | [0,1] | 0.2 | True | maximal density of aggregated row |
| `separating/aggregation/maxrowdensity` | `real` | [0,1] | 0.05 | True | maximal density of row to be used in aggregation |
| `separating/aggregation/densityoffset` | `int` | [0,2147483647] | 100 | True | additional number of variables allowed in row on top of density |
| `separating/aggregation/maxrowfac` | `real` | [0,1.79769313486232e+308] | 10000 | True | maximal row aggregation factor |
| `separating/aggregation/maxtestdelta` | `int` | [-1,2147483647] | -1 | True | maximal number of different deltas to try (-1: unlimited) |
| `separating/aggregation/aggrtol` | `real` | [0,1.79769313486232e+308] | 0.01 | True | tolerance for bound distances used to select continuous variable in current aggregated constraint to be eliminated |
| `separating/aggregation/trynegscaling` | `bool` | {TRUE,FALSE} | TRUE | True | should negative values also be tested in scaling? |
| `separating/aggregation/fixintegralrhs` | `bool` | {TRUE,FALSE} | TRUE | True | should an additional variable be complemented if f0 = 0? |
| `separating/aggregation/dynamiccuts` | `bool` | {TRUE,FALSE} | TRUE | False | should generated cuts be removed from the LP if they are no longer tight? |
| `separating/clique/priority` | `int` | [-536870912,536870911] | -5000 | True | priority of separator &lt;clique&gt; |
| `separating/clique/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling separator &lt;clique&gt; (-1: never, 0: only in root node) |
| `separating/clique/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;clique&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/clique/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/clique/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;clique&gt; is called (1: call at each multiple of frequency) |
| `separating/clique/scaleval` | `real` | [1,1.79769313486232e+308] | 1000 | True | factor for scaling weights |
| `separating/clique/maxtreenodes` | `int` | [-1,2147483647] | 10000 | True | maximal number of nodes in branch and bound tree (-1: no limit) |
| `separating/clique/backtrackfreq` | `int` | [0,2147483647] | 1000 | True | frequency for premature backtracking up to tree level 1 (0: no backtracking) |
| `separating/clique/maxsepacuts` | `int` | [-1,2147483647] | 10 | False | maximal number of clique cuts separated per separation round (-1: no limit) |
| `separating/clique/maxzeroextensions` | `int` | [-1,2147483647] | 1000 | True | maximal number of zero-valued variables extending the clique (-1: no limit) |
| `separating/clique/cliquetablemem` | `real` | [0,2097151.99902344] | 20000 | True | maximal memory size of dense clique table (in kb) |
| `separating/clique/cliquedensity` | `real` | [0,1] | 0 | True | minimal density of cliques to use a dense clique table |
| `separating/zerohalf/priority` | `int` | [-536870912,536870911] | -6000 | True | priority of separator &lt;zerohalf&gt; |
| `separating/zerohalf/freq` | `int` | [-1,1073741822] | 10 | False | frequency for calling separator &lt;zerohalf&gt; (-1: never, 0: only in root node) |
| `separating/zerohalf/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;zerohalf&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/zerohalf/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/zerohalf/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;zerohalf&gt; is called (1: call at each multiple of frequency) |
| `separating/zerohalf/maxrounds` | `int` | [-1,2147483647] | 5 | False | maximal number of zerohalf separation rounds per node (-1: unlimited) |
| `separating/zerohalf/maxroundsroot` | `int` | [-1,2147483647] | 20 | False | maximal number of zerohalf separation rounds in the root node (-1: unlimited) |
| `separating/zerohalf/maxsepacuts` | `int` | [0,2147483647] | 20 | False | maximal number of zerohalf cuts separated per separation round |
| `separating/zerohalf/initseed` | `int` | [0,2147483647] | 24301 | False | initial seed used for random tie-breaking in cut selection |
| `separating/zerohalf/maxsepacutsroot` | `int` | [0,2147483647] | 100 | False | maximal number of zerohalf cuts separated per separation round in the root node |
| `separating/zerohalf/maxcutcands` | `int` | [0,2147483647] | 2000 | False | maximal number of zerohalf cuts considered per separation round |
| `separating/zerohalf/maxslack` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal slack of rows to be used in aggregation |
| `separating/zerohalf/maxslackroot` | `real` | [0,1.79769313486232e+308] | 0 | True | maximal slack of rows to be used in aggregation in the root node |
| `separating/zerohalf/goodscore` | `real` | [0,1] | 1 | True | threshold for score of cut relative to best score to be considered good, so that less strict filtering is applied |
| `separating/zerohalf/badscore` | `real` | [0,1] | 0.5 | True | threshold for score of cut relative to best score to be discarded |
| `separating/zerohalf/objparalweight` | `real` | [0,1] | 0 | True | weight of objective parallelism in cut score calculation |
| `separating/zerohalf/efficacyweight` | `real` | [0,1] | 1 | True | weight of efficacy in cut score calculation |
| `separating/zerohalf/dircutoffdistweight` | `real` | [0,1] | 0 | True | weight of directed cutoff distance in cut score calculation |
| `separating/zerohalf/goodmaxparall` | `real` | [0,1] | 0.1 | True | maximum parallelism for good cuts |
| `separating/zerohalf/maxparall` | `real` | [0,1] | 0.1 | True | maximum parallelism for non-good cuts |
| `separating/zerohalf/minviol` | `real` | [0,1.79769313486232e+308] | 0.1 | True | minimal violation to generate zerohalfcut for |
| `separating/zerohalf/dynamiccuts` | `bool` | {TRUE,FALSE} | TRUE | False | should generated cuts be removed from the LP if they are no longer tight? |
| `separating/zerohalf/maxrowdensity` | `real` | [0,1] | 0.05 | True | maximal density of row to be used in aggregation |
| `separating/zerohalf/densityoffset` | `int` | [0,2147483647] | 100 | True | additional number of variables allowed in row on top of density |
| `separating/lagromory/priority` | `int` | [-536870912,536870911] | -8000 | True | priority of separator &lt;lagromory&gt; |
| `separating/lagromory/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling separator &lt;lagromory&gt; (-1: never, 0: only in root node) |
| `separating/lagromory/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;lagromory&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/lagromory/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/lagromory/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;lagromory&gt; is called (1: call at each multiple of frequency) |
| `separating/lagromory/away` | `real` | [0,1] | 0.01 | False | minimal integrality violation of a basis variable to try separation |
| `separating/lagromory/rootlpiterlimitfactor` | `real` | [-1,1.79769313486232e+308] | -1 | True | factor w.r.t. root node LP iterations for maximal separating LP iterations in the root node (negative for no limit) |
| `separating/lagromory/totallpiterlimitfactor` | `real` | [-1,1.79769313486232e+308] | -1 | True | factor w.r.t. root node LP iterations for maximal separating LP iterations in the tree (negative for no limit) |
| `separating/lagromory/perroundlpiterlimitfactor` | `real` | [-1,1.79769313486232e+308] | -1 | True | factor w.r.t. root node LP iterations for maximal separating LP iterations per separation round (negative for no limit) |
| `separating/lagromory/perroundcutsfactorroot` | `real` | [0,1.79769313486232e+308] | 1 | True | factor w.r.t. number of integer columns for number of cuts separated per separation round in root node |
| `separating/lagromory/perroundcutsfactor` | `real` | [0,1.79769313486232e+308] | 0.5 | True | factor w.r.t. number of integer columns for number of cuts separated per separation round at a non-root node |
| `separating/lagromory/totalcutsfactor` | `real` | [0,1.79769313486232e+308] | 50 | True | factor w.r.t. number of integer columns for total number of cuts separated |
| `separating/lagromory/muparaminit` | `real` | [0,100] | 0.01 | True | initial value of the mu parameter (factor for step length) |
| `separating/lagromory/muparamlb` | `real` | [0,1] | 0 | True | lower bound of the mu parameter (factor for step length) |
| `separating/lagromory/muparamub` | `real` | [1,10] | 2 | True | upper bound of the mu parameter (factor for step length) |
| `separating/lagromory/mubacktrackfactor` | `real` | [0,1] | 0.5 | True | factor of mu while backtracking the mu parameter (factor for step length) |
| `separating/lagromory/muslab1factor` | `real` | [0,1.79769313486232e+308] | 10 | True | factor of mu parameter (factor for step length) for larger increment |
| `separating/lagromory/muslab2factor` | `real` | [0,1.79769313486232e+308] | 2 | True | factor of mu parameter (factor for step length) for smaller increment |
| `separating/lagromory/muslab3factor` | `real` | [0,1.79769313486232e+308] | 0.5 | True | factor of mu parameter (factor for step length) for reduction |
| `separating/lagromory/deltaslab1ub` | `real` | [0,1] | 0.001 | True | factor of delta deciding larger increment of mu parameter (factor for step length) |
| `separating/lagromory/deltaslab2ub` | `real` | [0,1] | 0.01 | True | factor of delta deciding smaller increment of mu parameter (factor for step length) |
| `separating/lagromory/ubparamposfactor` | `real` | [1,100] | 2 | True | factor for positive upper bound used as an estimate for the optimal Lagrangian dual value |
| `separating/lagromory/ubparamnegfactor` | `real` | [0,1] | 0.5 | True | factor for negative upper bound used as an estimate for the optimal Lagrangian dual value |
| `separating/lagromory/perrootlpiterfactor` | `real` | [-1,1.79769313486232e+308] | 0.2 | True | factor w.r.t. root node LP iterations for iteration limit of each separating LP (negative for no limit) |
| `separating/lagromory/perlpiterfactor` | `real` | [-1,1.79769313486232e+308] | 0.1 | True | factor w.r.t. non-root node LP iterations for iteration limit of each separating LP (negative for no limit) |
| `separating/lagromory/cutsfilterfactor` | `real` | [0,1] | 1 | True | fraction of generated cuts per explored basis to accept from separator |
| `separating/lagromory/radiusinit` | `real` | [0,1] | 0.5 | True | initial radius of the ball used in stabilization of Lagrangian multipliers |
| `separating/lagromory/radiusmax` | `real` | [0,1.79769313486232e+308] | 20 | True | maximum radius of the ball used in stabilization of Lagrangian multipliers |
| `separating/lagromory/radiusmin` | `real` | [0,1.79769313486232e+308] | 1e-06 | True | minimum radius of the ball used in stabilization of Lagrangian multipliers |
| `separating/lagromory/constant` | `real` | [2,1.79769313486232e+308] | 2 | True | a constant for stablity center based stabilization of Lagrangian multipliers |
| `separating/lagromory/radiusupdateweight` | `real` | [0,1] | 0.98 | True | multiplier to evaluate cut violation score used for updating ball radius |
| `separating/lagromory/dualdegeneracyratethreshold` | `real` | [0,1] | 0.5 | False | minimum dual degeneracy rate for separator execution |
| `separating/lagromory/varconsratiothreshold` | `real` | [1,1.79769313486232e+308] | 1 | False | minimum variable-constraint ratio on optimal face for separator execution |
| `separating/lagromory/muparamconst` | `bool` | {TRUE,FALSE} | TRUE | True | is the mu parameter (factor for step length) constant? |
| `separating/lagromory/separaterows` | `bool` | {TRUE,FALSE} | TRUE | True | separate rows with integral slack? |
| `separating/lagromory/sortcutoffsol` | `bool` | {TRUE,FALSE} | TRUE | True | sort fractional integer columnsbased on fractionality? |
| `separating/lagromory/sidetypebasis` | `bool` | {TRUE,FALSE} | TRUE | True | choose side types of row (lhs/rhs) based on basis information? |
| `separating/lagromory/dynamiccuts` | `bool` | {TRUE,FALSE} | TRUE | False | should generated cuts be removed from LP if they are no longer tight? |
| `separating/lagromory/makeintegral` | `bool` | {TRUE,FALSE} | FALSE | True | try to scale all cuts to integral coefficients? |
| `separating/lagromory/forcecuts` | `bool` | {TRUE,FALSE} | FALSE | True | force cuts to be added to the LP? |
| `separating/lagromory/delayedcuts` | `bool` | {TRUE,FALSE} | FALSE | True | should cuts be added to the delayed cut pool |
| `separating/lagromory/allowlocal` | `bool` | {TRUE,FALSE} | FALSE | True | should locally valid cuts be generated? |
| `separating/lagromory/aggregatecuts` | `bool` | {TRUE,FALSE} | TRUE | True | aggregate all generated cuts using the Lagrangian multipliers? |
| `separating/lagromory/maxrounds` | `int` | [-1,2147483647] | 1 | False | maximal number of separation rounds per node (-1: unlimited) |
| `separating/lagromory/maxroundsroot` | `int` | [-1,2147483647] | 1 | False | maximal number of separation rounds in the root node (-1: unlimited) |
| `separating/lagromory/perroundnmaxlpiters` | `int` | [-1,2147483647] | 50000 | False | maximal number of separating LP iterations per separation round (-1: unlimited) |
| `separating/lagromory/nmaxcutsperlp` | `int` | [0,2147483647] | 10 | False | maximal number of cuts separated per Lagromory LP in the non-root node |
| `separating/lagromory/nmaxcutsperlproot` | `int` | [0,2147483647] | 50 | False | maximal number of cuts separated per Lagromory LP in the root node |
| `separating/lagromory/nmaxmainiters` | `int` | [0,2147483647] | 4 | True | maximal number of main loop iterations of the relax-and-cut algorithm |
| `separating/lagromory/nmaxsubgradientiters` | `int` | [0,2147483647] | 6 | True | maximal number of subgradient loop iterations of the relax-and-cut algorithm |
| `separating/lagromory/cutgenfreq` | `int` | [0,2147483647] | 1 | True | frequency of subgradient iterations for generating cuts |
| `separating/lagromory/cutaddfreq` | `int` | [0,2147483647] | 1 | True | frequency of subgradient iterations for adding cuts to objective function |
| `separating/lagromory/nmaxlagrangianvalsforavg` | `int` | [0,2147483647] | 2 | True | maximal number of iterations for rolling average of Lagrangian value |
| `separating/lagromory/nmaxconsecitersformuupdate` | `int` | [0,2147483647] | 10 | True | consecutive number of iterations used to determine if mu needs to be backtracked |
| `separating/lagromory/projectiontype` | `int` | [0,3] | 2 | True | the ball into which the Lagrangian multipliers are projected for stabilization (0: no projection, 1: L1-norm ball projection, 2: L2-norm ball projection, 3: L_inf-norm ball projection) |
| `separating/lagromory/stabilitycentertype` | `int` | [0,1] | 1 | True | type of stability center for taking weighted average of Lagrangian multipliers for stabilization (0: no weighted stabilization, 1: best Lagrangian multipliers) |
| `separating/lagromory/optimalfacepriority` | `int` | [0,2] | 2 | True | priority of the optimal face for separator execution (0: low priority, 1: medium priority, 2: high priority) |
| `separating/lagromory/minrestart` | `int` | [0,2147483647] | 1 | True | minimum restart round for separator execution (0: from beginning of the instance solving, &gt;= n with n &gt;= 1: from restart round n) |
| `separating/mcf/priority` | `int` | [-536870912,536870911] | -10000 | True | priority of separator &lt;mcf&gt; |
| `separating/mcf/freq` | `int` | [-1,1073741822] | 0 | False | frequency for calling separator &lt;mcf&gt; (-1: never, 0: only in root node) |
| `separating/mcf/maxbounddist` | `real` | [0,1] | 0 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;mcf&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/mcf/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/mcf/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;mcf&gt; is called (1: call at each multiple of frequency) |
| `separating/mcf/nclusters` | `int` | [2,32] | 5 | True | number of clusters to generate in the shrunken network -- default separation |
| `separating/mcf/maxweightrange` | `real` | [1,1.79769313486232e+308] | 1000000 | True | maximal valid range max(&#124;weights&#124;)/min(&#124;weights&#124;) of row weights |
| `separating/mcf/maxtestdelta` | `int` | [-1,2147483647] | 20 | True | maximal number of different deltas to try (-1: unlimited)  -- default separation |
| `separating/mcf/trynegscaling` | `bool` | {TRUE,FALSE} | FALSE | True | should negative values also be tested in scaling? |
| `separating/mcf/fixintegralrhs` | `bool` | {TRUE,FALSE} | TRUE | True | should an additional variable be complemented if f0 = 0? |
| `separating/mcf/dynamiccuts` | `bool` | {TRUE,FALSE} | TRUE | False | should generated cuts be removed from the LP if they are no longer tight? |
| `separating/mcf/modeltype` | `int` | [0,2] | 0 | True | model type of network (0: auto, 1:directed, 2:undirected) |
| `separating/mcf/maxsepacuts` | `int` | [-1,2147483647] | 100 | False | maximal number of mcf cuts separated per separation round |
| `separating/mcf/maxsepacutsroot` | `int` | [-1,2147483647] | 200 | False | maximal number of mcf cuts separated per separation round in the root node  -- default separation |
| `separating/mcf/maxinconsistencyratio` | `real` | [0,1.79769313486232e+308] | 0.02 | True | maximum inconsistency ratio for separation at all |
| `separating/mcf/maxarcinconsistencyratio` | `real` | [0,1.79769313486232e+308] | 0.5 | True | maximum inconsistency ratio of arcs not to be deleted |
| `separating/mcf/checkcutshoreconnectivity` | `bool` | {TRUE,FALSE} | TRUE | True | should we separate only if the cuts shores are connected? |
| `separating/mcf/separatesinglenodecuts` | `bool` | {TRUE,FALSE} | TRUE | True | should we separate inequalities based on single-node cuts? |
| `separating/mcf/separateflowcutset` | `bool` | {TRUE,FALSE} | TRUE | True | should we separate flowcutset inequalities on the network cuts? |
| `separating/mcf/separateknapsack` | `bool` | {TRUE,FALSE} | TRUE | True | should we separate knapsack cover inequalities on the network cuts? |
| `separating/eccuts/priority` | `int` | [-536870912,536870911] | -13000 | True | priority of separator &lt;eccuts&gt; |
| `separating/eccuts/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling separator &lt;eccuts&gt; (-1: never, 0: only in root node) |
| `separating/eccuts/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;eccuts&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/eccuts/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/eccuts/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;eccuts&gt; is called (1: call at each multiple of frequency) |
| `separating/eccuts/dynamiccuts` | `bool` | {TRUE,FALSE} | TRUE | False | should generated cuts be removed from the LP if they are no longer tight? |
| `separating/eccuts/maxrounds` | `int` | [-1,2147483647] | 10 | False | maximal number of eccuts separation rounds per node (-1: unlimited) |
| `separating/eccuts/maxroundsroot` | `int` | [-1,2147483647] | 250 | False | maximal number of eccuts separation rounds in the root node (-1: unlimited) |
| `separating/eccuts/maxdepth` | `int` | [-1,2147483647] | -1 | False | maximal depth at which the separator is applied (-1: unlimited) |
| `separating/eccuts/maxsepacuts` | `int` | [0,2147483647] | 10 | False | maximal number of edge-concave cuts separated per separation round |
| `separating/eccuts/maxsepacutsroot` | `int` | [0,2147483647] | 50 | False | maximal number of edge-concave cuts separated per separation round in the root node |
| `separating/eccuts/cutmaxrange` | `real` | [0,1e+20] | 10000000 | False | maximal coef. range of a cut (max coef. divided by min coef.) in order to be added to LP relaxation |
| `separating/eccuts/minviolation` | `real` | [0,0.5] | 0.3 | False | minimal violation of an edge-concave cut to be separated |
| `separating/eccuts/minaggrsize` | `int` | [3,5] | 3 | True | search for edge-concave aggregations of at least this size |
| `separating/eccuts/maxaggrsize` | `int` | [3,5] | 4 | True | search for edge-concave aggregations of at most this size |
| `separating/eccuts/maxbilinterms` | `int` | [0,2147483647] | 500 | True | maximum number of bilinear terms allowed to be in a quadratic constraint |
| `separating/eccuts/maxstallrounds` | `int` | [0,2147483647] | 5 | True | maximum number of unsuccessful rounds in the edge-concave aggregation search |
| `separating/oddcycle/priority` | `int` | [-536870912,536870911] | -15000 | True | priority of separator &lt;oddcycle&gt; |
| `separating/oddcycle/freq` | `int` | [-1,1073741822] | -1 | False | frequency for calling separator &lt;oddcycle&gt; (-1: never, 0: only in root node) |
| `separating/oddcycle/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;oddcycle&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/oddcycle/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/oddcycle/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;oddcycle&gt; is called (1: call at each multiple of frequency) |
| `separating/oddcycle/usegls` | `bool` | {TRUE,FALSE} | TRUE | False | Should the search method by Groetschel, Lovasz, Schrijver be used? Otherwise use levelgraph method by Hoffman, Padberg. |
| `separating/oddcycle/liftoddcycles` | `bool` | {TRUE,FALSE} | FALSE | False | Should odd cycle cuts be lifted? |
| `separating/oddcycle/maxsepacuts` | `int` | [0,2147483647] | 5000 | False | maximal number of oddcycle cuts separated per separation round |
| `separating/oddcycle/maxsepacutsroot` | `int` | [0,2147483647] | 5000 | False | maximal number of oddcycle cuts separated per separation round in the root node |
| `separating/oddcycle/maxrounds` | `int` | [-1,2147483647] | 10 | False | maximal number of oddcycle separation rounds per node (-1: unlimited) |
| `separating/oddcycle/maxroundsroot` | `int` | [-1,2147483647] | 10 | False | maximal number of oddcycle separation rounds in the root node (-1: unlimited) |
| `separating/oddcycle/scalingfactor` | `int` | [1,2147483647] | 1000 | True | factor for scaling of the arc-weights |
| `separating/oddcycle/addselfarcs` | `bool` | {TRUE,FALSE} | TRUE | True | add links between a variable and its negated |
| `separating/oddcycle/repaircycles` | `bool` | {TRUE,FALSE} | TRUE | True | try to repair violated cycles with double appearance of a variable |
| `separating/oddcycle/includetriangles` | `bool` | {TRUE,FALSE} | TRUE | True | separate triangles found as 3-cycles or repaired larger cycles |
| `separating/oddcycle/multiplecuts` | `bool` | {TRUE,FALSE} | FALSE | True | Even if a variable is already covered by a cut, still try it as start node for a cycle search? |
| `separating/oddcycle/allowmultiplecuts` | `bool` | {TRUE,FALSE} | TRUE | True | Even if a variable is already covered by a cut, still allow another cut to cover it too? |
| `separating/oddcycle/lpliftcoef` | `bool` | {TRUE,FALSE} | FALSE | True | Choose lifting candidate by coef*lpvalue or only by coef? |
| `separating/oddcycle/recalcliftcoef` | `bool` | {TRUE,FALSE} | TRUE | True | Calculate lifting coefficient of every candidate in every step (or only if its chosen)? |
| `separating/oddcycle/sortswitch` | `int` | [0,4] | 3 | True | use sorted variable array (unsorted(0), maxlp(1), minlp(2), maxfrac(3), minfrac(4)) |
| `separating/oddcycle/sortrootneighbors` | `bool` | {TRUE,FALSE} | TRUE | True | sort level of the root neighbors by fractionality (maxfrac) |
| `separating/oddcycle/percenttestvars` | `int` | [0,100] | 0 | True | percentage of variables to try the chosen method on [0-100] |
| `separating/oddcycle/offsettestvars` | `int` | [0,2147483647] | 100 | True | offset of variables to try the chosen method on (additional to the percentage of testvars) |
| `separating/oddcycle/maxpernodeslevel` | `int` | [0,100] | 100 | True | percentage of nodes allowed in the same level of the level graph [0-100] |
| `separating/oddcycle/offsetnodeslevel` | `int` | [0,2147483647] | 10 | True | offset of nodes allowed in the same level of the level graph (additional to the percentage of levelnodes) |
| `separating/oddcycle/maxnlevels` | `int` | [0,2147483647] | 20 | True | maximal number of levels in level graph |
| `separating/oddcycle/maxcutsroot` | `int` | [0,2147483647] | 1 | True | maximal number of oddcycle cuts generated per chosen variable as root of the level graph |
| `separating/oddcycle/maxcutslevel` | `int` | [0,2147483647] | 50 | True | maximal number of oddcycle cuts generated in every level of the level graph |
| `separating/oddcycle/maxreference` | `int` | [0,2147483647] | 0 | True | minimal weight on an edge (in level graph or bipartite graph) |
| `separating/oddcycle/maxunsucessfull` | `int` | [0,2147483647] | 3 | True | number of unsuccessful calls at current node |
| `separating/oddcycle/cutthreshold` | `int` | [-1,2147483647] | -1 | True | maximal number of other cuts s.t. separation is applied (-1 for direct call) |
| `separating/rapidlearning/priority` | `int` | [-536870912,536870911] | -1200000 | True | priority of separator &lt;rapidlearning&gt; |
| `separating/rapidlearning/freq` | `int` | [-1,1073741822] | 5 | False | frequency for calling separator &lt;rapidlearning&gt; (-1: never, 0: only in root node) |
| `separating/rapidlearning/maxbounddist` | `real` | [0,1] | 1 | True | maximal relative distance from current node's dual bound to primal bound compared to best node's dual bound for applying separator &lt;rapidlearning&gt; (0.0: only on current best node, 1.0: on all nodes) |
| `separating/rapidlearning/delay` | `bool` | {TRUE,FALSE} | FALSE | True | should separator be delayed, if other separators found cuts? |
| `separating/rapidlearning/expbackoff` | `int` | [1,100] | 4 | True | base for exponential increase of frequency at which separator &lt;rapidlearning&gt; is called (1: call at each multiple of frequency) |
| `separating/rapidlearning/applyconflicts` | `bool` | {TRUE,FALSE} | TRUE | True | should the found conflicts be applied in the original SCIP? |
| `separating/rapidlearning/applybdchgs` | `bool` | {TRUE,FALSE} | TRUE | True | should the found global bound deductions be applied in the original SCIP? |
| `separating/rapidlearning/applyinfervals` | `bool` | {TRUE,FALSE} | TRUE | True | should the inference values be used as initialization in the original SCIP? |
| `separating/rapidlearning/reducedinfer` | `bool` | {TRUE,FALSE} | FALSE | True | should the inference values only be used when rapidlearning found other reductions? |
| `separating/rapidlearning/applyprimalsol` | `bool` | {TRUE,FALSE} | TRUE | True | should the incumbent solution be copied to the original SCIP? |
| `separating/rapidlearning/applysolved` | `bool` | {TRUE,FALSE} | TRUE | True | should a solved status be copied to the original SCIP? |
| `separating/rapidlearning/checkdegeneracy` | `bool` | {TRUE,FALSE} | TRUE | True | should local LP degeneracy be checked? |
| `separating/rapidlearning/checkdualbound` | `bool` | {TRUE,FALSE} | FALSE | True | should the progress on the dual bound be checked? |
| `separating/rapidlearning/checkleaves` | `bool` | {TRUE,FALSE} | FALSE | True | should the ratio of leaves proven to be infeasible and exceeding the cutoff bound be checked? |
| `separating/rapidlearning/checkexec` | `bool` | {TRUE,FALSE} | TRUE | True | check whether rapid learning should be executed |
| `separating/rapidlearning/checkobj` | `bool` | {TRUE,FALSE} | FALSE | True | should the (local) objective function be checked? |
| `separating/rapidlearning/checknsols` | `bool` | {TRUE,FALSE} | TRUE | True | should the number of solutions found so far be checked? |
| `separating/rapidlearning/contvars` | `bool` | {TRUE,FALSE} | FALSE | True | should rapid learning be applied when there are continuous variables? |
| `separating/rapidlearning/contvarsquot` | `real` | [0,1] | 0.3 | True | maximal portion of continuous variables to apply rapid learning |
| `separating/rapidlearning/lpiterquot` | `real` | [0,1.79769313486232e+308] | 0.2 | True | maximal fraction of LP iterations compared to node LP iterations |
| `separating/rapidlearning/mindegeneracy` | `real` | [0,1] | 0.7 | True | minimal degeneracy threshold to allow local rapid learning |
| `separating/rapidlearning/mininflpratio` | `real` | [0,1.79769313486232e+308] | 10 | True | minimal threshold of inf/obj leaves to allow local rapid learning |
| `separating/rapidlearning/minvarconsratio` | `real` | [1,1.79769313486232e+308] | 2 | True | minimal ratio of unfixed variables in relation to basis size to allow local rapid learning |
| `separating/rapidlearning/maxnvars` | `int` | [0,2147483647] | 10000 | True | maximum problem size (variables) for which rapid learning will be called |
| `separating/rapidlearning/maxnconss` | `int` | [0,2147483647] | 10000 | True | maximum problem size (constraints) for which rapid learning will be called |
| `separating/rapidlearning/maxcalls` | `int` | [0,2147483647] | 100 | True | maximum number of overall calls |
| `separating/rapidlearning/maxnodes` | `int` | [0,2147483647] | 5000 | True | maximum number of nodes considered in rapid learning run |
| `separating/rapidlearning/minnodes` | `int` | [0,2147483647] | 500 | True | minimum number of nodes considered in rapid learning run |
| `separating/rapidlearning/nwaitingnodes` | `longint` | [0,9223372036854775807] | 100 | True | number of nodes that should be processed before rapid learning is executed locally based on the progress of the dualbound |
| `separating/rapidlearning/copycuts` | `bool` | {TRUE,FALSE} | TRUE | True | should all active cuts from cutpool be copied to constraints in subproblem? |

## solvingphases

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `solvingphases/enabled` | `bool` | {TRUE,FALSE} | FALSE | False | should the event handler adapt the solver behavior? |
| `solvingphases/testmode` | `bool` | {TRUE,FALSE} | FALSE | False | should the event handler test all phase transitions? |
| `solvingphases/feassetname` | `string` | String; interpretation stated in description | "-" | False | settings file for feasibility phase -- precedence over emphasis settings |
| `solvingphases/improvesetname` | `string` | String; interpretation stated in description | "-" | False | settings file for improvement phase -- precedence over emphasis settings |
| `solvingphases/proofsetname` | `string` | String; interpretation stated in description | "-" | False | settings file for proof phase -- precedence over emphasis settings |
| `solvingphases/nodeoffset` | `longint` | [1,9223372036854775807] | 50 | False | node offset for rank-1 and estimate transitions |
| `solvingphases/fallback` | `bool` | {TRUE,FALSE} | FALSE | False | should the event handler fall back from optimal phase? |
| `solvingphases/transitionmethod` | `char` | {elor} | r | False | transition method: Possible options are 'e'stimate,'l'ogarithmic regression,'o'ptimal-value based,'r'ank-1 |
| `solvingphases/interruptoptimal` | `bool` | {TRUE,FALSE} | FALSE | False | should the event handler interrupt the solving process after optimal solution was found? |
| `solvingphases/userestart1to2` | `bool` | {TRUE,FALSE} | FALSE | False | should a restart be applied between the feasibility and improvement phase? |
| `solvingphases/userestart2to3` | `bool` | {TRUE,FALSE} | FALSE | False | should a restart be applied between the improvement and the proof phase? |
| `solvingphases/optimalvalue` | `real` | [-1.79769313486232e+308,1.79769313486232e+308] | 1e+99 | False | optimal solution value for problem |
| `solvingphases/xtype` | `char` | {lnt} | n | False | x-type for logarithmic regression - (t)ime, (n)odes, (l)p iterations |
| `solvingphases/useemphsettings` | `bool` | {TRUE,FALSE} | TRUE | False | should emphasis settings for the solving phases be used, or settings files? |

## table

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `table/cons_nonlinear/active` | `bool` | {TRUE,FALSE} | FALSE | False | is statistics table &lt;cons_nonlinear&gt; active |
| `table/nlhdlr/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;nlhdlr&gt; active |
| `table/nlhdlr_bilinear/active` | `bool` | {TRUE,FALSE} | FALSE | False | is statistics table &lt;nlhdlr_bilinear&gt; active |
| `table/nlhdlr_quadratic/active` | `bool` | {TRUE,FALSE} | FALSE | False | is statistics table &lt;nlhdlr_quadratic&gt; active |
| `table/estim/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;estim&gt; active |
| `table/scheduler/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;scheduler&gt; active |
| `table/neighborhood/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;neighborhood&gt; active |
| `table/symmetry/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;symmetry&gt; active |
| `table/status/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;status&gt; active |
| `table/timing/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;timing&gt; active |
| `table/origprob/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;origprob&gt; active |
| `table/presolvedprob/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;presolvedprob&gt; active |
| `table/presolver/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;presolver&gt; active |
| `table/constraint/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;constraint&gt; active |
| `table/constiming/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;constiming&gt; active |
| `table/propagator/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;propagator&gt; active |
| `table/conflict/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;conflict&gt; active |
| `table/separator/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;separator&gt; active |
| `table/cutsel/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;cutsel&gt; active |
| `table/pricer/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;pricer&gt; active |
| `table/branchrules/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;branchrules&gt; active |
| `table/heuristics/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;heuristics&gt; active |
| `table/compression/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;compression&gt; active |
| `table/benders/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;benders&gt; active |
| `table/exprhdlr/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;exprhdlr&gt; active |
| `table/lp/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;lp&gt; active |
| `table/nlp/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;nlp&gt; active |
| `table/nlpi/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;nlpi&gt; active |
| `table/relaxator/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;relaxator&gt; active |
| `table/tree/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;tree&gt; active |
| `table/root/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;root&gt; active |
| `table/solution/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;solution&gt; active |
| `table/concurrentsolver/active` | `bool` | {TRUE,FALSE} | TRUE | False | is statistics table &lt;concurrentsolver&gt; active |

## timing

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `timing/clocktype` | `int` | [1,2] | 2 | False | default clock type (1: CPU user seconds, 2: wall clock time) |
| `timing/enabled` | `bool` | {TRUE,FALSE} | TRUE | False | is timing enabled? |
| `timing/reading` | `bool` | {TRUE,FALSE} | FALSE | False | belongs reading time to solving time? |
| `timing/rareclockcheck` | `bool` | {TRUE,FALSE} | FALSE | False | should clock checks of solving time be performed less frequently (note: time limit could be exceeded slightly) |
| `timing/statistictiming` | `bool` | {TRUE,FALSE} | TRUE | False | should timing for statistic output be performed? |
| `timing/nlpieval` | `bool` | {TRUE,FALSE} | FALSE | False | should time for evaluation in NLP solves be measured? |

## visual

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `visual/vbcfilename` | `string` | String; interpretation stated in description | "-" | False | name of the VBC tool output file, or - if no VBC tool output should be created |
| `visual/bakfilename` | `string` | String; interpretation stated in description | "-" | False | name of the BAK tool output file, or - if no BAK tool output should be created |
| `visual/realtime` | `bool` | {TRUE,FALSE} | TRUE | False | should the real solving time be used instead of a time step counter in visualization? |
| `visual/dispsols` | `bool` | {TRUE,FALSE} | FALSE | False | should the node where solutions are found be visualized? |
| `visual/displb` | `bool` | {TRUE,FALSE} | FALSE | False | should lower bound information be visualized? |
| `visual/objextern` | `bool` | {TRUE,FALSE} | TRUE | False | should be output the external value of the objective? |

## write

| Parameter | Type | Allowed values | Default | Advanced | Meaning |
| --- | --- | --- | --- | --- | --- |
| `write/allconss` | `bool` | {TRUE,FALSE} | FALSE | False | should all constraints be written (including the redundant constraints)? |
| `write/printzeros` | `bool` | {TRUE,FALSE} | FALSE | False | should variables set to zero be printed? |
| `write/genericnamesoffset` | `int` | [0,1073741823] | 0 | False | when writing a generic problem the index for the first variable should start with? |
| `write/implintlevel` | `int` | [-2,2] | 0 | False | should integrality constraints (i.c.) be written for implied integral variables? (0: use original i.c., 1: add i.c. to strongly implied integral vars, 2: add i.c. to all implied integral vars, -1: remove i.c. from strongly implied integral vars, -2: remove i.c. from all implied integral vars) |
