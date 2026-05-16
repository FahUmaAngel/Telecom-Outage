"use client";

import { useLanguage } from "../../context/LanguageContext";

const REFERENCES = [
    {
        id: 1,
        citation: "ITU-T Recommendation E.800 (09/2008)",
        title: "Definitions of terms related to quality of service",
        body: "International Telecommunication Union, Geneva.",
        use: { sv: "SLA-trösklar för kritiska och allvarliga incidenter (4h resp. 24h).", en: "SLA thresholds for critical and major incidents (4h and 24h respectively)." },
    },
    {
        id: 2,
        citation: "ETSI EG 202 057-1 V2.1.1 (2013)",
        title: "Speech and multimedia Transmission Quality (STQ); User related QoS parameter definitions and measurements; Part 1: General",
        body: "European Telecommunications Standards Institute.",
        use: { sv: "Europeisk referens för servicetid till återhämtning (P95 ≤ 48h).", en: "European reference for time-to-restore service (P95 ≤ 48h)." },
    },
    {
        id: 3,
        citation: "PTSFS 2014:1",
        title: "Föreskrifter om rapportering av integritetsincidenter och störningar av betydande omfattning",
        body: "Post- och telestyrelsen (Swedish Post and Telecom Authority).",
        use: { sv: "Svensk reglering — incident >1h och >10 000 abonnenter ska rapporteras.", en: "Swedish regulation — incidents >1h affecting >10,000 subscribers must be reported." },
    },
    {
        id: 4,
        citation: "ITU-T Recommendation M.3400 (02/2000)",
        title: "TMN management functions",
        body: "International Telecommunication Union, Geneva.",
        use: { sv: "Definition av MTTR (Mean Time To Repair) inom telekommunikationshantering.", en: "Definition of MTTR (Mean Time To Repair) in telecommunications management." },
    },
    {
        id: 5,
        citation: "Soldani, D., Li, M., & Cuny, R. (Eds.) (2006)",
        title: "QoS and QoE Management in UMTS Cellular Systems",
        body: "John Wiley & Sons.",
        use: { sv: "Viktningsschema för CVS-komponenterna (MTTR 30%, frekvens 20%, driftstopp 20%, täckning 15%, SLA 15%).", en: "Weighting scheme for CVS components (MTTR 30%, frequency 20%, downtime 20%, coverage 15%, SLA 15%)." },
    },
    {
        id: 6,
        citation: "ITU-T G.1011 (2015)",
        title: "Reference guide to quality of experience",
        body: "International Telecommunication Union, Geneva.",
        use: { sv: "Stöd för QoE/QoS-viktning i konsumentvärdesmodellen.", en: "Support for QoE/QoS weighting in the consumer value model." },
    },
    {
        id: 7,
        citation: "Kruskal, W. H., & Wallis, W. A. (1952)",
        title: "Use of ranks in one-criterion variance analysis",
        body: "Journal of the American Statistical Association, 47(260), 583–621.",
        use: { sv: "Kruskal-Wallis H-test för icke-parametrisk jämförelse av MTTR-distributioner per operatör.", en: "Kruskal-Wallis H-test for non-parametric comparison of MTTR distributions across operators." },
    },
];

const RQ = [
    {
        id: "RQ1",
        q_sv: "Vad är MTTR-fördelningen per operatör?",
        q_en: "What is the MTTR distribution per operator?",
        approach_sv: "Percentilanalys (P50, P75, P90, P95, P99) och histogram per operatör. Kruskal-Wallis H-test för att avgöra om skillnader är statistiskt signifikanta.",
        approach_en: "Percentile analysis (P50, P75, P90, P95, P99) and histogram per operator. Kruskal-Wallis H-test to determine whether differences are statistically significant.",
        page: "/statistics",
    },
    {
        id: "RQ2",
        q_sv: "Får konsumenter valuta för pengarna?",
        q_en: "Are consumers receiving value for their money?",
        approach_sv: "Sammansatt Consumer Value Score (CVS) viktat efter MTTR, avbrottsfrekvens, total driftstopp, tjänsttäckning och SLA-efterlevnad. Ranking per operatör.",
        approach_en: "Composite Consumer Value Score (CVS) weighted by MTTR, outage frequency, total downtime, service coverage, and SLA compliance. Ranking per operator.",
        page: "/value-score",
    },
    {
        id: "RQ3",
        q_sv: "Uppfyller operatörerna internationella SLA-standarder?",
        q_en: "Are operators meeting international SLA standards?",
        approach_sv: "Jämförelse av faktisk MTTR mot trösklar i ITU-T E.800, ETSI EG 202 057-1 och PTSFS 2014:1 — uppdelat per allvarlighetsnivå.",
        approach_en: "Comparison of actual MTTR against thresholds in ITU-T E.800, ETSI EG 202 057-1, and PTSFS 2014:1 — broken down by severity tier.",
        page: "/sla-compliance",
    },
];

const PIPELINE = [
    { sv: "Datainsamling", en: "Data Collection", detail_sv: "Automatisk skrapning av Telia, Telenor och Tre:s driftstatussidor via Playwright/Selenium/Requests.", detail_en: "Automated scraping of Telia, Telenor and Tre status pages via Playwright/Selenium/Requests." },
    { sv: "Lagring", en: "Storage", detail_sv: "SQLite-databas med tabeller för Outage och Operator. Varje incident har start_time, resolved_at, severity och berörda regioner.", detail_en: "SQLite database with Outage and Operator tables. Each incident has start_time, resolved_at, severity, and affected regions." },
    { sv: "MTTR-beräkning", en: "MTTR Calculation", detail_sv: "MTTR = (resolved_at − start_time) i timmar. Orealistiska värden (> 8 760h) utesluts. Bootstrap CI med 1 000 iterationer.", detail_en: "MTTR = (resolved_at − start_time) in hours. Unrealistic values (> 8,760h) excluded. Bootstrap CI with 1,000 iterations." },
    { sv: "Normalisering (CVS)", en: "Normalisation (CVS)", detail_sv: "Varje CVS-komponent normaliseras till [0, 1] med min-max-skalning. Lägre MTTR/frekvens/driftstopp → högre poäng.", detail_en: "Each CVS component normalised to [0, 1] using min-max scaling. Lower MTTR/frequency/downtime → higher score." },
    { sv: "Statistisk testning", en: "Statistical Testing", detail_sv: "Kruskal-Wallis H (icke-parametrisk) eller one-way ANOVA. Effektstorlek η² beräknas. α = 0,05.", detail_en: "Kruskal-Wallis H (non-parametric) or one-way ANOVA. Effect size η² computed. α = 0.05." },
    { sv: "SLA-matching", en: "SLA Matching", detail_sv: "Severity mappas till ITU-T-tier (critical/major/minor). Varje incident jämförs mot valt benchmark-tröskel.", detail_en: "Severity mapped to ITU-T tier (critical/major/minor). Each incident compared against selected benchmark threshold." },
];

export default function MethodologyPage() {
    const { lang } = useLanguage();
    const t = (sv, en) => lang === "sv" ? sv : en;

    return (
        <div className="page-container animate-fade-in">
            <header className="page-header">
                <div>
                    <h1 className="text-gradient">
                        {t("Forskningsmetodik", "Research Methodology")}
                    </h1>
                    <p className="subtitle">
                        {t(
                            "Datapipeline, statistiska metoder och referensram för IEEE-publikation",
                            "Data pipeline, statistical methods, and reference framework for IEEE publication"
                        )}
                    </p>
                </div>
            </header>

            {/* Research Questions */}
            <section className="section">
                <h2 className="section-title">{t("Forskningsfrågor", "Research Questions")}</h2>
                <div className="rq-list">
                    {RQ.map(rq => (
                        <div key={rq.id} className="rq-card">
                            <div className="rq-header">
                                <span className="rq-id">{rq.id}</span>
                                <span className="rq-question">{t(rq.q_sv, rq.q_en)}</span>
                            </div>
                            <p className="rq-approach">
                                <strong>{t("Metod: ", "Approach: ")}</strong>
                                {t(rq.approach_sv, rq.approach_en)}
                            </p>
                            <a href={rq.page} className="rq-link">
                                {t("Se resultat →", "View results →")}
                            </a>
                        </div>
                    ))}
                </div>
            </section>

            {/* Data Pipeline */}
            <section className="section">
                <h2 className="section-title">{t("Datapipeline", "Data Pipeline")}</h2>
                <div className="pipeline">
                    {PIPELINE.map((step, i) => (
                        <div key={step.en} className="pipeline-step">
                            <div className="step-number">{i + 1}</div>
                            <div className="step-content">
                                <div className="step-title">{t(step.sv, step.en)}</div>
                                <div className="step-detail">{t(step.detail_sv, step.detail_en)}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Architecture Diagram */}
            <section className="section">
                <h2 className="section-title">{t("Systemarkitektur", "System Architecture")}</h2>
                <div className="arch-card">
                    <div className="arch-diagram">
                        {/* Layer 1: Sources */}
                        <div className="arch-layer">
                            <div className="arch-layer-label">{t("Datakällor", "Data Sources")}</div>
                            <div className="arch-nodes">
                                <div className="arch-node node-source">Telia<br/><span className="node-sub">Playwright</span></div>
                                <div className="arch-node node-source">Telenor<br/><span className="node-sub">Selenium</span></div>
                                <div className="arch-node node-source">Tre<br/><span className="node-sub">Requests</span></div>
                            </div>
                        </div>

                        <div className="arch-arrow-row">
                            <div className="arch-arrow">↓</div>
                            <div className="arch-arrow-label">HTTP scrape / parse HTML</div>
                        </div>

                        {/* Layer 2: Scraper */}
                        <div className="arch-layer">
                            <div className="arch-layer-label">{t("Skrapningslager", "Scraper Layer")}</div>
                            <div className="arch-nodes">
                                <div className="arch-node node-scraper">scrapers/run.py<br/><span className="node-sub">Scheduler (5 min)</span></div>
                            </div>
                        </div>

                        <div className="arch-arrow-row">
                            <div className="arch-arrow">↓</div>
                            <div className="arch-arrow-label">SQLAlchemy ORM</div>
                        </div>

                        {/* Layer 3: Storage */}
                        <div className="arch-layer">
                            <div className="arch-layer-label">{t("Lagring", "Storage")}</div>
                            <div className="arch-nodes">
                                <div className="arch-node node-db">SQLite<br/><span className="node-sub">Outage · Operator · Region</span></div>
                            </div>
                        </div>

                        <div className="arch-arrow-row">
                            <div className="arch-arrow">↓</div>
                            <div className="arch-arrow-label">FastAPI + SQLAlchemy</div>
                        </div>

                        {/* Layer 4: API */}
                        <div className="arch-layer">
                            <div className="arch-layer-label">{t("API-lager", "API Layer")}</div>
                            <div className="arch-nodes">
                                <div className="arch-node node-api">REST API<br/><span className="node-sub">/api/v1/research/*</span></div>
                                <div className="arch-node node-api">numpy · scipy<br/><span className="node-sub">Statistical computation</span></div>
                            </div>
                        </div>

                        <div className="arch-arrow-row">
                            <div className="arch-arrow">↓</div>
                            <div className="arch-arrow-label">JSON / fetch()</div>
                        </div>

                        {/* Layer 5: Frontend */}
                        <div className="arch-layer">
                            <div className="arch-layer-label">{t("Presentationslager", "Presentation Layer")}</div>
                            <div className="arch-nodes">
                                <div className="arch-node node-ui">/statistics<br/><span className="node-sub">MTTR · Kruskal-Wallis</span></div>
                                <div className="arch-node node-ui">/sla-compliance<br/><span className="node-sub">ITU-T · ETSI · PTS</span></div>
                                <div className="arch-node node-ui">/value-score<br/><span className="node-sub">CVS Ranking</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* SLA Thresholds table */}
            <section className="section">
                <h2 className="section-title">{t("SLA-tröskelvärden (timmar)", "SLA Thresholds (hours)")}</h2>
                <div className="table-card">
                    <table className="stats-table">
                        <thead>
                            <tr>
                                <th>{t("Standard", "Standard")}</th>
                                <th>Critical</th>
                                <th>Major</th>
                                <th>Minor</th>
                                <th>{t("Källa", "Source")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><span className="std-badge">ITU-T E.800</span></td>
                                <td className="mono">≤ 4h</td>
                                <td className="mono">≤ 24h</td>
                                <td className="mono">≤ 72h</td>
                                <td className="cite">[1]</td>
                            </tr>
                            <tr>
                                <td><span className="std-badge">ETSI EG 202 057-1</span></td>
                                <td className="mono">≤ 8h</td>
                                <td className="mono">≤ 48h</td>
                                <td className="mono">≤ 120h</td>
                                <td className="cite">[2]</td>
                            </tr>
                            <tr>
                                <td><span className="std-badge">PTSFS 2014:1</span></td>
                                <td className="mono">≤ 1h</td>
                                <td className="mono">≤ 24h</td>
                                <td className="mono">≤ 96h</td>
                                <td className="cite">[3]</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            {/* CVS Weights */}
            <section className="section">
                <h2 className="section-title">{t("CVS-viktningsschema", "CVS Weighting Scheme")}</h2>
                <div className="table-card">
                    <table className="stats-table">
                        <thead>
                            <tr>
                                <th>{t("Komponent", "Component")}</th>
                                <th>{t("Vikt", "Weight")}</th>
                                <th>{t("Riktning", "Direction")}</th>
                                <th>{t("Motivering", "Rationale")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {[
                                ["MTTR", "30%", t("Lägre = bättre", "Lower = better"), t("Återhämtningshastighet är den starkaste QoS-indikatorn", "Recovery speed is the strongest QoS indicator")],
                                [t("Avbrottsfrekvens", "Outage Frequency"), "20%", t("Lägre = bättre", "Lower = better"), t("Tillförlitlighet påverkar konsumentupplevelsen direkt", "Reliability directly impacts consumer experience")],
                                [t("Total driftstopp", "Total Downtime"), "20%", t("Lägre = bättre", "Lower = better"), t("Samlad exponering för avbrott", "Cumulative exposure to outages")],
                                [t("Tjänsttäckning", "Service Coverage"), "15%", t("Högre = bättre", "Higher = better"), t("Bredden av berörda tjänster", "Breadth of services affected")],
                                [t("SLA-efterlevnad", "SLA Compliance"), "15%", t("Högre = bättre", "Higher = better"), t("Andel incidenter som möter internationell standard", "Fraction of incidents meeting international standard")],
                            ].map(([comp, w, dir, rat]) => (
                                <tr key={comp}>
                                    <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{comp}</td>
                                    <td><span className="weight-badge">{w}</span></td>
                                    <td style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>{dir}</td>
                                    <td style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>{rat}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <p className="table-note">{t("Källor: Soldani et al. (2006) [5]; ITU-T G.1011 (2015) [6].", "Sources: Soldani et al. (2006) [5]; ITU-T G.1011 (2015) [6].")}</p>
            </section>

            {/* References */}
            <section className="section">
                <h2 className="section-title">{t("Referenser", "References")}</h2>
                <div className="ref-list">
                    {REFERENCES.map(r => (
                        <div key={r.id} className="ref-item">
                            <span className="ref-num">[{r.id}]</span>
                            <div className="ref-body">
                                <div className="ref-citation">{r.citation}</div>
                                <div className="ref-title">"{r.title}." {r.body}</div>
                                <div className="ref-use">
                                    <span className="ref-use-label">{t("Använt för: ", "Used for: ")}</span>
                                    {t(r.use.sv, r.use.en)}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <style jsx>{`
                .page-container { max-width: 900px; margin: 0 auto; padding: 32px 24px; }
                .page-header { margin-bottom: 32px; }
                .subtitle { color: var(--text-secondary); font-size: 0.9rem; margin-top: 4px; }
                .text-gradient { background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
                .section { margin-bottom: 44px; }
                .section-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 16px; border-left: 3px solid var(--accent-primary); padding-left: 12px; }
                .rq-list { display: flex; flex-direction: column; gap: 12px; }
                .rq-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; display: flex; flex-direction: column; gap: 10px; }
                .rq-header { display: flex; align-items: flex-start; gap: 12px; }
                .rq-id { flex-shrink: 0; font-size: 0.7rem; font-weight: 900; letter-spacing: 0.1em; background: var(--accent-primary); color: #fff; padding: 3px 8px; border-radius: 4px; margin-top: 2px; }
                .rq-question { font-weight: 600; color: var(--text-primary); font-size: 0.95rem; line-height: 1.4; }
                .rq-approach { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6; margin: 0; }
                .rq-link { font-size: 0.8rem; color: var(--accent-primary); font-weight: 600; text-decoration: none; align-self: flex-start; }
                .rq-link:hover { text-decoration: underline; }
                .pipeline { display: flex; flex-direction: column; gap: 0; }
                .pipeline-step { display: flex; gap: 16px; padding: 16px 0; border-bottom: 1px solid var(--border-color); }
                .pipeline-step:last-child { border-bottom: none; }
                .step-number { flex-shrink: 0; width: 28px; height: 28px; background: var(--accent-primary); color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 800; margin-top: 2px; }
                .step-content { display: flex; flex-direction: column; gap: 4px; }
                .step-title { font-weight: 700; color: var(--text-primary); font-size: 0.9rem; }
                .step-detail { font-size: 0.83rem; color: var(--text-secondary); line-height: 1.6; }
                .table-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow-x: auto; }
                .stats-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
                .stats-table th { padding: 12px 16px; text-align: left; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; color: var(--text-muted); text-transform: uppercase; border-bottom: 1px solid var(--border-color); }
                .stats-table td { padding: 12px 16px; border-bottom: 1px solid var(--border-color); color: var(--text-secondary); vertical-align: top; }
                .stats-table tr:last-child td { border-bottom: none; }
                .mono { font-family: monospace; font-weight: 700; color: var(--text-primary); }
                .cite { font-family: monospace; color: var(--accent-primary); font-weight: 700; }
                .std-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; background: var(--surface-hover); color: var(--text-primary); }
                .weight-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; background: rgba(99,102,241,0.1); color: var(--accent-primary); font-size: 0.82rem; font-weight: 800; font-family: monospace; }
                .table-note { font-size: 0.78rem; color: var(--text-muted); margin-top: 10px; padding-left: 4px; }
                .ref-list { display: flex; flex-direction: column; gap: 0; }
                .ref-item { display: flex; gap: 16px; padding: 14px 0; border-bottom: 1px solid var(--border-color); }
                .ref-item:last-child { border-bottom: none; }
                .ref-num { flex-shrink: 0; font-family: monospace; font-weight: 700; color: var(--accent-primary); font-size: 0.85rem; min-width: 28px; }
                .ref-body { display: flex; flex-direction: column; gap: 3px; }
                .ref-citation { font-weight: 700; color: var(--text-primary); font-size: 0.85rem; }
                .ref-title { font-size: 0.83rem; color: var(--text-secondary); line-height: 1.5; }
                .ref-use { font-size: 0.78rem; color: var(--text-muted); line-height: 1.5; margin-top: 2px; }
                .ref-use-label { font-weight: 700; color: var(--text-muted); }
                .arch-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 28px 20px; }
                .arch-diagram { display: flex; flex-direction: column; align-items: center; gap: 0; }
                .arch-layer { width: 100%; display: flex; flex-direction: column; align-items: center; gap: 10px; }
                .arch-layer-label { font-size: 0.6rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-muted); opacity: 0.6; }
                .arch-nodes { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
                .arch-node { padding: 10px 18px; border-radius: 8px; font-size: 0.82rem; font-weight: 700; text-align: center; line-height: 1.5; min-width: 140px; }
                .node-sub { display: block; font-size: 0.68rem; font-weight: 500; opacity: 0.75; margin-top: 2px; }
                .node-source { background: rgba(163,31,208,0.1); border: 1px solid rgba(163,31,208,0.3); color: #A31FD0; }
                .node-scraper { background: rgba(235,111,42,0.1); border: 1px solid rgba(235,111,42,0.3); color: #EB6F2A; }
                .node-db { background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3); color: var(--status-warning); }
                .node-api { background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.3); color: var(--accent-primary); }
                .node-ui { background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.3); color: var(--status-success); }
                .arch-arrow-row { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 6px 0; }
                .arch-arrow { font-size: 1.2rem; color: var(--text-muted); opacity: 0.5; line-height: 1; }
                .arch-arrow-label { font-size: 0.68rem; color: var(--text-muted); opacity: 0.6; font-family: monospace; }
                @media (max-width: 768px) {
                    .page-container { padding: 20px 16px; }
                    .arch-node { min-width: 110px; font-size: 0.76rem; padding: 8px 12px; }
                    .arch-nodes { gap: 8px; }
                    .rq-card { padding: 14px; }
                    .pipeline-step { gap: 10px; }
                    .ref-item { gap: 10px; }
                    .stats-table th, .stats-table td { padding: 10px 10px; font-size: 0.8rem; }
                }
            `}</style>
        </div>
    );
}
