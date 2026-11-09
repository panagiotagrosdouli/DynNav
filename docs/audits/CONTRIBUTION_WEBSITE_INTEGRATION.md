# Contribution Website Integration Review

`app/pages/09_Contribution_Explorer.py` loads the canonical registry and dispatches through `src/dynnav_dashboard/contributions/RENDERERS`; all C01-C26 currently have registered renderers. A legacy `c11_twin_critic_rl.py` remains alongside the canonical C11 VLM renderer and should not be mistaken for the current registered C11 topic.

The public Next.js explorer displays C01-C26, C00 core framing, maturity filters and synthetic evidence boundaries. This audit changed cards to link directly to each canonical contribution directory and registered experiment runner, and added C27 as a separate research proposal card linking to its current review. The static site has no experiment-launch backend, so links point to reproducible source rather than pretending to run remote experiments.

Source review is complete; a production web build has not yet been run after these changes. Main Web Portal and Streamlit Dashboard checks were green for the base merge commit, before this branch. No unverified measurement plots are presented as live results.
