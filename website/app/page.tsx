"use client";

import { motion } from "framer-motion";

const sections = [
  "Research motivation",
  "System architecture",
  "Interactive pipeline",
  "Demo GIF",
  "Benchmark tables",
  "Research timeline",
  "Roadmap",
  "Publications",
  "Downloads",
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
            recoverability estimation, dynamic rerouting, and runtime monitoring.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <a className="rounded-full bg-cyan-300 px-5 py-3 font-medium text-slate-950" href="https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments">
              GitHub repository
            </a>
            <a className="rounded-full border border-slate-600 px-5 py-3" href="/demo.gif">
              View demo
            </a>
          </div>
        </motion.div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-6 pb-20 md:grid-cols-3">
        {sections.map((section, index) => (
          <motion.article
            key={section}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.04 }}
            className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6"
          >
            <h2 className="text-xl font-semibold">{section}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              This block is wired as a research-site placeholder. Replace with generated benchmark tables,
              architecture diagrams, publication links, and downloadable artifacts as the evaluation matures.
            </p>
          </motion.article>
        ))}
      </section>
    </main>
  );
}
