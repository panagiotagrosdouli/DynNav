# State-only aliasing lower bound

This note isolates the elementary information-theoretic consequence behind the same-state/different-history benchmark. It is a supporting proposition, not a novelty claim.

## Proposition

Let two executable histories, `h1` and `h2`, terminate at the same geometric state `x`. Suppose their true history-conditioned safe-return reliabilities are `R1` and `R2`, with `R1 != R2`. Any deterministic estimator `g(x)` that is state-only at that endpoint must satisfy

`max(|g(x)-R1|, |g(x)-R2|) >= |R1-R2| / 2`.

## Proof

By the triangle inequality,

`|R1-R2| <= |R1-g(x)| + |g(x)-R2|`.

If both absolute errors were strictly smaller than `|R1-R2|/2`, their sum would be strictly smaller than `|R1-R2|`, contradicting the inequality. Therefore at least one history must incur error at least half the history separation.

## Consequence for the counterfactual benchmark

In the controlled bridge example,

- safe history: `R1 = 1`,
- trigger-taking history: `R2 = 1-p`,
- history separation: `|R1-R2| = p`.

Therefore every state-only endpoint estimator has worst-history error at least `p/2`.

The particular marginal baseline used in the executable benchmark returns `g(x)=1-p` for both histories. It therefore has:

- risky-history error `0`,
- safe-history error `p`,
- worst-history error `p`, which is above the minimax lower bound `p/2`.

The lower bound is stronger than reporting the behavior of one chosen state-only baseline because it applies to **any** deterministic state-only scalar estimate at the aliased endpoint. It does not imply that history-aware planning is globally optimal or novel; it only formalizes the information loss caused by collapsing histories with different return reliability into one geometric state.

## Scope

The statement assumes that the state-only estimator has no additional latent variable, belief state, automaton state, or memory that distinguishes the histories. Once such information is added, the representation is no longer state-only in the sense used here.
