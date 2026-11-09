import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import contributions from "../../../data/contributions.json";

const repo = "https://github.com/panagiotagrosdouli/DynNav";

type Contribution = (typeof contributions)[number];

export function generateStaticParams() {
  return contributions.map(({ id }) => ({ id }));
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const item = contributions.find((entry) => entry.id === id);
  if (!item) return { title: "Contribution not found" };
  return {
    title: `${item.id} — ${item.title}`,
    description: item.experiment.hypothesis,
    alternates: { canonical: `/contributions/${item.id}` },
  };
}

export default async function ContributionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const item = contributions.find((entry) => entry.id === id) as Contribution | undefined;
  if (!item) notFound();

  const experiment = item.experiment;
  const command = [
    "python",
    experiment.runner,
    ...experiment.smoke_arguments,
    experiment.output_argument,
    `results/contribution_suite/artifacts/${experiment.artifact}`,
  ].join(" ");
  const sourceHref = item.source
    ? `${repo}/tree/main/${item.source}`
    : null;
  const rendererHref = item.renderer ? `${repo}/blob/main/${item.renderer}` : null;

  return (
    <main className="detail-page">
      <nav className="topbar" aria-label="Contribution navigation">
        <Link className="wordmark" href="/#contributions"><span className="mark" aria-hidden="true">D</span><span>DynNav</span></Link>
        <Link className="nav-cta" href="/#contributions">All contributions</Link>
      </nav>
      <article className="detail-content">
        <p className="eyebrow"><span /> {item.id} · {item.category.replaceAll("_", " ")}</p>
        <h1>{item.title}</h1>
        <p className="detail-lede">{experiment.hypothesis}</p>
        <div className="detail-status">
          <span><strong>Maturity</strong>{item.maturity}</span>
          <span><strong>Experiment evidence type</strong>{experiment.evidence_level}</span>
          <span><strong>Experiment ID</strong><code>{experiment.experiment_id}</code></span>
        </div>

        <section className="detail-panel">
          <h2>Registered experiment</h2>
          <p>The command below is the repository's controlled smoke configuration. It does not imply a real-robot or external-dataset result.</p>
          <pre><code>{command}</code></pre>
          <dl>
            <div><dt>Baselines</dt><dd>{experiment.baselines.join(", ")}</dd></div>
            <div><dt>Reported metrics</dt><dd>{experiment.primary_metrics.join(", ")}</dd></div>
            <div><dt>Optional dependencies</dt><dd>{experiment.optional_dependencies.length ? experiment.optional_dependencies.join(", ") : "None"}</dd></div>
            <div><dt>Output filename</dt><dd><code>{experiment.artifact}</code></dd></div>
          </dl>
        </section>

        <section className="detail-panel limitation-panel">
          <h2>Known limitation</h2>
          <p>{experiment.limitation}</p>
        </section>

        <section className="detail-panel">
          <h2>Repository resources</h2>
          <ul className="resource-links">
            <li><a href={`${repo}/blob/main/${item.readme}`}>Research README ↗</a></li>
            {sourceHref && <li><a href={sourceHref}>Contribution code directory ↗</a></li>}
            {rendererHref && <li><a href={rendererHref}>Dashboard renderer ↗</a></li>}
            <li><a href={`${repo}/blob/main/${experiment.runner}`}>Experiment runner ↗</a></li>
            <li><a href={`${repo}/${item.tests.endsWith(".py") ? "blob" : "tree"}/main/${item.tests}`}>{item.tests.startsWith("tests/") ? "Shared C01–C26 suite test" : "Contribution-specific tests"} ↗</a></li>
            {item.existing_results && <li><a href={`${repo}/tree/main/${item.existing_results}`}>Checked-in result files (historical files; provenance varies) ↗</a></li>}
            <li><a href={`${repo}/actions/workflows/contribution-experiments.yml`}>Latest C01–C26 workflow runs ↗</a></li>
            <li><a href={`${repo}/blob/main/configs/contributions/experiments.yaml`}>Canonical experiment registry ↗</a></li>
          </ul>
        </section>
        <p className="detail-boundary">The experiment registry classifies this smoke run as <strong>{experiment.evidence_level}</strong>. Consult the linked README and workflow artifact before citing results. Registry status and the existence of output folders are not scientific validation by themselves.</p>
      </article>
      <footer><span>DynNav · evidence boundaries are part of the research record</span><Link href="/#contributions">Back to the contribution explorer</Link></footer>
    </main>
  );
}
