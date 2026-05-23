# Exam Prep BD — Unified Platform Plan

## Vision

Combine three existing projects into a single Python-based educational platform for Bangladeshi government job aspirants:

| Project | What it brings |
|---|---|
| **examWebsite** | Exam system, question bank, anti-cheat, leaderboards — **core money-maker** |
| **cse-pro** | Lessons, flashcards, study timer, courses — **learning content** |
| **scrapper** | News aggregation, job scraping, AI enrichment — **traffic + stickiness** |

**Why it works**: Govt exam aspirants need current affairs (news) + study materials (lessons) + practice (exams) + job alerts. This covers the full funnel.

---

## Architecture

```
Next.js Web (Vercel) ──┐
Flutter Android (APK) ──┤── FastAPI (Python) ── PostgreSQL (Neon)
PWA (Vercel) ──────────┘     +                     + R2 Storage
                         APScheduler (scrapers)     + Redis (Upstash)
                         Inngest (background jobs)
                         Groq/Transformers (free AI)
```

---

## Zero-Budget Stack

| Layer | Service | Cost |
|---|---|---|
| Frontend | Vercel Hobby | $0 |
| Backend | Koyeb free or Render free | $0 |
| Database | Neon free (500MB) or Supabase free | $0 |
| File Storage | Cloudflare R2 (10GB) | $0 |
| Background Jobs | Inngest (50K/mo) | $0 |
| Domain | .xyz (~$1/yr) | ~$1/yr |
| AI | Groq free + HuggingFace Transformers | $0 |
| **Total** | | **$0/mo** |

---

## Monetization Strategy

| Tier | Price | Features |
|---|---|---|
| **Free** | $0 | News, **2 free exams/month (no result details)**, basic lessons, job listings, ads shown |
| **Premium** | ~৳199/mo (~$2) | Unlimited exams + full result analytics, model tests, detailed leaderboards, **proctored exam mode** (tab-switch detection, per-question timers, full-screen enforcement, auto-submit on violation), no ads |
| **Courses** | ৳200-1000 one-time | Recorded video courses |
| **Bookstore** | Per item | PDF study materials |
| **Ads** | AdSense/AdMob | On free tier pages |

**Payments**: SSLCommerz (bKash + Nagad + cards, single integration) for Bangladesh.

---

## ⚠️ Critical Risks

### Cold Starts Kill Trust
Koyeb/Render free tiers spin down after inactivity. A user starting a timed exam hitting a 30s cold start = lost trust.
- **Workaround**: Use a free keep-alive ping (cron-job.org, every 5 min) to keep the instance warm
- **Better fix**: Budget $7/mo for Koyeb Eco ($1.61) or Render Starter ($7) as soon as you have users

### Time Cost Is the Real Investment
Porting 3 codebases (JS/Dart → Python) is months of real work. The 16-week timeline is realistic but assumes consistent effort. The biggest cost isn't hosting — it's your hours.

### Free Tier Must Convert
5 free exams/month is too comfortable. Price-sensitive aspirants won't pay if they can get enough for free. Hard cap at **2 exams, no answer details, no leaderboard, ads everywhere**.

---

## SEO Strategy (Critical for Organic Growth)

News + jobs sections are the primary traffic drivers. Must be built for search from day one.

| Tactic | Where | Priority |
|---|---|---|
| SSR with proper meta tags | All pages | P0 |
| Bengali keyword targeting | News + lessons | P1 |
| JSON-LD structured data (JobPosting, Article) | Jobs + news | P1 |
| Sitemap.xml (auto-generated, updated on scrape) | News | P1 |
| RSS feed | News | P1 |
| AMP or fast mobile rendering | All | P2 |
| Category pages with H1/H2 hierarchy | News | P1 |
| Breadcrumb schema for deep pages | Exams + lessons | P2 |

---

## Database Schema (merged)

| Domain | Tables | Source |
|---|---|---|
| Users & Auth | `users`, `refresh_tokens`, `otp_codes` | examWebsite + cse-pro |
| Content | `topics`, `lessons`, `flashcards` | cse-pro |
| Content Structure | `folders`, `student_types`, `folder_access` | examWebsite |
| Exam System | `questions`, `mcq_options`, `exams`, `exam_questions`, `exam_attempts`, `student_answers` | examWebsite |
| News | `articles`, `sources`, `categories`, `tags`, `scrape_logs` | scrapper |
| Jobs | `job_circulars` | both |
| Commerce | `courses`, `enrollments`, `books`, `orders` | examWebsite |
| Blog | `blog_posts`, `comments` | examWebsite |
| Analytics | `activity_logs`, `article_views` | both |

---

## API Module Map (FastAPI)

| Module | Source | Endpoints |
|---|---|---|
| Auth | examWebsite + new | 6 |
| Users | examWebsite | 8 |
| Questions | examWebsite | 12 |
| Exams | examWebsite | 15 |
| Attempts | examWebsite | 10 |
| Lessons | cse-pro | 8 |
| Flashcards | cse-pro | 6 |
| Topics/Folders | both | 8 |
| News/Sources | scrapper | 15 |
| Jobs | both | 6 |
| Courses | examWebsite | 8 |
| Books/Store | examWebsite | 8 |
| Blog | examWebsite | 6 |
| Admin/Stats | all | 10 |
| Payments | new | 4 |

---

## Phased Timeline

| Phase | Duration | Deliverable | Success Metric | Revenue |
|---|---|---|---|---|
| **P0: Setup** | Week 1 | FastAPI project, DB schema, CI/CD, domain | Repo ready, DB deployed, CI passing | No |
| **P1: Auth + Core** | Week 2 | Auth, users, roles, basic frontend | 50 test accounts created | No |
| **P2: News Scraper** | Week 3-4 | News aggregation (port from scrapper) | **500 DAU** (reads), 10+ sources live, Google indexed | Ads |
| **P3: Lessons + Flashcards** | Week 5-6 | Study materials (port from cse-pro) | 200 weekly active learners | No |
| **P4: Exam System** | Week 7-10 | Full exam engine (port from examWebsite) | **100 premium signups**, 50% exam completion rate | Premium |
| **P5: Payments + Store** | Week 11-12 | SSLCommerz, subscriptions, bookstore, courses | 50 paid transactions, ৳10k+ revenue | **YES** |
| **P6: Mobile App** | Week 13-16 | Flutter Android app | 1,000 installs, 4+ star rating | **YES** |
| **P7: AI + Polish** | Ongoing | AI summaries, SEO, performance, analytics | 30% month-over-month traffic growth | Ads+ |

---

## Key Technical Decisions

| Decision | Choice | Why |
|---|---|---|
| ORM | SQLAlchemy 2.0 + Alembic | Mature, async, migrations |
| Auth | JWT (access 15min + refresh 7d) | Stateless, same as existing |
| HTML parsing | BeautifulSoup4 | Replaces Cheerio.js |
| Background | APScheduler + Inngest | Already in scrapper |
| Search | PostgreSQL FTS (tsvector) | Free, no external service |
| File upload | Cloudflare R2 presigned URLs | Free, zero egress |
| Caching | Upstash Redis (free 10MB) | Reduce DB load |
| Email | Resend (3K/mo free) | Transactional emails |
| Monitoring | Sentry (5K/mo free) | Error tracking |
| Scraper anti-abuse | Rotating user-agents, request delays (1-3s jitter), RSS-priority fallback chain, Playwright only as last resort | BD news sites (Prothom Alo, Daily Star, bdnews24) actively block scrapers |
| Anti-cheat (exam) | Tab-switch detection (blur → warning → auto-submit), question randomization, per-question time limits, full-screen enforcement | Key premium differentiator — call out in marketing |

---

## Frontend Strategy

Keep existing Next.js frontend from `examWebsite/frontend/`:
- shadcn/ui, Tailwind dark theme, Zustand state
- Role-based dashboards (Admin/Teacher/Student)
- Update API client to hit new Python backend
- Add news + study materials sections

## Mobile Strategy

Use `examWebsite/student_mobile/` Flutter app as base:
- Refactor API layer to new Python backend
- Add news feed + study screens
- Android APK distribution (no Play Store cost)
