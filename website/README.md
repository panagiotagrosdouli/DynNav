# DynNav research website

This directory contains the Next.js research landing page.

**Status:** Website build is **Implemented** and checked by GitHub Actions. The site is documentation and presentation software; it is not a robotics runtime, safety monitor, ROS2 node, or experimental result.

## Development

```bash
cd website
npm install --no-audit --no-fund
npm run dev
```

## Required checks

```bash
npm run typecheck
npm run build
```

The current CI uses Node 22. Package versions are pinned in [`package.json`](package.json). A reproducible `npm ci` workflow requires a committed lockfile and remains **Pending Validation** unless the lockfile is present and CI uses it.

## Content policy

- Describe only capabilities present in the repository.
- Label synthetic benchmarks and prototype features explicitly.
- Do not claim ROS2/Nav2 loading, Gazebo runs, hardware tests, formal verification, or safety guarantees without linked evidence.
- Keep media links consistent with [`../assets/`](../assets/README.md) and generated outputs under [`../results/`](../results/README.md).

See the [root README](../README.md) and [`../docs/README.md`](../docs/README.md).
