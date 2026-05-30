import Link from 'next/link';
import { LogoMark } from '@/components/Logo';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy — Capsule',
  description: 'Privacy Policy for Capsule, the deterministic replay and debugging platform for AI agents.',
};

const SECTIONS = [
  {
    id: 'overview',
    title: '1. Overview',
    body: `Capsule, Inc. ("Capsule", "we", "us", "our") respects your privacy and is committed to protecting the personal data you share with us. This Privacy Policy explains what data we collect when you use the Capsule platform and developer tools (the "Service"), how we use it, and your rights regarding that data. By using the Service you agree to the practices described here.`,
  },
  {
    id: 'data-collected',
    title: '2. Data We Collect',
    body: `We collect the following categories of data:\n\n• Account data: name, email address, hashed password, and billing information provided at registration.\n\n• Session data (Customer Data): AI agent execution traces, tool call logs, LLM inputs and outputs, and any other data you choose to capture using the Capsule SDK. This data is owned by you — see Section 5 for details.\n\n• Usage data: API request logs, dashboard activity, feature usage, error reports, and session metadata (timestamps, duration, status, token counts).\n\n• Device and technical data: IP address, browser type, operating system, and referrer URL collected automatically when you visit the Capsule website or dashboard.\n\n• Communications: support tickets, emails, and feedback you send us.`,
  },
  {
    id: 'how-used',
    title: '3. How We Use Your Data',
    body: `We use the data we collect to:\n\n• Provide, operate, and improve the Service.\n• Authenticate your identity and secure your account.\n• Process billing and send invoices.\n• Send transactional emails (account creation, password reset, usage alerts).\n• Send product updates and announcements — you can opt out at any time.\n• Investigate and resolve security incidents or Terms of Service violations.\n• Comply with legal obligations.\n\nWe do not use your Customer Data (agent session captures) to train machine learning models, and we do not sell your personal data to third parties.`,
  },
  {
    id: 'customer-data',
    title: '4. Customer Data (Agent Sessions)',
    body: `Customer Data — the agent execution sessions, traces, and logs you capture via the Capsule SDK — belongs to you. Capsule processes it only to provide the Service: storing, indexing, and displaying it in your dashboard, and making it available via our API. Customer Data is logically isolated per account. Our employees access Customer Data only with your explicit permission (e.g., to resolve a support request) or when required by law. You can delete your Customer Data at any time from the dashboard or via the API.`,
  },
  {
    id: 'sharing',
    title: '5. Data Sharing and Disclosure',
    body: `We do not sell, rent, or trade your personal data. We may share data with:\n\n• Service providers: cloud infrastructure (storage, compute), payment processors, and email delivery services — bound by confidentiality obligations and only given access to data they need to perform their function.\n\n• Legal requirements: we may disclose data when required by law, court order, or to protect the rights, property, or safety of Capsule, our users, or the public.\n\n• Business transfers: in the event of a merger, acquisition, or asset sale, your data may be transferred to the successor entity, subject to equivalent privacy protections.\n\n• With your consent: we may share data for other purposes when you give explicit permission.`,
  },
  {
    id: 'retention',
    title: '6. Data Retention',
    body: `We retain account data for the lifetime of your account. Session captures and Customer Data are stored according to your plan limits and any retention settings you configure. After account deletion, Customer Data is purged within 30 days and account data within 90 days, unless we are required to retain it longer by law. Aggregated, anonymized usage statistics may be retained indefinitely.`,
  },
  {
    id: 'security',
    title: '7. Security',
    body: `Capsule implements industry-standard security controls including encryption in transit (TLS 1.2+), encryption at rest, network isolation, access controls with least-privilege principles, and audit logging. We pursue SOC 2 Type II compliance. However, no system is completely secure. If you discover a vulnerability, please report it responsibly to security@capsule.dev. In the event of a data breach affecting your personal data, we will notify you as required by applicable law.`,
  },
  {
    id: 'cookies',
    title: '8. Cookies and Tracking',
    body: `We use essential cookies to maintain your authenticated session and remember preferences. We use analytics cookies (such as basic usage counters) to understand how the Service is used — no advertising networks are used. You can disable non-essential cookies in your browser settings, though this may affect functionality. We do not use tracking pixels or cross-site tracking technologies.`,
  },
  {
    id: 'rights',
    title: '9. Your Rights',
    body: `Depending on your location, you may have the following rights regarding your personal data:\n\n• Access: request a copy of the personal data we hold about you.\n• Correction: request correction of inaccurate data.\n• Deletion: request deletion of your personal data ("right to be forgotten").\n• Portability: receive your data in a machine-readable format.\n• Restriction: request that we restrict processing of your data.\n• Objection: object to processing based on legitimate interests.\n• Withdraw consent: where processing is based on consent, withdraw it at any time.\n\nEU/EEA and UK residents have additional rights under GDPR/UK GDPR. California residents have rights under CCPA. To exercise any of these rights, contact privacy@capsule.dev. We will respond within 30 days.`,
  },
  {
    id: 'international',
    title: '10. International Data Transfers',
    body: `Capsule is operated from servers that may be located outside your country of residence. By using the Service you consent to the transfer of your data to these locations. For transfers from the EU/EEA or UK, we rely on Standard Contractual Clauses (SCCs) or other appropriate safeguards as required by applicable data protection law.`,
  },
  {
    id: 'children',
    title: '11. Children',
    body: `The Service is not directed to individuals under the age of 16. We do not knowingly collect personal data from children under 16. If we learn that we have inadvertently collected such data, we will delete it promptly. If you believe a child has provided us personal data, please contact privacy@capsule.dev.`,
  },
  {
    id: 'dpa',
    title: '12. Data Processing Agreement',
    body: `If you use Capsule to process personal data on behalf of your end users (e.g., your AI agents interact with user data), Capsule acts as a data processor and you act as the data controller. Enterprise customers may request our standard Data Processing Agreement (DPA) at legal@capsule.dev. The DPA governs our obligations as processor under GDPR and equivalent regulations.`,
  },
  {
    id: 'changes',
    title: '13. Changes to This Policy',
    body: `We may update this Privacy Policy to reflect changes in our practices or applicable law. Material changes will be communicated by email or a prominent notice in the dashboard at least 14 days before taking effect. The current version is always available at capsule.dev/privacy. Continued use of the Service after the effective date constitutes acceptance of the revised policy.`,
  },
  {
    id: 'contact',
    title: '14. Contact and Data Controller',
    body: `Capsule, Inc. is the data controller for personal data collected through the Service. For privacy-related questions, requests, or complaints, contact us at privacy@capsule.dev. If you are in the EU/EEA and are not satisfied with our response, you have the right to lodge a complaint with your local supervisory authority.`,
  },
];

export default function PrivacyPage() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-base)', color: 'var(--text-primary)' }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid var(--border-subtle)',
        padding: '0 28px',
        height: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        background: 'var(--bg-base)',
        zIndex: 10,
      }}>
        <a href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
          <LogoMark size={28} />
          <span style={{ fontWeight: 600, fontSize: 15, letterSpacing: '-0.01em' }}>Capsule</span>
        </a>
        <div style={{ display: 'flex', gap: 24, fontSize: 13.5, color: 'var(--text-secondary)' }}>
          <Link href="/terms" style={{ color: 'var(--text-secondary)' }}>Terms of Service</Link>
          <Link href="/login" style={{ color: 'var(--text-secondary)' }}>Log in</Link>
        </div>
      </header>

      <main style={{ maxWidth: 760, margin: '0 auto', padding: '64px 28px 96px' }}>
        {/* Title block */}
        <div style={{ marginBottom: 48 }}>
          <p style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 12 }}>Legal</p>
          <h1 style={{ fontSize: 36, fontWeight: 600, letterSpacing: '-0.025em', lineHeight: 1.1, marginBottom: 16 }}>
            Privacy Policy
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
            Last updated: May 30, 2026 &nbsp;·&nbsp; Effective: May 30, 2026
          </p>
          <p style={{ color: 'var(--text-secondary)', marginTop: 20, lineHeight: 1.7 }}>
            We built Capsule for developers who care about reliability and trust. That means being equally transparent about how we handle your data.
          </p>
        </div>

        {/* Table of contents */}
        <nav style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 10,
          padding: '20px 24px',
          marginBottom: 52,
        }}>
          <p style={{ fontSize: 11.5, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 14 }}>Contents</p>
          <ol style={{ listStyle: 'none', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 24px' }}>
            {SECTIONS.map((s) => (
              <li key={s.id}>
                <a
                  href={`#${s.id}`}
                  style={{ fontSize: 13.5, color: 'var(--text-secondary)', textDecoration: 'none' }}
                  onMouseOver={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                  onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
                >
                  {s.title}
                </a>
              </li>
            ))}
          </ol>
        </nav>

        {/* Sections */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 44 }}>
          {SECTIONS.map((s) => (
            <section key={s.id} id={s.id}>
              <h2 style={{ fontSize: 17, fontWeight: 600, letterSpacing: '-0.015em', marginBottom: 12 }}>
                {s.title}
              </h2>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.75, fontSize: 14.5, whiteSpace: 'pre-line' }}>
                {s.body}
              </p>
            </section>
          ))}
        </div>

        {/* Footer note */}
        <div style={{
          marginTop: 64,
          paddingTop: 32,
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          gap: 12,
          flexWrap: 'wrap',
          fontSize: 13.5,
          color: 'var(--text-tertiary)',
        }}>
          <Link href="/terms" style={{ color: 'var(--text-secondary)' }}>Terms of Service</Link>
          <span>·</span>
          <a href="mailto:privacy@capsule.dev" style={{ color: 'var(--text-secondary)' }}>privacy@capsule.dev</a>
          <span>·</span>
          <span>© 2026 Capsule, Inc.</span>
        </div>
      </main>
    </div>
  );
}
