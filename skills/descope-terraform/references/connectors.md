# Connectors Reference

Connectors integrate Descope with third-party services. All connectors are configured under the `connectors` block of `descope_project`.

All connectors share these fields:
- `name` (String, Required) - Connector name
- `description` (String, Optional) - Description
- `id` (String, Read-Only) - Connector ID for referencing in flows

## Email & SMS Connectors

### smtp

```hcl
smtp = [{
  name     = "SMTP Server"
  host     = "smtp.example.com"
  port     = 587
  user     = var.smtp_user
  password = var.smtp_password
}]
```

### sendgrid

```hcl
sendgrid = [{
  name         = "SendGrid"
  auth_token   = var.sendgrid_api_key
  sender_email = "noreply@example.com"
  sender_name  = "My App"
}]
```

### ses

```hcl
ses = [{
  name       = "AWS SES"
  access_key = var.ses_access_key
  secret_key = var.ses_secret_key
  region     = "us-east-1"
  email      = "noreply@example.com"
}]
```

### postmark

```hcl
postmark = [{
  name       = "Postmark"
  server_token = var.postmark_token
}]
```

### twilio_core

```hcl
twilio_core = [{
  name        = "Twilio SMS"
  account_sid = var.twilio_sid
  auth_token  = var.twilio_token
  sender      = "+15551234567"
}]
```

### sns

```hcl
sns = [{
  name       = "AWS SNS"
  access_key = var.sns_access_key
  secret_key = var.sns_secret_key
  region     = "us-east-1"
}]
```

### generic_email_gateway / generic_sms_gateway

Custom email/SMS gateways via HTTP.

## HTTP & Webhook Connectors

### http

```hcl
http = [{
  name         = "My API"
  base_url     = "https://api.example.com"
  bearer_token = var.api_token
}]
```

### audit_webhook

```hcl
audit_webhook = [{
  name     = "Audit Webhook"
  base_url = "https://audit.example.com/events"
}]
```

## Observability & Logging Connectors

| Connector | Key Fields |
|-----------|------------|
| `datadog` | `api_key`, `site` |
| `splunk` | `token`, `url` |
| `sumologic` | `url` |
| `newrelic` | `api_key`, `data_center` |
| `coralogix` | `api_key`, `endpoint` |
| `google_cloud_logging` | `credentials_json`, `project_id`, `log_id` |
| `opentelemetry` | `endpoint` |
| `mixpanel` | `token`, `service_account_username`, `service_account_secret` |
| `amplitude` | `api_key` |
| `segment` | `write_key` |
| `mparticle` | `api_key`, `api_secret` |

## Cloud Storage Connectors

### aws_s3

```hcl
aws_s3 = [{
  name     = "S3 Audit Logs"
  role_arn = "arn:aws:iam::ACCOUNT:role/role-name"
  region   = "us-east-1"
  bucket   = "audit-logs"
}]
```

## Identity Verification Connectors

| Connector | Purpose |
|-----------|---------|
| `incode` | Identity verification |
| `rekognition` | AWS facial recognition |

## Fraud & Risk Connectors

| Connector | Purpose |
|-----------|---------|
| `recaptcha` | Google reCAPTCHA v2/v3 |
| `recaptcha_enterprise` | Google reCAPTCHA Enterprise |
| `hcaptcha` | hCaptcha verification |
| `turnstile` | Cloudflare Turnstile |
| `arkose` | Arkose Labs bot detection |
| `fingerprint` | Fingerprint Pro device identification |
| `fingerprint_descope` | Fingerprint via Descope integration |
| `forter` | Forter fraud prevention |
| `sardine` | Sardine fraud detection |
| `darwinium` | Darwinium risk assessment |
| `traceable` | Traceable API security |
| `radar` | Radar location verification |
| `bitsight` | BitSight security ratings |

## CRM & Business Connectors

| Connector | Purpose |
|-----------|---------|
| `salesforce` | Salesforce CRM integration |
| `salesforce_marketing_cloud` | Salesforce marketing |
| `hubspot` | HubSpot CRM |
| `intercom` | Intercom messaging |
| `devrev_grow` | DevRev integration |
| `docebo` | Docebo LMS |

## Directory & Identity Connectors

| Connector | Purpose |
|-----------|---------|
| `ldap` | LDAP directory |
| `ping_directory` | Ping Identity directory |
| `firebase_admin` | Firebase Admin |
| `supabase` | Supabase integration |

## Database Connectors

### sql

```hcl
sql = [{
  name              = "PostgreSQL"
  connection_string = var.db_connection_string
}]
```

## Translation Connectors

| Connector | Purpose |
|-----------|---------|
| `aws_translate` | AWS Translate |
| `google_cloud_translation` | Google Cloud Translation |
| `lokalise` | Lokalise localization |
| `smartling` | Smartling translation |

## Other Connectors

| Connector | Purpose |
|-----------|---------|
| `abuseipdb` | IP reputation checking |
| `hibp` | Have I Been Pwned breach checking |
| `zerobounce` | Email validation |
| `slack` | Slack notifications |
| `google_maps_places` | Google Maps Places API |
| `elephant` | Elephant integration |
| `unibeam` | Unibeam integration |
| `telesign` | TeleSign verification |
| `eight_by_eight_viber` | 8x8 Viber messaging |
| `eight_by_eight_whatsapp` | 8x8 WhatsApp messaging |
| `external_token_http` | External token validation |
| `twilio_verify` | Twilio Verify service |

## Audit Filters

Audit-capable connectors support filtering:

```hcl
audit_filters = [
  {
    key      = "actorId"        # Required
    operator = "equals"         # Required
    values   = ["user-123"]     # Required
  }
]
```

Additional audit fields: `audit_enabled` (Boolean), `troubleshoot_log_enabled` (Boolean).
