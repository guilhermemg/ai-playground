"""Transactional email bodies for AI Headshots (welcome, payment, generation)."""

from __future__ import annotations


def welcome_after_signup(name: str | None, verify_url: str) -> tuple[str, str]:
    """
    Subject and plain-text body for the email sent right after account creation.
    Supports online payment (CTA) and sets expectations for image-generation notifications.
    """
    display = (name or "there").strip() or "there"
    subject = "Bem-vindo ao AI Headshots — confirme seu e-mail"
    body = f"""Olá, {display},

Sua conta no AI Headshots foi criada com sucesso.

Confirme seu endereço de e-mail para ativar sua conta e habilitar pagamentos online com segurança:
{verify_url}

Depois da confirmação, você poderá concluir sua compra e acompanhar a geração das suas fotos profissionais.
Enviaremos outro e-mail quando suas imagens estiverem prontas ou se precisarmos de algum ajuste.

Abraços,
Equipe AI Headshots
"""
    return subject, body


def payment_receipt(order_id: str, amount_display: str) -> tuple[str, str]:
    subject = f"Pagamento confirmado — pedido {order_id}"
    body = f"""Recebemos seu pagamento ({amount_display}).

Pedido: {order_id}

Em breve começaremos a gerar seu pacote de fotos. Você receberá um e-mail quando o processamento for concluído.

— AI Headshots
"""
    return subject, body


def generation_complete(job_id: str, download_hint: str) -> tuple[str, str]:
    subject = "Suas fotos profissionais estão prontas"
    body = f"""Boas notícias: a geração do seu ensaio foi concluída.

Referência do job: {job_id}
{download_hint}

Obrigado por usar o AI Headshots.
"""
    return subject, body
