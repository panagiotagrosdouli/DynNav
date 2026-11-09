"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import contributionData from "../data/contributions.json";

type Contribution = (typeof contributionData)[number];

const views = [
  { id: "first-eleven", label: "C00 + C01–C11", matches: (id: string) => Number(id.slice(1)) <= 11 },
  { id: "all", label: "All C01–C26", matches: () => true },
] as const;

const repositoryBase = "https://github.com/panagiotagrosdouli/DynNav";

function repositoryHref(path: string, directory = false) {
  return `${repositoryBase}/${directory ? "tree" : "blob"}/main/${path}`;
}

function titleCase(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function ContributionExplorer() {
  const [view, setView] = useState<(typeof views)[number]["id"]>("first-eleven");
  const [maturity, setMaturity] = useState("All maturity levels");
  const [category, setCategory] = useState("All topics");
  const [query, setQuery] = useState("");

  const selectedView = views.find((item) => item.id === view) ?? views[0];
  const categories = Array.from(new Set(contributionData.map((item) => item.category))).sort();
  const visible = useMemo(() => contributionData.filter((item) => {
    const matchesView = selectedView.matches(item.id);
    const matchesMaturity = maturity === "All maturity levels" || item.maturity === maturity;
    const matchesCategory = category === "All topics" || item.category === category;
    const needle = query.trim().toLowerCase();
    const matchesQuery = !needle || [
      item.id,
      item.title,
      item.category,
      item.experiment.hypothesis,
      item.experiment.limitation,
    ].join(" ").toLowerCase().includes(needle);
    return matchesView && matchesMaturity && matchesCategory && matchesQuery;
  }), [category, maturity, query, selectedView]);

  return (
    <section className="contributions" id="contributions">
      <div className="section-heading">
        <p className="eyebrow"><span /> Contribution registry</p>
        <h2>From the core idea to all 26 research tracks.</h2>
        <p>Titles and maturity come from the canonical project registry. Open a research detail page for its hypothesis, experiment contract, limitations, and available repository evidence.</p>
      </div>
      <div className="explorer-controls" aria-label="Contribution filters">
        <div className="view-tabs" role="group" aria-label="Contribution range">
          {views.map((item) => (
            <button key={item.id} type="button" aria-pressed={view === item.id} onClick={() => setView(item.id)}>
              {item.label}
            </button>
          ))}
        </div>
        <label className="search-label">
          <span>Search</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Title, hypothesis, or limitation" />
        </label>
        <label className="maturity-label">
          <span>Maturity</span>
          <select value={maturity} onChange={(event) => setMaturity(event.target.value)}>
            <option>All maturity levels</option>
            {Array.from(new Set(contributionData.map((item) => item.maturity))).map((level) => <option key={level}>{level}</option>)}
          </select>
        </label>
        <label className="maturity-label">
          <span>Topic</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option>All topics</option>
            {categories.map((item) => <option key={item} value={item}>{titleCase(item)}</option>)}
          </select>
        </label>
      </div>
      <div className="explorer-summary" aria-live="polite">
        <strong>{visible.length} of 26</strong>
        <span>registered tracks shown · filter updates immediately</span>
      </div>
      {view === "first-eleven" && (
        <article className="core-card">
          <div className="contribution-card-top"><span className="contribution-id">C00 · CORE</span><span className="maturity-pill">Research hypothesis</span></div>
          <p className="contribution-category">Core research question</p>
          <h3>Dynamic navigation with recoverability</h3>
          <p className="contribution-summary">When a route changes or becomes blocked, can online replanning account for risk while preserving a feasible way to recover?</p>
          <a href={`${repositoryBase}/blob/main/README.md`}>Project hypothesis and protocol ↗</a>
        </article>
      )}
      <div className="contribution-grid">
        {visible.map((item: Contribution) => (
          <article className="contribution-card" key={item.id}>
            <div className="contribution-card-top">
              <span className="contribution-id">{item.id}</span>
              <span className="maturity-pill">{item.maturity}</span>
            </div>
            <p className="contribution-category">{titleCase(item.category)}</p>
            <h3>{item.title}</h3>
            <p className="contribution-summary">{item.experiment.hypothesis}</p>
            <div className="contribution-links">
              <Link href={`/contributions/${item.id}`}>Research details ↗</Link>
              <a href={repositoryHref(item.readme)}>README ↗</a>
              <a href="https://github.com/panagiotagrosdouli/DynNav/actions/workflows/contribution-experiments.yml">C01–C26 smoke workflow ↗</a>
            </div>
          </article>
        ))}
      </div>
      {visible.length === 0 && <p className="empty-state">No contributions match these filters.</p>}
      <p className="explorer-boundary">
        The registered experiment suite is a collection of controlled smoke benchmarks. A passing run demonstrates implementation and reproducibility only; it is not automatically real-world, Gazebo, formal-safety, or hardware evidence.
      </p>
    </section>
  );
}

export { repositoryHref };
