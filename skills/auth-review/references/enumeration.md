# Entrypoint Enumeration

Find **every** externally- or semi-externally-reachable handler. Miss one and the review is incomplete. Most real repos mix several frameworks — check them all.

## Process

1. Read root manifests (`package.json`, `pyproject.toml`, `go.mod`, `Gemfile`, `pom.xml`, `*.csproj`, etc.) to identify all frameworks in use.
2. Apply every relevant pattern below. Grep then read each match to confirm it is a handler.
3. Reconcile against central router files, OpenAPI/Swagger specs, GraphQL schemas, and tests. Divergences from the spec are themselves findings.
4. Record each entrypoint in the Endpoint Inventory.

## HTTP / REST by stack

### JavaScript / TypeScript

| Stack | Detection |
|-------|-----------|
| Express / Koa / Connect | `app\.(get\|post\|put\|patch\|delete\|all\|use)\(`, `router\.(get\|post\|...)\(` |
| Fastify | `fastify\.(get\|post\|route)\(`, `\.register\(` |
| Hapi | `server\.route\(`, `{ method:` |
| NestJS | `@(Get\|Post\|Put\|Patch\|Delete\|All)\(`, `@Controller\(` |
| Next.js pages | files under `pages/api/**`, default export |
| Next.js app | `route.(ts\|js)` files, exported `GET`/`POST`/etc. |
| Server Actions | `'use server'` directive, exported async functions |
| tRPC | `\.(query\|mutation)\(`, `publicProcedure`, `protectedProcedure` |
| Remix / SvelteKit | `loader`/`action` exports, `+server.ts` files |
| Hono | `app\.(get\|post\|...)\(` |

### Python

| Stack | Detection |
|-------|-----------|
| Flask | `@app\.route\(`, `@blueprint\.route\(`, `add_url_rule\(` |
| FastAPI | `@app\.(get\|post\|...)\(`, `@router\.(get\|...)\(`, `APIRouter` |
| Django | `urls.py` — `path\(`, `re_path\(`; class-based views |
| DRF | `@api_view\(`, `ViewSet`, `permission_classes =` |
| Starlette / Tornado | `Route\(`, `Mount\(`, `Application([(r"..."` |

### Go

| Stack | Detection |
|-------|-----------|
| net/http / gorilla | `http\.HandleFunc\(`, `mux\.Handle(Func)?\(`, `r\.HandleFunc\(` |
| chi | `r\.(Get\|Post\|Put\|Patch\|Delete\|Handle)\(`, `r\.Mount\(` |
| gin / echo / fiber | `router\.(GET\|POST\|...)\(`, `e\.(GET\|POST\|...)\(`, `app\.(Get\|Post\|...)\(` |

### Ruby / Java / .NET / PHP / Elixir / Rust

| Stack | Detection |
|-------|-----------|
| Rails | `config/routes.rb` — `resources`, `resource`, `get`, `match`, `namespace`, `mount` |
| Sinatra / Grape | `(get\|post\|...)\s+['"]`, `class \w+ < Grape::API` |
| Spring | `@(Get\|Post\|Put\|Patch\|Delete\|Request)Mapping\(`, `@RestController` |
| JAX-RS / Ktor / Micronaut | `@(GET\|POST\|...)`, `routing { ... }`, `@Controller\(` |
| ASP.NET | `\[Http(Get\|Post\|...)\]`, `\[Route\(`, `app\.Map(Get\|Post\|...)\(` |
| Laravel / Symfony | `Route::(get\|post\|...)\(`, `#\[Route\(` |
| Phoenix | `router.ex` — `get`, `post`, `scope`, `pipe_through` |
| Axum / Actix | `Router::new\(\)\.route\(`, `web::(get\|post\|...)\(` |

## Non-HTTP entrypoints (often missed)

### GraphQL

Extract every field under `Query`, `Mutation`, `Subscription` from `*.graphql`/`*.gql`/schema TS. Find resolver registrations: `resolvers = { Query: { ... } }`, `@Resolver`, `@Query`, `@Mutation`, `field :name, resolve:` (graphql-ruby), `Field(...)` (Hot Chocolate). **Treat each resolver as an endpoint** — teams often protect the `/graphql` route but forget per-resolver authz.

### WebSocket / real-time

`new WebSocketServer`, `ws.on('connection'`, `@SubscribeMessage\(` (Nest gateways), Socket.IO `io.on('connection', socket.on(`, ActionCable channels, Phoenix Channels. Connection auth is often present; per-message authz often is not.

### RPC / gRPC / tRPC

`.proto` service definitions (each `rpc` is an endpoint), `@GrpcMethod\(`, `server.addService\(`. tRPC procedures as above.

### Serverless

AWS Lambda: `exports.handler`, `def lambda_handler`, `serverless.yml` functions, SAM/CDK function definitions. Vercel/Netlify: `api/**`, `netlify/functions/**`. Cloudflare Workers: `export default { fetch(`.

### Background jobs / webhooks

Often process attacker-controlled data (uploads, webhook payloads) without authz. Enumerate:

- Queues: BullMQ `new Worker\(`, Sidekiq `include Sidekiq::Job`, Celery `@task`, AWS SQS consumers, `@KafkaListener`.
- Scheduled: cron, `@Scheduled`, APScheduler, Rails `ActiveJob`, Quartz.
- Webhooks: check for signature verification — or its absence.

### Admin / debug surfaces

Django `management/commands/`, Rails `lib/tasks/*.rake`, internal HTTP wrappers, `/debug`, `/admin`, `/internal`, `/actuator`, `/metrics` — sometimes exposed unintentionally.

## Middleware / guard inventory

Record auth plumbing separately; Phase 2 needs it.

- Global chains: Express `app.use\(`, Django `MIDDLEWARE =`, Rails `config.middleware`, Spring `SecurityFilterChain`, ASP.NET `app.Use*`.
- Per-route: `@UseGuards\(`, `@PreAuthorize\(`, `@Secured\(`, `before_action :authenticate`, `[Authorize]`, `permission_classes = [...]`, `authorize!`, `can?`.
- Gateway / proxy: `nginx.conf`, `Caddyfile`, API Gateway, Envoy, Traefik, Kong plugins — may enforce or bypass auth outside the app.

## Completeness check

Before ending Phase 1:

- [ ] Every framework from manifests has been searched with its patterns.
- [ ] Every route in a central router file is in the inventory.
- [ ] Every OpenAPI/Swagger path maps to a handler (and vice versa — undocumented handlers are notable).
- [ ] GraphQL, WebSocket, gRPC, serverless, and queue handlers each have rows.
- [ ] `auth required? = unknown` is used when unclear — do not guess.
