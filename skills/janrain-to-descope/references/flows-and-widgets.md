# Janrain to Descope: Terminology and Console Setup

This file covers the words Janrain and Descope each use for similar ideas, and when to use the Descope Console instead of writing code. Read this alongside `implementation-nuances.md`, which covers how Janrain itself actually works.

## Contents

- [Terminology](#terminology)
- [Console vs. code](#console-vs-code)
- [Replacing Janrain's login screen](#replacing-janrains-login-screen)
- [Enterprise SSO](#enterprise-sso)

## Terminology

| Janrain term | What it means | Closest Descope term |
|---|---|---|
| Entity | One user's record | User |
| Entity Type | The user database itself | No exact match. Closest is a Descope Project. |
| Hosted Login | Janrain's current login product | Flow |
| The JavaScript SDK, or Capture | Janrain's older, still-supported login product | Flow |
| profiles | The list holding a user's connected social logins | Custom OAuth Providers |
| roles | The list holding a user's assigned roles | Roles and Permissions |
| Two-factor authentication | A one-time code sent by email or text, only on newer Janrain accounts | A one-time code step in a Flow |
| No equivalent, Janrain has no built-in concept of this | Separating one company's users from another's | Tenant |
| Region | A separate, siloed environment for a group of users (for example, US versus Europe) | No exact match. Descope doesn't require this kind of regional split by default. |

## Console vs. code

Before writing code for something user-facing, check whether it can be done in the Descope Console instead. This is usually faster and easier to change later.

Do in the Console:
- The sign-in and sign-up screens themselves
- Turning authentication methods on or off
- Adding a one-time code step, the equivalent of Janrain's two-factor authentication
- Setting up a social login provider a customer already had connected in Janrain
- Turning on passkeys, something worth mentioning to a customer specifically, since Janrain never supported this at all

Do in code:
- Checking whether a user is signed in before letting them see a page
- Anything that needs to run on your own server

## Replacing Janrain's login screen

If a customer is on Hosted Login, their users are redirected to a login page hosted by Janrain. The Descope equivalent is a Flow, either embedded directly in the customer's site or shown as its own page, both are supported.

If a customer's Janrain login screens showed different fields for different countries or brands (for example, one country's signup form asking for an extra field another one didn't), the same thing can be done in a Descope Flow using conditional logic, so one Flow can still show different fields depending on which site or region a user is signing up from.

If a customer is on the older JavaScript SDK instead of Hosted Login, their login is not a redirect at all, it's rendered directly on their own page using Janrain's JavaScript. This still gets replaced by a Descope Flow, but the starting point in their code looks different, since there's no redirect to remove, only an embedded widget to remove.

## Enterprise SSO

Before touching this, figure out which direction of SSO a customer actually has, since Janrain can be involved in two completely different ways, and mapping the wrong one to the wrong Descope feature leaves an application without working login entirely.

**Direction 1: Janrain consumes an outside company's login system (the common case).** If a customer's Janrain setup lets users sign in through their employer's own identity provider (SAML or OIDC, Okta is Akamai's own example), Janrain is acting as the relying party, consuming someone else's IdP. This maps to Descope's **SSO Setup Suite**, which configures an external IdP for a Descope tenant the same way. This is the direction covered elsewhere in this file and in `implementation-nuances.md`.

**Direction 2: Janrain itself acts as the shared login for a customer's own other applications.** Some Janrain customers register several of their own apps as separate OIDC clients under one Identity Cloud tenant, so a user logs into one and is automatically recognized on the others, a real, named capability Akamai calls single sign-on. This is Janrain acting as the identity provider, not the relying party. **This does not map to the SSO Setup Suite.** It maps to Descope's **Federated Applications**, which let Descope itself act as the identity provider for a customer's other apps.

Ask which direction is actually in use before recommending either. Checking whether SAML or OIDC is involved does not resolve this, both directions can use either protocol, what matters is which side of the connection Janrain is actually on.
