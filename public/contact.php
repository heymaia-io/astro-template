<?php
declare(strict_types=1);

require_once __DIR__ . '/contact.config.php';

header('Content-Type: application/json; charset=utf-8');

function respond(int $status, array $payload): void {
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE);
    exit;
}

function clean(string $value): string {
    // Strip CR/LF/NUL to prevent header injection; trim whitespace.
    return trim(str_replace(["\r", "\n", "\0"], '', $value));
}

function verifyTurnstile(string $token, string $remoteIp): bool {
    $payload = http_build_query([
        'secret'   => TURNSTILE_SECRET,
        'response' => $token,
        'remoteip' => $remoteIp,
    ]);

    $context = stream_context_create([
        'http' => [
            'method'        => 'POST',
            'header'        => "Content-Type: application/x-www-form-urlencoded\r\n",
            'content'       => $payload,
            'timeout'       => 5,
            'ignore_errors' => true,
        ],
    ]);

    $response = @file_get_contents(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        false,
        $context
    );

    if ($response === false) {
        error_log('[contact.php] Turnstile verify request failed');
        return false;
    }

    $decoded = json_decode($response, true);
    return is_array($decoded) && !empty($decoded['success']);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(405, ['ok' => false, 'error' => 'Método no permitido.']);
}

// Honeypot: silently accept bot submissions but send nothing.
if (!empty($_POST['_hp'] ?? '')) {
    respond(200, ['ok' => true]);
}

$turnstileToken = clean((string) ($_POST['cf-turnstile-response'] ?? ''));
if ($turnstileToken === '') {
    respond(400, ['ok' => false, 'error' => 'Completa la verificación de seguridad.']);
}

if (!verifyTurnstile($turnstileToken, $_SERVER['REMOTE_ADDR'] ?? '')) {
    respond(400, ['ok' => false, 'error' => 'Verificación de seguridad falló. Inténtalo de nuevo.']);
}

$name    = clean((string) ($_POST['name']    ?? ''));
$email   = clean((string) ($_POST['email']   ?? ''));
$phone   = clean((string) ($_POST['phone']   ?? ''));
$subject = clean((string) ($_POST['subject'] ?? ''));
// Message is the only field allowed to contain newlines (it's the body).
$message = trim(str_replace(["\r\n", "\r"], "\n", (string) ($_POST['message'] ?? '')));
$message = str_replace("\0", '', $message);

$missing = [];
if ($name    === '') $missing[] = 'name';
if ($email   === '') $missing[] = 'email';
if ($message === '') $missing[] = 'message';

if ($missing) {
    respond(400, ['ok' => false, 'error' => 'Faltan campos requeridos: ' . implode(', ', $missing) . '.']);
}

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    respond(422, ['ok' => false, 'error' => 'El correo electrónico no es válido.']);
}

$body  = "Nueva solicitud de contacto desde el sitio web\n";
$body .= "------------------------------------------------\n\n";
$body .= "Nombre:   {$name}\n";
$body .= "Correo:   {$email}\n";
if ($phone   !== '') $body .= "Teléfono: {$phone}\n";
if ($subject !== '') $body .= "Asunto:   {$subject}\n";
$body .= "\nMensaje:\n{$message}\n";

$mailSubject = $subject !== ''
    ? "[Contacto Web] {$subject}"
    : "[Contacto Web] Nueva solicitud — {$name}";

$headers = [];
$headers[] = 'From: ' . MAIL_FROM_NAME . ' <' . MAIL_FROM . '>';
$headers[] = 'Reply-To: ' . $name . ' <' . $email . '>';
$headers[] = 'Content-Type: text/plain; charset=UTF-8';
$headers[] = 'X-Mailer: PHP/' . phpversion();

$sent = mail(MAIL_TO, $mailSubject, $body, implode("\r\n", $headers), '-f' . MAIL_FROM);

if ($sent) {
    respond(200, ['ok' => true]);
}

error_log('[contact.php] mail() returned false');
respond(500, ['ok' => false, 'error' => 'No fue posible enviar el mensaje. Inténtalo más tarde.']);
