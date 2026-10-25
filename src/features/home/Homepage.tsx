'use client';

import Link from 'next/link';
import './Homepage.css';

type ProcessStepProps = {
  number: string;
  title: string;
  description: string;
};

const PROCESS_STEPS = [
  {
    number: '01',
    title: 'Discover',
    description: 'Find a useful link, report, document, video, screenshot or insight.',
  },
  {
    number: '02',
    title: 'Contribute',
    description: 'Drop the resource into ART Investigation Lab.',
  },
  {
    number: '03',
    title: 'ART Investigates',
    description: 'ART structures the source, connects evidence and updates the investigation.',
  },
  {
    number: '04',
    title: 'Intelligence Evolves',
    description: 'Everyone sees what changed, who contributed and what still needs validation.',
  },
] as const;

function ProcessStep({ number, title, description }: ProcessStepProps) {
  return (
    <article className="home-step">
      <div className="home-step-number">{number}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}

export function Homepage() {
  return (
    <div className="homepage-shell">
      <section className="homepage-hero" aria-labelledby="home-title">
        <p className="homepage-kicker">ART Investigation Lab</p>
        <h1 id="home-title">Turn discoveries into shared intelligence.</h1>
        <p className="homepage-intro">
          Contribute research, evidence and insights. ART structures them into investigations your team can build on.
        </p>

        <div className="homepage-actions">
          <Link className="home-button home-button-primary" href="/start-contributing">
            Start Contributing
          </Link>
          <Link className="home-button home-button-secondary" href="/walkthrough">
            Explore Investigations
          </Link>
        </div>
      </section>

      <section className="how-it-works" aria-labelledby="how-it-works-title">
        <div className="section-head">
          <p className="homepage-kicker">How It Works</p>
          <h2 id="how-it-works-title">A short path from source to shared intelligence.</h2>
        </div>

        <div className="process-rail" aria-label="Process steps">
          {PROCESS_STEPS.map((step) => (
            <ProcessStep
              key={step.number}
              number={step.number}
              title={step.title}
              description={step.description}
            />
          ))}
        </div>
      </section>

    </div>
  );
}
