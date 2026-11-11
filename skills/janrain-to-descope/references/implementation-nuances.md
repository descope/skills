# Janrain (Akamai Identity Cloud) Migration: Implementation Notes

Janrain was acquired by Akamai in 2019. Its login product is called Hosted Login, and the platform is officially named Akamai Identity Cloud, though most existing customers still call it Janrain. This file uses "Janrain" throughout since that is the name most people searching for this will recognize.

This file explains how Janrain actually works, and where it differs from Descope. It does not explain Descope's own API in detail. For current Descope API shapes and method names, use the Descope Docs MCP or Descope's documentation directly.

Akamai has announced Identity Cloud will reach end of life on December 31, 2027, and stopped adding new features at the end of 2024. This is why migrations off it are urgent for many customers.

## Contents

- [Architecture and how login actually works](#architecture-and-how-login-actually-works)
- [No official SDK exists for Hosted Login, but an older one still does](#no-official-sdk-exists-for-hosted-login-but-an-older-one-still-does)
- [The JavaScript SDK (Capture), if a customer is still on it](#the-javascript-sdk-capture-if-a-customer-is-still-on-it)
- [How to read user data (schema basics)](#how-to-read-user-data-schema-basics)
- [Passwords](#passwords)
- [Social login and account linking](#social-login-and-account-linking)
- [Roles](#roles)
- [Multi-tenancy](#multi-tenancy)
- [Multiple regions](#multiple-regions)
- [Two-factor authentication (MFA)](#two-factor-authentication-mfa)
- [Account merging](#account-merging)
- [What Janrain doesn't support](#what-janrain-doesnt-support)
- [Consent and GDPR data](#consent-and-gdpr-data)
- [Exporting users in bulk](#exporting-users-in-bulk)
- [Tokens and claims](#tokens-and-claims)
- [Session handling and logout](#session-handling-and-logout)
- [What happens to old sessions when you cut over](#what-happens-to-old-sessions-when-you-cut-over)
- [Downstream integrations (webhooks and third-party syncs)](#downstream-integrations-webhooks-and-third-party-syncs)
- [Getting help from Akamai](#getting-help-from-akamai)
- [Common errors and what they actually mean](#common-errors-and-what-they-actually-mean)
- [Framework notes](#framework-notes)

---

## Architecture and how login actually works

Janrain's login product, called Hosted Login, is built on standard OpenID Connect (OIDC). This is good news: it means Janrain behaves like any other standards-based login provider, the same category as Auth0 or Okta, rather than something proprietary.

The basic flow is the standard OIDC authorization code flow with PKCE:

1. Your app sends the user to Janrain's authorize endpoint.
2. The user logs in (password, or a social login like Google or Facebook).
3. Janrain redirects back to your app with a code.
4. Your app exchanges that code for tokens at Janrain's token endpoint.

Janrain also publishes a standard OIDC discovery document, the same mechanism most modern OIDC libraries use to auto-configure themselves. This means you generally do not need to hardcode every endpoint URL by hand, a library that supports "OIDC discovery" or "auto-discovery" can read this document and configure itself from just one URL (the issuer URL).

## No official SDK exists for Hosted Login, but an older one still does

Janrain does not provide its own client library for Hosted Login, the current, standard login product. Akamai's own documentation tells developers to use a standard, off-the-shelf OIDC library instead (for example, a generic OIDC library for Node.js, or AppAuth for mobile apps).

**However, a real, official older product does exist, and some customers are still on it.** Before Hosted Login, Janrain offered a client-side library called the JavaScript SDK, also called Capture. Akamai's own documentation says it is still supported for existing customers using it, but new customers are directed to Hosted Login instead.

**This matters a lot, and needs to be checked first, before anything else in this file.** The JavaScript SDK and Hosted Login work completely differently:

- The JavaScript SDK is embedded directly into a site's pages as JavaScript and CSS files. Sign-in and registration are rendered by calling functions like `janrain.capture.ui.renderScreen('signIn')`, not by redirecting to a hosted login page.
- After a successful login, the JavaScript SDK stores an access token directly in the browser's local storage, under the key `janrainCaptureToken`. That token is only valid for one hour. If a site wants users to stay logged in longer than that, it has to send that token to its own server and build its own longer session on top of it.
- Social login for the JavaScript SDK is configured through a separate dashboard, with its own list of approved website addresses, completely separate from how Hosted Login handles social login.
- Everything else in this file, the OIDC login flow, the discovery document, the token claims, assumes a customer is on Hosted Login, not the JavaScript SDK.

**Before doing anything else with a customer's migration, confirm which of these two they are actually using.** If they're still on the JavaScript SDK, most of the rest of this file does not directly apply, and their migration will look more like removing embedded widget code and replacing client-side session handling, rather than swapping one OIDC-based login for another. See the JavaScript SDK section below for what actually applies to them instead.

If there is no official SDK for the situation the customer is actually in, integration is a standard, off-the-shelf sign-in library pointed at Janrain's endpoints instead.

## The JavaScript SDK (Capture), if a customer is still on it

If a customer is on the JavaScript SDK rather than Hosted Login, here is what actually applies to them. Everything else in this file (the OIDC login flow, discovery document, token claims, and so on) is written for Hosted Login and does not directly apply here.

**How it works:** the sign-in and registration forms are rendered directly on the customer's own page by calling functions like `janrain.capture.ui.renderScreen('signIn')`, not by redirecting to a hosted page. Being "logged in," from the browser's point of view, just means a valid access token is sitting in local storage under the key `janrainCaptureToken`.

**The token is short-lived, and there is no way to refresh it from the browser.** The access token is only valid for one hour, and Akamai does not allow extending this, for security reasons. There is no client-side refresh mechanism at all. If a customer wants users to stay signed in longer than an hour, which most sites do, they've already had to build their own server-side solution: storing the token on their own server, and calling a separate server-side API to get a fresh one before the old one expires, then feeding it back to the browser. This means any real customer on this SDK almost certainly already has custom server-side session code, since Akamai gives them nothing to handle this automatically.

**Adding a field to the sign-up form isn't just a UI change.** Custom fields on the registration form are tied directly to the underlying stored fields, adding one to the form requires also adding it to the customer's stored user data structure. The two can't be changed independently.

**Social login is configured through a completely separate dashboard**, sometimes called the Social Login Dashboard or Engage, with its own settings for which website addresses are allowed to use it.

**Something worth knowing about this SDK's social login specifically, though it's less urgent than it might first appear:** the dashboard used to manage social login settings for this SDK (called the Social Login Dashboard, or Engage) stopped working March 31, 2026. Apps that weren't actively being used were removed at that point, but apps still in active use keep working normally, on the same general shutdown timeline as everything else, the end of 2027. Per Akamai's own documentation, customers with an Akamai contract can still request changes after that date by submitting a support ticket; customers without a contract can no longer make changes to their social apps at all. So a customer on this SDK using social login likely doesn't face an earlier deadline for the login functionality itself, but they may have already lost the ability to reconfigure or manage their social login settings since that date. If a customer needs to make changes to their social login setup, this is worth confirming directly with Akamai rather than assumed either way.

**Does user data end up stored the same way as Hosted Login users?** The strong signal from Janrain's own documentation is yes, both ultimately create the same kind of user record in the same underlying user database. However, no single page states this outright as a fact, it's a reasonable read across several separate pages, not a confirmed statement. If a specific customer has a mix of JavaScript SDK and Hosted Login users, and the plan depends on exporting both the same way, this should be checked directly against their account rather than assumed.

**On cancelling old sessions during a cutover:** the same "no way to cancel everything at once" limitation that applies to Hosted Login also applies here, only one user's tokens can be cancelled at a time, never the whole account in one call. This matters less here than it does for Hosted Login, though, since a JavaScript SDK access token expires on its own after one hour no matter what, so anything left over closes itself out quickly either way.

**Do not assume this customer has any GDPR consent data at all just because it's common on Hosted Login.** The JavaScript SDK has no built-in consent feature, no consent screen, and no mention of consent anywhere in its own customization documentation. If a customer on this SDK has consent data, they built it themselves, for example as a custom checkbox on their sign-up form. Ask them directly whether and how they've been capturing consent, don't assume the standard Hosted Login pattern applies.

## How to read user data (schema basics)

Janrain stores each user as a record with a set of fields, similar to a row in a database. A few of those fields are not a single value, but a list that can hold more than one entry. Janrain calls this kind of field a "plural." Two you will run into during a migration:

- **profiles**, a list of the social logins a user has connected (for example, one entry for Google, another for Facebook).
- **roles**, a list of role assignments for the user.

You do not need to remember the word "plural." The important thing is: some fields on a user hold a single value, and a few hold a list of entries.

## Passwords

Janrain stores every user's password as a bcrypt hash. Descope also accepts bcrypt hashes when importing users, so in principle, a customer's existing passwords can be carried over with no password reset required.

**This is not guaranteed for every customer, and must be confirmed before promising it.** Janrain's documentation shows an example of a normal user-record read returning the password hash directly. However, we could not find any independent confirmation, from another developer, from a migration vendor, or from anyone outside Janrain's own documentation, that this actually happens in practice for a real account. It is possible a specific customer's account has restrictions that prevent this.

**Before telling a customer their passwords will migrate:** confirm this directly, either by making a real test call against the customer's own account, or by asking Akamai support or the customer's account team. Do not assume it will work just because it is documented.

**If password hashes cannot be exported for a specific customer:** do not fall back to a "wait for users to log in gradually" style migration. Janrain is being shut down soon, so there usually isn't enough time left for a gradual migration to reach every user. Recommend a password reset flow instead, where users set a new password the first time they sign in after the migration.

## Social login and account linking

The **profiles** list holds every social login a user has connected (Google, Facebook, and similar). Each entry includes:

- which provider it is
- the provider's own ID for that user
- a photo URL, if available

If a customer doesn't use social login at all, their users simply have no entries here.

**One thing we could not confirm:** if a customer also lets users sign in through an outside company login system (sometimes called enterprise SSO, using SAML or another standard), we don't know for certain whether those logins are stored in this same list, or somewhere else entirely. Janrain's documentation does not say either way. If a customer uses this kind of login, this needs to be checked directly against their account before assuming their data is stored the same way as social logins.

There is no way to directly copy a user's social login connections into Descope during a bulk import. The practical approach: let each user reconnect their social login the first time they sign in after the migration.

## Roles

The **roles** list holds a user's assigned roles. Each entry has a display name and a value.

**We could not find a real example anywhere of this list actually being returned by a normal data read**, only that it's listed as part of the schema. This is a weaker level of confidence than passwords, where at least one real example exists. Treat a customer's roles data the same way as passwords: confirm it can actually be read out before relying on it in a migration plan.

## Multi-tenancy

Janrain has no built-in concept of separate tenants or organizations the way Descope does. There is no setting that keeps one company's users cleanly separate from another's within the same account.

In practice, customers handle this one of two ways:

- **Most customers**: everyone's users live together in one shared user database. If needed, you can tell which app or site a user first signed up on, since Janrain keeps a record of that.
- **Some customers**: they set up a completely separate user database per business unit or brand, when the two need to be kept fully apart.

When planning a Descope Tenant structure for a customer, ask them directly which of these two setups they have. Do not assume it maps cleanly to Descope Tenants without checking, since Janrain simply wasn't built with that concept in mind.

## Multiple regions

If a customer's users are spread across different regions (for example, separate populations in the US, Europe, and Asia), each region is its own separate, siloed environment, with its own web address, its own credentials, and its own set of user records. There's no single call that reaches across all of them at once. A migration needs to be planned and run once per region, not once for the whole account.

The way the export and import process works is the same regardless of region, but the actual limits (how many users per page, any rate limits) have not been confirmed to be identical in every region. If a customer has a large population in a specific region, check that region's actual behavior directly rather than assuming it matches what was seen in another region.

## Two-factor authentication (MFA)

Two-factor authentication in Janrain only works on the newer version of Hosted Login (called "v2"). The older version ("v1") does not support it at all. Confirm which version a customer is on before assuming MFA is even possible for them.

Once turned on, MFA applies to everyone signing in through that application, there is no per-user on/off switch, and no per-login skip option built in for the end user.

How it works for the end user:
1. The user signs in normally with their password (or social login).
2. If they have a phone number and an email on file, they're asked to choose where to get their code, by text or by email.
3. If they only have an email on file, the code is sent there automatically.
4. They enter a 6-digit code, which expires after 10 minutes.
5. Once entered correctly, they're signed in.

There's also a "remembered device" setting, so a user doesn't have to enter a code every single time on a device they've used before. By default, that lasts 30 days.

**Important for migration:** Janrain does not store a simple "this user has MFA turned on" flag anywhere. Instead, whether MFA happens is decided at login time, based on whether the user has an email or phone number on file. This means you can migrate the phone number and email fields themselves, but there is nothing else to carry over marking someone as "enrolled." The equivalent in Descope is a one-time code step added to a sign-in flow.

## What Janrain doesn't support

Two things worth knowing, confirmed absent from the platform, not just under-documented, checked directly against Akamai's own feature-list pages.

**Passkeys.** Janrain has never supported passkeys or WebAuthn, the modern, passwordless sign-in method built into phones and computers (Face ID, Touch ID, Windows Hello, and similar). This is true across the platform's entire history, and won't change before it shuts down, since it's in feature-frozen maintenance mode. This is a genuine, positive selling point for a migration to Descope, worth mentioning to a customer as something they gain, not just something they're moving.

**SCIM provisioning.** Janrain also has no support for automatically creating, updating, or removing users based on an outside system like an HR tool or a corporate directory. If a customer wants this, they've had to build it themselves against Janrain's ordinary data API, there's no standard integration for it. Confirm whether Descope's own SCIM support actually covers what a specific customer needs before treating this as a clean win, don't assume parity without checking.

## Account merging

Janrain has a behavior with no direct equivalent in Descope, worth knowing about specifically: if someone first signs up with an email and password, and later signs in using a social login (like Google) that uses the same email address, Janrain notices this and offers to merge the two into one account.

If this isn't accounted for during a migration, it's possible to end up with duplicate accounts for the same real person, one from their original signup, and one created later from their social login.

## Consent and GDPR data

If a customer collects consent for things like marketing emails, or tracks acceptance of a privacy policy or terms of service, this is worth treating with more care than most other data during a migration, since getting it wrong is a compliance question, not just a data-quality one.

**A single user's current consent status can be read**, using the same general mechanism used for the rest of a user's data. But there is no confirmed way to pull a full, complete history of consent changes for every user in one bulk export. Janrain's own documentation, when asked this same question, points to building your own logging of consent changes over time, rather than offering a built-in bulk export. There is also a separate download of consent history through the Console, but it only covers the most recent 90 days per user.

**Privacy policy and terms of service acceptance work differently from marketing consent, and have a real gap.** Marketing consent includes a timestamp of when it was last updated. Acceptance of legal terms, on the other hand, is tracked only as a list of version identifiers a user has agreed to (for example, having agreed to version 1 of a privacy policy). There is no confirmed timestamp showing exactly when a specific version was accepted, only whether it was accepted at all.

**What this means in practice:** if a customer needs to prove, after migrating, exactly when a specific user agreed to a specific version of their terms, that information may not exist anywhere to migrate in the first place, only whether they agreed, not when. This should be raised directly with any customer who has real compliance requirements around this, rather than assumed to be available.

**Whether to carry old consent forward, or ask users to re-confirm it after migrating, is not something Janrain's own documentation takes a position on.** This is a real, undocumented gap, not a technical detail we're missing, it's a genuine legal and compliance decision for the customer to make with their own legal team, not something to decide on their behalf.

**The same kind of gap exists for deletion requests, not just consent.** If a customer has a process for deleting a user's data on request (a right-to-erasure request), Janrain's documentation confirms deleting a user's record is permanent, but leaves real questions open: whether that user's audit log history is also deleted or survives, and how long deletion actually takes to fully take effect everywhere. More concretely, if a customer syncs data to Salesforce Marketing Cloud, syncing a deletion is a separate, optional setting that isn't turned on by default. If a customer hasn't specifically enabled it, deleting a user in Janrain does not remove that person's data from Salesforce Marketing Cloud. Ask any customer using this integration whether that setting is actually turned on, since if it isn't, they may have data sitting there that they believe was already deleted.

## Exporting users in bulk

To pull all of a customer's users out of Janrain, you make repeated calls asking for a batch of user records at a time, then keep asking for the next batch until there's nothing left.

Unlike some other providers, this doesn't get slower or break down as the number of users grows. Janrain's own documentation describes using this same method for accounts with more than 100,000 users.

A few practical details, per Akamai's own guidance on querying large data sets:
- You can ask for only the specific fields you need per user, which keeps each request smaller and faster.
- Akamai recommends keeping each request under about 10 seconds.
- For very large exports (roughly 100,000+ users), Akamai asks that you let them know ahead of time, so it doesn't strain shared resources.
- The credentials needed to make these calls are generated in Janrain's admin console, and only need read access, not the ability to change anything.

**On the Descope side, don't assume a full export batch fits into one import call.** Descope's batch import allows up to 100 users per call if any of them include a plaintext password, but has no stated limit when importing password hashes instead, which is the normal case for a real migration. Since Descope doesn't publish an exact number for that case, start with a smaller batch, something like 100 to 250 users, and only increase it if testing shows no problems, rather than assuming Janrain's own documented per-page export limit of up to 1000 users (per Janrain's Entity API reference) will always go through cleanly on the Descope side. Also keep in mind: if even one user in a batch needs a plaintext temporary password instead of a hash, that single user caps the entire batch at 100, so keep those users in their own separate, smaller batches.

## Tokens and claims

When a user logs in, Janrain gives your app some information about them (their email, name, and so on) bundled into a token. This is where a common surprise happens:

**None of a user's actual information (email, name, photo) is included automatically.** You have to explicitly ask for it. If your app expects to read a user's email or name right after login and doesn't explicitly request it, it will come back empty.

A user's unique ID inside the token is always the same value as their unique ID in their stored record. This is useful: when migrating a user, you can match them to their old Janrain identity using this same ID, with no extra lookup needed.

Sign-in sessions last up to 1 hour by default before needing to refresh, and a user typically stays signed in for up to 90 days without having to log in again, unless they log out.

## Session handling and logout

A very easy mistake to make on your first integration: **logging a user in through Janrain does not automatically create a session in your own app.** Janrain's own login state and your application's login state are two separate things. Your app needs to create and manage its own session after a successful login, Janrain won't do this for you.

To fully log a user out, you need to do two things: end their session in your own app, and also tell Janrain to end its session, otherwise the user could still be considered logged in by Janrain even though your app thinks they're logged out.

## What happens to old sessions when you cut over

This is a genuine, confirmed gap in Janrain's own documentation, worth flagging directly to any customer doing a hard cutover:

Ending a user's Janrain session does not automatically cancel any tokens already issued to them. Those tokens keep working on their own until they naturally expire, up to 90 days by default, unless someone explicitly cancels them one by one. There is no single "cancel everything at once" option for an entire account, only a way to do it one user at a time.

Janrain's own documentation doesn't say whether this matters for a migration cutover, or what to do about it. If a customer is doing a hard cutover away from Janrain, this should be raised as a decision they need to make: either accept that old sessions may still work for a while after cutover, or plan to cancel them individually across their whole user base.

## Downstream integrations (webhooks and third-party syncs)

If a customer has other systems (a CRM, a marketing platform, an analytics tool) set up to receive real-time notifications whenever a user signs up or updates their profile, check for this before cutover, since these will silently stop working once Janrain shuts down, separate from the user data migration itself.

Two things to look for:
- **Webhooks**, real-time notifications for user creation, updates, and deletion. Descope has a direct equivalent, but it's worth knowing Descope's version is not quite real-time and includes some built-in throttling, whereas Janrain's is closer to instant. If a customer's downstream system is sensitive to delay, flag this difference to them.
- **The Integration Bus**, a separate, paid add-on some customers use to sync data to outside platforms, most commonly Salesforce Marketing Cloud. This is not a standard feature, only some customers will have it. **There is no ready-made Descope equivalent for this specific use case today.** Descope's Salesforce connector reads from Salesforce during login, it doesn't sync anything into a marketing list. Descope's Salesforce Marketing Cloud connector is only for sending sign-in codes and magic links through it, not for keeping a subscriber list current. If a customer relies on this feature, they'd need to build something custom, for example triggering their own sync into Salesforce Marketing Cloud from Descope's webhook events, be upfront with them that this is a real gap, not something already covered.

Janrain's documentation doesn't say what happens to these downstream connections when the platform shuts down, the same kind of silence found around session handling. Treat this the same way: raise it directly with the customer as something to plan for, rather than assuming it resolves itself.

## Getting help from Akamai

A few things about a customer's account require Akamai's own involvement, not something they can configure themselves. Worth knowing which ones, since some carry real lead time.

Things that need a one-time conversation with an Akamai representative, but no ongoing cost mentioned: setting up an account for the first time, custom domain setup, recovering lost configuration credentials, and certain less common social login providers needing extra setup.

Things that involve a real contract or paid engagement: getting Akamai's own help with a migration off the platform, and enabling the Integration Bus (the Salesforce Marketing Cloud sync mentioned earlier) in the first place.

**Important if a customer wants Akamai's help migrating:** Akamai's own migration assistance only covers their side, helping extract and prepare data out of Janrain. It does not cover setting up the Descope side. Don't let a customer assume engaging Akamai covers the whole migration.

If a customer doesn't already have an Akamai contact, Akamai's own end-of-life documentation also names a third-party company, Next Reason, as a migration specialist alternative, with a free self-service option and paid full-service packages, though this is a separate commercial arrangement from Akamai's own services, not interchangeable with it.

## Common errors and what they actually mean

A few specific error situations worth knowing, since they can be misleading at first glance:

- **"Incorrect username or password" for every single user**, even ones you know have correct passwords, usually isn't a real credentials problem. It's a sign that the sign-in setup and the underlying user database it's pointed at don't match up.
- A generic "forbidden" error on a setup or configuration call usually means the access token used to make that call has expired, not a permissions problem.
- A redirect that doesn't come back to your app correctly is almost always a mismatch between the exact web address configured in Janrain and the exact one your app is using, they have to match exactly, including whether it starts with https.

## Framework notes

These framework notes are for customers on Hosted Login. Since Hosted Login has no official SDK, integration there means pointing a standard, off-the-shelf OIDC library at Janrain's login endpoints, using the discovery document mentioned earlier so you don't have to type in every URL by hand. If the customer is on the JavaScript SDK instead, see the JavaScript SDK section above, none of the framework notes below apply to that product.

- **Node.js / Express**: works with a standard OIDC library. You'll still need to build your own basic session handling yourself (see Session handling above), since nothing does this for you automatically.
- **Next.js**: a generic sign-in setup should work, using the same standard OIDC approach. We could not find anyone who has actually done this and confirmed it works, so treat it as likely to work, not guaranteed, until tested.
- **Python (Flask, FastAPI, Django)**: same situation as Next.js, a standard OIDC library should work in principle, but we found no confirmed, real example of anyone doing this.
- One real example we did find: a small, independently-built plugin for Drupal websites that connects to Janrain this same standard way. It works, but it's not actively maintained, so it's more useful as proof this approach works at all than as something to copy directly.
