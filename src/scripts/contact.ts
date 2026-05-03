const ENDPOINT = '/contact.php';
const GENERIC_ERROR = 'No fue posible enviar el mensaje. Inténtalo más tarde.';

declare global {
  interface Window {
    turnstile?: {
      reset: (selector?: string | HTMLElement) => void;
    };
  }
}

const form = document.getElementById('contact-form') as HTMLFormElement | null;
const submitBtn = form?.querySelector('button[type="submit"]') as HTMLButtonElement | null;
const successEl = document.getElementById('form-success');
const errorEl = document.getElementById('form-error');
const turnstileEl = document.getElementById('turnstile-widget');

const submitBtnDefaultLabel = submitBtn?.textContent ?? 'Enviar';

function showSuccess(): void {
  successEl?.classList.remove('hidden');
  errorEl?.classList.add('hidden');
}

function showError(message: string): void {
  if (!errorEl) return;
  errorEl.textContent = message;
  errorEl.classList.remove('hidden');
  successEl?.classList.add('hidden');
}

function clearMessages(): void {
  successEl?.classList.add('hidden');
  errorEl?.classList.add('hidden');
}

function setSubmitting(isSubmitting: boolean): void {
  if (!submitBtn) return;
  submitBtn.disabled = isSubmitting;
  submitBtn.textContent = isSubmitting ? 'Enviando…' : submitBtnDefaultLabel;
}

function resetTurnstile(): void {
  if (turnstileEl) {
    window.turnstile?.reset(turnstileEl);
  }
}

async function submitContactForm(event: SubmitEvent): Promise<void> {
  event.preventDefault();
  if (!form) return;

  clearMessages();
  setSubmitting(true);

  try {
    const response = await fetch(ENDPOINT, {
      method: 'POST',
      body: new FormData(form),
      headers: { Accept: 'application/json' },
    });

    let payload: { ok?: boolean; error?: string } = {};
    try {
      payload = await response.json();
    } catch {
      payload = {};
    }

    if (response.ok && payload.ok) {
      form.reset();
      showSuccess();
    } else {
      showError(payload.error ?? GENERIC_ERROR);
    }
  } catch {
    showError(GENERIC_ERROR);
  } finally {
    setSubmitting(false);
    resetTurnstile();
  }
}

form?.addEventListener('submit', submitContactForm);
