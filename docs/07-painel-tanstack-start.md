# 07 — Painel TanStack Start + DaisyUI (`frontend/`)

## Status

**Não iniciar até o `backend/` estar completo** (superagente + matrículas + QR + APIs).

---

## Stack do frontend

| Item | Escolha |
|------|---------|
| Framework | [TanStack Start](https://tanstack.com/start) |
| UI | React + TypeScript |
| Estilo | **Tailwind CSS 4** + **[daisyUI 5](https://daisyui.com)** |
| Roteamento | TanStack Router (integrado) |
| Dados | TanStack Query + `@supabase/supabase-js` |
| Auth | Supabase Auth via `createServerFn` |
| Tabelas densas | TanStack Table (opcional, com classes `table`) |
| QR `/porta` | `html5-qrcode` ou similar + layout daisyUI |
| Deploy | Vercel / Netlify / Cloudflare |

### Por que DaisyUI no FIT

- Integração oficial com **React + Vite** (mesma base do TanStack Start).
- Painel rápido: `card`, `table`, `btn`, `badge`, `modal`, `navbar`.
- Temas prontos + dark mode (`data-theme`).
- Bundle leve (CSS) — bom para PWA na recepção.

**Docs:** https://daisyui.com/docs/install/react/

---

## Instalação (quando iniciar `frontend/`)

```bash
cd frontend
npm create @tanstack/start@latest .
npm install tailwindcss@latest @tailwindcss/vite@latest daisyui@latest
npm install @supabase/supabase-js @tanstack/react-query
```

### CSS principal (`src/styles/app.css`)

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: fit --default, dark --prefersdark, corporate;
}
```

### Tema FIT (custom — opcional)

Cores alinhadas a academia/saúde (verde primário). Ajustar em `@plugin "daisyui/theme"` quando criar o projeto.

```css
@plugin "daisyui/theme" {
  name: "fit";
  default: true;
  prefersdark: false;
  color-scheme: light;
  --color-primary: oklch(55% 0.18 145);
  --color-primary-content: oklch(98% 0.01 145);
  --color-secondary: oklch(45% 0.08 250);
  --color-accent: oklch(70% 0.15 85);
  --color-base-100: oklch(99% 0.005 145);
  --color-base-200: oklch(96% 0.01 145);
  --color-base-content: oklch(25% 0.02 145);
}
```

Aplicar no root:

```tsx
<html lang="pt-BR" data-theme="fit">
```

---

## Estrutura prevista `frontend/`

```
frontend/
├── src/
│   ├── routes/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppNavbar.tsx      # navbar + drawer (mobile)
│   │   │   └── AppSidebar.tsx     # menu lateral
│   │   ├── ui/                    # wrappers reutilizáveis (classes daisyUI)
│   │   │   ├── KpiCard.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── DataTable.tsx
│   │   │   └── ConfirmModal.tsx
│   │   └── chat/
│   │       └── ChatBubble.tsx
│   ├── styles/
│   │   └── app.css                # tailwind + daisyUI + tema fit
│   └── utils/
│       └── supabase.ts
├── package.json
└── .env
```

---

## Mapa de componentes daisyUI por tela

| Tela FIT | Componentes daisyUI |
|----------|---------------------|
| **Login** | `card`, `input`, `btn btn-primary`, `alert` (erro) |
| **Dashboard** | `stats`, `card`, `badge` |
| **Conversas** | `chat chat-start` / `chat-end`, `avatar` |
| **Leads / CRM** | `table table-zebra`, `badge`, `dropdown` |
| **Planos / Horários** | `table`, `modal`, `form-control`, `input`, `btn` |
| **Agendamentos** | `table`, `badge` (status booking) |
| **Configurações** | `fieldset`, `textarea`, `toggle` |
| **Presença** | `table`, `stat` |
| **/porta** | `hero`, `alert` success/error, fullscreen minimal |

### `StatusBadge` — funil CRM

| `lead_status` | Classe sugerida |
|---------------|-----------------|
| `novo` | `badge badge-ghost` |
| `qualificado` | `badge badge-info` |
| `experimental` | `badge badge-warning` |
| `matriculado` | `badge badge-success` |
| `inadimplente` | `badge badge-error` |
| `perdido` | `badge badge-neutral` |

---

## Layout padrão

```tsx
// Exemplo estrutura — drawer + navbar (daisyUI)
<div className="drawer lg:drawer-open">
  <input id="fit-drawer" type="checkbox" className="drawer-toggle" />
  <div className="drawer-content flex flex-col">
    <AppNavbar />
    <main className="p-4 md:p-6 flex-1 bg-base-200">{children}</main>
  </div>
  <div className="drawer-side">
    <label htmlFor="fit-drawer" className="drawer-overlay" />
    <AppSidebar />
  </div>
</div>
```

---

## Autenticação (MVP)

```typescript
const fetchUser = createServerFn({ method: 'GET' }).handler(async () => {
  const supabase = getSupabaseServerClient()
  const { data } = await supabase.auth.getUser()
  return data.user ?? null
})
```

- Rotas protegidas: `beforeLoad` no TanStack Router
- Página login: card centralizado `max-w-sm mx-auto`

---

## Mapa de rotas

| Rota | Tela |
|------|------|
| `/login` | Login |
| `/` | Dashboard |
| `/conversas`, `/conversas/$id` | WhatsApp |
| `/leads` | CRM |
| `/planos`, `/horarios`, `/agendamentos` | Gestão |
| `/configuracoes` | Academia + agente |
| `/matriculas`, `/presenca` | Pós-backend Fase 3–4 |
| `/porta` | Leitor QR |

---

## Integração com `backend/`

| Ação | Onde |
|------|------|
| CRUD dados | Supabase (RLS) |
| Check-in QR | `POST backend/.../attendance/check-in` |
| Tema escuro | `toggle` + `data-theme="dark"` no `<html>` |

---

## Critérios de pronto (frontend)

- [ ] TanStack Start + Tailwind + daisyUI instalados
- [ ] Tema `fit` (ou `corporate`) aplicado em todas as páginas
- [ ] Layout drawer/navbar responsivo
- [ ] Dono vê só dados da sua `gym_id`
- [ ] `/porta` com feedback `alert-success` / `alert-error`

---

## Referências

- TanStack Start: https://tanstack.com/start/latest/docs/framework/react/overview
- daisyUI + React: https://daisyui.com/docs/install/react/
- daisyUI components: https://daisyui.com/components/
- Cores/temas: https://daisyui.com/docs/colors/
