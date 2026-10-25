'use client';

import { startAuthentication, startRegistration } from '@simplewebauthn/browser';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';
import '../persistence/Persistence.css';

const INITIAL_FORM = {
  name: '',
  role: '',
};

const ONBOARDING_STEPS = [
  { number: '01', title: 'Identity', description: 'Name the contributor who will own the future research record.' },
  { number: '02', title: 'Role', description: 'Capture the contributor role needed for this MVP session.' },
  { number: '03', title: 'Passkey', description: 'Create or use a passkey to bind the profile to the server session.' },
] as const;

type Contributor = {
  id: string;
  name: string;
  role: string;
  created_at?: string;
  updated_at?: string;
};

function createClientId() {
  return globalThis.crypto?.randomUUID?.() || ('idem_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2));
}

function scrollToForm() {
  document.getElementById('create-profile-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

export function OnboardingFlow() {
  const router = useRouter();
  const [form, setForm] = useState(INITIAL_FORM);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [currentContributor, setCurrentContributor] = useState<Contributor | null>(null);
  const [createdContributor, setCreatedContributor] = useState<Contributor | null>(null);
  const [isCreatingProfile, setIsCreatingProfile] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [error, setError] = useState('');
  const [idempotencyKey] = useState(() => createClientId());

  useEffect(() => {
    let cancelled = false;
    async function loadSession() {
      try {
        const response = await fetch('/api/me');
        if (response.status === 401) {
          return;
        }
        if (!response.ok) {
          throw new Error('Unable to restore contributor.');
        }
        const payload = (await response.json()) as Contributor;
        if (!cancelled) {
          setCurrentContributor(payload);
          router.replace('/contribute');
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : 'Unable to restore contributor.');
        }
      } finally {
        if (!cancelled) {
          setIsLoadingSession(false);
        }
      }
    }
    loadSession();
    return () => {
      cancelled = true;
    };
  }, [router]);

  useEffect(() => {
    if (!createdContributor) {
      return undefined;
    }
    router.replace('/contribute');
  }, [createdContributor, router]);

  async function clearAndRestart() {
    try {
      await fetch('/api/session/logout', { method: 'POST' });
    } catch {
      // best effort
    }
    setCreatedContributor(null);
    setCurrentContributor(null);
    setForm(INITIAL_FORM);
    setError('');
  }

  async function continueWithPasskey() {
    setIsLoggingIn(true);
    setError('');
    try {
      const optionsResponse = await fetch('/api/passkeys/authentication/options', { method: 'POST' });
      const optionsPayload = await optionsResponse.json().catch(() => ({}));
      if (!optionsResponse.ok) {
        throw new Error(optionsPayload.error || 'Unable to start passkey authentication.');
      }
      const authenticationResponse = await startAuthentication({ optionsJSON: optionsPayload.options });
      const verifyResponse = await fetch('/api/passkeys/authentication/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ authentication_response: authenticationResponse }),
      });
      const verifyPayload = await verifyResponse.json().catch(() => ({}));
      if (!verifyResponse.ok) {
        throw new Error(verifyPayload.error || 'Passkey verification failed.');
      }
      const contributor = verifyPayload as Contributor;
      setCurrentContributor(contributor);
      router.replace('/contribute');
    } catch (passkeyError) {
      setError(passkeyError instanceof Error ? passkeyError.message : 'Passkey login failed.');
    } finally {
      setIsLoggingIn(false);
    }
  }

  async function createProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.name.trim() || !form.role.trim()) {
      setError('Name and role are required to create a profile.');
      return;
    }
    setIsCreatingProfile(true);
    setError('');
    try {
      const optionsResponse = await fetch('/api/passkeys/registration/options', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const optionsPayload = await optionsResponse.json().catch(() => ({}));
      if (!optionsResponse.ok) {
        throw new Error(optionsPayload.error || 'Unable to start passkey registration.');
      }
      const registrationResponse = await startRegistration({ optionsJSON: optionsPayload.options });
      const createResponse = await fetch('/api/contributors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify({ name: form.name, role: form.role, registration_response: registrationResponse }),
      });
      const createPayload = await createResponse.json().catch(() => ({}));
      if (!createResponse.ok) {
        throw new Error(createPayload.error || 'Unable to create contributor.');
      }
      const contributor = createPayload as Contributor;
      setCreatedContributor(contributor);
      setCurrentContributor(contributor);
      router.replace('/contribute');
    } catch (createError) {
      setError(createError instanceof Error && createError.message ? createError.message : 'Unable to create contributor. Try again or use an existing passkey.');
    } finally {
      setIsCreatingProfile(false);
    }
  }

  const activeContributor = createdContributor || currentContributor;

  return (
    <div className='persistence-shell'>
      {activeContributor ? (
        <section className='persistence-hero' aria-labelledby='active-session-title'>
          <p className='persistence-kicker'>Session Ready</p>
          <h1 id='active-session-title'>Welcome back, {activeContributor.name}.</h1>
          <p className='persistence-intro'>
            Active Contributor: <strong>{activeContributor.role}</strong> &bull; <span style={{ opacity: 0.85 }}>{activeContributor.id}</span>
          </p>
          <div className='persistence-actions' style={{ marginTop: '1.25rem' }}>
            <button className='persistence-button persistence-button-primary' onClick={() => router.push('/contribute')} type='button'>
              Continue to Contribute
            </button>
            <button className='persistence-button persistence-button-secondary' onClick={clearAndRestart} type='button'>
              Switch Account / Start Over
            </button>
          </div>
        </section>
      ) : (
        <>
          <section className='persistence-hero' aria-labelledby='onboarding-title'>
            <p className='persistence-kicker'>Onboarding</p>
            <h1 id='onboarding-title'>Set up contributor access.</h1>
            <p className='persistence-intro'>New contributors create a profile with a passkey. Returning contributors continue with a passkey and the server restores the signed session.</p>
            <div className='persistence-actions' style={{ marginTop: '1.25rem' }}>
              <button className='persistence-button persistence-button-primary' onClick={continueWithPasskey} disabled={isLoggingIn} type='button'>
                {isLoggingIn ? 'Opening Passkey...' : 'Continue with Passkey'}
              </button>
              <button className='persistence-button persistence-button-secondary' onClick={scrollToForm} type='button'>
                Create Profile
              </button>
            </div>
          </section>

          <section className='persistence-panel' aria-labelledby='onboarding-form-title' id='create-profile-form'>
            <h2 id='onboarding-form-title'>Contributor profile</h2>
            <div className='persistence-step-rail' aria-label='Onboarding steps'>
              {ONBOARDING_STEPS.map((step) => (
                <article className='persistence-step' key={step.number}>
                  <div className='persistence-step-number'>{step.number}</div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </article>
              ))}
            </div>
            {error ? <p className='persistence-error' role='alert'>{error}</p> : null}
            <form className='persistence-form' onSubmit={createProfile}>
              <div className='persistence-fields'>
                <div className='persistence-field'>
                  <label htmlFor='onboarding-name'>Name</label>
                  <input
                    id='onboarding-name'
                    className='persistence-input'
                    type='text'
                    value={form.name}
                    onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                    placeholder='e.g. Chiranjeevi PK'
                    autoComplete='name'
                  />
                </div>
                <div className='persistence-field'>
                  <label htmlFor='onboarding-role'>Role / Expertise</label>
                  <input
                    id='onboarding-role'
                    className='persistence-input'
                    type='text'
                    value={form.role}
                    onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}
                    placeholder='e.g. Jr AI Automation Engineer'
                    autoComplete='organization-title'
                  />
                </div>
              </div>
              <div className='persistence-note'>Step 3 creates a passkey, then the server links that credential to the new contributor profile.</div>
              <div className='persistence-actions'>
                <button className='persistence-button persistence-button-primary' type='submit' disabled={isCreatingProfile}>
                  {isCreatingProfile ? 'Creating Passkey...' : 'Create Passkey'}
                </button>
                <button className='persistence-button persistence-button-secondary' type='button' onClick={clearAndRestart}>Back Home</button>
              </div>
            </form>
          </section>
        </>
      )}
      {isLoadingSession ? <p className='persistence-note'>Loading your signed session...</p> : null}
    </div>
  );
}