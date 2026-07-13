"use client";

import { motion } from "framer-motion";

const pipeline = [
  "Scenario or sensor input",
  "Occupancy belief grid",
  "Uncertainty propagation",
  "Risk and recoverability fields",
  "Planner switching",
  "Risk-aware trajectory",
  "Runtime monitor",
  "Reroute, safe mode, or continue",
];

const benchmarks = [
  { metric: "Path success", status: "synthetic benchmark", output: "CSV + summary" },
  { metric: "Mission risk", status: "implemented estimator", output: "tables + plots" },
  { metric: "Recoverability", status: "prototype", output: "sampled return paths" },
  { metric: "Runtime mode", status: "implemented monitor", output: "timeline" },
];

const roadmap = [
  "Add hardware logs and ROS2 bag replay",
  "Calibrate risk thresholds with ablation studies",
  "Add learned local policy baselines",
  "Publish reproducible benchmark tables",
];

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto max-w-6xl px-6 py-24">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}>
          <p className="text-sm uppercase tracking-[0.35em] text-cyan-300">DynNav</p>
          <h1 className="mt-6 text-5xl font-semibold tracking-tight md:text-7xl">
            Risk-aware dynamic navigation in unknown environments
          </h1>
          <p className="mt-6 max-w-3xl text-lg text-slate-300">
            A reproducible research prototype for uncertainty-aware planning,
            recoverability estimation, online rerouting, and runtime safety monitoring.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <a className="rounded-full bg-cyan-300 px-5 py-3 font-medium text-slate-950" href="https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments">
              GitHub repository
            </a>
            <a className="rounded-full border border-slate-600 px-5 py-3" href="/demo.gif">
              Demo GIF
            </a>
          </div>
        </motion.div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 pb-20 md:grid-cols-2">
        <motion.article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6" whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 16 }} viewport={{ once: true }}>
          <h2 className="text-2xl font-semibold">Research motivation</h2>
          <p className="mt-3 leading-7 text-slate-300">
            DynNav studies navigation decisions where the shortest path is not necessarily the safest path.
            The stack explicitly models obstacle belief, uncertainty pressure, returnability, and mission risk.
          </p>
        </motion.article>
        <motion.article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6" whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 16 }} viewport={{ once: true }}>
          <h2 className="text-2xl font-semibold">Architecture</h2>
          <p className="mt-3 leading-7 text-slate-300">
            Core algorithms are ROS-independent Python modules. ROS2, benchmark scripts, visualizations,
            and the website are integration layers around the same tested APIs.
          </p>
        </motion.article>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <h2 className="text-3xl font-semibold">Interactive pipeline</h2>
        <div className="mt-6 grid gap-3 md:grid-cols-4">
          {pipeline.map((step, index) => (
            <motion.div key={step} className="rounded-2xl border border-cyan-900/60 bg-cyan-950/30 p-4" initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: index * 0.03 }}>
              <p className="text-xs text-cyan-300">Step {index + 1}</p>
              <p className="mt-2 font-medium">{step}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 pb-20 md:grid-cols-2">
        <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
          <h2 className="text-2xl font-semibold">Benchmark tables</h2>
          <div className="mt-4 overflow-hidden rounded-2xl border border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900 text-slate-300"><tr><th className="p-3">Metric</th><th className="p-3">Status</th><th className="p-3">Output</th></tr></thead>
              <tbody>
                {benchmarks.map((row) => (
                  <tr key={row.metric} className="border-t border-slate-800"><td className="p-3">{row.metric}</td><td className="p-3 text-slate-300">{row.status}</td><td className="p-3 text-slate-300">{row.output}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
        <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
          <h2 className="text-2xl font-semibold">Demo and downloads</h2>
          <p className="mt-3 leading-7 text-slate-300">
            Generated media should be placed in <code>assets/demo.gif</code> and <code>results/videos/demo.mp4</code>.
            Tables and figures are generated from deterministic scripts rather than edited manually.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <a className="rounded-full bg-slate-100 px-4 py-2 text-slate-950" href="/demo.gif">Demo</a>
            <a className="rounded-full border border-slate-700 px-4 py-2" href="https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments/tree/main/results">Results</a>
          </div>
        </article>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-24">
        <h2 className="text-3xl font-semibold">Research timeline and roadmap</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-4">
          {roadmap.map((item) => (
            <div key={item} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 text-slate-300">{item}</div>
          ))}
        </div>
        <p className="mt-8 text-sm text-slate-500">
          Publications placeholder: cite the repository with CITATION.cff until a peer-reviewed paper is available.
        </p>
      </section>
    </main>
  );
}
