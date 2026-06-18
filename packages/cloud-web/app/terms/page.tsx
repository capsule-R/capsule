import Link from 'next/link';
import { LogoMark } from '@/components/Logo';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service — Capsule',
  description: 'Terms of Service for Capsule, the deterministic replay and debugging platform for AI agents.',
};

const SECTIONS = [
  {
    id: 'acceptance',
    title: '1. Acceptance of Terms',
    body: `By creating an account or using the Capsule service (the "Service"), you agree to be bound by these Terms of Service ("Terms"). If you are using the Service on behalf of an organization, you represent that you have authority to bind that organization to these Terms, in which case "you" refers to that organization. If you do not agree to these Terms, do not use the Service.`,
  },
  {
    id: 'description',
    title: '2. Description of Service',
    body: `Capsule provides a cloud-hosted platform that allows developers to capture, store, replay, and debug AI agent execution sessions. The Service includes an SDK (the "Capsule SDK"), a web dashboard, a REST API, and associated developer tooling. Capsule, Inc. ("Capsule", "we", "us") reserves the right to modify, suspend, or discontinue any part of the Service at any time with reasonable notice.`,
  },
  {
    id: 'accounts',
    title: '3. Accounts and Registration',
    body: `You must provide accurate and complete information when creating an account. You are responsible for maintaining the confidentiality of your credentials and API keys, and for all activity that occurs under your account. You must notify us immediately at support@capsule.dev if you suspect unauthorized access. We may suspend or terminate accounts that violate these Terms or that have been inactive for an extended period.`,
  },
  {
    id: 'use',
    title: '4. Acceptable Use',
    body: `You agree not to: (a) use the Service to capture, store, or transmit data you are not authorized to access; (b) reverse-engineer, decompile, or attempt to extract the source code of the Service; (c) use the Service to develop a competing product; (d) introduce malicious code, conduct denial-of-service attacks, or circumvent rate limits; (e) violate any applicable laws or regulations, including data protection laws; (f) sell, resell, or sublicense access to the Service without written permission. Capsule may monitor usage to ensure compliance and reserves the right to remove content or suspend accounts that violate this policy.`,
  },
  {
    id: 'data',
    title: '5. Your Data',
    body: `You retain ownership of all data, agent execution logs, session captures, and other content you submit to the Service ("Customer Data"). By using the Service you grant Capsule a limited, non-exclusive license to host, process, and transmit Customer Data solely to provide the Service. Capsule will not sell your Customer Data to third parties or use it to train machine learning models without your explicit consent. You are solely responsible for ensuring your use of the Service complies with applicable data protection regulations, including obtaining any necessary consents before capturing data about end users of your AI agents.`,
  },
  {
    id: 'api',
    title: '6. API Keys and SDK',
    body: `API keys are bound to your account and must be kept confidential. You are responsible for all usage attributed to your API keys. Do not embed API keys in publicly accessible code or repositories. Capsule reserves the right to revoke keys that are compromised or used in violation of these Terms. The Capsule SDK is made available under the Apache 2.0 license; these Terms govern your use of the hosted Service, not the open-source SDK itself.`,
  },
  {
    id: 'billing',
    title: '7. Billing and Plans',
    body: `Capsule offers a free Hobby plan and paid plans (Pro, Enterprise). Paid plans are billed in advance on a monthly or annual basis. All fees are non-refundable except as required by law or as expressly stated in your plan documentation. Capsule may change pricing with 30 days' advance notice. Failure to pay may result in service suspension. Taxes are your responsibility where applicable. Enterprise pricing is governed by a separate order form or agreement.`,
  },
  {
    id: 'privacy',
    title: '8. Privacy',
    body: `Your use of the Service is also governed by our Privacy Policy, which is incorporated into these Terms by reference. By using the Service, you consent to the collection and use of information as described in the Privacy Policy.`,
  },
  {
    id: 'ip',
    title: '9. Intellectual Property',
    body: `Capsule and its licensors retain all right, title, and interest in the Service, including all software, designs, trademarks, and documentation. These Terms do not grant you any rights to the Capsule name, logo, or other intellectual property except as expressly stated herein. Feedback or suggestions you provide about the Service may be used by Capsule without obligation to you.`,
  },
  {
    id: 'confidentiality',
    title: '10. Confidentiality',
    body: `Each party agrees to protect the other's confidential information with at least the same degree of care it uses for its own confidential information, and not to disclose it to third parties without prior written consent. This obligation does not apply to information that is publicly known, independently developed, or required to be disclosed by law.`,
  },
  {
    id: 'disclaimer',
    title: '11. Disclaimers',
    body: `THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT. CAPSULE DOES NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR FULLY SECURE. USE OF THE SERVICE IS AT YOUR SOLE RISK.`,
  },
  {
    id: 'liability',
    title: '12. Limitation of Liability',
    body: `TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, CAPSULE SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS, REVENUE, DATA, OR GOODWILL, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. CAPSULE'S TOTAL CUMULATIVE LIABILITY ARISING OUT OF OR RELATED TO THESE TERMS OR THE SERVICE SHALL NOT EXCEED THE GREATER OF (A) THE FEES PAID BY YOU IN THE TWELVE MONTHS PRECEDING THE CLAIM, OR (B) USD $100.`,
  },
  {
    id: 'termination',
    title: '13. Termination',
    body: `Either party may terminate these Terms at any time. You may cancel your account from the dashboard settings. Capsule may suspend or terminate your access immediately for material breach of these Terms, non-payment, or conduct harmful to other users or the Service. Upon termination, your right to use the Service ceases. Customer Data is retained for 30 days after termination, after which it may be permanently deleted. Sections 5, 9, 11, 12, and 14 survive termination.`,
  },
  {
    id: 'governing',
    title: '14. Governing Law and Disputes',
    body: `These Terms are governed by the laws of the jurisdiction in which Capsule, Inc. is incorporated, without regard to conflict of law principles. Any disputes shall first be submitted to good-faith negotiation. If unresolved, disputes shall be settled by binding arbitration, except that either party may seek injunctive relief in a court of competent jurisdiction for intellectual property violations. Class actions and jury trials are waived to the extent permitted by law.`,
  },
  {
    id: 'changes',
    title: '15. Changes to Terms',
    body: `We may update these Terms from time to time. Material changes will be communicated by email or a prominent notice in the dashboard at least 14 days before taking effect. Continued use of the Service after the effective date constitutes acceptance of the revised Terms. The current version is always available at capsule-five-delta.vercel.app/terms.`,
  },
  {
    id: 'contact',
    title: '16. Contact',
    body: `Questions about these Terms should be directed to legal@capsule.dev. For general support, visit support@capsule.dev or the documentation at docs.capsule.dev.`,
  },
];

export default function TermsPage() {
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
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
          <LogoMark size={28} />
          <span style={{ fontWeight: 600, fontSize: 15, letterSpacing: '-0.01em' }}>Capsule</span>
        </Link>
        <div style={{ display: 'flex', gap: 24, fontSize: 13.5, color: 'var(--text-secondary)' }}>
          <Link href="/privacy" style={{ color: 'var(--text-secondary)' }}>Privacy Policy</Link>
          <Link href="/login" style={{ color: 'var(--text-secondary)' }}>Log in</Link>
        </div>
      </header>

      <main style={{ maxWidth: 760, margin: '0 auto', padding: '64px 28px 96px' }}>
        {/* Title block */}
        <div style={{ marginBottom: 48 }}>
          <p style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 12 }}>Legal</p>
          <h1 style={{ fontSize: 36, fontWeight: 600, letterSpacing: '-0.025em', lineHeight: 1.1, marginBottom: 16 }}>
            Terms of Service
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
            Last updated: May 30, 2026 &nbsp;·&nbsp; Effective: May 30, 2026
          </p>
          <p style={{ color: 'var(--text-secondary)', marginTop: 20, lineHeight: 1.7 }}>
            Please read these Terms carefully before using Capsule. They explain what you can expect from us and what we expect from you.
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
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.75, fontSize: 14.5 }}>
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
          <Link href="/privacy" style={{ color: 'var(--text-secondary)' }}>Privacy Policy</Link>
          <span>·</span>
          <a href="mailto:legal@capsule.dev" style={{ color: 'var(--text-secondary)' }}>legal@capsule.dev</a>
          <span>·</span>
          <span>© 2026 Capsule, Inc.</span>
        </div>
      </main>
    </div>
  );
}
