import clsx from 'clsx';
import Heading from '@theme/Heading';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import styles from './index.module.css';

export default function Home() {
  return (
    <Layout
      title="Home"
      description="Homelab runbooks, change records, and architecture">
      <main>
        <header className={clsx('hero hero--primary', styles.hero)}>
          <div className="container">
            <Heading as="h1" className="hero__title">
              Homelab Documentation
            </Heading>
            <p className="hero__subtitle">
              Runbooks, change records, and architecture for the lab.
            </p>
            <Link className="button button--secondary button--lg" to="/docs/intro">
              Open documentation
            </Link>
          </div>
        </header>
      </main>
    </Layout>
  );
}
